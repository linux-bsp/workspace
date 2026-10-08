/************************************************************************
 * PDI BMC IPMI backend
 ************************************************************************/

#include "pdi_bmc_ipmi_priv.h"
#include "../bmc_log.h"

#include <freeipmi/freeipmi.h>

#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct pdi_bmc_ipmi_ctx {
	ipmi_ctx_t ipmi;
	uint32_t timeout_ms;
	uint8_t authentication_type;
	unsigned int workaround_flags;
	const struct pdi_bmc_ipmi_vendor_ops *vendor;
	bool vendor_selected;
};

struct pdi_bmc_ipmi_open_mode {
	uint8_t authentication_type;
	unsigned int workaround_flags;
	const char *name;
};

static void ipmi_copy_text(char *dst, size_t dst_len, const char *src)
{
	if (!dst || !dst_len)
		return;
	if (!src) {
		dst[0] = '\0';
		return;
	}

	snprintf(dst, dst_len, "%s", src);
}

static int ipmi_ctx_errno(ipmi_ctx_t ipmi)
{
	int errnum;

	if (!ipmi)
		return -EINVAL;

	errnum = ipmi_ctx_errnum(ipmi);
	switch (errnum) {
	case IPMI_ERR_SUCCESS:
		return 0;
	case IPMI_ERR_USERNAME_INVALID:
	case IPMI_ERR_PASSWORD_INVALID:
	case IPMI_ERR_PRIVILEGE_LEVEL_INSUFFICIENT:
	case IPMI_ERR_PRIVILEGE_LEVEL_CANNOT_BE_OBTAINED:
	case IPMI_ERR_AUTHENTICATION_TYPE_UNAVAILABLE:
	case IPMI_ERR_CIPHER_SUITE_ID_UNAVAILABLE:
	case IPMI_ERR_K_G_INVALID:
		return -EACCES;
	case IPMI_ERR_PASSWORD_VERIFICATION_TIMEOUT:
	case IPMI_ERR_CONNECTION_TIMEOUT:
	case IPMI_ERR_SESSION_TIMEOUT:
	case IPMI_ERR_DRIVER_TIMEOUT:
	case IPMI_ERR_MESSAGE_TIMEOUT:
		return -ETIMEDOUT;
	case IPMI_ERR_IPMI_2_0_UNAVAILABLE:
	case IPMI_ERR_DEVICE_NOT_FOUND:
	case IPMI_ERR_NOT_FOUND:
		return -ENODEV;
	case IPMI_ERR_CTX_NULL:
	case IPMI_ERR_CTX_INVALID:
	case IPMI_ERR_DEVICE_ALREADY_OPEN:
	case IPMI_ERR_DEVICE_NOT_OPEN:
	case IPMI_ERR_HOSTNAME_INVALID:
	case IPMI_ERR_PARAMETERS:
		return -EINVAL;
	case IPMI_ERR_OUT_OF_MEMORY:
		return -ENOMEM;
	case IPMI_ERR_DRIVER_BUSY:
	case IPMI_ERR_BMC_BUSY:
		return -EBUSY;
	case IPMI_ERR_DEVICE_NOT_SUPPORTED:
	case IPMI_ERR_COMMAND_INVALID_FOR_SELECTED_INTERFACE:
	case IPMI_ERR_COMMAND_INVALID_OR_UNSUPPORTED:
		return -ENOTSUP;
	case IPMI_ERR_PERMISSION:
		return -EPERM;
	default:
		return -EIO;
	}
}

static void ipmi_log_ctx_error(ipmi_ctx_t ipmi, const char *operation,
				       uint8_t authentication_type,
				       unsigned int workaround_flags)
{
	int errnum;
	const char *errmsg;

	if (!ipmi || !operation)
		return;

	errnum = ipmi_ctx_errnum(ipmi);
	errmsg = ipmi_ctx_errormsg(ipmi);
	BMCTOOL_LOG_WARN("%s failed: errnum=%d msg=%s auth=0x%02x workaround=0x%08x",
		 operation, errnum, errmsg ? errmsg : "unknown",
		 authentication_type, workaround_flags);
}

