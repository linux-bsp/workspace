/************************************************************************
 * PDI BMC Redfish backend
 ************************************************************************/

#include "pdi_bmc_redfish_priv.h"
#include "pdi_curl_priv.h"

#include <cjson/cJSON.h>
#include <curl/curl.h>

#include <errno.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define PDI_BMC_REDFISH_DEFAULT_TIMEOUT_MS 5000U

struct pdi_bmc_redfish_ctx {
	char endpoint[PDI_BMC_MAX_ENDPOINT_LEN];
	char username[PDI_BMC_MAX_USERNAME_LEN];
	char password[PDI_BMC_MAX_PASSWORD_LEN];
	uint32_t flags;
	uint32_t timeout_ms;
	char system_path[PDI_BMC_REDFISH_PATH_LEN];
	char manager_path[PDI_BMC_REDFISH_PATH_LEN];
	const struct pdi_bmc_redfish_vendor_ops *vendor;
	bool vendor_selected;
};

struct redfish_buffer {
	char *data;
	size_t len;
};

void pdi_bmc_redfish_copy_text(char *dst, size_t dst_len, const char *src)
{
	if (!dst || !dst_len)
		return;
	if (!src) {
		dst[0] = '\0';
		return;
	}

	snprintf(dst, dst_len, "%s", src);
}

static size_t redfish_write_cb(void *ptr, size_t size, size_t nmemb,
			       void *userdata)
{
	struct redfish_buffer *buf = userdata;
	size_t add = size * nmemb;
	char *next;

	if (!buf || !ptr)
		return 0;

	next = realloc(buf->data, buf->len + add + 1U);
	if (!next)
		return 0;

	buf->data = next;
	memcpy(buf->data + buf->len, ptr, add);
	buf->len += add;
	buf->data[buf->len] = '\0';
	return add;
}

static int redfish_endpoint_url(const struct pdi_bmc_redfish_ctx *ctx,
				char *buf, size_t buf_len, const char *path)
{
	const char *endpoint;
	size_t len;

	if (!ctx || !buf || !buf_len || !path)
		return -EINVAL;

	endpoint = ctx->endpoint;
	if (!endpoint[0])
		return -EINVAL;

	len = strlen(endpoint);
	while (len > 0 && endpoint[len - 1U] == '/')
		len--;

	if (strncmp(endpoint, "http://", 7) == 0 ||
	    strncmp(endpoint, "https://", 8) == 0) {
		if (snprintf(buf, buf_len, "%.*s%s", (int)len, endpoint,
			     path) >= (int)buf_len)
			return -ENAMETOOLONG;
	} else {
		if (snprintf(buf, buf_len, "https://%.*s%s", (int)len,
			     endpoint, path) >= (int)buf_len)
			return -ENAMETOOLONG;
	}

	return 0;
}

