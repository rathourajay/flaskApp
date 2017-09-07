#include <stdio.h>
#include <string.h>
#include <memory.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <sys/shm.h>
#include <sys/uio.h>

#include "enslog.h"
#include "ensiwcshm.h"
#include "ensiwcdispatcher.h"


ENSIWCDispatcher::ENSIWCDispatcher(int host_ns) :
  _host_ns(host_ns),
  _workloads()
{
  pthread_spin_init(&_lock, PTHREAD_PROCESS_SHARED);
}

ENSIWCDispatcher::~ENSIWCDispatcher()
{
}

bool ENSIWCDispatcher::start()
{
  return true;
}

void ENSIWCDispatcher::stop()
{
}

bool ENSIWCDispatcher::connect_workload(int id, int port, int container_ns)
{
  LOG_INFO("Connect new workload, id=%d, port=%d", id, port);
  Workload* w = new Workload(id, port, _host_ns, container_ns);
  LOG_DEBUG("Workload object created (%p)", w);

  pthread_spin_lock(&_lock);
  _workloads[id] = w;
  pthread_spin_unlock(&_lock);

  LOG_DEBUG("Starting workload");
  if (!w->start())
  {
    LOG_ERROR("Failed to start workload");
    w->stop();
    pthread_spin_lock(&_lock);
    _workloads.erase(id);
    delete w;
    pthread_spin_unlock(&_lock);
    return false;
  }

  LOG_INFO("Workload connected");
  return true;
}

void ENSIWCDispatcher::disconnect_workload(int id)
{
  LOG_INFO("Disconnect workload %d", id);
  pthread_spin_lock(&_lock);
  Workload* w = _workloads[id];

  if (w != NULL)
  {
    pthread_spin_unlock(&_lock);
    w->stop();
    pthread_spin_lock(&_lock);
    _workloads.erase(id);
    delete w;
  }
  pthread_spin_unlock(&_lock);
}

ENSIWCDispatcher::Workload::Workload(int id, int port, int host_ns, int container_ns) :
  _id(id),
  _running(false),
  _client_thread(0),
  _port(port),
  _host_ns(host_ns),
  _container_ns(container_ns),
  _shmid(0),
  _shm(NULL)
{
}

ENSIWCDispatcher::Workload::~Workload()
{
  stop();
}

bool ENSIWCDispatcher::Workload::start()
{
  // Open the shared memory interface to the workload.
  LOG_INFO("Connecting to shared memory");
  if (!connect_workload())
  {
    // Shared memory isn't yet up, so sleep briefly to give to workload a
    // second chance.
    sleep(1);
    if (!connect_workload())
    {
      LOG_ERROR("Failed to connect to workload shared memory");
      return false;
    }
  }

  // Open the specified port for listening.
  LOG_INFO("Create listening socket");
  if (!open_bind_socket())
  {
    LOG_ERROR("Failed to create listening socket");
    return false;
  }

  // Start a thread to process messages from the client and workload.
  _running = true;
  if (pthread_create(&_client_thread, NULL, &client_thread, (void*)this) < 0)
  {
    return false;
  }

  return true;
}

void ENSIWCDispatcher::Workload::stop()
{
  LOG_INFO("Stopping workload %d", _id);
  _running = false;

  // Stop the threads.
  if (_client_thread)
  {
    void* res;
    LOG_DEBUG("Wait for client thread to terminate");
    pthread_join(_client_thread, &res);
    LOG_DEBUG("Client thread terminated");
  }

  // Disconnect from the workload.
  LOG_DEBUG("Disconnecting from workload shared memory");
  disconnect_workload();

  // Close the socket.
  LOG_DEBUG("Close socket");
  close_socket();
}

void* ENSIWCDispatcher::Workload::client_thread(void* p)
{
  ((ENSIWCDispatcher::Workload*)p)->client_loop();
  return NULL;
}

typedef struct
{
  uint32_t length;
  uint32_t id;
} NetMsg;

