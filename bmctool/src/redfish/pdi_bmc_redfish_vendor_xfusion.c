/************************************************************************
 * PDI BMC Redfish xFusion iBMC vendor support
 ************************************************************************/

#include "pdi_bmc_redfish_priv.h"

#include <cjson/cJSON.h>

#include <errno.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define XFUSION_CPU_REPORT_PATH "/redfish/v1/TelemetryService/MetricReports/CPUSensor"

static char xfusion_tolower(char c)
{
	if (c >= 'A' && c <= 'Z')
		return (char)(c - 'A' + 'a');
	return c;
}

static bool xfusion_contains_ci(const char *text, const char *needle)
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
			if (xfusion_tolower(text[i]) != xfusion_tolower(needle[i]))
				break;
		}
		if (i == needle_len)
			return true;
	}

	return false;
}

static const char *xfusion_json_string(cJSON *obj, const char *key)
{
	cJSON *item;

	if (!obj || !key)
		return NULL;
	item = cJSON_GetObjectItemCaseSensitive(obj, key);
	if (!cJSON_IsString(item))
		return NULL;
	return item->valuestring;
}

static cJSON *xfusion_json_object(cJSON *obj, const char *key)
{
	cJSON *item;

	if (!obj || !key)
		return NULL;
	item = cJSON_GetObjectItemCaseSensitive(obj, key);
	if (!cJSON_IsObject(item))
		return NULL;
	return item;
}

static bool xfusion_json_number_value(cJSON *item, double *value)
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

static bool xfusion_json_number(cJSON *obj, const char *key, double *value)
{
	if (!obj || !key)
		return false;
	return xfusion_json_number_value(
		cJSON_GetObjectItemCaseSensitive(obj, key), value);
}

static void xfusion_fill_status(struct pdi_bmc_sensor *sensor, cJSON *root)
{
	cJSON *status;

	if (!sensor || !root)
		return;
	status = xfusion_json_object(root, "Status");
	pdi_bmc_redfish_copy_text(sensor->health, sizeof(sensor->health),
				xfusion_json_string(status, "Health"));
	pdi_bmc_redfish_copy_text(sensor->state, sizeof(sensor->state),
				xfusion_json_string(status, "State"));
}

static bool xfusion_relevant_temperature_filter(
	const struct pdi_bmc_sensor_filter *filter)
{
	if (!filter)
		return true;
	if (filter->type != PDI_BMC_SENSOR_TYPE_ANY &&
	    filter->type != PDI_BMC_SENSOR_TYPE_TEMPERATURE)
		return false;

	switch (filter->scope) {
	case PDI_BMC_SENSOR_SCOPE_ANY:
	case PDI_BMC_SENSOR_SCOPE_CPU:
	case PDI_BMC_SENSOR_SCOPE_GPU:
	case PDI_BMC_SENSOR_SCOPE_PCIE:
		return true;
	default:
		return false;
	}
}

static bool xfusion_wants_cpu(const struct pdi_bmc_sensor_filter *filter)
{
	return !filter || filter->scope == PDI_BMC_SENSOR_SCOPE_ANY ||
	       filter->scope == PDI_BMC_SENSOR_SCOPE_CPU;
}

static bool xfusion_wants_pcie(const struct pdi_bmc_sensor_filter *filter)
{
	return !filter || filter->scope == PDI_BMC_SENSOR_SCOPE_ANY ||
	       filter->scope == PDI_BMC_SENSOR_SCOPE_GPU ||
	       filter->scope == PDI_BMC_SENSOR_SCOPE_PCIE;
}

static void xfusion_metric_processor_id(const char *metric_property,
					char *out, size_t out_len)
{
	const char *start;
	size_t len = 0;

	if (!out || !out_len)
		return;
	out[0] = '\0';
	if (!metric_property)
		return;

	start = strstr(metric_property, "/Processors/");
	if (!start)
		return;
	start += strlen("/Processors/");
	while (start[len] && start[len] != '/' && start[len] != '#')
		len++;
	if (!len)
		return;

	if (len >= out_len)
		len = out_len - 1U;
	memcpy(out, start, len);
	out[len] = '\0';
}

