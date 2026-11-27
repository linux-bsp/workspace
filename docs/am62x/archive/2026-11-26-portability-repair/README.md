# AM625 实机验收归档（EDK A19–A21）

三次阶段验收均使用 MAC `1c:63:49:22:c4:f7`、HWID `1010001000110000` 的指定 AM625。各记录保存当时的 boot ID、固件身份、健康与专项验证结果。[EDK 开发归档](../../../../edk/docs/archive/2026-11-26-portability-repair/README.md)

| 阶段 | AM625 实机记录 | 对应开发记录 | 工作区关闭提交 |
| --- | --- | --- | --- |
| A19 | [最终 FIT 与活动设备树、启动归档对照](edk-portability-a19-repair-validation.md) | [DTB 依赖记录完整性](../../../../edk/docs/archive/2026-11-26-portability-repair/edk-portability-a19-repair-validation.md) | `09fd151` |
| A20 | [所选构建配置与实际运行固件](edk-portability-a20-repair-validation.md) | [清单来源与双内核目录回归](../../../../edk/docs/archive/2026-11-26-portability-repair/edk-portability-a20-repair-validation.md) | `2cab0d6` |
| A21 | [旧格式 SOL、板上隔离接收及 OTA 事务](edk-portability-a21-repair-validation.md) | [无需 memfd 的已校验帧传输](../../../../edk/docs/archive/2026-11-26-portability-repair/edk-portability-a21-repair-validation.md) | `47c96f8` |

A19、A20 沿用已确认的 `draft-V54AKR`。A21 在 `draft-EP71gS` 安装后确认 A 槽及健康，再使用实装程序验证正常与进程内注入 `ENOSYS` 两条路径。原始命令和输出目录保留在各阶段板验记录中。

后续边界收敛工作的历史资料见[阶段验收索引](../../../../edk/docs/archive/2026-11-27-boundary-convergence/README.md)。此前实机记录见 [A13–A18 及两轮复查板验归档](../2026-11-26-portability/README.md)。
