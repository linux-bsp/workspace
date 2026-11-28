# A2 核心与管理业务 AM625 验收

2026-11-28。[EDK 工程结论](../../../../edk/docs/archive/framework-modules/a2-validation.md)。
E=output/edk-framework-modules-a2-20261128-135212-qvX2yj/、F=E/final。

指定 AM625 HWID 1010001000110000、MAC 1c:63:49:22:c4:f7。完整正式 ID 39cc6228840d2b9ef23b30db657eb43f5a139614eab0076dd0ee878614131d92、kernel SHA 85a0583710f40e0190211a459faf23b1495e3daaf29981b05d78f842ba768197、rootfs SHA 3401213a70399ea7d51d4057ff3776a043b7f525e10a8c4ca05a59ceaf1dd96c、OTA SHA 1c5611803ebb8bb3905aacddf800dac312b08ae22fb437b1548f5c42f3a15d1a，版本 v0.0.1/packed 1。publication draft-Pf6qG1，2026-11-28T14:13:12+08:00；设备报告 2026-11-28T14:15:04.843107+08:00 id=39cc6228840d2b9ef23b30db657eb43f5a139614eab0076dd0ee878614131d92 phase=success running=1 target=1 quarantined=False。可信串口确认 boot 8b01fd52-0f80-41c6-9203-ba915958b700 与 SSH key，FWCHECK1 match、确认槽、8 active、0 failed，四库、PDM、固件/日志/时间及遥测程序 11 项实装摘要匹配 rootfs.tar。实际 fwctld/logctld/timectld 进程映射、健康、日志 status 与 verify-boot、known r5-spl 只读及 unknown stage rc=2 复测通过（F/board-installed.log、board-package-compare.log、device-transaction.json）。

固件/日志局部 30/30；CI 62/212/104，默认真实包用例补跑，BSP 14/14、镜像 19/19、恢复/加载器检查通过。五项 BSP 测试仅迁移 EDK 源路径/内部链接，BSP 生产边界不变。其他真实服务器只读；未安装 bootloader 不算本次实装验证。阶段通过。
