# 新轮次 A1：SDK 双向分装 AM625 验收

2026-11-27。[工程记录](../../../../edk/docs/archive/sdk-install-contract/a1-validation.md) · [本轮板验索引](README.md)。E=`output/edk-sdk-install-contract-a1-20261127-172532-WHvHyv/`，C=E/candidate4/，F=C/final/。

指定 MAC `1c:63:49:22:c4:f7`，HWID `1010001000110000`，aarch64，可信 SSH key。修前 boot `d87217b2-c6bb-4ead-a790-e435dfa18802`，A 槽确认，完整现役固件 ID `e85826657468ad6d048ec954e8f2a367da455b0f9b50b59017edee0931a97b3c`，fwctl version、ota-status、health-check 通过（C/board-start.log，F/board-candidate.log）。

最终候选真实 AArch64 SDK 由 C/arm-split、bmc-arm 生成，配套、两顺序、已编译/仅配置开发头、合法超集、历史恢复、完整 SDK 裁剪及两架构拒绝后恢复。全部错配及整树不变测试在主机，实机只运行配套制品。F/board-probes.tar、board-probes.tar.sha256、manifest.sha256、links.manifest，681 个文件与 112 个软链接逐项核对。24 个 BSL/PDI 前缀和 4 个 Core/EPDU 前缀各经独立 CMake 和 pc 消费者，56 次实际调用 exit=0，实际 loader libbsl/libpdi/libserver 路径与对应独立临时前缀一致。CAN 与 hwmon 探针只用 NULL；BMC 探针仅纯枚举和空对象清理，无总线、控制或外部服务器写。旧六查询冻结消费者已知/未知产品返回正确；正式 ptelemetryd runtime-status、psatellited --check-config、health-check 只读；路由前后相同，临时目录清理通过。F/board-candidate.log。

## 正式发布

正式候选 ID `79086d3bf65f2ea2b7f0171f370e7aa1b24c12944833da4af301c641776d8e4d`，v0.0.1 packed 1，kernel SHA `da03081222321655517d56175e991f2497dd44d684106eb22088a24d9e91289b`、rootfs SHA `522b7dc3b4e1bc99cf05763b53d7d3004222c978dd168d5b1332765d009a924f`，OTA SHA `3cd3bb82142d94f971ae893c576fda073d39a9eec88a0bfdc72e613b42a3c52e`。内容不同于现役，未发布的三个尝试不作为验收。2026-11-27T18:13:38+08:00 发布 `draft-ZiKz5f`（F/publication.json、upload.json）；设备报告 `2026-11-27T18:15:24.584374+08:00 id=79086d3bf65f2ea2b7f0171f370e7aa1b24c12944833da4af301c641776d8e4d phase=success running=1 target=1 quarantined=False`。新 boot `279c4734-de74-4ca5-b0bf-f6e70f0e0a0a`，B 槽确认，FWCHECK1 match，健康、8 个 active、0 failed；串口确认新 SSH key，9/9 实装关键制品 SHA256 与正式镜像一致。F/serial-key.log、board-check.log、board-package-compare.log、ota-timeline.log、device-transaction.json、post-ota-verify.log。

发布后 F/board-installed.log 重新完整运行同一 56 个 ARM64 探针，加载路径、摘要、退出码、旧查询、正式服务只读、整板路由保持、健康与临时目录清理均通过。只对指定 AM625 发布和运行临时资源；其他真实服务器未写入、未控制。A1 实机验收通过。