int pdi_bmc_redfish_http(struct pdi_bmc_redfish_ctx *ctx, const char *method,
			const char *path, const char *body, char **response_out)
{
	struct redfish_buffer response = { 0 };
	struct curl_slist *headers = NULL;
	char url[512];
	CURL *curl;
	CURLcode code;
	long status = 0;
	long timeout;
	int ret;

	if (response_out)
		*response_out = NULL;
	if (!ctx || !method || !path)
		return -EINVAL;

	ret = redfish_endpoint_url(ctx, url, sizeof(url), path);
	if (ret < 0)
		return ret;

	curl = curl_easy_init();
	if (!curl)
		return -ENOMEM;

	timeout = ctx->timeout_ms ? ctx->timeout_ms :
		PDI_BMC_REDFISH_DEFAULT_TIMEOUT_MS;

	curl_easy_setopt(curl, CURLOPT_URL, url);
	curl_easy_setopt(curl, CURLOPT_CUSTOMREQUEST, method);
	curl_easy_setopt(curl, CURLOPT_TIMEOUT_MS, timeout);
	curl_easy_setopt(curl, CURLOPT_CONNECTTIMEOUT_MS, timeout);
	curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, redfish_write_cb);
	curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
	curl_easy_setopt(curl, CURLOPT_USERAGENT, "libpdi-bmc-redfish/1.0");
	curl_easy_setopt(curl, CURLOPT_NOSIGNAL, 1L);

	if (ctx->username[0] || ctx->password[0]) {
		curl_easy_setopt(curl, CURLOPT_HTTPAUTH, CURLAUTH_BASIC);
		curl_easy_setopt(curl, CURLOPT_USERNAME, ctx->username);
		curl_easy_setopt(curl, CURLOPT_PASSWORD, ctx->password);
	}

	if (ctx->flags & PDI_BMC_OPEN_F_INSECURE_TLS) {
		curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0L);
		curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 0L);
	}

	headers = curl_slist_append(headers, "Accept: application/json");
	if (body) {
		headers = curl_slist_append(headers,
					    "Content-Type: application/json");
		curl_easy_setopt(curl, CURLOPT_POSTFIELDS, body);
		curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE, (long)strlen(body));
	}
	if (headers)
		curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);

	code = curl_easy_perform(curl);
	if (code != CURLE_OK) {
		ret = -EIO;
		goto out;
	}

	curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &status);
	if (status < 200 || status >= 300) {
		ret = status == 401 || status == 403 ? -EACCES : -EIO;
		goto out;
	}

	if (response_out) {
		*response_out = response.data;
		response.data = NULL;
	}
	ret = 0;

out:
	free(response.data);
	if (headers)
		curl_slist_free_all(headers);
	curl_easy_cleanup(curl);
	return ret;
}

static const char *redfish_json_string(cJSON *obj, const char *key)
{
	cJSON *item;

	if (!obj || !key)
		return NULL;
	item = cJSON_GetObjectItemCaseSensitive(obj, key);
	if (!cJSON_IsString(item))
		return NULL;
	return item->valuestring;
}

static const char *redfish_status_string(cJSON *obj, const char *key)
{
	cJSON *status;

	if (!obj || !key)
		return NULL;
	status = cJSON_GetObjectItemCaseSensitive(obj, "Status");
	return redfish_json_string(status, key);
}

int pdi_bmc_redfish_collection_first_path(struct pdi_bmc_redfish_ctx *ctx,
					    const char *collection_path,
					    char *out, size_t out_len)
{
	char *body = NULL;
	cJSON *root = NULL;
	cJSON *members;
	cJSON *first;
	const char *path;
	int ret;

	if (!out || !out_len)
		return -EINVAL;

	ret = pdi_bmc_redfish_http(ctx, "GET", collection_path, NULL, &body);
	if (ret < 0)
		return ret;

	root = cJSON_Parse(body);
	if (!root) {
		ret = -EPROTO;
		goto out;
	}

	members = cJSON_GetObjectItemCaseSensitive(root, "Members");
	if (!cJSON_IsArray(members) || cJSON_GetArraySize(members) <= 0) {
		ret = -ENOENT;
		goto out;
	}

	first = cJSON_GetArrayItem(members, 0);
	path = redfish_json_string(first, "@odata.id");
	if (!path) {
		ret = -EPROTO;
		goto out;
	}

	pdi_bmc_redfish_copy_text(out, out_len, path);
	ret = 0;

out:
	cJSON_Delete(root);
	free(body);
	return ret;
}

int pdi_bmc_redfish_ensure_system_path(struct pdi_bmc_redfish_ctx *ctx)
{
	int ret;

	if (!ctx)
		return -EINVAL;
	if (ctx->system_path[0])
		return 0;

	ret = pdi_bmc_redfish_collection_first_path(ctx, "/redfish/v1/Systems",
					    ctx->system_path,
					    sizeof(ctx->system_path));
	if (ret < 0)
		pdi_bmc_redfish_copy_text(ctx->system_path, sizeof(ctx->system_path),
				  "/redfish/v1/Systems/1");

	return 0;
}

