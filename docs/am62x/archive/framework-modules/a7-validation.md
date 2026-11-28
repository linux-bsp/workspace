# A7 AM625 provider 查询验收

2026-11-28；[工程记录](../../../../edk/docs/archive/framework-modules/a7-validation.md)，E=`output/edk-framework-modules-a7-20261128-155326-qtGCyt/`。

指定设备 HWID 1010001000110000、MAC 1c:63:49:22:c4:f7；v0.0.1/packed 1，完整 ID `20ea3fbdae4094cd5d164418250074b74bfbbd0fe8997ad59a661922d21c3b6b`，kernel `9350c859106372d7dfa4c40864e6377b40e1ad311ee1e627c01384a849546d6c`，rootfs `9e63ddba4be44ee6e7359a9e425b076c67791d8240c03cbafbb1dc5ee7b27e2b`，OTA `4f29f4a3b03abe7df36bff1a039820a18f961e7b8e55dfec3647066244bb04b8`。publication `draft-qxRY6X` 2026-11-28T16:01:32+08:00；2026-11-28T16:03:19.461363+08:00 id=20ea3fbdae4094cd5d164418250074b74bfbbd0fe8997ad59a661922d21c3b6b phase=success running=1 target=1 quarantined=False。

串口确认新 boot `b609e694-c7a6-4959-b7c0-0323ee66f220`、B 槽 confirmed，FWCHECK1 match、8 active、0 failed、11 实装 SHA 匹配。实际 `/etc/edk/satellite.conf` builtin 选择 phytium-s5000c；原有 IPC 查询 `ptelemetryd --query status` = `{"mcu_enabled":false}`、`ptelemetryd --query telemetry` = `{"mcu":null}`，OTA 前后均匹配；--check-config、两遥测服务及健康通过。E/board-query-before-retry.log、E/final/board-query-after.log、board-installed.log、serial-key.log、board-package-compare.log、device-transaction.json。隔离夹具负责多 provider/错误注入；其他真实服务器只读；未装 bootloader 未计验。通过。
