# A8：AM625 文档交接与已发布固件复核

2026-11-26 13:37:18–13:37:25+08:00，证据 E=`output/edk-module-audit-a8-20261126-133648-Sbh7B8/`。
[EDK 文档专项验收](../../../../edk/docs/archive/2026-11-26-module-audit/edk-module-audit-a8-validation.md)。

A8 只交付文档，未改变 A7 正式镜像或版本；不创建新发布。
使用 A7 的物理串口核实的 ED25519 主机密钥（SHA256:FwGx3XSb7Ex8dm3hFyAGwWFbX8Jg5mZdTqDT1TCks4U）严格 SSH。在 A7 的只读 V6 脚本中先断言 hostname、架构、MAC、HWID，再核对实际运行制品与健康。命令与检查内容见 A7 `bootlog-repair/board-v6.sh`，E/board-v6.log 是本阶段实际执行，末尾历史脚本标签 A7 不代表重用旧日志。

| 断言 | 当次结果 |
| --- | --- |
| 指定设备 | am625、aarch64、MAC `1c:63:49:22:c4:f7`、HWID `1010001000110000`，断言通过 |
| boot ID | `8fb95921-66b5-431b-b5b5-1074e58148c3` |
| running | v0.0.1，packed 1，confirmed successful=1，kernel/rootfs A 槽 |
| firmware_id | `16f44b78e3915e830ae7bdcf2293ebc06738b1a187edead8d74aab3359b81730` |
| A7 publication | `draft-3v0bSf`，2026-11-26 11:51:37 最终 success；本次本地 catalog GET 同设备/ID/running=1/phase=success |
| OTA 包 SHA256 | `b05b1f984f7e9e2dad669f81b08bab8926e91c5b9bdecaa6b322553e64fe8b7c`（重新计算） |
| kernel（12940588 bytes） | `472e197eb3f8874e9bf5f9af2502b87b03771f396d6ef47aa1a82f119c2cc392` |
| rootfs（30420992 bytes） | `9fd537d46e5eae6ce9e89c8a1c1dc779d3b58dacf25221070291cc40351f0fdf` |
| 分区检查 | `FWCHECK1 match`，实际九项运行制品与 A7 rootfs 摘要逐项相同 |
| 健康 | `fwctl health-check` 成功，八个单元 active、无 failed unit |
| 启动日志 | startup-state=acknowledged、active-buffer=2、next-buffer=1；`logctl verify-boot` 成功 |
| 运行状态 | 旧 Satellite 三文件均不存在；六遥测来源 last_status=0、consecutive_failures=0；部分来源有历史累计失败，不声称持续零失败 |

E/current-catalog.json、a7-success-transaction.json 及 A7 正式包在
`output/edk-standalone-test-boundary-20261126-104403/bootlog-repair/`。设备交易 source boot
`34a43973-7489-478c-bfe1-7a2e8a47fb96`，本次核对同一成功版本，不把历史 success 当作新的 OTA。
仅指定 AM625 只读检查；无任何服务器电源、复位、配置写入、部署、OTA 操作。

## 提交关闭核验

文档/工作簿、归档及链接检查详见 E/doc-check*.log。EDK master 先提交和推送，BSP 保持原 gitlink
`0fb4302eb7c640ac7c2a483fe3b2fc8d4e3c80db`。工作区 master 更新准确 EDK gitlink 与本阶段文档。
提交后 E/git-verification.log 记录实际 commit、远端头与 gitlink，E/clean-checkout.log 记录干净检出复验；只有核验通过才进入 A9。
