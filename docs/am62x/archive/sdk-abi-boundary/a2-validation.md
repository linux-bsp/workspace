# A2：SDK 分装边界与 ELF 工具兼容 AM625 验收

2026-11-28。[工程记录](../../../../edk/docs/archive/sdk-abi-boundary/a2-validation.md) · [本轮计划](../../../../edk/docs/edk-sdk-abi-boundary-plan.md) · [A1 板验](a1-validation.md)。E=`output/edk-sdk-abi-boundary-a2-20261128-113454-6C2X1m/`、F=E/final。

指定 MAC `1c:63:49:22:c4:f7`、HWID `1010001000110000`、aarch64。可信 A1 SSH key、初始 boot `3cb1870c-fc78-4dd0-a1e0-bafa6d025e68`，B 槽确认，完整现役 ID `56e7c3b9454d9c83fc41eb6838a88abe787615b0bc90c163cf2bd5f857e6dfa5`，fwctl version、ota-status、health-check、路由通过（E/board-start.log）。

E/arm-layout、arm-strict、arm-boundary-final 实际 Buildroot 工具链和宿主 GNU/LLVM readelf 19，共 61 个配套前缀：17 个布局、历史及干净恢复；5 个严格、带空格及旧 include；39 个 A2 前缀含两种旧头刷新/完整受管更新、双分装顺序、双工具分别验收实际 default/GC/strip、16 个已验证历史 target/staging 双工具迁移、源码移除的四种干净运行库/四种已有 SDK、真实防降级后 CAN-on SDK/运行前缀。最终配套重放重新打包，保留先前板验与前缀于 F/board-pre-final-replay/；F/manifest.sha256 与 links.manifest 逐项核对 1517 个实际文件及 230 个软链。每前缀两种真实消费入口和同一修前冻结 ARM64 消费者，合计 183 次真实调用；仅 log/process API，执行本机 /bin/true，不进行 CAN 操控。实际 loader 指向各独立前缀，日志 enum=4、policy=84、偏移68/72/76/80，set/list=0,count=1，落盘 OSALOG1 和 review 42 2 3 25，读回逐项一致。进程 launch=112 io=56、API rc=0、exit=0、signal=0、exec_error=0、pending=0。F/board-candidate.log；目录权限0700，整板路由保持且回收、健康通过。所有拒绝、错配、工具异常仅主机隔离环境。

## 正式发布

固定 v0.0.1，packed 1。候选完整 ID `5eecf33fe086df3b74da6c554dd2c6af39a7069c492dcf441ee8c1919f737a53`，kernel SHA `d3077b086b955cc1a98fbf5c5c2df09d4535eed8221a020d5d5170262a0d913c`，rootfs SHA `a263063397159362d0f239f6e19f0d725e75778f4bbf69ae885c3eec295e675b`，OTA SHA `d9a2540148f85c7a2da25dae91879d82d951f118e7c9bdafbc69381ebdddcef7`；2026-11-28T12:00:39+08:00 发布 `draft-t7dqWa`（F/publication.json），设备报告 `2026-11-28T12:02:28.094278+08:00 id=5eecf33fe086df3b74da6c554dd2c6af39a7069c492dcf441ee8c1919f737a53 phase=success running=1 target=1 quarantined=False`。新 boot `0d062456-105c-4664-b680-878dd4ad6a55`，A 槽确认；串口确认新 SSH key、FWCHECK1 match、健康、8 服务 active、0 failed，9 个实装文件 SHA 与正式 rootfs.tar 一致（F/serial-key.log、board-check.log、board-package-compare.log、device-transaction.json）。F/board-installed.log 原样复跑 183 次；F/official-consumer.log 冻结旧程序实际加载正式 /usr/lib/libbsl.so.2 的进程、日志测试也通过。仅写阶段临时目录，正式策略、其他服务只读，整板路由保持并清理；其他真实服务器未写入或控制。A2 实机验收及本轮完成。
