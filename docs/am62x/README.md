# AM625 文档索引

## 当前使用

- EDK 安装与遥测验收 · A1–A9 已在指定 AM625 完成逐阶段验收 · [阶段计划](../../edk/docs/edk-install-reload-repair-plan.md) · [本轮实机验收](archive/2026-11-27-install-reload-repair/README.md) · [新会话提示词](../../edk/docs/edk-install-reload-repair-prompt.md) · [上轮核心与业务解耦板验](archive/2026-11-27-core-business-decoupling/README.md)
- [工作区拉取和构建](../../README.md)
- [固件升级、槽位与恢复操作](firmware-upgrade-guide.md)
- [固件包 HWID 与自动发布](firmware-hwid-publication.md)
- [HWID 编码规范](hwid-specification.md)
- [systemd 服务与健康检查](system-services.md)
- [可靠性与验证边界](reliability-boundaries.md)
- [TFTP 配置](tftp-server.md)、[电源串口连接](power-control.md)

固件生成和板级布局见 BSP 的
[板级说明](../../bsp-base-external/board/ti/am625/README.md)、
[initramfs 与 A/B 恢复](../../bsp-base-external/board/ti/am625/verified-boot.md)。
设备管理命令、SOL 和时间功能见 [EDK 构建与运维入口](../../edk/README.md)。

## 验证与溯源

- 边界收敛 A1–A6（含 A6.5）的[工程与 AM625 实机验收索引](../../edk/docs/archive/2026-11-27-boundary-convergence/README.md)
- Redfish 冷启动超时整改 · [AM625 实机验收](archive/2026-11-25-redfish-recovery/edk-redfish-recovery-validation.md) · [工程回归](../../edk/docs/archive/2026-11-25-redfish-recovery/edk-redfish-recovery-validation.md)
- [构建框架优化验收](build-framework-validation.md)

- [EDK 历次板级验收](edk-module-refactoring-validation.md) · [2026-11-25 子系统重构 M0–M7 实机记录](archive/2026-11-25-edk-subsystem-validation.md)
- [历史模块复核 A1–A12 板级验收归档](archive/2026-11-26-module-audit/README.md) · [对应 EDK 开发记录](../../edk/docs/archive/2026-11-26-module-audit/README.md)
- A13–A18 多项目移植与修改边界优化、两轮复查修复及 OTA 验收 · [AM625 实机记录归档](archive/2026-11-26-portability/README.md) · [EDK/BSP 回归记录](../../edk/docs/archive/2026-11-26-portability/README.md)
  - [A13](archive/2026-11-26-portability/edk-portability-a13-validation.md) · [A14](archive/2026-11-26-portability/edk-portability-a14-validation.md) · [A15](archive/2026-11-26-portability/edk-portability-a15-validation.md) · [A16](archive/2026-11-26-portability/edk-portability-a16-validation.md) · [A17](archive/2026-11-26-portability/edk-portability-a17-validation.md) · [A18](archive/2026-11-26-portability/edk-portability-a18-validation.md)
  - [A14–A18 复查修复及正式 AM625 OTA 验收](archive/2026-11-26-portability/edk-portability-remediation-validation.md) · [EDK/BSP 回归记录](../../edk/docs/archive/2026-11-26-portability/edk-portability-remediation-validation.md)
  - [A16/A18 二次复查修复及 AM625 实机验收](archive/2026-11-26-portability/edk-portability-followup-validation.md) · [EDK/BSP 回归记录](../../edk/docs/archive/2026-11-26-portability/edk-portability-followup-validation.md)
- A19–A21 移植复查修复 · [AM625 实机记录归档](archive/2026-11-26-portability-repair/README.md) · [EDK/BSP 回归记录](../../edk/docs/archive/2026-11-26-portability-repair/README.md)
  - [A19 依赖记录完整性实板验收](archive/2026-11-26-portability-repair/edk-portability-a19-repair-validation.md) · [工程记录](../../edk/docs/archive/2026-11-26-portability-repair/edk-portability-a19-repair-validation.md)
  - [A20 所选构建清单实板验收](archive/2026-11-26-portability-repair/edk-portability-a20-repair-validation.md) · [工程记录](../../edk/docs/archive/2026-11-26-portability-repair/edk-portability-a20-repair-validation.md)
  - [A21 无 memfd 兼容及实板 OTA 验收](archive/2026-11-26-portability-repair/edk-portability-a21-repair-validation.md) · [工程记录](../../edk/docs/archive/2026-11-26-portability-repair/edk-portability-a21-repair-validation.md)
- [固件下载、事务与恢复优化验证](firmware-upgrade-optimization-validation.md)
- [OTA 启动失败日志实机验证](ota-boot-failure-log-validation.md)
- [历史功能验收](validation-history.md)
- [板级历史发布](../../bsp-base-external/board/ti/am625/releases/README.md)
- [管理服务与固件发布](../../edk/user/apps/pmcd/README.md#固件包与发布)

历史文档保留原始固件身份、启动记录和验证限制，命令可能反映旧目录。
当前使用以上述操作指南与源码配置为准。原始测试、串口及固件产物位于
各记录注明的 output/ota-validation 目录，生成文件不提交到 Git。
