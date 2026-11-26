# A1 板级验收与交付

2026-11-25，23:27:06–23:27:10+08:00。
[EDK A1 实施与验证记录](../../../../edk/docs/archive/2026-11-26-module-audit/edk-module-audit-a1-validation.md)。
证据 `output/edk-module-audit-a1-20261125-2323/`。

指定 AM625 MAC 1c:63:49:22:c4:f7、HWID 1010001000110000、
boot `542e6381-e300-41b7-ae2b-41dddbbd0583`。沿用
[Redfish 成功发布](../../edk-redfish-recovery-validation.md)，A 槽，版本 0.0.1，
full ID `683e05eaa30726d7d54eced37f55f0c446f3ddcb7b366d75a9fcca935fa9bfed`。
纯主机验收变更，无正式目标输入变动，不重新发布；
严格 pinned SSH、fwctl version/ota-status/ota-check/health-check，
实际八制品 SHA256 与正式包匹配，八服务正常。
调用 M0 旧 SDK 编译的只读 probe，核对 probe SHA256 和 LD_DEBUG=libs
实际 /usr/lib 库，确认 HWID/project、Satellite 协议及 PDM generation=15，
枚举 main_mcu、dc_power 两个设备，关闭句柄并清理 tmpfs。
六源 telemetry last_status=0/failures=0。所有真实服务器仅只读。
命令和原始输出见 board-v6.sh/log；本地 host 46/46、格式正反例和三种依赖目录均通过。

子仓 EDK master 先推，核对后更新现场工作区准确 gitlink。
工作区提交与远端核验保存在同一证据目录。

EDK 子仓远端已验证：`67f46bf2d2a9c7f265f06a6a4b371f318b7680d9`。
