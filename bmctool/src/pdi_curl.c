#include "pdi_curl_priv.h"

#include <curl/curl.h>
#include <errno.h>
#include <pthread.h>

static pthread_once_t curl_once = PTHREAD_ONCE_INIT;
static int curl_init_result;

static void init_curl(void)
{
    curl_init_result = curl_global_init(CURL_GLOBAL_DEFAULT) == CURLE_OK ? 0 : -EIO;
}

int bmctool_curl_global_init(void)
{
    int ret = pthread_once(&curl_once, init_curl);

    return ret ? -ret : curl_init_result;
}
