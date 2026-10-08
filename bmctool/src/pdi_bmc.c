/************************************************************************
 * PDI BMC user API implementation
 ************************************************************************/

#include "pdi_bmc_priv.h"
#include "bmc_log.h"

#include <errno.h>
#include <pthread.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#define PDI_BMC_MAX_HANDLES 16
#define PDI_BMC_MAX_CANDIDATES 2U

struct pdi_bmc_handle {
	bool used;
	bool closing;
	unsigned int inflight;
	const struct pdi_bmc_backend_ops *ops;
	void *backend_ctx;
	pthread_mutex_t request_lock;
	pthread_cond_t idle;
};

struct pdi_bmc_backend_candidate {
	const struct pdi_bmc_backend_ops *ops;
	struct pdi_bmc_open_params params;
	char endpoint[PDI_BMC_MAX_ENDPOINT_LEN];
	char username[PDI_BMC_MAX_USERNAME_LEN];
	char password[PDI_BMC_MAX_PASSWORD_LEN];
};

static struct pdi_bmc_handle pdi_bmc_handles[PDI_BMC_MAX_HANDLES];
static pthread_mutex_t pdi_bmc_handles_lock = PTHREAD_MUTEX_INITIALIZER;
static pthread_once_t pdi_bmc_handles_once = PTHREAD_ONCE_INIT;

static void pdi_bmc_handles_init(void)
{
	for (int i = 0; i < PDI_BMC_MAX_HANDLES; i++) {
		pthread_mutex_init(&pdi_bmc_handles[i].request_lock, NULL);
		pthread_cond_init(&pdi_bmc_handles[i].idle, NULL);
	}
}

static const struct pdi_bmc_backend_ops *pdi_bmc_backend_ops_for_protocol(
	enum pdi_bmc_protocol protocol)
{
	switch (protocol) {
#ifdef BMCTOOL_REDFISH
	case PDI_BMC_PROTOCOL_REDFISH:
		return &pdi_bmc_redfish_ops;
#endif
#ifdef BMCTOOL_IPMI
	case PDI_BMC_PROTOCOL_IPMI:
		return &pdi_bmc_ipmi_ops;
#endif
#ifdef BMCTOOL_PMCP
	case PDI_BMC_PROTOCOL_PMCP:
		return &pdi_bmc_pmcp_ops;
#endif
	default:
		return NULL;
	}
}

static int pdi_bmc_init_candidate(struct pdi_bmc_backend_candidate *candidate,
				  enum pdi_bmc_protocol protocol,
				  const char *endpoint, const char *username,
				  const char *password, uint32_t flags,
				  uint32_t timeout_ms)
{
	const struct pdi_bmc_backend_ops *ops;
	int ret;

	if (!candidate || !endpoint || !endpoint[0])
		return -EINVAL;

	ops = pdi_bmc_backend_ops_for_protocol(protocol);
	if (!ops)
		return -ENOTSUP;

	memset(candidate, 0, sizeof(*candidate));
	candidate->ops = ops;
	ret = pdi_bmc_copy_string(candidate->endpoint, sizeof(candidate->endpoint),
				  endpoint);
	if (ret < 0)
		return ret;
	ret = pdi_bmc_copy_string(candidate->username, sizeof(candidate->username),
				  username);
	if (ret < 0)
		return ret;
	ret = pdi_bmc_copy_string(candidate->password, sizeof(candidate->password),
				  password);
	if (ret < 0)
		return ret;

	candidate->params.endpoint = candidate->endpoint;
	candidate->params.username = candidate->username;
	candidate->params.password = candidate->password;
	candidate->params.protocol = protocol;
	candidate->params.flags = flags;
	candidate->params.timeout_ms = timeout_ms;
	return 0;
}

static int pdi_bmc_add_candidate(struct pdi_bmc_backend_candidate *candidates,
				 size_t max_candidates, size_t *count,
				 enum pdi_bmc_protocol protocol,
				 const char *endpoint, const char *username,
				 const char *password, uint32_t flags,
				 uint32_t timeout_ms)
{
	int ret;

	if (!candidates || !count)
		return -EINVAL;
	if (*count >= max_candidates)
		return -ENOSPC;

	ret = pdi_bmc_init_candidate(&candidates[*count], protocol, endpoint,
				     username, password, flags, timeout_ms);
	if (ret < 0)
		return ret;

	(*count)++;
	return 0;
}

