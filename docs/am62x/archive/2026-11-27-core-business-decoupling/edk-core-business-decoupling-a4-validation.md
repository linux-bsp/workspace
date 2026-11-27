# A4：本机采集、按节点板载输入与正式 AM625 实机专项

[工程、构型与回归记录](../../../../edk/docs/archive/2026-11-27-core-business-decoupling/edk-core-business-decoupling-a4-validation.md)。E=`output/edk-decoupling-a4-20261127-114411-mhTrND/`，F=E/final/。日期 2026-11-27，实际核验 am625 / aarch64，MAC `1c:63:49:22:c4:f7`、HWID `1010001000110000`。

| 验收项 | 实测 |
| --- | --- |
| 发布前设备 | A3 可信 SSH key、boot `4bd75a3f-3310-4db0-9d6f-cb59913d8bee`，B 槽 confirmed successful=1，完整运行 ID `2d4fd5368d2230f98b18eaa081044634d54440b2044884e91e65619c7e421d86`。F/board-prepublication.log。 |
| 纯本机（ARM64 隔离） | 注入 temp1_input=65300 m°C，point 4/index 0 FRESH；另按 sysfs name 查到真实 `main0_thermal`，`/sys/class/hwmon/hwmon0/temp1_input`，候选最终复跑读取前后 40613/40148 m°C、采样 40381 m°C，误差在属性瞬时读值 ±2000 m°C 窗口；重启后属性前后 40613/40381 m°C、读取值 40381 m°C。/proc/pid/maps 仅候选 libpdi/libbsl，无 libserver。注入值不是物理温度。 |
| 节点型板载采集（ARM64 隔离） | 无 BMC/PMC transport、目录保留，FPGA fixture node_id=3/index=37/value=ON(1)，MCU fixture node_id=19/index=4/value=OFF(2)。QUERY_POINT 513 与 runtime-status legacy source alias 32805/32772 一致。错误绑定 -19、重复 index -17；HUP 原目录 generation 2，目录变动 -116 拒绝且原绑定/样本仍有效。实际 libserver maps、已知 BMC 配置键解析通过。两个节点是模拟板载输入而非实际服务器。 |
| 正式运行只读对照 | A3 现役发布前，BMC Redfish index 2/3 FRESH、ON(1)，PMC index 3 FRESH，CPU 988 bp、memory 464 bp，合并点一致。A4 正式安装后 index 2/3 ON(1)，PMC index 3 CPU 86 bp（0.86%）、memory 465 bp（4.65%），合并点一致，sequence=15、status=0。正式 `ptelemetryd` IPC DESCRIBE 6 sources/0 commands、点 512/513/514/515 的 3 indexes、实际加载 /lib64/libbsl.so.2；`psatellited --check-config` v1.0、can0、6 sources/0 commands。BMC index 1 发布前后均 timeout (-110)、quality=3；未配置 PMC 的 index 1/2 -95，未把这些状态误报为成功采样。F/board-discovery.log、board-candidate.log、board-installed.log 的实际值与状态。 |
| 正式候选与旧兼容 | A1 冻结 ARM64 原程序 SHA `ac133cb3696f679d263f6b220c07327c0fc75712004866441d75381565db2527`，实际候选及系统 libbsl.so.2 SHA `4ab3fc4dd2e438ec06de1f1c2337051ef58de1110cdf3de067e0ebd772f40de4`，生产 HWID→phytium-s5000c 四点/一命令/无覆盖；未知 HWID -ENODEV、输出清空。系统链接解析 /usr/lib/libbsl.so.0.0.1。 |
| OTA 事务 | `draft-KdnvCM`，11:58:18+08:00 published，11:59:59+08:00 success（running=version=1、未隔离）；唯一目标及 channel，完整 ID `babb77088af6a68961c66954ad35042ec4e04e2f108cac664d7d3188fd830ae1`，tag v0.0.1 packed 1。F/publication.json、ota-timeline.log、ota-success.json、device-transaction.json。 |
| 重启及正式制品 | 物理串口复核新 SSH 指纹、MAC/HWID、boot `844d2807-a3b6-415c-a546-c013070f9a61`，12:00:17+08:00 实装检查，A 槽 confirmed successful=1，FWCHECK1 match（kernel 12940577 bytes SHA `8742d9d99652424ec910aa8039cff2a8dc5620bc6ed72078ba9e279dec554931`，rootfs 30429184 bytes SHA `37ea8531272c86faf4022d9385068efabe9b33bca28757311fea1f6ecaf6c5e4`），8 active、0 failed、health 正常、startup ACK 及日志同步正常；9/9 实装文件 SHA 与 rootfs.tar 匹配。F/serial-key.log、board-check.log、board-package-compare.log、post-ota-verify.log。 |

执行 `bash "$F/run-board-candidate.sh" "$F" "$F/board-known-hosts" candidate <prior-id> <prior-boot>` 及 `bash "$F/post-ota-verify.sh" "$F"`，探针目录、SHA、实际加载路径与临时脚本在 F/board-probes/；前后两轮检查结束只清理隔离临时路径。首轮目标 BusyBox 无 seq，保留 F/board-candidate-first.log；临时脚本使用 POSIX while 重跑通过，不改二进制和源码快照。正式业务只执行 DESCRIBE、QUERY_POINT、runtime-status 与星务配置检查。没有向其他真实服务器提交命令、控制或写操作；只向指定 AM625 发布 kernel/rootfs，bootloader 原始输入没有变化，未以此声明安装 bootloader。

A4 全部实机专项通过。
