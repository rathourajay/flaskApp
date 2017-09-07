#ifndef __ENSLOG_H__
#define __ENSLOG_H__

extern int log_level;

extern void ENSLog(const char* level, const char *module, int line_no, const char* fmt, ...);

#define LOG_ERROR(...)    if (log_level >= 1) ENSLog("ERROR", __FILE__, __LINE__, __VA_ARGS__)
#define LOG_WARNING(...)  if (log_level >= 2) ENSLog("WARNING", __FILE__, __LINE__, __VA_ARGS__)
#define LOG_INFO(...)     if (log_level >= 3) ENSLog("INFO", __FILE__, __LINE__, __VA_ARGS__)
#define LOG_DEBUG(...)    if (log_level >= 4) ENSLog("DEBUG", __FILE__, __LINE__, __VA_ARGS__)
#define LOG_VERBOSE(...)  if (log_level >= 5) ENSLog("VERBOSE", __FILE__, __LINE__, __VA_ARGS__)

#endif

