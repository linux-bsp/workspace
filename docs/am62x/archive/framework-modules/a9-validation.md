# A9 AM625 身份、查询与健康验收

2026-11-28；[工程记录](../../../../edk/docs/archive/framework-modules/a9-validation.md)，E=`output/edk-framework-modules-a9-20261128-163237-2ylsCJ/`。

指定设备 HWID 1010001000110000、MAC 1c:63:49:22:c4:f7，v0.0.1/packed 1，完整 ID `8aee91f88d8db346a95dcfff83e93273f88f845597358407235123125350f84a`，kernel `884f541ff49d15ab9a76ce1f01dcc88a6d625c47bb2207555bcccc90cde6fa52`，rootfs `10d35fbd44e56a8ce9f1201b4dfd21f251ce49154ce45c267bffef88d79e0622`，OTA `3cf613b9d860934b68b821df7cfaf98fe9abc256550929e501ba71eee770741c`。publication `draft-78dqwJ`，2026-11-28T16:44:09+08:00；2026-11-28T16:45:51.474366+08:00 id=8aee91f88d8db346a95dcfff83e93273f88f845597358407235123125350f84a phase=success running=1 target=1 quarantined=False。

串口确认新 boot `45f09a8b-7399-47c7-922f-ec427792e347`、A 槽 confirmed；`fwctl version`、`fwctl ota-status`、`fwctl ota-check` 与现役完整身份及 success/running=1 相符，FWCHECK1 match、8 active、0 failed、11 实装 SHA 匹配。`/etc/edk/satellite.conf` builtin 产品 phytium-s5000c；实际只读 IPC status=`{"mcu_enabled":false}`，telemetry=`{"mcu":null}`，OTA 前后相同，--check-config、两遥测服务及健康通过。E/board-query-before.log、E/final/board-query-after.log、board-installed.log、serial-key.log、board-package-compare.log、device-transaction.json。其他真实服务器仅只读；不计未安装 bootloader。通过。
