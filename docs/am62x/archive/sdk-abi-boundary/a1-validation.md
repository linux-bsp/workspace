# A1：公共 SDK 真实头及进程布局 AM625 验收

2026-11-28。[工程记录](../../../../edk/docs/archive/sdk-abi-boundary/a1-validation.md) · [本轮计划](../../../../edk/docs/edk-sdk-abi-boundary-plan.md)。E=`output/edk-sdk-abi-boundary-a1-20261128-110518-7a7Q2J/`、F=E/final。

指定 MAC `1c:63:49:22:c4:f7`、HWID `1010001000110000`、aarch64。可信 SSH key、初始 boot `2077eca9-cd0c-4bc6-b46d-7a9fb8865983`，A 槽确认，完整现役 ID `e3d61798be66a4f93a1530aeb6765766f8505e16f0fc0a2d4b836c690241386c`，fwctl version、ota-status、health-check、路由（E/board-start.log）。E/legacy-board/board.log 对旧 ARM64 默认布局实测；修前冻结消费者 SHA 83947eb9b825e641a303d8aa954110de9ccdb3ba73783758c549d6544b962cf0，真实旧默认重建和四份正式 V0/V1 target、staging 运行配套正例成功。

E/arm-layout、arm-strict 使用既有 Buildroot GCC，16 个默认、历史及恢复配套前缀，5 个普通/严格/带空格/旧 include 配套前缀。F/board-probes.tar、manifest.sha256、links.manifest 逐项核对 752 个实际文件和 78 个链接；21 前缀各真实 CMake/pkg-config 消费者和同一个冻结旧程序，共 63 次真实调用。实际 loader 指向各独立前缀，日志 enum=4、policy=84、偏移68/72/76/80，set/list=0,count=1，落盘 OSALOG1 和 review 42 2 3 25，读回逐项一致。进程 launch=112 io=56、公开初始化执行 /bin/true，API rc=0、exit=0、signal=0、exec_error=0、pending=0。F/board-candidate.log；目录权限0700，原路由保留且全部回收、健康检查通过。错配和异常仅主机隔离测试。

## 正式发布

固定 v0.0.1，packed 1。实际候选完整 ID `56e7c3b9454d9c83fc41eb6838a88abe787615b0bc90c163cf2bd5f857e6dfa5`，kernel SHA `ef158f8810d7c3ab4ca2b78d31040c6bece29734372e3f8113ab46d1663c75cc`，rootfs SHA `51dda09492e8ce8858ed67d4f034b8c8a786791a44d39dae08c958a6a08eee7d`，OTA SHA `9a10e694d9cc1f0a7ee8528295f84420ce4ab998a849855e4547ffbbddeb49f2`；2026-11-28T11:31:22+08:00 发布 `draft-wT1xjP`（F/publication.json），设备报告 `2026-11-28T11:33:15.336955+08:00 id=56e7c3b9454d9c83fc41eb6838a88abe787615b0bc90c163cf2bd5f857e6dfa5 phase=success running=1 target=1 quarantined=False`。新 boot `3cb1870c-fc78-4dd0-a1e0-bafa6d025e68`，B 槽确认；串口确认新 SSH key、FWCHECK1 match、健康、8 服务 active、0 failed，9 个实装文件 SHA 与正式 rootfs.tar 一致（F/serial-key.log、board-check.log、board-package-compare.log、device-transaction.json）。F/board-installed.log 原样复跑 63 次；F/official-consumer.log 冻结旧程序实际加载正式 /usr/lib/libbsl.so.2 的进程、日志测试也通过。仅写阶段临时目录，正式策略、其他服务只读，整板路由保持并清理。其他真实服务器未写入或控制。阶段验收通过。
