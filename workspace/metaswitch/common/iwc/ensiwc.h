
#ifndef __ENSICC_INCLUDED
#define __ENSICC_INCLUDED

#include <stdint.h>
#include <pthread.h>
#include <semaphore.h>

class ENSIwc
{
public:
  ENSIwc(bool host=false, int container_ns=0, int host_ns=0);
  ~ENSIwc();

  bool push(int i);
  int pop();

private:

  struct RingBuffer
  {
    int key;
    pthread_spinlock_t lock;
    sem_t sem_work;
    int64_t read;
    int64_t write;
    int buffer[1024];
  };

  // IPC namespaces for the container and the host.  These should only be
  // needed if the class is instantiated in the host.
  bool _host;
  int _container_ns;
  int _host_ns;

  // Shared memory reference.  These are always in the container namespace.
#ifdef POSIX
  int _shmfd;
#else
  int _shmid;
#endif
  RingBuffer* _shm;
};

#endif
