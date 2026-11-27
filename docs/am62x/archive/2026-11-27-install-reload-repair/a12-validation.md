# A12：独立安装契约矩阵 AM625 验收

[工程记录](../../../../edk/docs/archive/2026-11-27-install-reload-repair/a12-validation.md)。E=`output/edk-install-reload-a12-20261127-163036-ExQ4Xc/`，F=E/final/，2026-11-27。

**范围复用，未构建正式候选。** A12 仅测试/文档，原 A11 OTA 包 SHA abc1da493b10c0ea94f35e5ed86cf7db5fcc99994c4ae7c16450f35e1b3ce07c，实际正式配置不启用测试，非测试/非文档源文件与 A11 构建快照及实际两包拷贝 834/834 一致，真实安装清单无测试。原包摘要核验、范围及正式输入证据见 E/reused-ota-check.log、production-source-scope.log、formal-tests-config.log、formal-install-manifests.log。不是本次重新构建的候选。

可信 A11 SSH key、MAC 1c:63:49:22:c4:f7、HWID 1010001000110000，boot d87217b2-c6bb-4ead-a790-e435dfa18802，A 槽确认、完整 ID e85826657468ad6d048ec954e8f2a367da455b0f9b50b59017edee0931a97b3c、v0.0.1 packed 1，FWCHECK1 match、健康、8 active、0 failed，9/9 实装 SHA 对原 A11 真实 rootfs.tar 匹配。E/board-start.log、F/board-check.log、board-package-compare.log、reused-firmware-identity.json。

本阶段 E/arm-matrix/matrix.tsv 135 个主机 ARM64 写前、编译链接格；原生 163 个真实执行格，真实 x86-64/AArch64 双向各八入口误装拒绝（E/cross-layout-replay.log、前后整树），配套重试。F/board-probes.tar 使用此次冻结源码的实际 ARM64 配套安装树及真实跨架构拒绝后的原前缀，不用正式同名库补齐；2819 个文件 SHA、956 个链接逐项在临时目录核对。26 个 SDK 前缀各自 CMake/pc 独立交叉编译的 52 个 probe 退出 0、真实 libbsl 路径匹配；36 个库↔工具组合、49 个命令实体原入口、21 个合法第二入口、受保护 cross-arm 共 107 个真实查询全部退出 0、project=phytium-s5000c，libbsl/libserver 等 EDK loader 实际路径均对应各自临时位置，未执行无效链接。冻结 CAN 消费者只调用空句柄，can-protected/can-added 2 次通过，sdk/managed-sdk/ordinary 三种裁剪后基础 API 成功；旧 A1 冻结消费者已知/未知产品查询正确。F/board-candidate.log、manifest.sha256、links.manifest，E/matrix-board.sha256。

正式 ptelemetryd runtime-status、psatellited --check-config、路由及健康只读核验成功，无真实服务修改或外部服务器控制。临时目录回收；2026-11-27 16:51:25+08:00 最终可信复查原完整 ID、原 boot、确认 A 槽、健康，确切临时路径不存在（E/board-final.log）。未有本次新 publication、未重启、未安装 bootloader。A12 板验通过。
