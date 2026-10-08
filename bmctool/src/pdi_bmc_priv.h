/************************************************************************
 * PDI BMC internal backend interface
 ************************************************************************/

#ifndef PDI_BMC_PRIV_H
#define PDI_BMC_PRIV_H

#include "bmctool/pdi_bmc.h"

#include <errno.h>
#include <stdbool.h>
#include <stddef.h>
#include <string.h>

static inline int pdi_bmc_copy_string(char *dst, size_t dst_len,
				      const char *src)
{
	size_t len;

	if (!dst || dst_len == 0)
		return -EINVAL;

	dst[0] = 0;
	if (!src)
		return 0;

	len = strlen(src);
	if (len >= dst_len)
		return -ENAMETOOLONG;

	memcpy(dst, src, len + 1U);
	return 0;
}

enum pdi_bmc_backend_request_type {
	PDI_BMC_BACKEND_REQ_GET_INFO = 0,
	PDI_BMC_BACKEND_REQ_GET_POWER_STATE,
	PDI_BMC_BACKEND_REQ_POWER_CONTROL,
	PDI_BMC_BACKEND_REQ_GET_SENSORS,
};

struct pdi_bmc_backend_request {
	enum pdi_bmc_backend_request_type type;
	union {
		struct pdi_bmc_info *info;
		enum pdi_bmc_power_state *state;
		enum pdi_bmc_power_action action;
		struct {
			const struct pdi_bmc_sensor_filter *filter;
			struct pdi_bmc_sensor *sensors;
			uint32_t *count;
		} sensors;
	} args;
};

struct pdi_bmc_sensor_accumulator {
	const struct pdi_bmc_sensor_filter *filter;
	struct pdi_bmc_sensor *sensors;
	uint32_t capacity;
	uint32_t count;
	uint32_t *out_count;
	bool overflow;
};

static inline bool
pdi_bmc_sensor_filter_matches(const struct pdi_bmc_sensor_filter *filter,
				      const struct pdi_bmc_sensor *sensor)
{
	if (!sensor)
		return false;
	if (!filter)
		return true;
	if (filter->type != PDI_BMC_SENSOR_TYPE_ANY &&
	    filter->type != sensor->type)
		return false;
	if (filter->scope != PDI_BMC_SENSOR_SCOPE_ANY &&
	    filter->scope != sensor->scope)
		return false;

	return true;
}

static inline int
pdi_bmc_sensor_accumulator_init(struct pdi_bmc_sensor_accumulator *acc,
				       const struct pdi_bmc_sensor_filter *filter,
				       struct pdi_bmc_sensor *sensors, uint32_t *count)
{
	if (!acc || !count)
		return -EINVAL;

	memset(acc, 0, sizeof(*acc));
	acc->filter = filter;
	acc->sensors = sensors;
	acc->capacity = sensors ? *count : 0U;
	acc->out_count = count;
	return 0;
}

static inline int
pdi_bmc_sensor_accumulator_add(struct pdi_bmc_sensor_accumulator *acc,
				       const struct pdi_bmc_sensor *sensor)
{
	if (!acc || !sensor)
		return -EINVAL;
	if (!pdi_bmc_sensor_filter_matches(acc->filter, sensor))
		return 0;

	if (acc->sensors && acc->count < acc->capacity)
		acc->sensors[acc->count] = *sensor;
	else if (acc->sensors)
		acc->overflow = true;

	acc->count++;
	return 0;
}

static inline int
pdi_bmc_sensor_accumulator_finish(struct pdi_bmc_sensor_accumulator *acc)
{
	if (!acc || !acc->out_count)
		return -EINVAL;

	*acc->out_count = acc->count;
	return acc->overflow ? -ENOSPC : 0;
}

struct pdi_bmc_backend_ops {
	const char *name;
	enum pdi_bmc_protocol protocol;
	int (*open)(const struct pdi_bmc_open_params *params, void **backend_ctx);
	void (*close)(void *backend_ctx);
	int32_t (*request)(void *backend_ctx,
			   const struct pdi_bmc_backend_request *request);
};

#ifdef BMCTOOL_REDFISH
extern const struct pdi_bmc_backend_ops pdi_bmc_redfish_ops;
#endif
#ifdef BMCTOOL_IPMI
extern const struct pdi_bmc_backend_ops pdi_bmc_ipmi_ops;
#endif
#ifdef BMCTOOL_PMCP
extern const struct pdi_bmc_backend_ops pdi_bmc_pmcp_ops;
#endif

#endif /* PDI_BMC_PRIV_H */