static int pdi_bmc_add_direct_candidate(
	const struct pdi_bmc_open_params *params,
	struct pdi_bmc_backend_candidate *candidates, size_t max_candidates,
	size_t *count)
{
	enum pdi_bmc_protocol protocol;
#ifdef BMCTOOL_REDFISH
	int ret;
#endif

	if (!params || !params->endpoint || !params->endpoint[0])
		return 0;

	protocol = params->protocol;
	if (protocol == PDI_BMC_PROTOCOL_AUTO) {
#ifdef BMCTOOL_REDFISH
		ret = pdi_bmc_add_candidate(candidates, max_candidates, count,
					    PDI_BMC_PROTOCOL_REDFISH,
					    params->endpoint, params->username,
					    params->password, params->flags,
					    params->timeout_ms);
		if (ret < 0)
			return ret;
#endif

#ifdef BMCTOOL_IPMI
		return pdi_bmc_add_candidate(candidates, max_candidates, count,
					     PDI_BMC_PROTOCOL_IPMI,
					     params->endpoint, params->username,
					     params->password, params->flags,
					     params->timeout_ms);
#else
		return *count ? 0 : -ENOTSUP;
#endif
	}

	return pdi_bmc_add_candidate(candidates, max_candidates, count, protocol,
				     params->endpoint, params->username,
				     params->password, params->flags,
				     params->timeout_ms);
}

static int pdi_bmc_find_backend(const struct pdi_bmc_open_params *params,
				struct pdi_bmc_backend_candidate *candidates,
				size_t max_candidates, size_t *count)
{
	int ret;

	if (!params || !candidates || !count || !max_candidates)
		return -EINVAL;

	*count = 0;
	ret = pdi_bmc_add_direct_candidate(params, candidates, max_candidates,
					   count);
	if (ret < 0)
		return ret;
	if (*count)
		return 0;

	return -ENODEV;
}

static int pdi_bmc_alloc_handle(const struct pdi_bmc_backend_ops *ops,
				 void *backend_ctx)
{
	int handle = -EMFILE;

	pthread_once(&pdi_bmc_handles_once, pdi_bmc_handles_init);
	pthread_mutex_lock(&pdi_bmc_handles_lock);
	for (int i = 0; i < PDI_BMC_MAX_HANDLES; i++) {
		if (pdi_bmc_handles[i].used)
			continue;

		pdi_bmc_handles[i].used = true;
		pdi_bmc_handles[i].closing = false;
		pdi_bmc_handles[i].inflight = 0;
		pdi_bmc_handles[i].ops = ops;
		pdi_bmc_handles[i].backend_ctx = backend_ctx;
		handle = i + 1;
		break;
	}
	pthread_mutex_unlock(&pdi_bmc_handles_lock);

	return handle;
}

static struct pdi_bmc_handle *pdi_bmc_get_handle_locked(int fd)
{
	if (fd <= 0 || fd > PDI_BMC_MAX_HANDLES)
		return NULL;
	if (!pdi_bmc_handles[fd - 1].used)
		return NULL;

	return &pdi_bmc_handles[fd - 1];
}

static void pdi_bmc_free_handle_locked(struct pdi_bmc_handle *handle)
{
	if (!handle)
		return;

	handle->used = false;
	handle->closing = false;
	handle->inflight = 0;
	handle->ops = NULL;
	handle->backend_ctx = NULL;
}

static int32_t pdi_bmc_request(int fd,
			       const struct pdi_bmc_backend_request *request)
{
	struct pdi_bmc_handle *handle;
	const struct pdi_bmc_backend_ops *ops;
	void *backend_ctx;
	int32_t ret;

	if (!request)
		return -EINVAL;

	pthread_once(&pdi_bmc_handles_once, pdi_bmc_handles_init);
	pthread_mutex_lock(&pdi_bmc_handles_lock);
	handle = pdi_bmc_get_handle_locked(fd);
	if (!handle || handle->closing) {
		pthread_mutex_unlock(&pdi_bmc_handles_lock);
		return -EBADF;
	}
	if (!handle->ops || !handle->ops->request) {
		pthread_mutex_unlock(&pdi_bmc_handles_lock);
		return -ENOTSUP;
	}
	handle->inflight++;
	ops = handle->ops;
	backend_ctx = handle->backend_ctx;
	pthread_mutex_unlock(&pdi_bmc_handles_lock);

	pthread_mutex_lock(&handle->request_lock);
	ret = ops->request(backend_ctx, request);
	pthread_mutex_unlock(&handle->request_lock);

	pthread_mutex_lock(&pdi_bmc_handles_lock);
	handle->inflight--;
	if (handle->closing && !handle->inflight)
		pthread_cond_signal(&handle->idle);
	pthread_mutex_unlock(&pdi_bmc_handles_lock);
	return ret;
}

int pdi_bmc_open(const char *endpoint, const char *username,
		 const char *password)
{
	struct pdi_bmc_open_params params = {
		.endpoint = endpoint,
		.username = username,
		.password = password,
		.protocol = PDI_BMC_PROTOCOL_AUTO,
	};

	return pdi_bmc_open_ext(&params);
}

