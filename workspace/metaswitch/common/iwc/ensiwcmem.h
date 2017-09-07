
#ifndef ENSIWCMEM_H__
#define ENSIWCMEM_H__

#include <stdlib.h>
#include <stdint.h>

// Class implementing a managed memory pool for buffering messages passed
// between containers.  The class may be embedded in shared memory, so
// must use offsets rather than pointers.
class ENSIWCMem
{
public:
  typedef int32_t Handle;

  // Creates memory pool using the supplied memory.  Multiple instances of
  // this class can be created all referring to the same memory.
  ENSIWCMem();
  ~ENSIWCMem();

  // Initializes the memory pool.  If the pool is embedded in shared memory
  // this must only be called once.
  void init(char* mem, int32_t size, int32_t min_size);

  // Joins the memory pool.  This can be called by other processes wanting
  // to use the memory pool.
  void join(char* mem);

  // Allocates a block of memory from the pool of the required size, and
  // returns a handle to the memory.  The handle is portable across all
  // users of the memory pool (even if they are in different processes) so
  // can be passed across a suitable IPC mechanism.  The returned handle is
  // zero if the request cannot be satisfied.
  Handle alloc(size_t size);

  // Free the block of memory referenced by the handle.
  void free(Handle h);

  // Returns a pointer to the memory block referenced by the handle.
  inline uint8_t* mem(Handle h) {return ((h > 0) && (h < _pool->size)) ? (uint8_t*)&_pool->mem[h] : NULL;};

  // Returns the handle if the pointer refers to an allocated block in the pool.
  inline bool handle(uint8_t* p)
  {
    if ((size_t)p % sizeof(mhdr))
    {
      return 0;
    }
    Handle h = (((mhdr*)p) - 1) - &_pool->mem[0];
    return ((h > 0) && (h < _pool->size) && (!b_is_free(h))) ? h : 0;
  }

#ifdef UNITTEST
  static bool unit_test();
#endif

private:
  // Split a block at the specified size, provided the remainder will
  // not be too small.
  void split_block(Handle block, size_t size);

  // Join two free blocks.
  void join_blocks(Handle prev, Handle next);

  // Memory block header.  The next/prev fields form a circular list of
  // ascending memory handles (indexes into the pool array), cycling back to the
  // root node at the end).  The next_free/prev_free fields form a free list of
  // memory handles, again cycling back to the root node.  next_free/prev_free
  // are set to -1 for in-use blocks.
  typedef struct
  {
    Handle next;
    Handle prev;
    Handle next_free;
    Handle prev_free;
  } mhdr;

  // Scales sizes in bytes to size units used by the allocator.
  inline size_t scale(size_t size) {return (size + sizeof(mhdr) - 1) / sizeof(mhdr);}

  // Function to convert from a memory handle to the relevant mhdr structure.
  inline mhdr* b_hdr(Handle h) {return (mhdr*)&_pool->mem[h];}

  // Accessor functions for fields in memory block headers.
  inline bool b_is_free(Handle h) {return ((h > 0) && (b_hdr(h)->next_free >= 0));}
  inline int32_t& b_next(Handle h) {return b_hdr(h)->next;}
  inline int32_t& b_prev(Handle h) {return b_hdr(h)->prev;}
  inline int32_t& b_next_free(Handle h) {return b_hdr(h)->next_free;}
  inline int32_t& b_prev_free(Handle h) {return b_hdr(h)->prev_free;}

  // Computes the size of the block.
  inline int32_t b_size(Handle h) {return ((b_next(h) > 0) ? b_next(h) : _pool->size) - h - 1;}

  typedef struct
  {
    pthread_spinlock_t lock;
    int32_t size;
    int32_t min_size;
    int32_t pad;
    mhdr mem[0];
  } mpool;

  mpool* _pool;
};

#endif
