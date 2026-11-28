# 新轮次 A2：严格 BSL 构建与整轮 SDK ABI AM625 验收

2026-11-28。[工程记录](../../../../edk/docs/archive/sdk-abi-compatibility/a2-validation.md) · [本轮计划](../../../../edk/docs/edk-sdk-abi-compatibility-plan.md) · [A1 板验](a1-validation.md)。E=`output/edk-sdk-abi-compatibility-a2-20261128-103128-y8DQ5D/`，F=E/final/。

指定 MAC `1c:63:49:22:c4:f7`，HWID `1010001000110000`，aarch64，可信 A1 SSH key。开工 boot `9df4b3ce-4fa4-4a10-a2c8-9aec3a8c3e16`，B 槽确认，完整现役 ID `1bab5b05507f357b4dbf15f3892cc6f22746384f45976d528f53b999ebc7e5ea`，fwctl version、ota-status、health-check 通过（E/board-start.log）。

E/arm-strict 实际 Buildroot GCC AArch64 BSL-only 严格构建，真实 `-Werror=missing-prototypes` 到达保留的 ABI 探针、BSL runtime 源编译、独立 CMake/pc 消费者；仅配置头包成功、补装实际库。strict/default 完整库 SHA 同为 `a03b5a3317a5fc2583f9205a82aa2b4a920bdd2e637cb37ec74ceb439158c288`，布局证明、SONAME 保持。E/arm-layout 重新生成完整 A1 12 个配套与恢复前缀，另本阶段 strict/default 两前缀；F/board-probes.tar、board-probes.tar.sha256、manifest.sha256、links.manifest 596 个文件与 56 个链接逐项核对。14 个前缀各真实 CMake/pc 和同一个 A1 前冻结旧程序，42 次实际调用。所有目录 0700、libbsl 实际加载对应 staging 前缀，domain=review/event=42、enum=4 policy=84、字段偏移 68/72/76/80，真实 set/list 0、count=1，文件 `OSALOG1
review 42 2 3 25
`、读回 2/3/25，exit=0。严格/短枚举错误方向、历史不明库及其他拒绝/反证均只在主机，板上不运行错配。仅独立临时策略目录，正式策略和正式服务只读，整板路由保持、健康及回收通过。F/board-candidate.log。

## 正式发布

正式候选 ID `e3d61798be66a4f93a1530aeb6765766f8505e16f0fc0a2d4b836c690241386c`，固定 v0.0.1 packed 1，kernel SHA `e58453fcb58f367c09eb62ddefa1f93d9b65a00326a7f79f87b9e693f69cc671`、rootfs SHA `335712c4d7fbdde593883e150560a3cdd33352d4d4091a721ca1bb1d55ebd833`、OTA SHA `d3d3e36f2f4e7eac4a1e16150e89bcc91799961ee8da75b07011b94227b904d4`。四库实际二进制与 A1 相同，实际 PDM 构建标识及可安装内容变化；2026-11-28T10:50:28+08:00 发布 `draft-1yfKqh`（F/publication.json、upload.json）；设备报告 `2026-11-28T10:52:19.759894+08:00 id=e3d61798be66a4f93a1530aeb6765766f8505e16f0fc0a2d4b836c690241386c phase=success running=1 target=1 quarantined=False`。新 boot `2077eca9-cd0c-4bc6-b46d-7a9fb8865983`，A 槽确认，FWCHECK1 match，健康、8 个 active、0 failed；串口核验新 SSH key，9/9 正式实装 SHA 匹配 rootfs.tar。F/serial-key.log、board-check.log、board-package-compare.log、ota-timeline.log、device-transaction.json、post-ota-verify.log。

发布后 F/board-installed.log 原样复跑 42 次字段探针，实际加载路径、摘要、退出码、字段、权限、健康、路由及清理均通过。只对指定 AM625 发版，其他真实服务器未写入/控制。A2 通过，本轮 AM625 验收完成。
