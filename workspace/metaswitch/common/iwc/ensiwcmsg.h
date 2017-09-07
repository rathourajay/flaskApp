
#ifndef ENSIWCMSG_H__
#define ENSIWCMSG_H__

#include "ensiwcmem.h"

#define MSG_WORKLOAD_INIT 1
#define MSG_WORKLOAD_TERM 2
#define MSG_SESSION_START 3
#define MSG_SESSION_STOP  4
#define MSG_EVENT         5

typedef struct
{
  int session_id;
  int msg_id;
  size_t length;
  ENSIWCMem::Handle data;
} ENSIWCMsg;

#endif

