# AM625 实机验收归档（EDK A13–A18 及两轮复查修复）

八份板验记录列出指定 AM625 上的实测项、运行固件身份与原始证据位置。

[EDK 开发归档](../../../../edk/docs/archive/2026-11-26-portability/README.md) · [A1–A12 板验归档](../2026-11-26-module-audit/README.md)

| 阶段 | AM625 实机记录 | EDK 开发记录 | 工作区关闭提交 |
| --- | --- | --- | --- |
| A13 | [旧 PDI 升级与板上候选探针](edk-portability-a13-validation.md) | [开发记录](../../../../edk/docs/archive/2026-11-26-portability/edk-portability-a13-validation.md) | `acb9d14` |
| A14 | [SDK 更新及既有内容保留](edk-portability-a14-validation.md) | [开发记录](../../../../edk/docs/archive/2026-11-26-portability/edk-portability-a14-validation.md) | `7fc8413` |
| A15 | [分开运行通用包与板级测试](edk-portability-a15-validation.md) | [开发记录](../../../../edk/docs/archive/2026-11-26-portability/edk-portability-a15-validation.md) | `213e062` |
| A16 | [启动日志采集与 kernel/rootfs OTA](edk-portability-a16-validation.md) | [开发记录](../../../../edk/docs/archive/2026-11-26-portability/edk-portability-a16-validation.md) | `526765f` |
| A17 | [HWID 协议向量与板上设备身份](edk-portability-a17-validation.md) | [开发记录](../../../../edk/docs/archive/2026-11-26-portability/edk-portability-a17-validation.md) | `b509e11` |
| A18 | [实际构建输入、最终 FIT 与活动设备树](edk-portability-a18-validation.md) | [开发记录](../../../../edk/docs/archive/2026-11-26-portability/edk-portability-a18-validation.md) | `d53c314` |
| 首次复查修复 | [正式镜像与修复后的实机验收](edk-portability-remediation-validation.md) | [开发记录](../../../../edk/docs/archive/2026-11-26-portability/edk-portability-remediation-validation.md) | `0b3f143` |
| 二次复查修复 | [修复后的正式制品与实机验收](edk-portability-followup-validation.md) | [开发记录](../../../../edk/docs/archive/2026-11-26-portability/edk-portability-followup-validation.md) | `1ab7cb8` |

A13–A15 沿用 A7 正式固件，A17、A18 沿用 A16 正式固件。A16 和两轮复查修复的记录分别保留了当次 kernel/rootfs OTA 的设备事务与健康确认结果。

后续 A19–A21 的修复及阶段验收结果已归档。[AM625 板验记录](../2026-11-26-portability-repair/README.md) · [开发记录](../../../../edk/docs/archive/2026-11-26-portability-repair/README.md)