const char *pdi_bmc_redfish_system_path(struct pdi_bmc_redfish_ctx *ctx)
{
	if (!ctx || !ctx->system_path[0])
		return NULL;

	return ctx->system_path;
}

int pdi_bmc_redfish_ensure_manager_path(struct pdi_bmc_redfish_ctx *ctx)
{
	if (!ctx)
		return -EINVAL;
	if (ctx->manager_path[0])
		return 0;

	return pdi_bmc_redfish_collection_first_path(ctx, "/redfish/v1/Managers",
					     ctx->manager_path,
					     sizeof(ctx->manager_path));
}

enum pdi_bmc_power_state
pdi_bmc_redfish_power_state_from_string(const char *str)
{
	if (!str)
		return PDI_BMC_POWER_UNKNOWN;
	if (strcmp(str, "On") == 0)
		return PDI_BMC_POWER_ON;
	if (strcmp(str, "Off") == 0)
		return PDI_BMC_POWER_OFF;
	if (strcmp(str, "PoweringOn") == 0)
		return PDI_BMC_POWER_POWERING_ON;
	if (strcmp(str, "PoweringOff") == 0)
		return PDI_BMC_POWER_POWERING_OFF;
	return PDI_BMC_POWER_UNKNOWN;
}

static int redfish_fill_system_info(struct pdi_bmc_redfish_ctx *ctx,
				    struct pdi_bmc_info *info)
{
	char *body = NULL;
	cJSON *root = NULL;
	const char *power;
	int ret;

	if (!ctx || !info)
		return -EINVAL;

	ret = pdi_bmc_redfish_ensure_system_path(ctx);
	if (ret < 0)
		return ret;

	ret = pdi_bmc_redfish_http(ctx, "GET", ctx->system_path, NULL, &body);
	if (ret < 0)
		return ret;

	root = cJSON_Parse(body);
	if (!root) {
		ret = -EPROTO;
		goto out;
	}

	power = redfish_json_string(root, "PowerState");
	info->power_state = pdi_bmc_redfish_power_state_from_string(power);
	pdi_bmc_redfish_copy_text(info->system_id, sizeof(info->system_id),
			  redfish_json_string(root, "Id"));
	pdi_bmc_redfish_copy_text(info->system_model, sizeof(info->system_model),
			  redfish_json_string(root, "Model"));
	pdi_bmc_redfish_copy_text(info->system_manufacturer,
			  sizeof(info->system_manufacturer),
			  redfish_json_string(root, "Manufacturer"));
	pdi_bmc_redfish_copy_text(info->bios_version, sizeof(info->bios_version),
			  redfish_json_string(root, "BiosVersion"));
	pdi_bmc_redfish_copy_text(info->serial_number, sizeof(info->serial_number),
			  redfish_json_string(root, "SerialNumber"));
	ret = 0;

out:
	cJSON_Delete(root);
	free(body);
	return ret;
}

int32_t pdi_bmc_redfish_standard_get_power_state(struct pdi_bmc_redfish_ctx *ctx,
				       enum pdi_bmc_power_state *state)
{
	char *body = NULL;
	cJSON *root = NULL;
	const char *power;
	int ret;

	if (!ctx || !state)
		return -EINVAL;

	ret = pdi_bmc_redfish_ensure_system_path(ctx);
	if (ret < 0)
		return ret;

	ret = pdi_bmc_redfish_http(ctx, "GET", ctx->system_path, NULL, &body);
	if (ret < 0)
		return ret;

	root = cJSON_Parse(body);
	if (!root) {
		ret = -EPROTO;
		goto out;
	}

	power = redfish_json_string(root, "PowerState");
	*state = pdi_bmc_redfish_power_state_from_string(power);
	ret = 0;

out:
	cJSON_Delete(root);
	free(body);
	return ret;
}