static int ipmi_ctx_open_mode(struct pdi_bmc_ipmi_ctx *ctx,
			      const char *endpoint, const char *username,
			      const char *password,
			      const struct pdi_bmc_ipmi_open_mode *mode)
{
	unsigned int session_timeout;
	int ret;

	if (!ctx || !ctx->ipmi || !endpoint || !mode)
		return -EINVAL;

	session_timeout = ctx->timeout_ms ? ctx->timeout_ms :
		IPMI_SESSION_TIMEOUT_DEFAULT;

	ret = ipmi_ctx_open_outofband(ctx->ipmi, endpoint, username, password,
				       mode->authentication_type,
				       IPMI_PRIVILEGE_LEVEL_ADMIN,
				       session_timeout,
				       IPMI_RETRANSMISSION_TIMEOUT_DEFAULT,
				       mode->workaround_flags,
				       IPMI_FLAGS_DEFAULT);
	if (ret < 0) {
		ipmi_log_ctx_error(ctx->ipmi, mode->name,
				   mode->authentication_type,
				   mode->workaround_flags);
		return ipmi_ctx_errno(ctx->ipmi);
	}

	ctx->authentication_type = mode->authentication_type;
	ctx->workaround_flags = mode->workaround_flags;
	BMCTOOL_LOG_INFO("BMC IPMI LAN session opened with auth=0x%02x workaround=0x%08x",
		 mode->authentication_type, mode->workaround_flags);
	return 0;
}

static int ipmi_fiid_get(fiid_obj_t obj, const char *field, uint64_t *val)
{
	if (!obj || !field || !val)
		return -EINVAL;

	if (FIID_OBJ_GET(obj, field, val) < 0)
		return -EPROTO;

	return 0;
}

int32_t pdi_bmc_ipmi_standard_get_power_state(
	struct pdi_bmc_ipmi_ctx *ctx, enum pdi_bmc_power_state *state)
{
	fiid_obj_t obj_cmd_rs;
	uint64_t val = 0;
	int ret;

	if (!ctx || !ctx->ipmi || !state)
		return -EINVAL;

	obj_cmd_rs = fiid_obj_create(tmpl_cmd_get_chassis_status_rs);
	if (!obj_cmd_rs)
		return -ENOMEM;

	ret = ipmi_cmd_get_chassis_status(ctx->ipmi, obj_cmd_rs);
	if (ret < 0) {
		ret = ipmi_ctx_errno(ctx->ipmi);
		goto out;
	}

	ret = ipmi_fiid_get(obj_cmd_rs, "current_power_state.power_is_on",
			    &val);
	if (ret < 0)
		goto out;

	*state = val ? PDI_BMC_POWER_ON : PDI_BMC_POWER_OFF;
	ret = 0;

out:
	fiid_obj_destroy(obj_cmd_rs);
	return ret;
}

static int ipmi_get_device_id_field(fiid_obj_t obj, const char *field,
				    uint64_t *val)
{
	return ipmi_fiid_get(obj, field, val);
}

int pdi_bmc_ipmi_get_device_id(struct pdi_bmc_ipmi_ctx *ctx,
				       struct pdi_bmc_ipmi_device_id *device_id)
{
	fiid_obj_t obj_cmd_rs;
	int ret;

	if (!ctx || !ctx->ipmi || !device_id)
		return -EINVAL;

	memset(device_id, 0, sizeof(*device_id));
	obj_cmd_rs = fiid_obj_create(tmpl_cmd_get_device_id_rs);
	if (!obj_cmd_rs)
		return -ENOMEM;

	ret = ipmi_cmd_get_device_id(ctx->ipmi, obj_cmd_rs);
	if (ret < 0) {
		ret = ipmi_ctx_errno(ctx->ipmi);
		goto out;
	}

	ret = ipmi_get_device_id_field(obj_cmd_rs, "device_id",
				       &device_id->device_id);
	if (ret < 0)
		goto out;
	ret = ipmi_get_device_id_field(obj_cmd_rs,
				       "firmware_revision1.major_revision",
				       &device_id->major);
	if (ret < 0)
		goto out;
	ret = ipmi_get_device_id_field(obj_cmd_rs,
				       "firmware_revision2.minor_revision",
				       &device_id->minor);
	if (ret < 0)
		goto out;
	ret = ipmi_get_device_id_field(obj_cmd_rs,
				       "firmware_revision1.device_available",
				       &device_id->device_available);
	if (ret < 0)
		goto out;
	ret = ipmi_get_device_id_field(obj_cmd_rs, "manufacturer_id.id",
				       &device_id->manufacturer_id);
	if (ret < 0)
		goto out;
	ret = ipmi_get_device_id_field(obj_cmd_rs, "product_id",
				       &device_id->product_id);

out:
	fiid_obj_destroy(obj_cmd_rs);
	return ret;
}