static int xfusion_add_cpu_metric(struct pdi_bmc_sensor_accumulator *acc,
				  cJSON *metric, uint32_t index, uint32_t *seen)
{
	struct pdi_bmc_sensor sensor;
	char processor[PDI_BMC_MAX_ID_LEN];
	const char *metric_id;
	const char *metric_property;
	double reading;
	uint32_t before_count;
	int ret;

	metric_id = xfusion_json_string(metric, "MetricId");
	if (metric_id && strcmp(metric_id, "CPUTemperatureReading") != 0)
		return 0;
	if (!xfusion_json_number(metric, "MetricValue", &reading))
		return 0;

	metric_property = xfusion_json_string(metric, "MetricProperty");
	xfusion_metric_processor_id(metric_property, processor, sizeof(processor));

	memset(&sensor, 0, sizeof(sensor));
	sensor.type = PDI_BMC_SENSOR_TYPE_TEMPERATURE;
	sensor.scope = PDI_BMC_SENSOR_SCOPE_CPU;
	sensor.reading = reading;
	if (processor[0]) {
		snprintf(sensor.id, sizeof(sensor.id), "cpu-%.47s-temperature",
			 processor);
		snprintf(sensor.name, sizeof(sensor.name), "CPU %s Temperature",
			 processor);
	} else {
		snprintf(sensor.id, sizeof(sensor.id), "cpu-%u-temperature",
			 index);
		snprintf(sensor.name, sizeof(sensor.name), "CPU %u Temperature",
			 index);
	}
	pdi_bmc_redfish_copy_text(sensor.source, sizeof(sensor.source),
				metric_property ? metric_property : XFUSION_CPU_REPORT_PATH);
	pdi_bmc_redfish_copy_text(sensor.units, sizeof(sensor.units), "C");
	before_count = acc->count;
	ret = pdi_bmc_sensor_accumulator_add(acc, &sensor);
	if (ret == 0 && seen && acc->count != before_count)
		(*seen)++;
	return ret;
}

static int xfusion_collect_cpu_sensors(struct pdi_bmc_redfish_ctx *ctx,
				       struct pdi_bmc_sensor_accumulator *acc,
				       uint32_t *seen)
{
	char *body = NULL;
	cJSON *root = NULL;
	cJSON *values;
	int ret;

	ret = pdi_bmc_redfish_http(ctx, "GET", XFUSION_CPU_REPORT_PATH, NULL,
				       &body);
	if (ret < 0)
		return ret;

	root = cJSON_Parse(body);
	if (!root) {
		ret = -EPROTO;
		goto out;
	}

	values = cJSON_GetObjectItemCaseSensitive(root, "MetricValues");
	if (!cJSON_IsArray(values)) {
		ret = -EPROTO;
		goto out;
	}

	ret = 0;
	for (int i = 0; i < cJSON_GetArraySize(values); i++) {
		cJSON *metric = cJSON_GetArrayItem(values, i);
		int item_ret;

		item_ret = xfusion_add_cpu_metric(acc, metric, (uint32_t)i + 1U,
						   seen);
		if (item_ret < 0 && ret == 0)
			ret = item_ret;
	}

out:
	cJSON_Delete(root);
	free(body);
	return ret;
}

static enum pdi_bmc_sensor_scope xfusion_pcie_scope(bool force_gpu,
						    const char *card_type,
						    const char *name)
{
	if (force_gpu || xfusion_contains_ci(card_type, "gpu") ||
	    xfusion_contains_ci(name, "gpu") ||
	    xfusion_contains_ci(name, "graphics"))
		return PDI_BMC_SENSOR_SCOPE_GPU;

	return PDI_BMC_SENSOR_SCOPE_PCIE;
}

static int xfusion_add_pcie_temperature(struct pdi_bmc_redfish_ctx *ctx,
					const char *path, bool force_gpu,
					struct pdi_bmc_sensor_accumulator *acc,
					uint32_t *seen)
{
	struct pdi_bmc_sensor sensor;
	char *body = NULL;
	cJSON *root = NULL;
	cJSON *oem;
	cJSON *xfusion;
	const char *id;
	const char *name;
	const char *card_type;
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

	oem = xfusion_json_object(root, "Oem");
	xfusion = xfusion_json_object(oem, "xFusion");
	if (!xfusion_json_number(xfusion, "ReadingCelsius", &reading)) {
		ret = 0;
		goto out;
	}

	id = xfusion_json_string(root, "Id");
	name = xfusion_json_string(root, "Name");
	card_type = xfusion_json_string(xfusion, "PCIeCardType");

	memset(&sensor, 0, sizeof(sensor));
	sensor.type = PDI_BMC_SENSOR_TYPE_TEMPERATURE;
	sensor.scope = xfusion_pcie_scope(force_gpu, card_type, name);
	sensor.reading = reading;
	pdi_bmc_redfish_copy_text(sensor.id, sizeof(sensor.id),
				id ? id : name);
	pdi_bmc_redfish_copy_text(sensor.name, sizeof(sensor.name),
				name ? name : id);
	pdi_bmc_redfish_copy_text(sensor.source, sizeof(sensor.source), path);
	pdi_bmc_redfish_copy_text(sensor.units, sizeof(sensor.units), "C");
	xfusion_fill_status(&sensor, root);
	before_count = acc->count;
	ret = pdi_bmc_sensor_accumulator_add(acc, &sensor);
	if (ret == 0 && seen && acc->count != before_count)
		(*seen)++;

out:
	cJSON_Delete(root);
	free(body);
	return ret;
}

