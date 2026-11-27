# A2：AM625 BusyBox 同一节点测试脚本验收

[工程回归、超时断言和脚本摘要](../../../../edk/docs/archive/2026-11-27-install-reload-repair/a2-validation.md)。E=`output/edk-install-reload-a2-20261127-130651-FDwGh9/`，F=E/final/，2026-11-27。

| 验收 | 实测 |
| --- | --- |
| 指定目标 | 受信 A1 key、am625/aarch64、MAC `1c:63:49:22:c4:f7`、HWID `1010001000110000`、boot `6b1025fa-c2b9-49f3-a84b-be3c482a208b`、B 槽、confirmed successful=1；FWCHECK1 match，health 正常。 |
| 旧版失败 | 实际原脚本 SHA `b0336af8c930c4f658fe232c72ead59392cae24266e200ce4220e83ac1e15022`，正例与前置负例通过后 line 53 seq: not found，退出 1，隔离 temp 清理。BusyBox sleep 不支持小数，已有 usleep 50000 成功。E/baseline/board.log、board-timer-tools.log。 |
| 同字节候选 | SHA `b38c34fa79ec77660ff222c5d3e3196654ff2521bdee8a904a0b757c54a84157`，主机源码、板上脚本运行前后完全相同；板上直接 sh 原样执行，50 ms、100 次、usleep=yes，未增装命令。F/script-host.sha256、board-candidate.log。 |
| 节点绑定 | BMC/PMC transport 关闭。FPGA fixture node 3/index 37/ON(1)，MCU fixture node 19/index 4/OFF(2)；错误绑定 -ENODEV(-19)、重复 index -EEXIST(-17)。正常 HUP generation 1→2；同路径 index 37→39 修改返回 -ESTALE(-116)，generation 2、index 37 与两新鲜样本保持；server node catalog PASS。模拟节点不是实际服务器。 |
| 清理与镜像 | 脚本临时文件/socket 路径在本次独立目录，结束空目录且 /proc 无本次 fixture ELF；只向本次 PID 发 HUP。A1 原 publication `draft-g8EWNz`，完整 ID `47ccc5cdfaad628497513a9c3a051764f18acba6246615ae430844c8745e4173`，kernel/rootfs 完整摘要与 A1 一致；未改变生产制品、不重新发布。 |

A2 实机专项通过。

## 2026-11-27 A4 复查补记

历史 A2 的同字节脚本、真实板验和已确认 A1 publication `draft-g8EWNz` 仍有效；当时验证的是 A1 原包完整摘要与设备身份，未构建 A2 正式候选、没有两版候选摘要逐字比较。PDM 的 EDK_GIT_COMMIT 构建标识进入模块，复查元数据日志 `output/edk-review-install-reload-g1GhndWw/pdm-metadata.log`；详见[工程补记](../../../../edk/docs/archive/2026-11-27-install-reload-repair/a2-validation.md)。本次不向设备补发历史镜像。
