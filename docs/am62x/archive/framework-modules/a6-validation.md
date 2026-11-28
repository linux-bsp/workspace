# A6 AM625 固件身份及现役报告验收

2026-11-28；[工程记录](../../../../edk/docs/archive/framework-modules/a6-validation.md)，E=`output/edk-framework-modules-a6-20261128-153643-QFNxWl/`。

指定设备 HWID 1010001000110000、MAC 1c:63:49:22:c4:f7；固件 v0.0.1/packed 1，完整 ID `fbf95ad60763997067e9abd62cd36062d2519bcafe652c2c40da05cf96ca8b86`，kernel `5aa3a56a0ce1a947d67589d4b7ef7503c2e1c52be2b2a5dd6a559c3ec535c372`，rootfs `4c9c35d72d21c99efa901235be1d0acab1d939d52a3978694626888deabaa1c9`，OTA `82421ef081e410313e37c93a4a02b2026db9d84ff489b959ea545dea1bb73098`。publication `draft-PNZvNw` 2026-11-28T15:47:58+08:00；2026-11-28T15:49:45.087888+08:00 id=fbf95ad60763997067e9abd62cd36062d2519bcafe652c2c40da05cf96ca8b86 phase=success running=1 target=1 quarantined=False。

串口确认 boot `32570932-d411-4167-952d-7368e14021bc`、A 槽 confirmed，`fwctl version`、`fwctl ota-status`、`fwctl ota-check` 与现役 PMC 上报完整身份和运行版本匹配，FWCHECK1 match；健康检查 8 active、0 failed，实际 11 项制品与 rootfs.tar SHA 匹配。复测日志阶段查询；其余真实服务器只读。E/final/board-installed.log、serial-key.log、board-package-compare.log、device-transaction.json。已验证 kernel/rootfs，不计未装 bootloader。通过。
