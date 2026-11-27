# A7：遥测验收判定与文档交付 AM625 实机验收

[工程记录](../../../../edk/docs/archive/2026-11-27-install-reload-repair/a7-validation.md)。E=`output/edk-install-reload-a7-20261127-142754-QvziSW/`，C=E/accepted/，F=C/final/，2026-11-27。

可信 A6 key 核验 MAC 1c:63:49:22:c4:f7、HWID 1010001000110000、旧 boot 754f9c8d-c5c5-4caa-943c-b90d0fda5518、B 槽、完整 ID e84272efd2699b83d3b142fa710f299f57797373f5e63db521310c90bb77d4d4，健康。最终版原样入库脚本 SHA 见 F/scripts-host.sha256，板端核对同字节。BusyBox 50ms usleep、100 轮及最终检查，正常阻断 generation/catalog 7/6 s、101 次、内层退出 1、PID 和目录清理通过；只取消一条延时的测试副本分别 2/0 s，均 101 次、内层退出 1、外层退出 1，无误判 PASS。

2026-11-27T14:40:14+08:00 发布 draft-lQ4vbI，最终 OTA tar SHA ffd39530a1cf5ed8a64c18d5cd6f951acb40d707db8564b4831481490ce9f7c3，2026-11-27T14:42:01.459615+08:00 完整 ID 2e37916a65a9c07578facd982fc1169671c6e4f7f36316fe6ccd0fca6a0761dd phase=success running=1 target=1 quarantined=False；重启 boot 85d93e54-a20a-4034-ba28-b2fc6f15d75d、A 槽确认、FWCHECK1 match、健康、8 active、0 failed、9/9 实装文件匹配。发布后重跑真实专项：正常阻断 7/6s、无休眠 2/1s，101 次检查、内层退出 1、外层相应判定以及清理均正确；同字节原脚本节点 19/index4 MCU OFF(2)、节点3/index37 FPGA ON(1)，loaded/optional-board 目录保护及旧绑定采样通过。

真实 main0_thermal 仅读，样本点 4/index 0，质量 FRESH。固定三轮均精确 65300 m°C，真实读数（m°C，前/IPC/后）如下，代次、周期及 sequence 各自独立记录：

| 代次 / 周期 ms | 序号 | 发布前：前/样本/后 | 发布后：前/样本/后 |
| --- | --- | --- | --- |
| 1 / 100 | 1 | 40613 / 40845 / 41077 | 40613 / 41308 / 40613 |
| 2 / 140 | 2 | 40845 / 40613 / 41077 | 40613 / 40845 / 40613 |
| 3 / 180 | 3 | 40845 / 40845 / 40381 | 40613 / 40845 / 40381 |

F/formal-elf/local-ptelemetryd.dynamic、local-ptelemetryd_fixture.dynamic 及 local-elf.sha256 分别核对实际本机构型正式 ELF、夹具 ELF；运行夹具 maps 无 libserver。板端生产正式服务另用正式 IPC 只读核对，F/board-installed.log 保留 DESCRIBE 6 sources/0 commands，节点 2/3 power_state=1（FRESH seq16），节点 3 CPU239 bp、memory465 bp，节点 1 保留真实 -110，未触发任何控制。真实 sysfs 仅 cat，HUP 仅临时夹具 PID，整板路由保持，临时目录和夹具进程全部回收。F/board-candidate.log、board-installed.log、board-check.log、post-ota-verify.log、device-transaction.json、serial-key.log；kernel/rootfs OTA 不宣称 bootloader 安装。A7 实机通过。
