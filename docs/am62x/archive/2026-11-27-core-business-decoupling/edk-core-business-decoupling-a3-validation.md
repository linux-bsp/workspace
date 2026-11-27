# A3：独立产品装配与现役 ABI 2 AM625 专项

[工程、主机映射对照与冻结消费者](../../../../edk/docs/archive/2026-11-27-core-business-decoupling/edk-core-business-decoupling-a3-validation.md)。E=`output/edk-decoupling-a3-20261127-111931-UvNSiJ/`，F=E/final/。

| 验收 | 实测 |
| --- | --- |
| 发布前指定设备 | 可信 A2 key、am625/aarch64、MAC `1c:63:49:22:c4:f7`、HWID `1010001000110000`；boot `ace1bf10-fe27-490e-8ebd-312c6060b946`、slot A 已确认、完整运行 ID `bf223cb6bff041fb4038c0c8811201131c77e9b5684fb0aa0ada93db06594554`，健康正常。F/board-prepublication.log。 |
| 新装配 A | 实际加载隔离前缀 a/lib/libbsl.so.2，SHA `f41ebb7d755d19f41d2ccc4ba10381337e179a2fc46efae702666936f32ea656`；生产 HWID→phytium-s5000c，v1.0、4 points、1 command、无覆盖；实际 Satellite profile can0 / 2000ms，执行器报告对应项目。 |
| 新装配 B | 实际加载隔离前缀 b/lib/libbsl.so.2，同一完整 SHA；同一 HWID→ccm-indexed-cpu，v1.0、2 points、0 commands、CPU schedule 1000ms（同对象身份，复制对象不匹配）；实际 Satellite、执行器配置各通过。两构型未知 HWID -ENODEV/NULL，旧查询动态符号不存在；F/board-probes/manifest.sha256、board-candidate.log。 |
| 正式兼容候选 | 同一 A1 冻结 ARM64 程序 SHA `ac133cb3696f679d263f6b220c07327c0fc75712004866441d75381565db2527`，实际候选正式 libbsl.so.2 SHA `4ab3fc4dd2e438ec06de1f1c2337051ef58de1110cdf3de067e0ebd772f40de4`，6 个 API、数据及未知/无效错误码、缺失视图全部通过。 |
| publication | `draft-oiqgch`，唯一设备及 channel 校验，11:30:56+08:00 published，11:32:47+08:00 success、running=version=1、未隔离。tag v0.0.1 packed 1，完整 ID `2d4fd5368d2230f98b18eaa081044634d54440b2044884e91e65619c7e421d86`。F/publication.json、ota-timeline.log、ota-success.json、device-transaction.json。 |
| 重启后实装 | 物理串口先复核 MAC/HWID、新 SSH 指纹和新 boot `4bd75a3f-3310-4db0-9d6f-cb59913d8bee`，slot B confirmed successful=1、FWCHECK1 match（kernel 12940577 / `845bd085ed23e4269414c46aa76302ae879718e9eea638ad5a6fa211b66b346f`，rootfs 30429184 / `302f81747b4d8a0c6bf0a657f244cdddccd4649533baf9a1dce2b3e7d9962a4b`），8 active、0 failed，健康及日志同步正常；9/9 实装文件 SHA 与正式 rootfs.tar 相符。F/board-check.log、board-package-compare.log、serial-key.log。 |
| 最终复验 | 11:33:16+08:00 起再次运行 A/B 隔离前缀及正式旧消费者。系统 `/lib64/libbsl.so.2` 解析 `/usr/lib/libbsl.so.0.0.1`，SHA 同候选；原 A1 程序未重编、前后 SHA 一致，6 API 及产品查询通过。F/board-installed.log。 |

两套测试装配仅用于临时目录，执行器使用零节点隔离 fixture 的配置检查，未启动控制/网络执行，未改 HWID 或 CAN 状态；测试结束清理独立目录。物理串口及只读查询、OTA 仅指定板。kernel/rootfs 变更按授权发布，bootloader 原始输入逐字不变，不能以本次 OTA 声称安装 bootloader。本阶段实机验收通过。
