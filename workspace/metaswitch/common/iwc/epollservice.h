

#ifndef EPOLLSERVICE_H__
#define EPOLLSERVICE_H__

#include <epoll.h>
#include <pthread.h>
#include <vector>


class EPollService
{
public:
  EPollService(int num_threads);
  ~EpollService();

  bool start();
  void stop();

  class Actor
  {
  public:
    Actor(EPollService& service);
    virtual ~Actor();

  protected:
    virtual void process_pollerr();
    virtual void process_pollin();
    virtual void process_pollout();

  private:
    bool enable_epoll(int fd, int events);
    bool disable_epoll(int fd);

    EpollService& _service;
  }

private:

  friend class Actor;

  void add(int fd, Actor& actor, int events);
  void remove(int fd);

  static void* poll_thread(void* p);
  void run();

  std::vector<pthread_t threads);
  int _epoll_fd;
};

#endif
