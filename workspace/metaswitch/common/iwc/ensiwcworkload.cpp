#include <memory.h>
#include <sys/shm.h>
#include "enslog.h"
#include "ensiwcshm.h"
#include "ensiwcworkload.h"

ENSIWCWorkload::ENSIWCWorkload(int id, size_t qsize, size_t memsize) :
  _id(id),
  _qsize(qsize),
  _memsize(memsize)
{
}

ENSIWCWorkload::~ENSIWCWorkload()
{
  stop();
}

bool ENSIWCWorkload::start()
{
  // Calculate the required shared memory space.
  size_t smhdrsize = sizeof(ENSIWCSMHdr);
  size_t iwcqmemsize = ENSIWCQ<ENSIWCMsg>::mem_size(_qsize);
  size_t memsize = smhdrsize + 2 * iwcqmemsize + _memsize;

  // Create the shared memory within the container IPC namespace.
  if ((_shmid = shmget(_id, memsize, IPC_CREAT | 0666)) < 0)
  {
    LOG_ERROR("Failed to create shared memory");
    return false;
  }

  _shm = shmat(_shmid, NULL, 0);
  if (_shm == (void*)-1)
  {
    LOG_ERROR("Failed to map shared section");
    _shm = NULL;
    return false;
  }

  ENSIWCSMHdr* hdr = (ENSIWCSMHdr*)_shm;
  hdr->in_offset = smhdrsize;
  hdr->out_offset = smhdrsize + iwcqmemsize;
  hdr->pool_offset = smhdrsize + 2 * iwcqmemsize;

  _in.init(((char*)_shm) + hdr->in_offset, _qsize);
  _out.init(((char*)_shm) + hdr->out_offset, _qsize);
  _pool.init(((char*)_shm) + hdr->pool_offset, _memsize, 128);

  return true;
}

void ENSIWCWorkload::stop()
{
  if (_shm != NULL)
  {
    shmdt(_shm);
    _shm = NULL;
  }
}

bool ENSIWCWorkload::recv(ENSIWCMsg& msg)
{
  return _in.pop(msg);
}

bool ENSIWCWorkload::send(ENSIWCMsg& msg)
{
  return _out.push(msg);
}

ENSIWCMem::Handle ENSIWCWorkload::alloc(size_t length)
{
  return _pool.alloc(length);
}

void ENSIWCWorkload::free(ENSIWCMem::Handle handle)
{
  _pool.free(handle);
}
