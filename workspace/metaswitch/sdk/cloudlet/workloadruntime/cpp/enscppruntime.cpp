
#include <stdio.h>
#include <pthread.h>
#include <string.h>
#include <dlfcn.h>
#include <vector>
#include <string>
#include <json/json.h>
#include "ensiwcworkload.h"

typedef uint8_t* (*EventFn)(uint8_t* data);

class Reactor
{
public:
  Reactor(int id, const std::string& fn);
  ~Reactor();

  void run();

private:

  static void* thread(void* p);
  void loop();

  int _id;
  std::string _module_name;
  std::string _fn_name;
  void* _mod_handle;
  EventFn _event_fn;

  ENSIWCWorkload* _iwc;
  std::vector<pthread_t> _threads;
};

int main(int argc, char *argv[])
{
  if (argc < 2)
  {
    exit(1);
  }

  Json::Reader r;
  Json::Value config;
  printf("Parsing configuration: %s\n", argv[1]);
  fflush(stdout);
  r.parse(std::string(argv[1]), config);

  // Start a reactor for the first event in the list.
  Json::Value& events = config["events"];
  Json::Value::const_iterator ii = events.begin();
  Reactor* reactor = new Reactor(config["id"].asInt(), (*ii)["fn"].asString());
  reactor->run();
}

Reactor::Reactor(int id, const std::string& fn) :
  _id(id),
  _threads()
{
  _module_name = fn.substr(0, fn.find('.')) + ".so";
  _fn_name = fn.substr(fn.find('.')+1, -1);
  printf("Configured reactor: id=%d, module=%s, fn=%s\n", _id, _module_name.c_str(), _fn_name.c_str());
  fflush(stdout);
}

Reactor::~Reactor()
{
}

void Reactor::run()
{
  // Load the workload and link to the event entry point.
  dlerror();
  _mod_handle = dlopen(_module_name.c_str(), RTLD_NOW);
  if (_mod_handle == NULL)
  {
    printf("Failed to load module %s (%d)\n", _module_name.c_str(), errno);
    fflush(stdout);
    return;
  }

  _event_fn = reinterpret_cast<EventFn>(dlsym(_mod_handle, _fn_name.c_str()));
  printf("Linked to event function %s, address %p\n", _fn_name.c_str(), _event_fn);

  _iwc = new ENSIWCWorkload(_id, 4, 10000);
  _iwc->start();

  _threads.resize(1);
  pthread_create(&_threads[0], NULL, &Reactor::thread, (void*)this);

  for (size_t ii = 0; ii < _threads.size(); ++ii)
  {
    void* res;
    pthread_join(_threads[ii], &res);
  }

  _iwc->stop();

  dlclose(_mod_handle);
}

void* Reactor::thread(void* p)
{
  ((Reactor*)p)->loop();
  return NULL;
}

void Reactor::loop()
{
  printf("Starting reactor loop\n");
  fflush(stdout);

  Json::Reader r;

  while (true)
  {
    ENSIWCMsg msg;
    //printf("Waiting for message\n");
    //fflush(stdout);
    if (!_iwc->recv(msg))
    {
      //printf("Failed to receive message\n");
      //fflush(stdout);
      break;
    }
    //printf("Received message\n");
    //fflush(stdout);

    //printf("Process message id %d\n", msg.msg_id);
    //fflush(stdout);

    if (msg.msg_id == MSG_EVENT)
    {
      // Process the event.
      //printf("Message event: %.*s\n", (int)msg.length, _iwc->msg_data(msg));
      //fflush(stdout);
      uint8_t* req = _iwc->msg_data(msg);

      //printf("Calling event function %p\n", _event_fn);
      uint8_t* rsp = _event_fn(req);

      if (rsp != req)
      {
        // Workload has not reused data buffer from request
        _iwc->free(msg.data);
        msg.data = _iwc->alloc(strlen((char*)rsp));
        memcpy(_iwc->msg_data(msg), rsp, strlen((char*)rsp));
      }

      //printf("Sending response: %.*s\n", (int)msg.length, _iwc->msg_data(msg));
      //fflush(stdout);
      _iwc->send(msg);
      //printf("Sent response\n");
      //fflush(stdout);
    }
    else if (msg.msg_id == MSG_WORKLOAD_TERM)
    {
      // Workload is being terminated.
      printf("Workload terminating\n");
      fflush(stdout);
      break;
    }
    // Ignore other messages for now.
  }
  printf("Exiting reactor loop\n");
  fflush(stdout);
}

