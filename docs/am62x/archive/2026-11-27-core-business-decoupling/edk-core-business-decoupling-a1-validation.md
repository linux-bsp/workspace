# A1：旧 SDK 与现役产品 AM625 板验

[工程验收与冻结程序](../../../../edk/docs/archive/2026-11-27-core-business-decoupling/edk-core-business-decoupling-a1-validation.md)。E=`output/edk-decoupling-a1-20261127-104317-OsCsrE/`。2026-11-27 10:51:30+08:00，使用 A6.5 已核实的固定可信 SSH host key，先断言 hostname am625、aarch64、MAC `1c:63:49:22:c4:f7`、HWID `1010001000110000`（`fwctl hwid value`），boot `e1a0b6a9-d485-46ef-8da5-1a669a345fd7`，B 槽 confirmed successful=1，tag `v0.0.1` packed 1、完整运行 ID `0533de4150ef885a209d505fa080b7648e0a0b360c3f8cffd0cbd6d4abe24303`。A6.5 publication `draft-IcwVZ8` 的留存设备事务 success/running=1 与当前身份相同；当前 kernel/rootfs 摘要与已确认制品逐字相符，没有新增发布。E/board-before.log、image-comparison.log、frozen/confirmed-device-transaction.json、board-probes.log。

| 实机专项 | 实际结果 |
| --- | --- |
| `fwctl version`、`ota-status`、`ota-check 1` 对应确认制品字节数和完整摘要 | ID、槽位、版本匹配，FWCHECK1 match |
| `fwctl health-check`、8 个正式 unit、failed 列表 | 前后 health 返回 0、8/8 active、0 failed |
| ARM64 核心消费者 | 仅临时文件及日志，回读一致，SHA256 `6517135f9535a19f7deda600e941772f3c2520e7d350c4974459f32159ffb143` 上传前后相同，通过 |
| ARM64 旧 ABI 消费者 | 实际加载 `/lib64/libbsl.so.2`；规范路径 `/usr/lib/libbsl.so.0.0.1`，SHA `f7dd1b255569a6443ef63560512428a1f64eed75d5da845449ef5223cfd18969`；同一旧程序 SHA `ac133cb3696f679d263f6b220c07327c0fc75712004866441d75381565db2527` 上传前后相同；生产 HWID 对应 phytium-s5000c、v1.0、4 点、1 命令、无 schedule；未知合法 HWID -ENODEV/NULL，格式错误 -EINVAL/NULL、缺失视图和零计数等断言均通过 |
| 四公开库实际文件 | BSL、PDI、Server、Satellite 4/4 SHA 匹配确认 rootfs.tar，见 E/frozen/formal-elf/target.sha256、board-probes.log |

初次板脚本的 `date -Is`、第二次的 `sha256sum -c` 为板上 BusyBox 不支持的选项，分别保留 E/board-probes-first.log 与 board-probes-second.log；改显式时间格式、逐文件比较完整摘要后全部通过，未修改系统工具。实际运行探针不发送网络请求或设备控制、不修改系统库和 HWID；三个 `/tmp/edk-decoupling-a1.*` 验证目录均清理，E/board-loader-check.log。双表冲突、不同映射、非空 schedule 对照仅在主机夹具验证，不是正式板变更。A1 板验通过。