int32_t pdi_bmc_ipmi_standard_get_info(struct pdi_bmc_ipmi_ctx *ctx,
				       struct pdi_bmc_info *info)
{
	struct pdi_bmc_ipmi_device_id device_id;
	char manufacturer[64] = { 0 };
	int ret;

	if (!ctx || !ctx->ipmi || !info)
		return -EINVAL;

	memset(info, 0, sizeof(*info));
	info->protocol = PDI_BMC_PROTOCOL_IPMI;

	ret = pdi_bmc_ipmi_standard_get_power_state(ctx, &info->power_state);
	if (ret < 0)
		info->power_state = PDI_BMC_POWER_UNKNOWN;

	ret = pdi_bmc_ipmi_get_device_id(ctx, &device_id);
	if (ret < 0)
		return ret;

	snprintf(info->manager_id, sizeof(info->manager_id), "device-%llu",
		 (unsigned long long)device_id.device_id);
	snprintf(info->firmware_version, sizeof(info->firmware_version),
		 "%llu.%02llx", (unsigned long long)device_id.major,
		 (unsigned long long)device_id.minor);

	if (ipmi_iana_enterprise_numbers_string(
		    (uint32_t)device_id.manufacturer_id, manufacturer,
		    sizeof(manufacturer)) > 0) {
		ipmi_copy_text(info->model, sizeof(info->model), manufacturer);
	} else {
		snprintf(info->model, sizeof(info->model), "manufacturer-%llu",
			 (unsigned long long)device_id.manufacturer_id);
	}

	snprintf(info->state, sizeof(info->state), "%s product=%llu",
		 device_id.device_available ? "updating" : "enabled",
		 (unsigned long long)device_id.product_id);
	ipmi_copy_text(info->health, sizeof(info->health),
		       device_id.device_available ? "Unavailable" : "OK");
	return 0;
}

static uint8_t ipmi_chassis_control(enum pdi_bmc_power_action action)
{
	switch (action) {
	case PDI_BMC_POWER_ACTION_ON:
		return IPMI_CHASSIS_CONTROL_POWER_UP;
	case PDI_BMC_POWER_ACTION_FORCE_OFF:
		return IPMI_CHASSIS_CONTROL_POWER_DOWN;
	case PDI_BMC_POWER_ACTION_GRACEFUL_SHUTDOWN:
		return IPMI_CHASSIS_CONTROL_INITIATE_SOFT_SHUTDOWN;
	case PDI_BMC_POWER_ACTION_RESTART:
		return IPMI_CHASSIS_CONTROL_POWER_CYCLE;
	case PDI_BMC_POWER_ACTION_FORCE_RESTART:
		return IPMI_CHASSIS_CONTROL_HARD_RESET;
	default:
		return UINT8_MAX;
	}
}

int32_t pdi_bmc_ipmi_standard_power_control(
	struct pdi_bmc_ipmi_ctx *ctx, enum pdi_bmc_power_action action)
{
	fiid_obj_t obj_cmd_rs;
	uint8_t control;
	int ret;

	if (!ctx || !ctx->ipmi)
		return -EINVAL;

	control = ipmi_chassis_control(action);
	if (!IPMI_CHASSIS_CONTROL_VALID(control))
		return -EINVAL;

	obj_cmd_rs = fiid_obj_create(tmpl_cmd_chassis_control_rs);
	if (!obj_cmd_rs)
		return -ENOMEM;

	ret = ipmi_cmd_chassis_control(ctx->ipmi, control, obj_cmd_rs);
	if (ret < 0)
		ret = ipmi_ctx_errno(ctx->ipmi);

	fiid_obj_destroy(obj_cmd_rs);
	return ret;
}

