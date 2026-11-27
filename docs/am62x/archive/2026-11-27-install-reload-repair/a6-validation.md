# A6：序列化 ARM64 安装胜出前缀 AM625 验收

[工程记录](../../../../edk/docs/archive/2026-11-27-install-reload-repair/a6-validation.md)。E=`output/edk-install-reload-a6-20261127-141457-GWhkyA/`，F=E/final/，2026-11-27。

可信 A5 key 核验 MAC 1c:63:49:22:c4:f7、HWID 1010001000110000、旧 boot 54528f60-f3b5-4a8c-b7b3-e1e2b79b4aaa、A 槽、完整 ID f4bd026369af3859fd7fce6312d53609630bdff1d4549f3d8c08e5585de6017c，健康。主机真实 ARM64 普通/普通、受管/受管及双向混合四组胜出树与串行参考一致。F/board-probes.tar 封装这四组实际胜出树；临时板目录校验全部实体 SHA、链接目标、第三方哨兵，四组 ptelemetryd --check-config 均匹配 phytium-s5000c 且加载相应的临时 libbsl.so.2；兼容两组运行 A1 冻结查询消费者正确，系统库的 A1 匹配及未知 HWID 查询通过。真实服务仅读、整板路由前后相同；F/board-candidate.log。板上未安装 CMake、未并发或写入系统前缀。

正式候选 OTA SHA 7631e1a4eca685d939b4c2b0800fe1eaf3835c8fd5c26809f937386823f78cb2。2026-11-27T14:23:23+08:00 发布 draft-QMwKnJ，2026-11-27T14:25:14.857906+08:00 完整 ID e84272efd2699b83d3b142fa710f299f57797373f5e63db521310c90bb77d4d4 phase=success running=1 target=1 quarantined=False；新 boot 754f9c8d-c5c5-4caa-943c-b90d0fda5518、B 槽确认、FWCHECK1 match、健康、8 active、0 failed、9/9 文件与镜像一致。F/serial-key.log、board-check.log、board-package-compare.log、board-installed.log、device-transaction.json。本次发布后同样完成四组胜出前缀运行及健康核对；其他服务器无控制，无 bootloader 安装。A6 实机通过。
