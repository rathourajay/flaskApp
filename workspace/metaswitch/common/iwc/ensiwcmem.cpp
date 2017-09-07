#include <stdio.h>
#include <vector>
#include <pthread.h>
#include <time.h>
#include "ensiwcmem.h"

ENSIWCMem::ENSIWCMem() :
  _pool(NULL)
{
}

ENSIWCMem::~ENSIWCMem()
{
}

void ENSIWCMem::init(char* mem, int32_t size, int32_t min_size)
{
  join(mem);

  pthread_spin_init(&_pool->lock, PTHREAD_PROCESS_SHARED);
  _pool->size = scale(size - sizeof(mpool));
  _pool->min_size = scale(min_size);

  // Set up the root block.
  b_next(0) = 1;
  b_prev(0) = 1;
  b_next_free(0) = 1;
  b_prev_free(0) = 1;

  // Set up a single block covering the rest of the memory in the pool.
  b_next(1) = 0;
  b_prev(1) = 0;
  b_next_free(1) = 0;
  b_prev_free(1) = 0;
}

void ENSIWCMem::join(char* mem)
{
  _pool = (mpool*)mem;
}

ENSIWCMem::Handle ENSIWCMem::alloc(size_t size)
{
  // Scale the size to the units understood by the allocator.
  size = scale(size);

  pthread_spin_lock(&_pool->lock);

  // Loop through the free list until we find a large enough block or
  // get back to the root.
  Handle free = b_next_free(0);
  while (free)
  {
#if 1
    // If the block isn'yt big enough, try and join with subsequent free ones
    // to get one that is large enough.
    while ((b_size(free) < (int32_t)size) &&
           (b_is_free(b_next(free))))
    {
      join_blocks(free, b_next(free));
    }
#endif

    if (b_size(free) >= (int32_t)size)
    {
      // Found a large enough block, so remove it from the free list.
      b_next_free(b_prev_free(free)) = b_next_free(free);
      b_prev_free(b_next_free(free)) = b_prev_free(free);
      b_next_free(free) = -1;
      b_prev_free(free) = -1;

      // Split the block if it makes sense.
      split_block(free, size);

      // Return the allocated free block.
      break;
    }

    free = b_next_free(free);
  }

  pthread_spin_unlock(&_pool->lock);

  return free;
}


void ENSIWCMem::free(Handle free)
{
  if ((free > 0) && (free < _pool->size) && (b_next_free(free) == -1))
  {
    // Block is valid, so free it.
    pthread_spin_lock(&_pool->lock);

    // Add the block to the head of the free list
    b_next_free(free) = b_next_free(0);
    b_prev_free(free) = 0;
    b_prev_free(b_next_free(0)) = free;
    b_next_free(0) = free;

    // Check whether the block can be combined with free blocks either side.
#if 0
    while (b_is_free(b_next(free)))
    {
      join_blocks(free, b_next(free));
    }
    while (b_is_free(b_prev(free)))
    {
      free = b_prev(free);
      join_blocks(free, b_next(free));
    }
#endif

    pthread_spin_unlock(&_pool->lock);
  }
}


void ENSIWCMem::split_block(Handle block, size_t size)
{
  // Check to see if the split will result in a new block this at least the
  // required minimum size.
  if ((b_size(block) - (int32_t)size - 1) >= _pool->min_size)
  {
    // Determine the offset of the new block.
    Handle n = block + 1 + size;

    // Insert the new block into the main list.
    b_next(n) = b_next(block);
    b_prev(n) = block;
    b_prev(b_next(block)) = n;
    b_next(block) = n;

    // Insert the new set into the free list.
    b_next_free(n) = b_next_free(0);
    b_prev_free(n) = 0;
    b_prev_free(b_next_free(0)) = n;
    b_next_free(0) = n;
  }
}

void ENSIWCMem::join_blocks(Handle prev, Handle next)
{
  // Remove the next block from the main list.
  b_prev(b_next(next)) = prev;
  b_next(prev) = b_next(next);

  // Remove it from the free list as well.
  b_next_free(b_prev_free(next)) = b_next_free(next);
  b_prev_free(b_next_free(next)) = b_prev_free(next);
}

int64_t time_delta(struct timespec tp1, struct timespec tp2)
{
  int64_t t1 = tp1.tv_sec * 1000000000 + tp1.tv_nsec;
  int64_t t2 = tp2.tv_sec * 1000000000 + tp2.tv_nsec;

  return (t2 - t1);
}

#ifdef UNITTEST
bool ENSIWCMem::unit_test()
{
  char* mem = (char*)malloc(1000000);

  ENSIWCMem pool;
  pool.init(mem, 1000000, 128);

  srand(100);

  printf("ENSIWCMem::unit_test (1) : basic allocate and free of random sizes ... ");
  std::vector<Handle> alloc(100);
  for (int ii = 0; ii<100; ++ii)
  {
    alloc[ii] = pool.alloc(rand() % 10000);
    if ((alloc[ii] == 0) || (pool.mem(alloc[ii]) == NULL))
    {
      printf("Alloc %d failed\n", ii);
      return false;
    }
  }

  for (int ii = 0; ii<100; ++ii)
  {
    pool.free(alloc[ii]);
    alloc[ii] = 0;
  }
  printf("Passed\n");

  printf("ENSIWCMem::unit_test (2) : interleaved mixed alloc/free operations ... ");
  for (int ii = 0; ii<10000; ++ii)
  {
    int jj = rand() % 100;
    if (alloc[jj] == 0)
    {
      alloc[jj] = pool.alloc(rand() % 10000);
      if ((alloc[jj] == 0) || (pool.mem(alloc[jj]) == NULL))
      {
        printf("Alloc failed\n");
        return false;
      }
    }
    else
    {
      pool.free(alloc[jj]);
    }
  }
  printf("Passed\n");

  printf("ENSIWCMem::unit_test (3) : performance test ... ");
  alloc[0] = pool.alloc(100);
  alloc[1] = pool.alloc(200);
  alloc[2] = pool.alloc(300);

  struct timespec start, end;
  clock_gettime(CLOCK_MONOTONIC, &start);

  for (int ii = 3; ii<100003; ++ii)
  {
    alloc[ii % 100] = pool.alloc(((ii* 100) % 1000) + 100);
    pool.free(alloc[(ii - 3) % 100]);
  }

  clock_gettime(CLOCK_MONOTONIC, &end);

  int64_t elapsed = (int64_t)(end.tv_sec - start.tv_sec) * (int64_t)1000000000 + (int64_t)(end.tv_nsec - start.tv_nsec);

  printf("Passed (total time = %ld ns, per alloc/free = %ld ns)\n", elapsed, elapsed/100000);
  //printf("(Start = %ld.%9.9ld, end = %ld.%9.9ld)\n", start.tv_sec, start.tv_nsec, end.tv_sec, end.tv_nsec);

  return true;
}
#endif
