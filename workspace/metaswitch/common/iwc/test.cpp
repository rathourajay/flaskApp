#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include "ensiwc.h"

int main(int argc, char** argv)
{
  if (argc < 2)
  {
    printf("Must specify host or container mode\n");
    exit(1);
  }

  if (!strcmp(argv[1], "host"))
  {
    // Host mode
    if (argc < 4)
    {
      printf("Must specify host and container namespaces for host mode");
      exit(1);
    }

    int host_fd = open(argv[2], O_RDONLY);
    int container_fd = open(argv[3], O_RDONLY);
    printf("Opened namespaces %d, %d\n", host_fd, container_fd);

    ENSIwc* iwc = new ENSIwc(true, container_fd, host_fd);

    for (int ii = 1; ii <= 10; ++ii)
    {
      iwc->push(ii);
      //int jj = icc->pop();
      printf("%d\n", ii);
      sleep(1);
    }
  }
  else
  {
    // Assume container mode
    ENSIwc* iwc = new ENSIwc();

    int ii;
    do
    {
      ii = iwc->pop();
      printf("%d\n", ii);
    }
    while (ii < 10);
  }
}