const char *pdi_bmc_redfish_reset_type(enum pdi_bmc_power_action action)
{
	switch (action) {
	case PDI_BMC_POWER_ACTION_ON:
		return "On";
	case PDI_BMC_POWER_ACTION_FORCE_OFF:
		return "ForceOff";
	case PDI_BMC_POWER_ACTION_GRACEFUL_SHUTDOWN:
		return "GracefulShutdown";
	case PDI_BMC_POWER_ACTION_RESTART:
		return "GracefulRestart";
	case PDI_BMC_POWER_ACTION_FORCE_RESTART:
		return "ForceRestart";
	default:
		return NULL;
	}
}

int32_t pdi_bmc_redfish_standard_power_control(struct pdi_bmc_redfish_ctx *ctx,
				     enum pdi_bmc_power_action action)
{
	const char *reset_type;
	char action_path[PDI_BMC_REDFISH_PATH_LEN + 64U];
	char body[96];
	int ret;

	if (!ctx)
		return -EINVAL;

	reset_type = pdi_bmc_redfish_reset_type(action);
	if (!reset_type)
		return -EINVAL;

	ret = pdi_bmc_redfish_ensure_system_path(ctx);
	if (ret < 0)
		return ret;

	if (snprintf(action_path, sizeof(action_path),
		     "%s/Actions/ComputerSystem.Reset",
		     ctx->system_path) >= (int)sizeof(action_path))
		return -ENAMETOOLONG;

	if (snprintf(body, sizeof(body), "{\"ResetType\":\"%s\"}",
		     reset_type) >= (int)sizeof(body))
		return -ENAMETOOLONG;

	return pdi_bmc_redfish_http(ctx, "POST", action_path, body, NULL);
}

int32_t pdi_bmc_redfish_standard_get_info(struct pdi_bmc_redfish_ctx *ctx,
					  struct pdi_bmc_info *info)
{
	char *body = NULL;
	cJSON *root = NULL;
	int ret;

	if (!ctx || !info)
		return -EINVAL;

	memset(info, 0, sizeof(*info));
	info->protocol = PDI_BMC_PROTOCOL_REDFISH;
	ret = redfish_fill_system_info(ctx, info);
	if (ret < 0)
		return ret;

	ret = pdi_bmc_redfish_ensure_manager_path(ctx);
	if (ret < 0)
		return 0;

	ret = pdi_bmc_redfish_http(ctx, "GET", ctx->manager_path, NULL, &body);
	if (ret < 0)
		return 0;

	root = cJSON_Parse(body);
	if (!root)
		goto out;

	pdi_bmc_redfish_copy_text(info->manager_id, sizeof(info->manager_id),
			  redfish_json_string(root, "Id"));
	pdi_bmc_redfish_copy_text(info->model, sizeof(info->model),
			  redfish_json_string(root, "Model"));
	pdi_bmc_redfish_copy_text(info->firmware_version,
			  sizeof(info->firmware_version),
			  redfish_json_string(root, "FirmwareVersion"));
	pdi_bmc_redfish_copy_text(info->health, sizeof(info->health),
			  redfish_status_string(root, "Health"));
	pdi_bmc_redfish_copy_text(info->state, sizeof(info->state),
			  redfish_status_string(root, "State"));

out:
	cJSON_Delete(root);
	free(body);
	return 0;
}

static int redfish_path_join(char *out, size_t out_len, const char *base,
				     const char *suffix)
{
	if (!out || !out_len || !base || !suffix)
		return -EINVAL;
	if (snprintf(out, out_len, "%s%s", base, suffix) >= (int)out_len)
		return -ENAMETOOLONG;

	return 0;
}

static char redfish_ascii_tolower(char c)
{
	if (c >= 'A' && c <= 'Z')
		return (char)(c - 'A' + 'a');
	return c;
}

static bool redfish_contains_ci(const char *text, const char *needle)
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
			if (redfish_ascii_tolower(text[i]) !=
			    redfish_ascii_tolower(needle[i]))
				break;
		}
		if (i == needle_len)
			return true;
	}

	return false;
}

