/************************************************************************
 * PDI BMC IPMI internal vendor interface
 ************************************************************************/

#ifndef PDI_BMC_IPMI_PRIV_H
#define PDI_BMC_IPMI_PRIV_H

#include "../pdi_bmc_priv.h"

#include <stdint.h>

struct pdi_bmc_ipmi_ctx;

struct pdi_bmc_ipmi_device_id {
	uint64_t device_id;
	uint64_t major;
	uint64_t minor;
	uint64_t device_available;
	uint64_t manufacturer_id;
	uint64_t product_id;
};

struct pdi_bmc_ipmi_vendor_ops {
	const char *name;
	int (*probe)(struct pdi_bmc_ipmi_ctx *ctx,
		     const struct pdi_bmc_ipmi_device_id *device_id);
	int32_t (*get_info)(struct pdi_bmc_ipmi_ctx *ctx,
			    struct pdi_bmc_info *info);
	int32_t (*get_power_state)(struct pdi_bmc_ipmi_ctx *ctx,
				   enum pdi_bmc_power_state *state);
	int32_t (*power_control)(struct pdi_bmc_ipmi_ctx *ctx,
				 enum pdi_bmc_power_action action);
};

int pdi_bmc_ipmi_get_device_id(struct pdi_bmc_ipmi_ctx *ctx,
			       struct pdi_bmc_ipmi_device_id *device_id);
int32_t pdi_bmc_ipmi_standard_get_info(struct pdi_bmc_ipmi_ctx *ctx,
				       struct pdi_bmc_info *info);
int32_t pdi_bmc_ipmi_standard_get_power_state(
	struct pdi_bmc_ipmi_ctx *ctx, enum pdi_bmc_power_state *state);
int32_t pdi_bmc_ipmi_standard_power_control(
	struct pdi_bmc_ipmi_ctx *ctx, enum pdi_bmc_power_action action);

const struct pdi_bmc_ipmi_vendor_ops *
pdi_bmc_ipmi_vendor_detect(struct pdi_bmc_ipmi_ctx *ctx);

#endif /* PDI_BMC_IPMI_PRIV_H */
