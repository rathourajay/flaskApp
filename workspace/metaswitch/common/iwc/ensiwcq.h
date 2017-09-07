
#ifndef ENSIWCQ_H__
#define ENSIWCQ_H__

#include <stdio.h>
#include <pthread.h>
#include <time.h>
#include <semaphore.h>
#include <errno.h>
#include <vector>

// Template for implementing in-memory queues used for message passing.
// The queues may be embedded in shared memory, so cannot use pointers.
template <class T>
class ENSIWCQ
{
public:
  static size_t mem_size(size_t qsize)
  {
    return sizeof(RingBuf) + sizeof(T) * (qsize - 1);
  }

  ENSIWCQ() :
    _q(NULL)
  {
  }

  ~ENSIWCQ()
  {
  }

  void init(char* mem, size_t qsize)
  {
    _q = (RingBuf*)mem;
    pthread_spin_init(&_q->lock, PTHREAD_PROCESS_SHARED);
    sem_init(&_q->sem_work,1,0);
    _q->qsize = qsize;
    _q->write = 0;
    _q->read = 0;
    _q->waiters = 0;
    _q->term = false;
  }

  void join(char* mem)
  {
    _q = (RingBuf*)mem;
  }

  void terminate()
  {
    if (_q)
    {
      pthread_spin_lock(&_q->lock);
      _q->term = true;
      int waiters = _q->waiters;
      _q->waiters = 0;
      pthread_spin_unlock(&_q->lock);
      for (int ii = 0; ii < waiters; ii++)
      {
        sem_post(&_q->sem_work);
      }
    }
  }

  bool push(const T& v)
  {
    bool rc = false;

    if ((_q != NULL) && (!_q->term))
    {
      bool post = false;
      pthread_spin_lock(&_q->lock);
      if (_q->write < _q->read + _q->qsize)
      {
        _q->buffer[(_q->write++) % _q->qsize] = v;
        if (_q->waiters > 0)
        {
          post = true;
        }
        rc = true;
      }
      pthread_spin_unlock(&_q->lock);

      if (post)
      {
        sem_post(&_q->sem_work);
      }
    }
    return rc;
  }