static cJSON *redfish_json_object(cJSON *obj, const char *key)
{
	cJSON *item;

	if (!obj || !key)
		return NULL;
	item = cJSON_GetObjectItemCaseSensitive(obj, key);
	if (!cJSON_IsObject(item))
		return NULL;
	return item;
}

static bool redfish_json_number_value(cJSON *item, double *value)
{
	char *end;
	double reading;

	if (!item || !value)
		return false;
	if (cJSON_IsNumber(item)) {
		*value = item->valuedouble;
		return true;
	}
	if (!cJSON_IsString(item) || !item->valuestring)
		return false;

	reading = strtod(item->valuestring, &end);
	if (end == item->valuestring)
		return false;

	*value = reading;
	return true;
}

static bool redfish_json_number(cJSON *obj, const char *key, double *value)
{
	if (!obj || !key)
		return false;
	return redfish_json_number_value(
		cJSON_GetObjectItemCaseSensitive(obj, key), value);
}

static enum pdi_bmc_sensor_type
redfish_sensor_type_from_strings(const char *reading_type, const char *units,
				 const char *name)
{
	if (redfish_contains_ci(reading_type, "temperature") ||
	    redfish_contains_ci(units, "cel") ||
	    redfish_contains_ci(units, "celsius"))
		return PDI_BMC_SENSOR_TYPE_TEMPERATURE;
	if (redfish_contains_ci(reading_type, "power") ||
	    redfish_contains_ci(units, "w"))
		return PDI_BMC_SENSOR_TYPE_POWER;
	if (redfish_contains_ci(reading_type, "fan") ||
	    redfish_contains_ci(units, "rpm") ||
	    redfish_contains_ci(name, "fan"))
		return PDI_BMC_SENSOR_TYPE_FAN;
	if (redfish_contains_ci(reading_type, "voltage") ||
	    redfish_contains_ci(units, "v"))
		return PDI_BMC_SENSOR_TYPE_VOLTAGE;
	if (redfish_contains_ci(reading_type, "current") ||
	    redfish_contains_ci(units, "a"))
		return PDI_BMC_SENSOR_TYPE_CURRENT;
	if (redfish_contains_ci(reading_type, "percent") ||
	    redfish_contains_ci(units, "%"))
		return PDI_BMC_SENSOR_TYPE_UTILIZATION;

	return PDI_BMC_SENSOR_TYPE_ANY;
}

static enum pdi_bmc_sensor_scope
redfish_sensor_scope_from_strings(const char *name, const char *source)
{
	if (redfish_contains_ci(name, "gpu") ||
	    redfish_contains_ci(name, "graphics") ||
	    redfish_contains_ci(source, "gpu") ||
	    redfish_contains_ci(source, "graphics"))
		return PDI_BMC_SENSOR_SCOPE_GPU;
	if (redfish_contains_ci(name, "cpu") ||
	    redfish_contains_ci(name, "processor") ||
	    redfish_contains_ci(source, "processors"))
		return PDI_BMC_SENSOR_SCOPE_CPU;
	if (redfish_contains_ci(name, "dimm") ||
	    redfish_contains_ci(name, "memory"))
		return PDI_BMC_SENSOR_SCOPE_MEMORY;
	if (redfish_contains_ci(name, "fan"))
		return PDI_BMC_SENSOR_SCOPE_FAN;
	if (redfish_contains_ci(name, "psu") ||
	    redfish_contains_ci(name, "power supply"))
		return PDI_BMC_SENSOR_SCOPE_PSU;
	if (redfish_contains_ci(name, "drive") ||
	    redfish_contains_ci(name, "disk") ||
	    redfish_contains_ci(name, "nvme"))
		return PDI_BMC_SENSOR_SCOPE_DRIVE;
	if (redfish_contains_ci(name, "pcie") ||
	    redfish_contains_ci(source, "pcie"))
		return PDI_BMC_SENSOR_SCOPE_PCIE;

	return PDI_BMC_SENSOR_SCOPE_CHASSIS;
}

