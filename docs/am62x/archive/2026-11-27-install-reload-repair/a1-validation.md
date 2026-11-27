# A1：BSL 安装兼容性 AM625 实机验收

[工程记录](../../../../edk/docs/archive/2026-11-27-install-reload-repair/a1-validation.md)。E=`output/edk-install-reload-a1-20261127-123953-pSpcLm/`，W=E/validated-final/，F=W/final/，2026-11-27。

| 验收 | 实测 |
| --- | --- |
| 身份与基线 | 可信 A4 key，am625/aarch64、MAC `1c:63:49:22:c4:f7`、HWID `1010001000110000`、boot `844d2807-a3b6-415c-a546-c013070f9a61`、A 槽、confirmed successful=1、完整 ID `babb77088af6a68961c66954ad35042ec4e04e2f108cac664d7d3188fd830ae1`。健康正常。 |
| 旧 runtime/SDK 被保护 | 主机从 106104c2d338 编译 ARM64，实际受管更新及 headers 入口拒绝，全部文件、符号链接、SDK metadata 和第三方哨兵前后逐字相同；板上同一冻结旧程序 SHA `ac133cb3696f679d263f6b220c07327c0fc75712004866441d75381565db2527`，两旧前缀各加载本目录 libbsl.so.2，未知 HWID -19/清空、退出 0。W/cross/、F/board-candidate.log。 |
| 新纯核心/独立装配 | core-runtime、core-sdk、isolated-runtime、isolated-sdk 同契约重装成功，板上安装前缀分别加载候选 libbsl.so.2，纯核心 file consumer PASS；独立装配 libsatellite.so.3 实际查询 HWID，v1.0/can0/2000ms，未启动 CAN 或控制任务。 |
| 正式兼容 ABI | 原 A4 兼容候选 runtime/sdk 更新到本轮候选各成功，板上旧程序查询 4 点、1 命令、无覆盖，未知 HWID -19/清空；正式候选与系统 libbsl.so.2 各加载实际库，完整 SHA `4ab3fc4dd2e438ec06de1f1c2337051ef58de1110cdf3de067e0ebd772f40de4`。首次临时板验脚本循环 mode 覆盖外层变量，保留 F/board-candidate-first.log，修正临时 runner 完整复验系统库。 |
| 唯一目标 OTA | 13:02:01+08:00 published `draft-g8EWNz`，13:03:48+08:00 观测 success（running=version=1、未隔离）；完整 ID `47ccc5cdfaad628497513a9c3a051764f18acba6246615ae430844c8745e4173`，tag v0.0.1 packed 1。 |
| 重启及实装 | 物理串口复核真实新 key、MAC/HWID/boot `6b1025fa-c2b9-49f3-a84b-be3c482a208b`，13:03:53+08:00 检查 B 槽 confirmed successful=1、FWCHECK1 match（kernel 12940577 / `fc6761fee796d51f5b1d47bdaeb9cf0ff8de1149bc62e9e88db6681f38d25197`，rootfs 30429184 / `9f7bf61edac94c7e388f1d36f77ee0618e4925b844628faea20c73e1a6e214e7`），健康、8 active、0 failed，9/9 实装文件 SHA 与 rootfs.tar 相符；完整冻结探针及隔离前缀重复通过。F/board-check.log、board-package-compare.log、serial-key.log、board-installed.log。 |

板上执行 F/run-board-candidate.sh 与 F/post-ota-verify.sh；实际 SHA 和符号链接核验前后均通过，探针 tar 独立目录仅在测试期间存在。只读 HWID/配置查询、不访问其他真实服务器控制路径；kernel/rootfs 按授权发布，bootloader raw inputs 逐字不变、未安装。A1 实机验收通过。