static int xfusion_collect_pcie_collection(struct pdi_bmc_redfish_ctx *ctx,
					   const char *collection_path,
					   struct pdi_bmc_sensor_accumulator *acc,
					   uint32_t *seen)
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
		const char *path = xfusion_json_string(member, "@odata.id");
		int item_ret;

		if (!path)
			continue;
		item_ret = xfusion_add_pcie_temperature(ctx, path, false, acc,
							  seen);
		if (item_ret < 0 && ret == 0)
			ret = item_ret;
	}

out:
	cJSON_Delete(root);
	free(body);
	return ret;
}

static int xfusion_collect_graphics_controllers(
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
		char *controller_body = NULL;
		cJSON *controller = NULL;
		cJSON *links;
		cJSON *pcie;
		const char *controller_path;
		const char *pcie_path;
		int item_ret;

		controller_path = xfusion_json_string(cJSON_GetArrayItem(members, i),
							  "@odata.id");
		if (!controller_path)
			continue;

		item_ret = pdi_bmc_redfish_http(ctx, "GET", controller_path, NULL,
						    &controller_body);
		if (item_ret < 0) {
			if (ret == 0)
				ret = item_ret;
			continue;
		}

		controller = cJSON_Parse(controller_body);
		if (!controller) {
			free(controller_body);
			if (ret == 0)
				ret = -EPROTO;
			continue;
		}

		links = xfusion_json_object(controller, "Links");
		pcie = xfusion_json_object(links, "PCIeDevice");
		pcie_path = xfusion_json_string(pcie, "@odata.id");
		if (pcie_path) {
			item_ret = xfusion_add_pcie_temperature(ctx, pcie_path, true,
							      acc, seen);
			if (item_ret < 0 && ret == 0)
				ret = item_ret;
		}

		cJSON_Delete(controller);
		free(controller_body);
	}

out:
	cJSON_Delete(root);
	free(body);
	return ret;
}

static int xfusion_path_join(char *out, size_t out_len, const char *base,
				    const char *suffix)
{
	if (!out || !out_len || !base || !suffix)
		return -EINVAL;
	if (snprintf(out, out_len, "%s%s", base, suffix) >= (int)out_len)
		return -ENAMETOOLONG;

	return 0;
}

static int xfusion_collect_pcie_sensors(struct pdi_bmc_redfish_ctx *ctx,
					struct pdi_bmc_sensor_accumulator *acc,
					uint32_t *seen)
{
	char collection[PDI_BMC_REDFISH_PATH_LEN + 40U];
	char chassis_path[PDI_BMC_REDFISH_PATH_LEN];
	const char *system_path;
	uint32_t before_count = acc->count;
	int ret;
	int last_ret = -ENOTSUP;

	ret = pdi_bmc_redfish_ensure_system_path(ctx);
	if (ret < 0)
		return ret;
	system_path = pdi_bmc_redfish_system_path(ctx);
	if (!system_path)
		return -ENOENT;

	ret = xfusion_path_join(collection, sizeof(collection), system_path,
				 "/PCIeDevices");
	if (ret == 0)
		ret = xfusion_collect_pcie_collection(ctx, collection, acc, seen);
	if (ret < 0)
		last_ret = ret;
	if (acc->count != before_count)
		return 0;

	ret = xfusion_path_join(collection, sizeof(collection), system_path,
				 "/GraphicsControllers");
	if (ret == 0)
		ret = xfusion_collect_graphics_controllers(ctx, collection, acc,
							       seen);
	if (ret < 0)
		last_ret = ret;
	if (acc->count != before_count)
		return 0;

	ret = pdi_bmc_redfish_collection_first_path(
		ctx, "/redfish/v1/Chassis", chassis_path, sizeof(chassis_path));
	if (ret < 0)
		pdi_bmc_redfish_copy_text(chassis_path, sizeof(chassis_path),
					  "/redfish/v1/Chassis/1");
	ret = xfusion_path_join(collection, sizeof(collection), chassis_path,
				 "/PCIeDevices");
	if (ret == 0)
		ret = xfusion_collect_pcie_collection(ctx, collection, acc, seen);
	if (ret < 0)
		last_ret = ret;

	return last_ret == -ENOTSUP ? 0 : last_ret;
}