static int ipmi_open(const struct pdi_bmc_open_params *params,
		     void **backend_ctx)
{
	static const struct pdi_bmc_ipmi_open_mode modes[] = {
		{
			.authentication_type = IPMI_AUTHENTICATION_TYPE_MD5,
			.workaround_flags = IPMI_WORKAROUND_FLAGS_DEFAULT,
			.name = "ipmi lan open md5",
		},
		{
			.authentication_type = IPMI_AUTHENTICATION_TYPE_MD5,
			.workaround_flags =
				IPMI_WORKAROUND_FLAGS_OUTOFBAND_AUTHENTICATION_CAPABILITIES,
			.name = "ipmi lan open md5 authcap",
		},
		{
			.authentication_type = IPMI_AUTHENTICATION_TYPE_STRAIGHT_PASSWORD_KEY,
			.workaround_flags = IPMI_WORKAROUND_FLAGS_DEFAULT,
			.name = "ipmi lan open password-key",
		},
		{
			.authentication_type = IPMI_AUTHENTICATION_TYPE_NONE,
			.workaround_flags = IPMI_WORKAROUND_FLAGS_DEFAULT,
			.name = "ipmi lan open none",
		},
	};
	struct pdi_bmc_ipmi_ctx *ctx;
	char endpoint[PDI_BMC_MAX_ENDPOINT_LEN];
	char username[PDI_BMC_MAX_USERNAME_LEN];
	char password[PDI_BMC_MAX_PASSWORD_LEN];
	int ret;
	int last_ret = -EIO;

	if (!params || !params->endpoint || !params->endpoint[0] || !backend_ctx)
		return -EINVAL;

	ret = pdi_bmc_copy_string(endpoint, sizeof(endpoint), params->endpoint);
	if (ret < 0)
		return ret;
	ret = pdi_bmc_copy_string(username, sizeof(username), params->username);
	if (ret < 0)
		return ret;
	ret = pdi_bmc_copy_string(password, sizeof(password), params->password);
	if (ret < 0)
		return ret;

	ctx = calloc(1, sizeof(*ctx));
	if (!ctx)
		return -ENOMEM;

	ctx->timeout_ms = params->timeout_ms;
	ctx->ipmi = ipmi_ctx_create();
	if (!ctx->ipmi) {
		ret = errno ? -errno : -ENOMEM;
		goto err_free;
	}

	for (size_t i = 0; i < (sizeof(modes) / sizeof((modes)[0])); i++) {
		ret = ipmi_ctx_open_mode(ctx, endpoint, username, password,
					 &modes[i]);
		if (ret == 0) {
			*backend_ctx = ctx;
			return 0;
		}

		last_ret = ret;
		if (ret == -EINVAL)
			break;
	}

	ret = last_ret;
	ipmi_ctx_destroy(ctx->ipmi);
err_free:
	free(ctx);
	return ret;
}

static void ipmi_close(void *backend_ctx)
{
	struct pdi_bmc_ipmi_ctx *ctx = backend_ctx;

	if (!ctx)
		return;

	if (ctx->ipmi) {
		ipmi_ctx_close(ctx->ipmi);
		ipmi_ctx_destroy(ctx->ipmi);
	}
	free(ctx);
}

static const struct pdi_bmc_ipmi_vendor_ops *
ipmi_vendor(struct pdi_bmc_ipmi_ctx *ctx)
{
	if (!ctx)
		return NULL;

	if (!ctx->vendor_selected) {
		ctx->vendor = pdi_bmc_ipmi_vendor_detect(ctx);
		ctx->vendor_selected = true;
	}

	return ctx->vendor;
}

static int32_t ipmi_request(void *backend_ctx,
			    const struct pdi_bmc_backend_request *request)
{
	struct pdi_bmc_ipmi_ctx *ctx = backend_ctx;
	const struct pdi_bmc_ipmi_vendor_ops *vendor;
	int32_t ret;

	if (!ctx || !request)
		return -EINVAL;

	vendor = ipmi_vendor(ctx);

	switch (request->type) {
	case PDI_BMC_BACKEND_REQ_GET_INFO:
		if (vendor && vendor->get_info) {
			ret = vendor->get_info(ctx, request->args.info);
			if (ret != -ENOTSUP)
				return ret;
		}
		return pdi_bmc_ipmi_standard_get_info(ctx, request->args.info);
	case PDI_BMC_BACKEND_REQ_GET_POWER_STATE:
		if (vendor && vendor->get_power_state) {
			ret = vendor->get_power_state(ctx, request->args.state);
			if (ret != -ENOTSUP)
				return ret;
		}
		return pdi_bmc_ipmi_standard_get_power_state(
			ctx, request->args.state);
	case PDI_BMC_BACKEND_REQ_POWER_CONTROL:
		if (vendor && vendor->power_control) {
			ret = vendor->power_control(ctx, request->args.action);
			if (ret != -ENOTSUP)
				return ret;
		}
		return pdi_bmc_ipmi_standard_power_control(
			ctx, request->args.action);
	case PDI_BMC_BACKEND_REQ_GET_SENSORS:
		if (!request->args.sensors.count)
			return -EINVAL;
		*request->args.sensors.count = 0;
		return -ENOTSUP;
	default:
		return -EINVAL;
	}
}

const struct pdi_bmc_backend_ops pdi_bmc_ipmi_ops = {
	.name = "ipmi",
	.protocol = PDI_BMC_PROTOCOL_IPMI,
	.open = ipmi_open,
	.close = ipmi_close,
	.request = ipmi_request,
};
