# bmctool Integration Guide

## Overview

bmctool exposes `pdi_bmc_*()` APIs from `libbmctool.so`. BMC is a remote
network service, so it is handled entirely in userspace. It is not represented
as a PDM kernel device, is not listed by `/dev/pdm_manager`, and does not need a
Device Tree node.

Current implementation status:

- `BMC_REDFISH` builds the Redfish backend and links libcurl/cJSON.
- `BMC_IPMI` builds the IPMI backend and links libfreeipmi.
- `BMC_PMCP` builds the PMCP backend. PMCP is the PAF Management
  Controller Protocol, a private TCP socket protocol for a PAF-defined
  management controller such as an in-band server agent.

There is no central PDI BMC daemon or Unix-socket IPC path in the active
architecture. Applications link against `libbmctool.so` and call the BMC API
directly. PMCP can talk to a product-defined controller process over TCP, but
that process is a backend endpoint rather than a library broker.

## Architecture

```text
Application configuration
  endpoint, credentials, protocol, flags, timeout
        |
        v
libbmctool.so public API
  pdi_bmc_open_ext()
  pdi_bmc_get_info()
  pdi_bmc_get_power_state()
  pdi_bmc_power_control()
  pdi_bmc_get_sensors()
        |
        v
BMC frontend
  handle table
  direct backend selection
  backend request dispatch
      |
      +--> pdi_bmc_redfish backend -> libcurl + cJSON -> HTTPS Redfish BMC
      |
      +--> pdi_bmc_ipmi backend    -> libfreeipmi -> IPMI 1.5 LAN BMC
      |
      +--> pdi_bmc_pmcp backend    -> TCP socket -> PMCP controller
```

The frontend owns common API behavior. Protocol-specific backends implement a
single internal request op and dispatch `get_info`, `get_power_state`,
`power_control`, and `get_sensors` from the request type.

Vendor-specific behavior stays below the protocol backend. Redfish vendor
modules use Redfish helpers such as `pdi_bmc_redfish_http()` and fall back to
the standard Redfish implementation by returning `-ENOTSUP`. IPMI vendor
modules are detected from Get Device ID manufacturer/product information and
fall back to the standard IPMI implementation the same way. The PDI frontend
does not build vendor packets and does not expose vendor-specific public APIs.

`PDI_BMC_PROTOCOL_AUTO` tries the enabled Redfish backend first and then the
enabled IPMI backend. PMCP is selected explicitly with
`PDI_BMC_PROTOCOL_PMCP`, because it targets a private PAF controller endpoint
rather than a standards-based BMC service. A trimmed-out backend is absent from
the candidate list. Selecting an explicit protocol that was not built returns
`-ENOTSUP`; the frontend does not carry placeholder backend objects.

## Configuration

```sh
cmake -S bmctool -B /tmp/bmctool-build \
    -DBMC_REDFISH=ON -DBMC_IPMI=ON -DBMC_PMCP=ON
```

When `BMC_REDFISH=ON`, `libbmctool.so` links against `libcurl` and `cJSON`.
When `BMC_IPMI=ON`, it links against `libfreeipmi`.
When `BMC_PMCP=ON`, it uses POSIX TCP sockets only and does
not add external library dependencies.

## API Use

Pass endpoint, credentials, protocol, flags, and timeout in
`struct pdi_bmc_open_params`:

```c
#include <bmctool/pdi_bmc.h>

struct pdi_bmc_open_params params = {
    .endpoint = "192.168.18.247",
    .username = "ADMIN",
    .password = "Dfts251211..",
    .protocol = PDI_BMC_PROTOCOL_AUTO,
    .flags = PDI_BMC_OPEN_F_INSECURE_TLS,
    .timeout_ms = 10000,
};
struct pdi_bmc_info info;
int fd;
int ret;

fd = pdi_bmc_open_ext(&params);
if (fd < 0)
    return fd;

ret = pdi_bmc_get_info(fd, &info);
pdi_bmc_close(fd);
```

The endpoint and credentials should come from a secure userspace configuration
source in product code. Device Tree should not store network addresses,
usernames, passwords, or backend policy for BMC.

Sensor readings use `pdi_bmc_get_sensors()`. `count` is both input capacity and
output result count. Passing `sensors == NULL` performs a count-only query. If
the provided array is too small, the API returns `-ENOSPC` and still writes the
required count.

```c
struct pdi_bmc_sensor_filter filter = {
    .type = PDI_BMC_SENSOR_TYPE_TEMPERATURE,
    .scope = PDI_BMC_SENSOR_SCOPE_GPU,
};
struct pdi_bmc_sensor sensors[8];
uint32_t count = 8;

ret = pdi_bmc_get_sensors(fd, &filter, sensors, &count);
```