static int xfusion_probe(struct pdi_bmc_redfish_ctx *ctx)
{
	const char *system_path;
	char *body = NULL;
	int ret;

	if (!ctx)
		return -EINVAL;

	ret = pdi_bmc_redfish_ensure_system_path(ctx);
	if (ret < 0)
		return ret;
	system_path = pdi_bmc_redfish_system_path(ctx);
	if (!system_path)
		return -ENOENT;

	ret = pdi_bmc_redfish_http(ctx, "GET", system_path, NULL, &body);
	if (ret < 0)
		return ret;

	ret = xfusion_contains_ci(body, "xFusion") ? 0 : -ENODEV;
	free(body);
	return ret;
}

static const char *xfusion_reset_type(enum pdi_bmc_power_action action)
{
	switch (action) {
	case PDI_BMC_POWER_ACTION_ON:
		return "On";
	case PDI_BMC_POWER_ACTION_FORCE_OFF:
		return "ForceOff";
	case PDI_BMC_POWER_ACTION_GRACEFUL_SHUTDOWN:
		return "GracefulShutdown";
	case PDI_BMC_POWER_ACTION_RESTART:
		return "ForcePowerCycle";
	case PDI_BMC_POWER_ACTION_FORCE_RESTART:
		return "ForceRestart";
	default:
		return NULL;
	}
}

static int32_t xfusion_power_control(struct pdi_bmc_redfish_ctx *ctx,
				     enum pdi_bmc_power_action action)
{
	const char *reset_type;
	const char *system_path;
	char action_path[PDI_BMC_REDFISH_PATH_LEN + 64U];
	char body[96];
	int ret;

	if (!ctx)
		return -EINVAL;

	reset_type = xfusion_reset_type(action);
	if (!reset_type)
		return -EINVAL;

	ret = pdi_bmc_redfish_ensure_system_path(ctx);
	if (ret < 0)
		return ret;
	system_path = pdi_bmc_redfish_system_path(ctx);
	if (!system_path)
		return -ENOENT;

	if (snprintf(action_path, sizeof(action_path),
		     "%s/Actions/ComputerSystem.Reset",
		     system_path) >= (int)sizeof(action_path))
		return -ENAMETOOLONG;
	if (snprintf(body, sizeof(body), "{\"ResetType\":\"%s\"}",
		     reset_type) >= (int)sizeof(body))
		return -ENAMETOOLONG;

	return pdi_bmc_redfish_http(ctx, "POST", action_path, body, NULL);
}

static int32_t xfusion_get_sensors(
	struct pdi_bmc_redfish_ctx *ctx,
	const struct pdi_bmc_sensor_filter *filter,
	struct pdi_bmc_sensor *sensors, uint32_t *count)
{
	struct pdi_bmc_sensor_accumulator acc;
	uint32_t seen = 0;
	int ret;
	int last_ret = -ENOTSUP;

	if (!ctx)
		return -EINVAL;
	if (!xfusion_relevant_temperature_filter(filter))
		return -ENOTSUP;

	ret = pdi_bmc_sensor_accumulator_init(&acc, filter, sensors, count);
	if (ret < 0)
		return ret;

	if (xfusion_wants_cpu(filter)) {
		ret = xfusion_collect_cpu_sensors(ctx, &acc, &seen);
		if (ret < 0)
			last_ret = ret;
	}

	if (xfusion_wants_pcie(filter)) {
		ret = xfusion_collect_pcie_sensors(ctx, &acc, &seen);
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

const struct pdi_bmc_redfish_vendor_ops pdi_bmc_redfish_xfusion_ops = {
	.name = "xfusion",
	.probe = xfusion_probe,
	.power_control = xfusion_power_control,
	.get_sensors = xfusion_get_sensors,
};
