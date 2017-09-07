#include <stdio.h>
#include <time.h>
#include <stdarg.h>
#include <string.h>
#include "enslog.h"

int log_level = 3;

void ENSLog(const char* level, const char *module, int line_no, const char *fmt, ...)
{
  va_list args;
  va_start(args, fmt);

  struct timespec ts;
  struct tm dt;
  clock_gettime(CLOCK_REALTIME, &ts);
  gmtime_r(&ts.tv_sec, &dt);

#define MAX_LINE 512
  char line[MAX_LINE];

  const char* mod = strrchr(module, '/');
  module = (mod != NULL) ? mod + 1 : module;

  int written = 0;
  written += snprintf(line, MAX_LINE-2, "%4.4d-%2.2d-%2.2d %2.2d:%2.2d:%2.2d,%3.3d %-8.8s %-16.16s %4d ",
                      dt.tm_year+1900, dt.tm_mon+1, dt.tm_mday, dt.tm_hour, dt.tm_min, dt.tm_sec, (int)(ts.tv_nsec / 1000000), level, module, line_no);
  written += vsnprintf(line+written, MAX_LINE-written-2, fmt, args);
  line[written] = '\n';
  line[written+1] = '\0';
  puts(line);
  fflush(stdout);
  va_end(args);
}