static void redfish_fill_sensor_status(struct pdi_bmc_sensor *sensor,
				       cJSON *root)
{
	cJSON *status;

	if (!sensor || !root)
		return;
	status = redfish_json_object(root, "Status");
	pdi_bmc_redfish_copy_text(sensor->health, sizeof(sensor->health),
				redfish_json_string(status, "Health"));
	pdi_bmc_redfish_copy_text(sensor->state, sizeof(sensor->state),
				redfish_json_string(status, "State"));
}

static int redfish_add_sensor(struct pdi_bmc_sensor_accumulator *acc,
			      enum pdi_bmc_sensor_type type,
			      enum pdi_bmc_sensor_scope scope,
			      const char *id, const char *name,
			      const char *source, const char *units,
			      double reading, cJSON *status_root)
{
	struct pdi_bmc_sensor sensor;

	if (!acc)
		return -EINVAL;
	if (type == PDI_BMC_SENSOR_TYPE_ANY)
		return 0;

	memset(&sensor, 0, sizeof(sensor));
	sensor.type = type;
	sensor.scope = scope;
	sensor.reading = reading;
	pdi_bmc_redfish_copy_text(sensor.id, sizeof(sensor.id),
				id ? id : name);
	pdi_bmc_redfish_copy_text(sensor.name, sizeof(sensor.name),
				name ? name : id);
	pdi_bmc_redfish_copy_text(sensor.source, sizeof(sensor.source), source);
	pdi_bmc_redfish_copy_text(sensor.units, sizeof(sensor.units), units);
	redfish_fill_sensor_status(&sensor, status_root);
	return pdi_bmc_sensor_accumulator_add(acc, &sensor);
}

static int redfish_collect_sensor_resource(struct pdi_bmc_redfish_ctx *ctx,
					   const char *path,
					   struct pdi_bmc_sensor_accumulator *acc,
					   uint32_t *seen)
{
	char *body = NULL;
	cJSON *root = NULL;
	const char *id;
	const char *name;
	const char *source;
	const char *units;
	const char *reading_type;
	enum pdi_bmc_sensor_type type;
	enum pdi_bmc_sensor_scope scope;
	double reading;
	uint32_t before_count;
	int ret;

	ret = pdi_bmc_redfish_http(ctx, "GET", path, NULL, &body);
	if (ret < 0)
		return ret;

	root = cJSON_Parse(body);
	if (!root) {
		ret = -EPROTO;
		goto out;
	}

	if (!redfish_json_number(root, "Reading", &reading)) {
		ret = 0;
		goto out;
	}

	id = redfish_json_string(root, "Id");
	name = redfish_json_string(root, "Name");
	source = redfish_json_string(root, "@odata.id");
	if (!source)
		source = path;
	units = redfish_json_string(root, "ReadingUnits");
	reading_type = redfish_json_string(root, "ReadingType");
	type = redfish_sensor_type_from_strings(reading_type, units, name);
	scope = redfish_sensor_scope_from_strings(name, source);
	before_count = acc->count;
	ret = redfish_add_sensor(acc, type, scope, id, name, source, units,
				     reading, root);
	if (ret == 0 && seen && acc->count != before_count)
		(*seen)++;

out:
	cJSON_Delete(root);
	free(body);
	return ret;
}

static int redfish_collect_sensors_collection(
	struct pdi_bmc_redfish_ctx *ctx, const char *collection_path,
	struct pdi_bmc_sensor_accumulator *acc, uint32_t *seen)
{
	char *body = NULL;
	cJSON *root = NULL;
	cJSON *members;
	int ret;

	ret = pdi_bmc_redfish_http(ctx, "GET", collection_path, NULL, &body);
	if (ret < 0)
		return ret;

	root = cJSON_Parse(body);
	if (!root) {
		ret = -EPROTO;
		goto out;
	}

	members = cJSON_GetObjectItemCaseSensitive(root, "Members");
	if (!cJSON_IsArray(members)) {
		ret = -EPROTO;
		goto out;
	}

