

EPollService::EPollService(int num_threads) :
  _threads(num_threads)
{

}

EPollService::~EPollService()
{
  stop();
}

bool EPollService::start()
{
  // Create the epoller.
  _epoll_fd = epoll_create(1);
  if (_epoll_fd == -1)
  {
    // Failed to create the epollers, so log error and fail.
    return false;
  }

  _running = true;
  for (int ii = 0; ii < _threads.size(); ++ii)
  {
    int rc = pthread_create(&_threads[ii], NULL, &epoll_thread, (void*)this);
  }
}

void EPollService::start()
{
  _running = false;

  for (int ii = 0; ii < _threads.size(); ++ii)
  {
    if (_threads[ii] != 0)
    {
      void* res;
      pthread_join(_threads[ii], &res);
    }
  }
}

void* EPollService::epoll_thread(void* p)
{
  ((EPollService*)p)->run();
  return NULL;
}

void EPollService::run()
{
  while (_running)
  {
    struct epoll_event events[MAX_EVENTS];
    int nfds = epoll_wait(_epoll_rx, events, MAX_EVENTS, 100);
    if (nfds == -1)
    {
      // TODO
    }

    for (int i = 0; i < nfds; ++i)
    {
      if (events[i].events & EPOLLERR)
      {
        ((epoll_actor*)events[i].data.ptr)->epollerr();
      }
      if (events[i].events & EPOLLIN)
      {
        ((epoll_actor*)events[i].data.ptr)->epollin();
      }
      if (events[i].events & EPOLLOUT)
      {
        ((epoll_actor*)events[i].data.ptr)->epollout();
      }
    }
  }
  return NULL;
}

bool EPollService::add(int fd, Actor& actor, int events)
{
  struct epoll_event ev;
  ev.events = events;
  ev.data.ptr = &actor;
  int rc = epoll_ctl(_epoll_fd, EPOLL_CTL_ADD, fd, &ev);
  if (rc != 0)
  {
    return false;
  }
  return true;
}


bool EPollService::remove(int fd)
{
  int rc = epoll_ctl(_epoll_fd, EPOLL_CTL_DEL, fd, NULL);
  if (rc != 0)
  {
    return false;
  }
  return true;
}

EPollService::Actor::Actor(EPollService& service) :
  _service(service)
{
}

EPollService::Actor::~Actor()
{
  remove();
}

void EPollService::Actor::process_pollerr()
{
}

void EPollService::Actor::process_pollin()
{
}

void EPollService::Actor::process_pollout()
{
}

bool EPollService::Actor::enable_epoll(int fd, int events)
{
  return _service->add(fd, *this, events);
}

bool EPollService::Actor::disable_epoll(int fd)
{
  return _service->remove(fd);
}



