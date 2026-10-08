/************************************************************************
 * PDI BMC Redfish vendor registry
 ************************************************************************/

#include "pdi_bmc_redfish_priv.h"

#include <stddef.h>

#ifdef BMCTOOL_REDFISH_VENDOR_SUPERMICRO
extern const struct pdi_bmc_redfish_vendor_ops pdi_bmc_redfish_supermicro_ops;
#endif
#ifdef BMCTOOL_REDFISH_VENDOR_XFUSION
extern const struct pdi_bmc_redfish_vendor_ops pdi_bmc_redfish_xfusion_ops;
#endif

static const struct pdi_bmc_redfish_vendor_ops *const redfish_vendors[] = {
#ifdef BMCTOOL_REDFISH_VENDOR_SUPERMICRO
	&pdi_bmc_redfish_supermicro_ops,
#endif
#ifdef BMCTOOL_REDFISH_VENDOR_XFUSION
	&pdi_bmc_redfish_xfusion_ops,
#endif
	NULL,
};

const struct pdi_bmc_redfish_vendor_ops *
pdi_bmc_redfish_vendor_detect(struct pdi_bmc_redfish_ctx *ctx)
{
	if (!ctx)
		return NULL;

	for (size_t i = 0; redfish_vendors[i]; i++) {
		const struct pdi_bmc_redfish_vendor_ops *vendor =
			redfish_vendors[i];

		if (!vendor->probe)
			continue;
		if (vendor->probe(ctx) == 0)
			return vendor;
	}

	return NULL;
}
