# A5 应用接口与整体 AM625 验收

2026-11-28。[EDK 工程与独立交接结论](../../../../edk/docs/archive/framework-modules/a5-validation.md)。
E=output/edk-framework-modules-a5-20261128-150109-gBNGZy/、F=E/final。

指定 HWID 1010001000110000、MAC 1c:63:49:22:c4:f7，完整 ID 7413359ba7ab346536d67991d1c58bbcf1b590c69d9434a76446d38081c76a0b、kernel SHA a8671450bb0cabf59c853bf6e0a44627150734ee28932fddcc7347d1130d9882、rootfs SHA db92a3e42dd201ffcf2c07c6c734b56bd230aea07f36a18d64849317ea35bef1、OTA SHA 08e3eb299213b842e245a913008d6fafa76f5ef49cf1ede3952e17ebb3d135ab，v0.0.1/packed 1。publication draft-zBXCIn，2026-11-28T15:15:36+08:00；设备报告 2026-11-28T15:17:25.610719+08:00 id=7413359ba7ab346536d67991d1c58bbcf1b590c69d9434a76446d38081c76a0b phase=success running=1 target=1 quarantined=False。可信串口 boot e716b787-0596-4caa-9fa1-332ad5d0f6d9，确认槽、FWCHECK1 match、8 active、0 failed、健康及四库、PDM、六工具/进程共11项实际 SHA 与正式 rootfs.tar 匹配。fwctld/logctld/timectld 实际进程映射、日志 status/verify-boot、已知 r5-spl、未知阶段 rc=2、复测健康通过。F/board-installed.log、board-package-compare.log、device-transaction.json。

PMC 主机专属功能由真实正式 host-edk pmcd 在隔离网络及临时根目录验证上传、发布、状态、长下载及审计计数，未部署到其他真实服务器。20 项局部、CI 62/212/106、真实包补跑、BSP 14/14、镜像 19/19、恢复与 loader 全通过；独立维护者交接三任务和最终复核通过。四库/进程及协议未改变；实际 PDM build metadata 导致本次镜像身份变化，发布后成功确认。未安装 bootloader 不算实装验收。本轮 A1–A5 完成。