	ret = 0;
	for (int i = 0; i < cJSON_GetArraySize(members); i++) {
		cJSON *member = cJSON_GetArrayItem(members, i);
		const char *path = redfish_json_string(member, "@odata.id");
		int item_ret;

		if (!path)
			continue;
		item_ret = redfish_collect_sensor_resource(ctx, path, acc, seen);
		if (item_ret < 0 && ret == 0)
			ret = item_ret;
	}

out:
	cJSON_Delete(root);
	free(body);
	return ret;
}

static int redfish_collect_thermal_temperatures(
	struct pdi_bmc_redfish_ctx *ctx, const char *thermal_path,
	struct pdi_bmc_sensor_accumulator *acc, uint32_t *seen)
{
	char *body = NULL;
	cJSON *root = NULL;
	cJSON *temps;
	int ret;

	ret = pdi_bmc_redfish_http(ctx, "GET", thermal_path, NULL, &body);
	if (ret < 0)
		return ret;

	root = cJSON_Parse(body);
	if (!root) {
		ret = -EPROTO;
		goto out;
	}

	temps = cJSON_GetObjectItemCaseSensitive(root, "Temperatures");
	if (!cJSON_IsArray(temps)) {
		ret = -EPROTO;
		goto out;
	}

	ret = 0;
	for (int i = 0; i < cJSON_GetArraySize(temps); i++) {
		cJSON *temp = cJSON_GetArrayItem(temps, i);
		const char *id;
		const char *name;
		const char *source;
		double reading;
		uint32_t before_count;
		int item_ret;

		if (!redfish_json_number(temp, "ReadingCelsius", &reading))
			continue;

		id = redfish_json_string(temp, "MemberId");
		name = redfish_json_string(temp, "Name");
		source = redfish_json_string(temp, "@odata.id");
		if (!source)
			source = thermal_path;

		before_count = acc->count;
		item_ret = redfish_add_sensor(
			acc, PDI_BMC_SENSOR_TYPE_TEMPERATURE,
			redfish_sensor_scope_from_strings(name, source), id, name,
			source, "C", reading, temp);
		if (item_ret < 0 && ret == 0)
			ret = item_ret;
		if (item_ret == 0 && seen && acc->count != before_count)
			(*seen)++;
	}

out:
	cJSON_Delete(root);
	free(body);
	return ret;
}

int32_t pdi_bmc_redfish_standard_get_sensors(
	struct pdi_bmc_redfish_ctx *ctx,
	const struct pdi_bmc_sensor_filter *filter,
	struct pdi_bmc_sensor *sensors, uint32_t *count)
{
	struct pdi_bmc_sensor_accumulator acc;
	char chassis_path[PDI_BMC_REDFISH_PATH_LEN];
	char path[PDI_BMC_REDFISH_PATH_LEN + 32U];
	uint32_t seen = 0;
	int ret;
	int last_ret = -ENOTSUP;

	if (!ctx)
		return -EINVAL;

	ret = pdi_bmc_sensor_accumulator_init(&acc, filter, sensors, count);
	if (ret < 0)
		return ret;

	ret = pdi_bmc_redfish_collection_first_path(
		ctx, "/redfish/v1/Chassis", chassis_path,
		sizeof(chassis_path));
	if (ret < 0)
		pdi_bmc_redfish_copy_text(chassis_path, sizeof(chassis_path),
					  "/redfish/v1/Chassis/1");

	ret = redfish_path_join(path, sizeof(path), chassis_path, "/Sensors");
	if (ret == 0)
		ret = redfish_collect_sensors_collection(ctx, path, &acc, &seen);
	if (ret < 0)
		last_ret = ret;

	if (!seen) {
		ret = redfish_path_join(path, sizeof(path), chassis_path,
					"/Thermal");
		if (ret == 0)
			ret = redfish_collect_thermal_temperatures(ctx, path, &acc,
								       &seen);
		if (ret < 0)
			last_ret = ret;
	}

