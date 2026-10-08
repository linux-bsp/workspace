/************************************************************************
 * PDI BMC user API
 ************************************************************************/

#ifndef PDI_BMC_API_H
#define PDI_BMC_API_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define PDI_BMC_MAX_ENDPOINT_LEN 256U
#define PDI_BMC_MAX_USERNAME_LEN 64U
#define PDI_BMC_MAX_PASSWORD_LEN 128U
#define PDI_BMC_MAX_ID_LEN 64U
#define PDI_BMC_MAX_TEXT_LEN 128U
#define PDI_BMC_MAX_SOURCE_LEN 256U
#define PDI_BMC_MAX_UNIT_LEN 16U

#define PDI_BMC_OPEN_F_INSECURE_TLS (1U << 0)

enum pdi_bmc_protocol {
	PDI_BMC_PROTOCOL_AUTO = 0,
	PDI_BMC_PROTOCOL_REDFISH = 1,
	PDI_BMC_PROTOCOL_IPMI = 2,
	PDI_BMC_PROTOCOL_PMCP = 3,
};

enum pdi_bmc_power_state {
	PDI_BMC_POWER_UNKNOWN = 0,
	PDI_BMC_POWER_ON = 1,
	PDI_BMC_POWER_OFF = 2,
	PDI_BMC_POWER_POWERING_ON = 3,
	PDI_BMC_POWER_POWERING_OFF = 4,
};

enum pdi_bmc_power_action {
	PDI_BMC_POWER_ACTION_ON = 0,
	PDI_BMC_POWER_ACTION_FORCE_OFF = 1,
	PDI_BMC_POWER_ACTION_GRACEFUL_SHUTDOWN = 2,
	PDI_BMC_POWER_ACTION_RESTART = 3,
	PDI_BMC_POWER_ACTION_FORCE_RESTART = 4,
};

enum pdi_bmc_sensor_type {
	PDI_BMC_SENSOR_TYPE_ANY = 0,
	PDI_BMC_SENSOR_TYPE_TEMPERATURE = 1,
	PDI_BMC_SENSOR_TYPE_POWER = 2,
	PDI_BMC_SENSOR_TYPE_FAN = 3,
	PDI_BMC_SENSOR_TYPE_VOLTAGE = 4,
	PDI_BMC_SENSOR_TYPE_CURRENT = 5,
	PDI_BMC_SENSOR_TYPE_UTILIZATION = 6,
};

enum pdi_bmc_sensor_scope {
	PDI_BMC_SENSOR_SCOPE_ANY = 0,
	PDI_BMC_SENSOR_SCOPE_SYSTEM = 1,
	PDI_BMC_SENSOR_SCOPE_CHASSIS = 2,
	PDI_BMC_SENSOR_SCOPE_CPU = 3,
	PDI_BMC_SENSOR_SCOPE_GPU = 4,
	PDI_BMC_SENSOR_SCOPE_MEMORY = 5,
	PDI_BMC_SENSOR_SCOPE_DRIVE = 6,
	PDI_BMC_SENSOR_SCOPE_FAN = 7,
	PDI_BMC_SENSOR_SCOPE_PSU = 8,
	PDI_BMC_SENSOR_SCOPE_PCIE = 9,
};

struct pdi_bmc_open_params {
	const char *endpoint;
	const char *username;
	const char *password;
	enum pdi_bmc_protocol protocol;
	uint32_t flags;
	uint32_t timeout_ms;
};

struct pdi_bmc_info {
	enum pdi_bmc_protocol protocol;
	enum pdi_bmc_power_state power_state;
	char system_id[PDI_BMC_MAX_ID_LEN];
	char system_model[PDI_BMC_MAX_TEXT_LEN];
	char system_manufacturer[PDI_BMC_MAX_TEXT_LEN];
	char bios_version[PDI_BMC_MAX_TEXT_LEN];
	char serial_number[PDI_BMC_MAX_TEXT_LEN];
	char manager_id[PDI_BMC_MAX_ID_LEN];
	char model[PDI_BMC_MAX_TEXT_LEN];
	char firmware_version[PDI_BMC_MAX_TEXT_LEN];
	char health[PDI_BMC_MAX_TEXT_LEN];
	char state[PDI_BMC_MAX_TEXT_LEN];
};

struct pdi_bmc_sensor_filter {
	enum pdi_bmc_sensor_type type;
	enum pdi_bmc_sensor_scope scope;
};

struct pdi_bmc_sensor {
	enum pdi_bmc_sensor_type type;
	enum pdi_bmc_sensor_scope scope;
	char id[PDI_BMC_MAX_ID_LEN];
	char name[PDI_BMC_MAX_TEXT_LEN];
	char source[PDI_BMC_MAX_SOURCE_LEN];
	char units[PDI_BMC_MAX_UNIT_LEN];
	double reading;
	char health[PDI_BMC_MAX_TEXT_LEN];
	char state[PDI_BMC_MAX_TEXT_LEN];
};

int pdi_bmc_open(const char *endpoint, const char *username,
		 const char *password);
int pdi_bmc_open_ext(const struct pdi_bmc_open_params *params);
int32_t pdi_bmc_close(int fd);
int32_t pdi_bmc_get_info(int fd, struct pdi_bmc_info *info);
int32_t pdi_bmc_get_power_state(int fd, enum pdi_bmc_power_state *state);
int32_t pdi_bmc_power_control(int fd, enum pdi_bmc_power_action action);
int32_t pdi_bmc_get_sensors(int fd,
			    const struct pdi_bmc_sensor_filter *filter,
			    struct pdi_bmc_sensor *sensors, uint32_t *count);

const char *pdi_bmc_protocol_name(enum pdi_bmc_protocol protocol);
const char *pdi_bmc_power_state_name(enum pdi_bmc_power_state state);

#ifdef __cplusplus
}
#endif

#endif /* PDI_BMC_API_H */