  bool pop(T& v, int timeout_ms=-1)
  {
    bool rc = false;
    struct timespec at = {0,0};

    if ((_q != NULL) && (!_q->term))
    {
      // Timeout specified, so calculate the appropriate absolute timeout time.
      if (timeout_ms > 0)
      {
        clock_gettime(CLOCK_REALTIME, &at);
        at.tv_sec += timeout_ms / 1000;
        at.tv_nsec += ((timeout_ms % 1000) * 1000000);
        if (at.tv_nsec >= 1000000000)
        {
          at.tv_nsec -= 1000000000;
          at.tv_sec += 1;
        }
      }

      pthread_spin_lock(&_q->lock);
      bool timedout = false;

      while ((!_q->term) &&
             (!timedout) &&
             (_q->read == _q->write))
      {
        _q->waiters++;
        pthread_spin_unlock(&_q->lock);
        if (timeout_ms >= 0)
        {
          // Timeout is specified, so wait at most for the specified time.
          timedout = (sem_timedwait(&_q->sem_work, &at) < 0) && (errno == ETIMEDOUT);
        }
        else
        {
          // Wait indefinitely.
          sem_wait(&_q->sem_work);
        }
        pthread_spin_lock(&_q->lock);
        _q->waiters--;
      }

      if ((!_q->term) && (!timedout) && (_q->read < _q->write))
      {
        v = _q->buffer[(_q->read++) % _q->qsize];
        rc = true;
      }
      pthread_spin_unlock(&_q->lock);
    }
    return rc;
  }

#ifdef UNITTEST
  static bool unit_test()
  {
    char* mem = (char*)malloc(mem_size(10));

    ENSIWCQ<T> q;
    q.init(mem, 10);

    printf("ENSIWCQ::unit_test (1) : Basic push/pop tests ... ");

    for (int ii = 0; ii < 100; ii++)
    {
      if (!q.push(ii))
      {
        printf("Push %d failed\n", ii);
        return false;
      }
      int jj;
      if (!q.pop(jj))
      {
        printf("Pop %d failed\n", ii);
        return false;
      }
      if (jj != ii)
      {
        printf("Pop returned unexpected value - expected %d returned %d\n", ii, jj);
        return false;
      }
    }

    if (!q.push(101))
    {
      printf("Push 101 failed\n");
      return false;
    }

    if (!q.push(102))
    {
      printf("Push 102 failed\n");
    }

    int jj;
    if ((!q.pop(jj, 0)) || (jj != 101))
    {
      printf("Pop 101 (zero timeout) failed\n");
      return false;
    }

    if ((!q.pop(jj, 100)) || (jj != 102))
    {
      printf("Pop 102 (100ms timeout) failed\n");
      return false;
    }

    if (q.pop(jj, 0))
    {
      printf("Pop with empty queue and zero timeout succeeded\n");
      return false;
    }

    if (q.pop(jj, 1000))
    {
      printf("Pop with empty queue and 100ms timeout succeeded\n");
      return false;
    }

    printf("Passed\n");

    printf("ENSIWCQ::unit_test (2) : Overflow ... ");

    for (int ii = 0; ii < 10; ii++)
    {
      if (!q.push(ii))
      {
        printf("Push %d failed\n", ii);
        return false;
      }
    }
    if (q.push(11))
    {
      printf("Push succeeded when queue should be full\n");
      return false;
    }

    for (int ii = 0; ii < 10; ii++)
    {
      int jj;
      q.pop(jj);
    }

    printf("Passed\n");

    printf("ENSIWCQ::unit_test (3) : Push/pop from separate threads ... ");

    pthread_t tid;
    pthread_create(&tid, 0, &ENSIWCQ<T>::thread_func1, (void*)&q);

    for (int ii = 0; ii < 100; ii++)
    {
      int jj;
      if (!q.pop(jj))
      {
        printf("Pop %d failed\n", ii);
        return false;
      }
      if (jj != ii)
      {
        printf("Pop returned unexpected value - expected %d returned %d\n", ii, jj);
        return false;
      }
    }
    void* res;
    pthread_join(tid, &res);

    printf("Passed\n");

    printf("ENSIWCQ::unit_test (4) : Performance test ... ");

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    for (int ii = 0; ii < 100000; ii++)
    {
      int jj;
      q.push(ii);
      q.pop(jj);
    }
    clock_gettime(CLOCK_MONOTONIC, &end);
    int64_t elapsed = (int64_t)(end.tv_sec - start.tv_sec) * (int64_t)1000000000 + (int64_t)(end.tv_nsec - start.tv_nsec);

    printf("Passed (total time = %ld ns, per push/pop = %ld ns)\n", elapsed, elapsed/100000);
    //printf("(Start = %ld.%9.9ld, end = %ld.%9.9ld)\n", start.tv_sec, start.tv_nsec, end.tv_sec, end.tv_nsec);

    printf("ENSIWCQ::unit_test (5) : Termination ... ");

    std::vector<pthread_t> tids(5);
    for (int ii = 0; ii < 5; ii++)
    {
      pthread_create(&tids[ii], 0, &ENSIWCQ<T>::thread_func2, (void*)&q);
    }

    q.terminate();

    for (int ii = 0; ii < 5; ii++)
    {
      void* res;
      pthread_join(tids[ii], &res);
      if (res != (void*)false)
      {
        printf("Terminated waiter returned true\n");
        return false;
      }
    }

    printf("Passed\n");

    return true;
  }
#endif

private:

#ifdef UNITTEST
  static void* thread_func1(void* p)
  {
    ENSIWCQ<T>* q = (ENSIWCQ<T>*)p;

    for (int ii = 0; ii < 100; ii++)
    {
      while (!q->push(ii))
      {
        struct timespec target = {0, 1000};
        clock_nanosleep(CLOCK_MONOTONIC, 0, &target, NULL);
      }
    }
    return NULL;
  }

  static void* thread_func2(void* p)
  {
    ENSIWCQ<T>* q = (ENSIWCQ<T>*)p;
    int jj;
    bool rc = q->pop(jj);
    return (void*)rc;
  }
#endif

  typedef struct
  {
    // Terminated flag.
    bool term;

    // Spin-lock used to protect access to the ring buffer.
    pthread_spinlock_t lock;

    // Semaphore used to signal to readers when there are items waiting on the
    // queue.
    sem_t sem_work;

    // Count of threads waiting on the semaphore.
    int waiters;

    // Read/write pointers.  These are 64-bit integers and monotonically
    // increasing to remove the need to handle wrap-around.
    int64_t read;
    int64_t write;

    // Ring buffer.
    size_t qsize;
    T buffer[1];

  } RingBuf;

  RingBuf* _q;
};

#endif
