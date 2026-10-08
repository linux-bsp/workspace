/************************************************************************
 * PDI BMC IPMI vendor registry
 ************************************************************************/

#include "pdi_bmc_ipmi_priv.h"

#include <stddef.h>

static const struct pdi_bmc_ipmi_vendor_ops *const ipmi_vendors[] = {
	NULL,
};

const struct pdi_bmc_ipmi_vendor_ops *
pdi_bmc_ipmi_vendor_detect(struct pdi_bmc_ipmi_ctx *ctx)
{
	struct pdi_bmc_ipmi_device_id device_id;
	int ret;

	if (!ctx)
		return NULL;

	if (!ipmi_vendors[0])
		return NULL;

	ret = pdi_bmc_ipmi_get_device_id(ctx, &device_id);
	if (ret < 0)
		return NULL;

	for (size_t i = 0; ipmi_vendors[i]; i++) {
		const struct pdi_bmc_ipmi_vendor_ops *vendor = ipmi_vendors[i];

		if (!vendor->probe)
			continue;
		if (vendor->probe(ctx, &device_id) == 0)
			return vendor;
	}

	return NULL;
}