void ENSIWCDispatcher::Workload::client_loop()
{
  LOG_INFO("Starting client loop for workload %d", _id);
  NetMsg nmsg;
  struct iovec iov[2];
  iov[0].iov_base = &nmsg;
  iov[0].iov_len = sizeof(nmsg);

  while (_running)
  {
    // Issue a listen on the socket.
    int rc = ::listen(_so, 20);
    if (rc != 0)
    {
      LOG_ERROR("Listen failed");
      return;
    }

    // Set the maximum time to wait for a connection to 5 seconds.
    struct timeval timeout;
    timeout.tv_sec = 5;
    timeout.tv_usec = 0;
    if (setsockopt(_so, SOL_SOCKET, SO_RCVTIMEO, (char *)&timeout, sizeof(timeout)) < 0)
    {
      LOG_ERROR("setsockopt failed (%d)", errno);
      return;
    }

    sockaddr_in addr;
    socklen_t inane = sizeof(addr);
    LOG_DEBUG("Waiting for client to connect");
    int in_so = ::accept(_so, (struct sockaddr *)&addr, &inane);
    if (in_so < 0)
    {
      if (errno != EAGAIN)
      {
        LOG_ERROR("accept failed (%d)", errno);
      }
      return;
    }

    // Receive and respond to the handshake message from the client.
    LOG_DEBUG("Client connected, wait for handshake");
    size_t len = ::recv(in_so, &nmsg, sizeof(nmsg), MSG_WAITALL);
    if ((nmsg.length != 0) &&
        (nmsg.id != htonl(1)))
    {
      LOG_ERROR("Badly formed handshake");
      return;
    }
    nmsg.length = 0;
    ::send(in_so, &nmsg, sizeof(nmsg), 0);
    LOG_INFO("Client connected and handshake complete");

    // Send a session start message to the workload.
    ENSIWCMsg msg;
    msg.msg_id = MSG_SESSION_START;
    _in.push(msg);

    // Loop processing requests from the client.
    while (_running)
    {
      struct timespec start, end;

      // Read a message header from the client.
      LOG_DEBUG("Waiting for data");
      len = ::recv(in_so, &nmsg, sizeof(nmsg), MSG_WAITALL);
      clock_gettime(CLOCK_MONOTONIC, &start);

      if (len != sizeof(nmsg))
      {
        // Connection has been broken.
        break;
      }

      LOG_DEBUG("Received data, length %d", (int)ntohl(nmsg.length));

      // Received the start of a message, so allocate memory from the workload
      // buffer pool and receive the data into it.
      msg.msg_id = MSG_EVENT;
      msg.length = (size_t)ntohl(nmsg.length);
      msg.data = _pool.alloc(msg.length);
      LOG_DEBUG("Allocated shared memory, handle=%d", msg.data);
      len = ::recv(in_so, _pool.mem(msg.data), msg.length, MSG_WAITALL);
      LOG_DEBUG("Received all data for message");

      if (len != msg.length)
      {
        // Connection has been broken.
        break;
      }

      // Received the full message, so pass it to the workload.
      LOG_DEBUG("Pushing data to workload");
      _in.push(msg);
      LOG_DEBUG("Pushed data to workload");

      // Wait for the response from the workload.
      LOG_DEBUG("Waiting for response from workload");
      _out.pop(msg);
      LOG_DEBUG("Received response from workload");

      // Send the response.  Use writev to write the header and data in
      // a single operation.
      nmsg.length = htonl((uint32_t)msg.length);
      nmsg.id = 0;
      iov[1].iov_base = _pool.mem(msg.data);
      iov[1].iov_len = msg.length;
      LOG_DEBUG("Sending response");
      ::writev(in_so, iov, 2);
      LOG_DEBUG("Sent response");
      clock_gettime(CLOCK_MONOTONIC, &end);
      int64_t elapsed = (int64_t)(end.tv_sec - start.tv_sec) * (int64_t)1000000000 + (int64_t)(end.tv_nsec - start.tv_nsec);
      LOG_INFO("Event processing completed, elapsed time %ld ns", elapsed);

      // Free the shared memory holding the response.
      _pool.free(msg.data);
    }
    LOG_INFO("Client disconnected");
    ::close(in_so);

    // Send a session stopped message to the workload.
    //msg.msg_id = MSG_SESSION_STOP;
    //_in.push(msg);

    // Send a workload terminated message to the workload.
    msg.msg_id = MSG_WORKLOAD_TERM;
    _in.push(msg);
  }

  return;
}

bool ENSIWCDispatcher::Workload::connect_workload()
{
  // Switch to the workload namespace and connect to the workload shared memory.
  if (setns(_container_ns, 0) != -1)
  {
    if ((_shmid = shmget(_id, 0, 0666)) >= 0)
    {
      _shm = (void*)shmat(_shmid, NULL, 0);
      if (_shm == (void*)(-1))
      {
        _shm = NULL;
      }
    }
    setns(_host_ns, 0);
  }

  if (!_shm)
  {
    // Failed to connect to the shared memory.
    return false;
  }

  // Fix up pointers to the queues and memory pool.
  ENSIWCSMHdr* smhdr = (ENSIWCSMHdr*)_shm;
  _in.join(((char*)_shm) + smhdr->in_offset);
  _out.join(((char*)_shm) + smhdr->out_offset);
  _pool.join(((char*)_shm) + smhdr->pool_offset);

  return true;
}

void ENSIWCDispatcher::Workload::disconnect_workload()
{
  if (_shm != NULL)
  {
    // Switch to the workload namespace and disconnect from the workload shared memory.
    if (setns(_container_ns, 0) != -1)
    {
      shmdt(_shm);
      setns(_host_ns, 0);
      _shm = NULL;
    }
  }
}

bool ENSIWCDispatcher::Workload::open_bind_socket()
{
  int rc;
  struct sockaddr_in addr;

  if ((_so = ::socket(AF_INET, SOCK_STREAM, 0)) == -1)
  {
    return false;
  }

  int reuse = 1;
  rc = ::setsockopt(_so, SOL_SOCKET, SO_REUSEADDR, (const char*)&reuse, sizeof(reuse));
  if (rc < 0)
  {
    return false;
  }

  memset(&addr, 0, sizeof(addr));
  addr.sin_family = AF_INET;
  addr.sin_port = htons(_port);

  rc = ::bind(_so, (struct sockaddr *)&addr, sizeof(addr));

  if (rc != 0)
  {
    return false;
  }

  return true;
}

void ENSIWCDispatcher::Workload::close_socket()
{
  if (_so)
  {
    ::close(_so);
    _so = 0;
  }
}
