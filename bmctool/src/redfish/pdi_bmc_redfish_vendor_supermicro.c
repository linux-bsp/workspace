/************************************************************************
 * PDI BMC Redfish Supermicro vendor support
 ************************************************************************/

#include "pdi_bmc_redfish_priv.h"

#include <cjson/cJSON.h>

#include <errno.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

static char supermicro_tolower(char c)
{
	if (c >= 'A' && c <= 'Z')
		return (char)(c - 'A' + 'a');
	return c;
}

static bool supermicro_contains_ci(const char *text, const char *needle)
{
	size_t needle_len;

	if (!text || !needle)
		return false;
	needle_len = strlen(needle);
	if (!needle_len)
		return true;

	for (; *text; text++) {
		size_t i;

		for (i = 0; i < needle_len; i++) {
			if (!text[i])
				return false;
			if (supermicro_tolower(text[i]) !=
			    supermicro_tolower(needle[i]))
				break;
		}
		if (i == needle_len)
			return true;
	}

	return false;
}

static bool supermicro_body_matches(const char *body)
{
	return supermicro_contains_ci(body, "Supermicro") ||
	       supermicro_contains_ci(body, "Super Micro");
}

static int supermicro_probe_path(struct pdi_bmc_redfish_ctx *ctx,
				 const char *path)
{
	char *body = NULL;
	int ret;

	ret = pdi_bmc_redfish_http(ctx, "GET", path, NULL, &body);
	if (ret < 0)
		return ret;

	ret = supermicro_body_matches(body) ? 0 : -ENODEV;
	free(body);
	return ret;
}

static int supermicro_probe(struct pdi_bmc_redfish_ctx *ctx)
{
	const char *path;
	int ret;

	if (!ctx)
		return -EINVAL;

	ret = pdi_bmc_redfish_ensure_system_path(ctx);
	if (ret == 0) {
		path = pdi_bmc_redfish_system_path(ctx);
		if (path && supermicro_probe_path(ctx, path) == 0)
			return 0;
	}

	ret = pdi_bmc_redfish_ensure_manager_path(ctx);
	if (ret < 0)
		return ret;

	return supermicro_probe_path(ctx, "/redfish/v1/Managers/1") == 0 ?
		0 : -ENODEV;
}

const struct pdi_bmc_redfish_vendor_ops pdi_bmc_redfish_supermicro_ops = {
	.name = "supermicro",
	.probe = supermicro_probe,
};
