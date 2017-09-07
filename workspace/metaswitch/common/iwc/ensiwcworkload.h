
#ifndef ENSIWCWORKLOAD_H__
#define ENSIWCWORKLOAD_H__

#include "ensiwcmem.h"
#include "ensiwcmsg.h"
#include "ensiwcq.h"

// Class handling the workload runtime side of the communication channel.
// This side is responsible for
// -  setting up the shared memory buffer pool and ingress and egress queues
// -  providing an API to language specific run-times to receive and send
//    events
//
// @@TODO@@ - currently this is limited to a single ingress and a single
// egress queue.  Need experimentation to decide whether it is better
// to always go with this approach, or whether to include the complexity of
// -  multiple ingress/egress queues for a multi-tenant workload
// -  separate egress/ingress queues for communication to other workloads
class ENSIWCWorkload
{
public:
  ENSIWCWorkload(int id, size_t qsize, size_t memsize);
  ~ENSIWCWorkload();

  bool start();
  void stop();

  bool recv(ENSIWCMsg& msg);

  bool send(ENSIWCMsg& msg);

  ENSIWCMem::Handle alloc(size_t len);
  void free(ENSIWCMem::Handle);

  inline uint8_t* msg_data(const ENSIWCMsg& msg) { return _pool.mem(msg.data);}

private:
  int _id;
  size_t _qsize;
  size_t _memsize;

  int _shmid;
  void* _shm;

  ENSIWCQ<ENSIWCMsg> _in;
  ENSIWCQ<ENSIWCMsg> _out;
  ENSIWCMem _pool;
};

#endif
