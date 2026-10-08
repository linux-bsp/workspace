/************************************************************************
 * PDI BMC Redfish internal vendor interface
 ************************************************************************/

#ifndef PDI_BMC_REDFISH_PRIV_H
#define PDI_BMC_REDFISH_PRIV_H

#include "../pdi_bmc_priv.h"

#include <stdint.h>

#define PDI_BMC_REDFISH_PATH_LEN 256U

struct pdi_bmc_redfish_ctx;

struct pdi_bmc_redfish_vendor_ops {
	const char *name;
	int (*probe)(struct pdi_bmc_redfish_ctx *ctx);
	int32_t (*get_info)(struct pdi_bmc_redfish_ctx *ctx,
			    struct pdi_bmc_info *info);
	int32_t (*get_power_state)(struct pdi_bmc_redfish_ctx *ctx,
				   enum pdi_bmc_power_state *state);
	int32_t (*power_control)(struct pdi_bmc_redfish_ctx *ctx,
				 enum pdi_bmc_power_action action);
	int32_t (*get_sensors)(struct pdi_bmc_redfish_ctx *ctx,
				const struct pdi_bmc_sensor_filter *filter,
				struct pdi_bmc_sensor *sensors, uint32_t *count);
};

int pdi_bmc_redfish_http(struct pdi_bmc_redfish_ctx *ctx, const char *method,
			 const char *path, const char *body,
			 char **response_out);
int pdi_bmc_redfish_collection_first_path(struct pdi_bmc_redfish_ctx *ctx,
					    const char *collection_path,
					    char *out, size_t out_len);
int pdi_bmc_redfish_ensure_system_path(struct pdi_bmc_redfish_ctx *ctx);
int pdi_bmc_redfish_ensure_manager_path(struct pdi_bmc_redfish_ctx *ctx);
const char *pdi_bmc_redfish_system_path(struct pdi_bmc_redfish_ctx *ctx);
void pdi_bmc_redfish_copy_text(char *dst, size_t dst_len, const char *src);
enum pdi_bmc_power_state
pdi_bmc_redfish_power_state_from_string(const char *str);
const char *pdi_bmc_redfish_reset_type(enum pdi_bmc_power_action action);

int32_t pdi_bmc_redfish_standard_get_info(struct pdi_bmc_redfish_ctx *ctx,
					  struct pdi_bmc_info *info);
int32_t pdi_bmc_redfish_standard_get_power_state(
	struct pdi_bmc_redfish_ctx *ctx, enum pdi_bmc_power_state *state);
int32_t pdi_bmc_redfish_standard_power_control(
	struct pdi_bmc_redfish_ctx *ctx, enum pdi_bmc_power_action action);
int32_t pdi_bmc_redfish_standard_get_sensors(
	struct pdi_bmc_redfish_ctx *ctx,
	const struct pdi_bmc_sensor_filter *filter,
	struct pdi_bmc_sensor *sensors, uint32_t *count);

const struct pdi_bmc_redfish_vendor_ops *
pdi_bmc_redfish_vendor_detect(struct pdi_bmc_redfish_ctx *ctx);

#endif /* PDI_BMC_REDFISH_PRIV_H */
