# A3：遥测实例重载及正式 AM625 实机验收

[工程、源码及主机回归](../../../../edk/docs/archive/2026-11-27-install-reload-repair/a3-validation.md)。E=`output/edk-install-reload-a3-20261127-131717-1C69jJ/`，F=E/final/，2026-11-27。

| 验收 | 实测 |
| --- | --- |
| 发布前设备 | 可信 A1 key、am625/aarch64、MAC `1c:63:49:22:c4:f7`、HWID `1010001000110000`、boot `6b1025fa-c2b9-49f3-a84b-be3c482a208b`、B 槽 confirmed、完整 ID `47ccc5cdfaad628497513a9c3a051764f18acba6246615ae430844c8745e4173`。 |
| 纯本机 ARM64 production/fixture | 清洁 local 构型无 libserver NEEDED，实际运行 fixture maps 无 libserver；注入属性 65300 m°C，point 4/index 0，generation 1→2→3、period 100→140→180，sequence 1/2/3 新鲜值，第二次 HUP 更换未使用目录路径。两次 HUP 成功。 |
| 真实板载属性 | 按 name 查到 `main0_thermal` / `/sys/class/hwmon/hwmon0/temp1_input`，候选首轮读值前 40845/后 40381 m°C；三个实际样本依次 41308/40845/40613 m°C。重启后前 40381/后 40613 m°C，三个新鲜样本 40613/41077/41077 m°C；均在实际前值 ±2000 m°C 窗口内，非注入值。 |
| 已加载目录 | A2 原脚本 SHA `b38c34fa79ec77660ff222c5d3e3196654ff2521bdee8a904a0b757c54a84157`，同字节原样运行，FPGA fixture node 3/index37/ON(1)、MCU fixture node19/index4/OFF(2)；错绑 -19、重复 index -17，正常 HUP generation 2，原路径 index 修改 -116。新增 loaded script 同路径合法更新后，另一相同内容目录路径 -95，原路径同字节新 inode -116，原代次 2、绑定和两新鲜样本保持。 |
| 已选目录但启动缺失 | 可选 FPGA 项目 transport-free 夹具，0 sources/commands，原路径继续缺失 HUP 从 1→2；换另一缺失路径 -95、原路径出现 node_count=0 文件 -116，保留 generation 2、0 sources/commands，服务查询正常、不重绑。所有 HUP 限当次隔离 fixture PID，临时目录空、无该 fixture 映射残留。 |
| 正式只读产品 | 原 A1 发布前 IPC DESCRIBE 6 sources/0 commands，BMC index2/3 ON、PMC index3 CPU 47 bp/memory 462 bp；实装 A3 仍 6/0、BMC index2/3 ON (sequence 13, FRESH)、PMC index3 CPU 359 bp（3.59%）/memory 462 bp（4.62%），合并点一致，星务 v1.0/can0。BMC index1 发布前后持续 -110、quality=3，未配置 PMC index1/2 -95；没有掩盖错误或对其他服务器执行控制。 |
| 正式旧 ABI | A1 冻结 ARM64 程序 SHA `ac133cb3696f679d263f6b220c07327c0fc75712004866441d75381565db2527` 未重编，实际候选和系统 libbsl.so.2 SHA `4ab3fc4dd2e438ec06de1f1c2337051ef58de1110cdf3de067e0ebd772f40de4`，phytium-s5000c 四点/一命令/无覆盖，未知 HWID -19/输出清空均通过。 |
| publication | `draft-ut6Ztn`，13:25:21+08:00 published、13:26:57+08:00 观测 success/running=version=1、未隔离，唯一目标及 channel。完整 ID `36ffeb03271a8db9a3365f20b2c4732642d3aaf34667bf72a43de90e93ce4bb7`，v0.0.1 packed 1。 |
| 重启及实装 | 物理串口复核新 SSH 指纹、MAC/HWID、boot `b5e07085-a443-4365-8451-2d72bcbff67a`；13:27:02+08:00 检查 A 槽 confirmed successful=1、FWCHECK1 match（kernel 12940577 / `a3603db8c0d4bc9dd5418ae7107b504d1439faf3678e5e93c3385e1be4663725`，rootfs 30429184 / `52642cd695f552572058c607b6cf283d4305d220bb044b5c159011272c8f5d29`），8 active、0 failed，日志和健康通过，9/9 实装文件 SHA 与 rootfs.tar 匹配。正式程序复验、所有 ARM64 隔离专项重复通过。 |

F/board-candidate.log、board-installed.log、board-probes/manifest.sha256、scripts-host.sha256；F/serial-key.log、board-check.log、board-package-compare.log、publication.json、device-transaction.json、ota-timeline.log、post-ota-verify.log。采集源值、路径、实际加载对象和返回值均保留。板上未使用真实 BMC/PMC 传输进行夹具测试；正式服务仅只读核验；没有修改整板路由、其他真实服务器配置或给正式实例发 HUP。kernel/rootfs OTA 不声明安装 bootloader。A3 实机验收通过。
