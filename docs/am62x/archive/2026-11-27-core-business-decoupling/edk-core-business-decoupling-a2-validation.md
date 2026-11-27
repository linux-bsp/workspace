# A2：三套 SDK 与遥测契约指定 AM625 专项

[工程验收](../../../../edk/docs/archive/2026-11-27-core-business-decoupling/edk-core-business-decoupling-a2-validation.md)。E=`output/edk-decoupling-a2-20261127-105642-XF42T0/`，F=E/final/。

| 实机证据 | 结果 |
| --- | --- |
| 发布前 | 可信 A1 SSH key，am625/aarch64，MAC `1c:63:49:22:c4:f7`，HWID `1010001000110000`，boot `e1a0b6a9-d485-46ef-8da5-1a669a345fd7`，B 槽确认，运行 ID `0533de4150ef885a209d505fa080b7648e0a0b360c3f8cffd0cbd6d4abe24303`，health 成功。F/board-prepublication.log。 |
| 独立 SDK | `core/lib/libbsl.so.2`、`business/lib/libsatellite.so.3` 实际加载于临时目录，分别原子文件/日志及业务类型、协议 v1.0 通过；上传/前后完整 SHA 均核对，F/board-probes/manifest.sha256、board-candidate.log。core 不替换系统 libbsl。 |
| 样本/IPC | 冻结编号 2 rc=-22、其余合法编号 1、3–8 及边界共 15/15；原三份 IPC 固定字节、query selector、remote sample 拒绝等 8 条通过；只运行无网无设备的 codec/engine 隔离进程。 |
| 兼容 | A1 `legacy_pconfig-arm64` SHA `ac133cb3696f679d263f6b220c07327c0fc75712004866441d75381565db2527` 不重编，候选正式库命中 phytium-s5000c、4 points、1 command、v1.0、无 schedule，未知/格式错误清空输出等全断言通过。 |
| OTA 唯一目标 | 单设备、单 HWID channel 与仅 `.211/32` 的既有发布代理核对；先验证 draft ID/完整 firmware ID/version/HWID。`draft-7i1WUn` 11:10:12+08:00 published，经 installing、boot-testing，11:11:53+08:00 success、running=version=1、未隔离；完整 firmware ID `bf223cb6bff041fb4038c0c8811201131c77e9b5684fb0aa0ada93db06594554`。F/publication.json、upload.json、ota-timeline.log、ota-success.json、device-transaction.json。 |
| 重启及健康 | 新 boot `ace1bf10-fe27-490e-8ebd-312c6060b946`，A 槽 confirmed successful=1；固定物理串口核实新 SSH 指纹，FWCHECK1 match（kernel 12940585 / `c731a9027477ff9ca82af67d6c3ded8e7426c8f5a6bd8ef30e0cbe7b8233a7d3`、rootfs 30429184 / `5da627cb4e01108b2749ea1e9f97376aff47a5762ab3fe5d35991ad9a6c879a3`）；health-check 前后通过、8 active、0 failed，日志同步 ok。F/board-check.log、serial-key.log。 |
| 实装制品复验 | 9/9 SHA 匹配最终 rootfs.tar（四库、PDM、两个业务 daemon、fwctl、logctl）；ptelemetryd SHA `bce54c0b0bc12c43850d5017a9fd2c40b56ed62725e051b0ccf3e645653d68bf`。实际 `/lib64/libbsl.so.2` 解析 `/usr/lib/libbsl.so.0.0.1`（SHA `f7dd1b255569a6443ef63560512428a1f64eed75d5da845449ef5223cfd18969`）；原 A1 ARM64 6 API 全部再次通过，实装库链接 IPC v3 固定向量及候选隔离 schema 再次通过。F/board-package-compare.log、board-installed.log。 |

候选首轮板脚本使用不存在的 tee，改为重定向/回读后通过；重启后 socket activation 尚未生成 dropbear host key，最初两次串口指纹读取失败（保留 serial-key-first/second.log），先获取未信任 public key 触发正常 socket 启动，再准确从物理串口核对 MAC/HWID、新 boot 和 SHA256 指纹，只有匹配后才固定 SSH key，未跳过校验。所有临时目录均由验证脚本清理。其他真实服务器未执行控制操作或变更，不涉及 bootloader 更新；本阶段实机验收通过。
