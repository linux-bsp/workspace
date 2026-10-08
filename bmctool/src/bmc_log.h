#ifndef BMC_LOG_H
#define BMC_LOG_H

#include <syslog.h>

#define BMCTOOL_LOG_WARN(...) syslog(LOG_WARNING, __VA_ARGS__)
#define BMCTOOL_LOG_ERROR(...) syslog(LOG_ERR, __VA_ARGS__)
#define BMCTOOL_LOG_INFO(...) syslog(LOG_INFO, __VA_ARGS__)

#endif
