# AM625 板级验收归档（EDK A1–A12）

每份原始记录包含本阶段的设备、运行身份、实测断言与证据位置。开发范围和接手验收见 [EDK 归档索引](../../../../edk/docs/archive/2026-11-26-module-audit/README.md)。

| 阶段 | 板级记录 | 对应工作区提交 |
| --- | --- | --- |
| A1 | [依赖诊断与格式基线](edk-module-audit-a1-validation.md) | `8911d52` |
| A2 | [PDI 库内私有边界及 hwmon 错误契约](edk-module-audit-a2-validation.md) | `1196a62` |
| A3 | [SDK 头与清单的安装前检查](edk-module-audit-a3-validation.md) | `cea037b` |
| A4 | [项目约束与 Buildroot 包提示归属](edk-module-audit-a4-validation.md) | `337ff25` |
| A5 | [Satellite 历史文件退役及正式 OTA](edk-module-audit-a5-validation.md) | `56d6e4e` |
| A6 | [独立 AI 首次接手 hwmon](edk-module-audit-a6-validation.md) | `cf70b56` |
| A7 | [EDK 独立测试、BSP 集成与 bootlog 修复](edk-standalone-test-boundary-validation.md) | `078770c` |
| A8 | [文档交接与 M0–M7 归档](edk-module-audit-a8-validation.md) | `db5c25c` |
| A9 | [共享 staging 的库布局预检](edk-module-audit-a9-validation.md) | `45801b3` |
| A10 | [runtime-only 更新与已有 SDK 一致性](edk-module-audit-a10-validation.md) | `a0e3546` |
| A11 | [最终 DTB 的 bootlog 内存引用](edk-module-audit-a11-validation.md) | `05bb615` |
| A12 | [独立 hwmon 测试与最终交接](edk-module-audit-a12-validation.md) | `f1b7fa7` |

A12 关闭时工作区为 `f1b7fa7376bc7aa205fd1bedb5f7ad5c1075d46c`。A8–A12 板验沿用 A7 已成功发布的 `0.0.1`，固件内容 ID 为 `16f44b78e3915e830ae7bdcf2293ebc06738b1a187edead8d74aab3359b81730`。此前板验见 [M0–M7 记录](../2026-11-25-edk-subsystem-validation.md)。
