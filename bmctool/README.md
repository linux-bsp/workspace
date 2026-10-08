# bmctool

`bmctool` is a temporary standalone copy of the PAF BMC implementation. It
builds `libbmctool.so` without a PAF build or runtime dependency. The original
PAF BMC implementation remains available in `libpdi.so`. The public header is
`bmctool/pdi_bmc.h`; existing `pdi_bmc_*` function names and structures are
retained for callers. Do not link both libraries into the same application
when using these symbols.

## Build

```sh
cmake -S bmctool -B /tmp/bmctool-build -DBMC_REDFISH=ON
cmake --build /tmp/bmctool-build
cmake --install /tmp/bmctool-build --prefix /usr
```

Redfish requires libcurl and cJSON. IPMI requires libfreeipmi. PMCP uses POSIX
sockets only. Select backends with `BMC_REDFISH`, `BMC_IPMI`, and `BMC_PMCP`;
at least one must be enabled. Redfish vendor support uses
`BMC_REDFISH_VENDOR_SUPERMICRO` and `BMC_REDFISH_VENDOR_XFUSION`.

Buildroot selects these backends with `BR2_PACKAGE_BMCTOOL_*`. The package is
independent of PAF. Applications using this copy link `libbmctool.so` and
include `<bmctool/pdi_bmc.h>`.

See [docs/integration.md](docs/integration.md) for API and protocol details.
