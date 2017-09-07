#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <json/json.h>
#include <iostream>
#include <string>
#include "enslog.h"
#include "ensiwcdispatcher.h"

int main (int argc, char *argv[])
{
  // Create the dispatcher.
  pid_t pid = getpid();
  char host_ns_file[100];
  sprintf(host_ns_file, "/proc/%d/ns/ipc", pid);
  int host_ns = open(host_ns_file, O_RDONLY);
  ENSIWCDispatcher* d = new ENSIWCDispatcher(host_ns);
  d->start();
  LOG_INFO("Started dispatcher");

  // Read and execute JSON formatted commands from stdin.
  Json::Reader r;
  while (true)
  {
    std::string s;
    getline(std::cin, s);

    if (s.length() == 0)
    {
      LOG_INFO("Exiting");
      exit(0);
    }

    LOG_INFO("Processing command: %s", s.c_str());
    Json::Value cmd;
    r.parse(s, cmd);
    LOG_DEBUG("Parsed command");

    if (cmd.isMember("connect"))
    {
      LOG_DEBUG("connect command");
      Json::Value conn = cmd["connect"];
      if (conn.isMember("id") && conn.isMember("port") && conn.isMember("pid"))
      {
        int id = conn["id"].asInt();
        int port = conn["port"].asInt();
        char container_ns_file[100];
        sprintf(container_ns_file, "/proc/%d/ns/ipc", conn["pid"].asInt());
        int container_ns = open(container_ns_file, O_RDONLY);
        if ((container_ns >= 0) &&
            (d->connect_workload(id, port, container_ns)))
        {
          LOG_INFO("Connected to workload %d on port %d", id, port);
        }
        else
        {
          LOG_ERROR("Failed to connect to workload %d", id);
        }
      }
      else
      {
        LOG_ERROR("Missing parameter on connect workload command");
      }
    }

    if (cmd.isMember("disconnect"))
    {
      LOG_DEBUG("disconnect command");
      Json::Value disconn = cmd["disconnect"];
      if (disconn.isMember("id"))
      {
        int id = disconn["id"].asInt();
        d->disconnect_workload(id);
        LOG_INFO("Disconnected from workload %d", id);
      }
    }
  }
}