## BMC Validation Tooling

`pdebug` is intentionally limited to PDM manager and peripheral-node
validation; it no longer contains a BMC menu or network credential parser.
BMC AUTO, Redfish, IPMI, and PMCP checks should use a dedicated product or
integration-test utility that obtains credentials from its secure runtime
configuration. A disabled backend returns `-ENOTSUP` when selected explicitly.
PMCP uses the endpoint string and defaults to TCP
port `62300` when the endpoint does not include a port.

## Redfish Vendor Support

Redfish vendor handling is selected inside the Redfish backend. The public PDI
API stays vendor-neutral; applications request power state or sensors by type
and scope.

Current vendor entries:

- Supermicro is kept as an explicit vendor probe for the current validation
  server. It does not override operations yet, so it uses the standard Redfish
  implementation and sensor fallback paths such as `Chassis/*/Sensors` and
  `Chassis/*/Thermal`.
- xFusion iBMC is detected from Redfish resources containing `xFusion`. It
  overrides the non-standard sensor paths documented by the xFusion iBMC
  Redfish interface manual.

For xFusion iBMC, the examples map as follows:

- Power state: standard `GET /redfish/v1/Systems/1` and `PowerState` are already
  covered by the standard Redfish implementation.
- Power control: `POST /redfish/v1/Systems/1/Actions/ComputerSystem.Reset` is
  handled by the xFusion vendor layer so `PDI_BMC_POWER_ACTION_RESTART` maps to
  `ForcePowerCycle`, matching the xFusion allowable values.
- CPU temperature: `GET /redfish/v1/TelemetryService/MetricReports/CPUSensor`,
  reading `MetricValues[]` entries with `MetricId=CPUTemperatureReading` and
  `MetricValue`.
- GPU temperature: first enumerate system PCIe devices, then graphics
  controllers, and finally chassis PCIe devices. The reading is taken from
  `Oem/xFusion/ReadingCelsius`; graphics-controller linked PCIe devices are
  reported with GPU scope, otherwise PCIe scope.

## IPMI Backend

The IPMI backend fills the same internal request contract as Redfish:

- `PDI_BMC_BACKEND_REQ_GET_INFO`
- `PDI_BMC_BACKEND_REQ_GET_POWER_STATE`
- `PDI_BMC_BACKEND_REQ_POWER_CONTROL`
- `PDI_BMC_BACKEND_REQ_GET_SENSORS`

The implementation uses libfreeipmi with IPMI 1.5 LAN out-of-band sessions.
This avoids RMCP+ encryption/random-number requirements and covers simple
commands such as device ID, chassis status, and chassis control. Standard IPMI
data does not provide Redfish-style system serial number, BIOS version, host
system model, or Redfish-style typed sensor records, so those fields are left
empty or return `-ENOTSUP` unless a future OEM extension supplies them.


## PMCP Backend

PMCP means PAF Management Controller Protocol. In the PAF BMC framework, the
PMC is a PAF-defined management controller. The first target implementation is
expected to be an in-band process running on the managed server, but the PDI
side treats it as a peer backend to Redfish and IPMI.

PMCP uses a TCP stream. Endpoint forms are `host`, `host:port`,
`pmcp://host:port`, `tcp://host:port`, or `[ipv6]:port`. If no port is given,
PDI uses `62300`.

Each PMCP frame starts with this fixed 32-byte header. Multi-frame messages use
the same `seq` and monotonically increasing `offset`; the receiver assembles
frames until `offset + data_len == total_len`.

```c
struct pmcp_frame_header {
    uint32_t magic;      /* "PMCP", big endian */
    uint8_t  version;    /* 1 */
    uint8_t  header_len; /* 32 */
    uint16_t flags;      /* bit0=response */
    uint16_t type;
    uint16_t reserved;
    uint32_t seq;
    uint32_t offset;
    uint32_t total_len;
    uint32_t data_len;
    uint32_t crc32;      /* CRC32 over this frame payload */
};
```

All integer payload fields are big endian. Current PDI request types are:

- `1` HELLO: request carries fixed username/password fields; response starts
  with `int32 status` and may report peer frame/message limits.
- `2` GET_INFO: response maps to `struct pdi_bmc_info` and sets protocol PMCP.
- `3` GET_POWER_STATE: response returns a PDI power-state enum value.
- `4` POWER_CONTROL: request carries a PDI power-action enum value.
- `5` GET_SENSORS: request carries sensor type/scope filters; response carries
  a count followed by fixed sensor records. Sensor readings are signed milli
  units, so `42375` means `42.375` in the record units.

The client currently uses 4 KiB maximum frame payloads and 1 MiB maximum full
messages. The service should return negative errno-compatible status values in
responses, for example `-ENOTSUP` for unsupported operations.