int pdi_bmc_open_ext(const struct pdi_bmc_open_params *params)
{
	struct pdi_bmc_backend_candidate candidates[PDI_BMC_MAX_CANDIDATES];
	void *backend_ctx = NULL;
	int last_ret = -ENODEV;
	size_t count = 0;
	int ret;

	if (!params) {
		BMCTOOL_LOG_WARN("pdi_bmc_open_ext called with params=NULL");
		return -EINVAL;
	}

	ret = pdi_bmc_find_backend(params, candidates, PDI_BMC_MAX_CANDIDATES,
				   &count);
	if (ret < 0) {
		BMCTOOL_LOG_ERROR("no BMC backend candidate for protocol %u",
			  params->protocol);
		return ret;
	}

	for (size_t i = 0; i < count; i++) {
		const struct pdi_bmc_backend_candidate *candidate = &candidates[i];

		if (!candidate->ops || !candidate->ops->open) {
			last_ret = -ENOTSUP;
			continue;
		}

		ret = candidate->ops->open(&candidate->params, &backend_ctx);
		if (ret < 0) {
			BMCTOOL_LOG_WARN("BMC %s backend open failed for %s: %d",
				 candidate->ops->name ? candidate->ops->name : "unknown",
				 candidate->params.endpoint, ret);
			last_ret = ret;
			continue;
		}

		ret = pdi_bmc_alloc_handle(candidate->ops, backend_ctx);
		if (ret < 0) {
			if (candidate->ops->close)
				candidate->ops->close(backend_ctx);
			return ret;
		}

		return ret;
	}

	return last_ret;
}

int32_t pdi_bmc_close(int fd)
{
	struct pdi_bmc_handle *handle;
	const struct pdi_bmc_backend_ops *ops;
	void *backend_ctx;

	pthread_once(&pdi_bmc_handles_once, pdi_bmc_handles_init);
	pthread_mutex_lock(&pdi_bmc_handles_lock);
	handle = pdi_bmc_get_handle_locked(fd);
	if (!handle || handle->closing) {
		pthread_mutex_unlock(&pdi_bmc_handles_lock);
		BMCTOOL_LOG_WARN("pdi_bmc_close called with invalid handle %d", fd);
		return -EBADF;
	}

	handle->closing = true;
	while (handle->inflight)
		pthread_cond_wait(&handle->idle, &pdi_bmc_handles_lock);
	ops = handle->ops;
	backend_ctx = handle->backend_ctx;
	pthread_mutex_unlock(&pdi_bmc_handles_lock);

	if (ops && ops->close)
		ops->close(backend_ctx);

	pthread_mutex_lock(&pdi_bmc_handles_lock);
	pdi_bmc_free_handle_locked(handle);
	pthread_mutex_unlock(&pdi_bmc_handles_lock);
	return 0;
}

int32_t pdi_bmc_get_info(int fd, struct pdi_bmc_info *info)
{
	struct pdi_bmc_backend_request request = {
		.type = PDI_BMC_BACKEND_REQ_GET_INFO,
		.args.info = info,
	};

	if (!info)
		return -EINVAL;

	return pdi_bmc_request(fd, &request);
}

int32_t pdi_bmc_get_power_state(int fd, enum pdi_bmc_power_state *state)
{
	struct pdi_bmc_backend_request request = {
		.type = PDI_BMC_BACKEND_REQ_GET_POWER_STATE,
		.args.state = state,
	};

	if (!state)
		return -EINVAL;

	return pdi_bmc_request(fd, &request);
}

int32_t pdi_bmc_power_control(int fd, enum pdi_bmc_power_action action)
{
	struct pdi_bmc_backend_request request = {
		.type = PDI_BMC_BACKEND_REQ_POWER_CONTROL,
		.args.action = action,
	};

	return pdi_bmc_request(fd, &request);
}

int32_t pdi_bmc_get_sensors(int fd,
			    const struct pdi_bmc_sensor_filter *filter,
			    struct pdi_bmc_sensor *sensors, uint32_t *count)
{
	struct pdi_bmc_backend_request request = {
		.type = PDI_BMC_BACKEND_REQ_GET_SENSORS,
		.args.sensors = {
			.filter = filter,
			.sensors = sensors,
			.count = count,
		},
	};

	if (!count)
		return -EINVAL;

	return pdi_bmc_request(fd, &request);
}

const char *pdi_bmc_protocol_name(enum pdi_bmc_protocol protocol)
{
	switch (protocol) {
	case PDI_BMC_PROTOCOL_AUTO:
		return "auto";
	case PDI_BMC_PROTOCOL_REDFISH:
		return "redfish";
	case PDI_BMC_PROTOCOL_IPMI:
		return "ipmi";
	case PDI_BMC_PROTOCOL_PMCP:
		return "pmcp";
	default:
		return "unknown";
	}
}

const char *pdi_bmc_power_state_name(enum pdi_bmc_power_state state)
{
	switch (state) {
	case PDI_BMC_POWER_ON:
		return "on";
	case PDI_BMC_POWER_OFF:
		return "off";
	case PDI_BMC_POWER_POWERING_ON:
		return "powering-on";
	case PDI_BMC_POWER_POWERING_OFF:
		return "powering-off";
	case PDI_BMC_POWER_UNKNOWN:
	default:
		return "unknown";
	}
}