	if (!seen) {
		if (count)
			*count = 0;
		if (last_ret == -EACCES || last_ret == -EINVAL)
			return last_ret;
		return -ENOTSUP;
	}

	return pdi_bmc_sensor_accumulator_finish(&acc);
}

static int redfish_open(const struct pdi_bmc_open_params *params,
			void **backend_ctx)
{
	struct pdi_bmc_redfish_ctx *ctx;
	int ret;

	if (!params || !params->endpoint || !backend_ctx)
		return -EINVAL;

	ret = bmctool_curl_global_init();
	if (ret)
		return ret;

	ctx = calloc(1, sizeof(*ctx));
	if (!ctx)
		return -ENOMEM;

	ret = pdi_bmc_copy_string(ctx->endpoint, sizeof(ctx->endpoint),
				  params->endpoint);
	if (ret < 0)
		goto err_free;
	ret = pdi_bmc_copy_string(ctx->username, sizeof(ctx->username),
				  params->username);
	if (ret < 0)
		goto err_free;
	ret = pdi_bmc_copy_string(ctx->password, sizeof(ctx->password),
				  params->password);
	if (ret < 0)
		goto err_free;

	ctx->flags = params->flags;
	ctx->timeout_ms = params->timeout_ms;
	*backend_ctx = ctx;
	return 0;

err_free:
	free(ctx);
	return ret;
}

static void redfish_close(void *backend_ctx)
{
	free(backend_ctx);
}

static const struct pdi_bmc_redfish_vendor_ops *
redfish_vendor(struct pdi_bmc_redfish_ctx *ctx)
{
	if (!ctx)
		return NULL;

	if (!ctx->vendor_selected) {
		ctx->vendor = pdi_bmc_redfish_vendor_detect(ctx);
		ctx->vendor_selected = true;
	}

	return ctx->vendor;
}

static int32_t redfish_request(void *backend_ctx,
			       const struct pdi_bmc_backend_request *request)
{
	struct pdi_bmc_redfish_ctx *ctx = backend_ctx;
	const struct pdi_bmc_redfish_vendor_ops *vendor;
	int32_t ret;

	if (!ctx || !request)
		return -EINVAL;

	vendor = redfish_vendor(ctx);

	switch (request->type) {
	case PDI_BMC_BACKEND_REQ_GET_INFO:
		if (vendor && vendor->get_info) {
			ret = vendor->get_info(ctx, request->args.info);
			if (ret != -ENOTSUP)
				return ret;
		}
		return pdi_bmc_redfish_standard_get_info(ctx,
							 request->args.info);
	case PDI_BMC_BACKEND_REQ_GET_POWER_STATE:
		if (vendor && vendor->get_power_state) {
			ret = vendor->get_power_state(ctx, request->args.state);
			if (ret != -ENOTSUP)
				return ret;
		}
		return pdi_bmc_redfish_standard_get_power_state(
			ctx, request->args.state);
	case PDI_BMC_BACKEND_REQ_POWER_CONTROL:
		if (vendor && vendor->power_control) {
			ret = vendor->power_control(ctx, request->args.action);
			if (ret != -ENOTSUP)
				return ret;
		}
		return pdi_bmc_redfish_standard_power_control(
			ctx, request->args.action);
	case PDI_BMC_BACKEND_REQ_GET_SENSORS:
		if (vendor && vendor->get_sensors) {
			ret = vendor->get_sensors(ctx, request->args.sensors.filter,
						  request->args.sensors.sensors,
						  request->args.sensors.count);
			if (ret != -ENOTSUP)
				return ret;
		}
		return pdi_bmc_redfish_standard_get_sensors(
			ctx, request->args.sensors.filter,
			request->args.sensors.sensors,
			request->args.sensors.count);
	default:
		return -EINVAL;
	}
}

const struct pdi_bmc_backend_ops pdi_bmc_redfish_ops = {
	.name = "redfish",
	.protocol = PDI_BMC_PROTOCOL_REDFISH,
	.open = redfish_open,
	.close = redfish_close,
	.request = redfish_request,
};
