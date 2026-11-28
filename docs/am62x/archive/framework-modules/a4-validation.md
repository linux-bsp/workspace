# A4 遥测契约与宿主 AM625 验收

2026-11-28。[EDK 工程结论](../../../../edk/docs/archive/framework-modules/a4-validation.md)。
E=output/edk-framework-modules-a4-20261128-144154-lFlXkZ/、F=E/final。

指定 HWID 1010001000110000、MAC 1c:63:49:22:c4:f7，完整 ID c374e13d85ba601b5faab68184cda0f0b7124539da89459cd386306f7fda4b6e、kernel SHA 16fd80099892eb2d986a81224b17dcd7877b000754a66de81705509340828444、rootfs SHA b479b86206270c1eddfb94423eda87b67334e0ef12d7e26209aeca01f8d168a9、OTA SHA 315f9175ce3372a4732b079880297459a049aa3b68d6be6e10fbe6eaf68e461e，v0.0.1/packed 1。publication draft-bBo1I9，2026-11-28T14:53:31+08:00；设备报告 2026-11-28T14:55:14.430569+08:00 id=c374e13d85ba601b5faab68184cda0f0b7124539da89459cd386306f7fda4b6e phase=success running=1 target=1 quarantined=False。可信串口 boot 5cfa5718-5f13-4d3d-bcbb-d0d6a65c693c，确认槽、FWCHECK1 match、8 active、0 failed、健康及 8 实装 SHA 匹配。正式 ptelemetryd/psatellited --check-config、runtime-status、节点只读 probe 发布前后点/索引/provider 集合一致。

实际 AM625 独立 ARM64 本机采集组合（非正式产品预设的 hwmon 功能变更）：E/arm-local.config、arm-local-build.log、board-local-package.sha256；私有临时目录验证真实 thermal_zone0/temp，只读 IPC fresh 样本，100/140/180 ms、三个新 sequence、generation 1→2→3，实际加载隔离 libbsl/libpdi、无 libserver；重启前后复测均通过，临时进程/目录清理，正式服务健康保持。F/board-local-installed.log、board-installed.log、board-package-compare.log、device-transaction.json。CI 62/212/106、真实包补跑、BSP 14/14、镜像 19/19、恢复和 loader 通过。其他真实服务器只读，未安装 bootloader 不计本次实装。阶段通过。
