# A10 AM625 MCU 查询、身份与健康验收

2026-11-28；[工程记录](../../../../edk/docs/archive/framework-modules/a10-validation.md)，E=`output/edk-framework-modules-a10-20261128-165831-9eaSQH/`。

指定设备 HWID 1010001000110000、MAC 1c:63:49:22:c4:f7，v0.0.1/packed 1，完整 ID `3578cf0e2329e52e595698d516fb9494d4d9073279ef91f68894468010c67f42`，kernel `5ec31a01ff80cfe9f943bcf4c32892bc995eaa768c9ce0a8497a21c74fd28950`，rootfs `f41a4f1a8a406e95f7795bf0b2cfc6d87d2a9e878a848cb8e330f0a786e472f1`，OTA `303a8de033d158c49e17f0f03eb348f520f926a73db6dc6b6b5c14caec6306ee`。publication `draft-qnH0V1`，2026-11-28T17:07:22+08:00；2026-11-28T17:09:04.175049+08:00 id=3578cf0e2329e52e595698d516fb9494d4d9073279ef91f68894468010c67f42 phase=success running=1 target=1 quarantined=False。

串口确认新 boot `5c420f5e-41f6-4a0a-8baf-528ae732ba48`、B 槽 confirmed；fwctl version、ota-status、ota-check 与现役完整身份、success/running=1 相符，FWCHECK1 match、8 active、0 failed、11 实装 SHA 匹配。实装 `/etc/edk/satellite.conf` builtin 选择 phytium-s5000c，OTA 前后真实 IPC 分别返回 status=`{"mcu_enabled":false}`、telemetry=`{"mcu":null}`，--check-config、ptelemetryd/psatellited active、fwctl health-check 合格。小容量由真实主机 provider 隔离夹具覆盖；其他真实服务器只读，未安装 bootloader 不计验。E/board-query-before.log、final/board-query-after.log、board-installed.log、serial-key.log、board-package-compare.log、device-transaction.json。通过。
