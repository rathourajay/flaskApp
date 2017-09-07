#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
#include <pthread.h>
#include <errno.h>
#include <sys/shm.h>
#include <semaphore.h>
#include <sched.h>
#include "ensiwc.h"

ENSIwc::ENSIwc(bool host, int container_ns, int host_ns) :
  _host(host),
  _container_ns(container_ns),
  _host_ns(host_ns),
  _shmid(0),
  _shm(NULL)
{
  printf("Creating ENSIwc in %s mode\n", host ? "host" : "container");
  if (!_host)
  {
    // Create the shared memory within the container IPC namespace.
    if ((_shmid = shmget(1235, sizeof(RingBuffer), IPC_CREAT | 0666)) < 0)
    {
      printf("Failed to create shared memory\n");
      return;
    }

    _shm = (RingBuffer*)shmat(_shmid, NULL, 0);
    if (_shm == (RingBuffer*)-1)
    {
      printf("Failed to map shared section\n");
      _shm = NULL;
      return;
    }

    _shm->write = 0;
    _shm->read = 0;
    pthread_spin_init(&_shm->lock, PTHREAD_PROCESS_SHARED);
    sem_init(&_shm->sem_work,1,0);
    printf("Created container resources, write = %ld, read = %ld\n", _shm->write, _shm->read);
  }
  else
  {
    // In host namespace, so switch to container namespace and open shared
    // memory.
    if (setns(_container_ns, 0) != -1)
    {
      if ((_shmid = shmget(1235, 0, 0666)) >= 0)
      {
        _shm = (RingBuffer*)shmat(_shmid, NULL, 0);
        if (_shm == (RingBuffer*)(-1))
        {
          printf("Failed to map shared memory (%d), shmid=%d, shm=%p\n", errno, _shmid, _shm);
          _shm = NULL;
        }
      }
      else
      {
        printf("Failed to open shared memory (%d), shmid=%d", errno, _shmid);
      }
      setns(_host_ns, 0);
    }
    else
    {
      printf("Failed to link to container namespace (%d)\n", errno);
    }
    if (_shm)
    {
      printf("Host linked to container ring buffer, key= %d, write = %ld, read = %ld\n", _shm->key, _shm->write, _shm->read);
    }
    else
    {
      printf("Failed to link to container ring buffer\n");
    }
  }
}

ENSIwc::~ENSIwc()
{
}

bool ENSIwc::push(int i)
{
  bool rc = false;
  if (_shm != NULL)
  {
    pthread_spin_lock(&_shm->lock);
    if (_shm->write < _shm->read + sizeof(_shm->buffer))
    {
      printf("Write to buffer %d => buffer[%ld]\n", i, _shm->write);
      _shm->buffer[(_shm->write++) % sizeof(_shm->buffer)] = i;
      sem_post(&_shm->sem_work);
      rc = true;
    }
    pthread_spin_unlock(&_shm->lock);
  }
  return rc;
}

int ENSIwc::pop()
{
  int i = -1;
  if (_shm != NULL)
  {
    printf("pop - wait for work\n");
    sem_wait(&_shm->sem_work);
    pthread_spin_lock(&_shm->lock);
    if (_shm->read < _shm->write)
    {
      i = _shm->buffer[(_shm->read++) % sizeof(_shm->buffer)];
      printf("Read from buffer %d <= buffer[%ld]\n", i, _shm->read - 1);
    }
    pthread_spin_unlock(&_shm->lock);
  }
  return i;
}
