#include <pthread.h>
#include <map>
#include "ensiwcmem.h"
#include "ensiwcmsg.h"
#include "ensiwcq.h"

class ENSIWCDispatcher
{
public:
  ENSIWCDispatcher(int host_ns);
  ~ENSIWCDispatcher();

  bool start();
  void stop();

  bool connect_workload(int id, int port, int container_ns);
  void disconnect_workload(int id);

private:
  class Workload
  {
  public:
    Workload(int id, int port, int host_ns, int container_ns);
    ~Workload();

    bool start();
    void stop();

  private:

    bool connect_workload();
    void disconnect_workload();

    bool open_bind_socket();
    void close_socket();

    static void* client_thread(void* p);
    void client_loop();

    int _id;

    bool _running;
    pthread_t _client_thread;

    int _port;
    int _so;

    int _host_ns;
    int _container_ns;
    int _shmid;
    void* _shm;
    ENSIWCQ<ENSIWCMsg> _in;
    ENSIWCQ<ENSIWCMsg> _out;
    ENSIWCMem _pool;
  };

  pthread_spinlock_t _lock;
  int _host_ns;
  std::map<int, Workload*> _workloads;

};
