# AM625 启动阶段固件信息验证

## 日志位置与校验责任

- R5 SPL 和 A53 SPL 打印被选择的 U-Boot A/B 槽、版本、固件 ID。此阶段确认启动元数据，不宣称已校验 U-Boot 镜像负载。
- U-Boot 校验 kernel FIT 后打印槽位、版本、固件 ID 和 FIT SHA256；同时从已校验 FIT 配置读取 rootfs 槽位、版本和预期 SHA256。
- Linux 内核打印继承自 U-Boot 的 kernel FIT 校验状态，以及 rootfs 的目标槽位和预期 payload SHA256。
- initramfs 读取完整 rootfs 分区并校验 SHA256，建立 dm-verity 映射后打印实际校验成功的槽位、版本和 payload SHA256。该结果在 switch_root 前输出。

日志格式统一为 `[fwctl] [INFO]`，人读哈希显示前 8 位；实际校验使用完整 SHA256。

## 实机验证

2026-11-03，在 AM62x 板上通过 OTA 发布 32 验证 `v0.0.1 / 425cba2e`。串口确认：SPL 选择 U-Boot 槽 A；U-Boot 校验 kernel FIT 并读取 rootfs 信息，kernel 与 rootfs 均使用 B 槽；initramfs 的 rootfs SHA256 校验通过并启用 dm-verity。rootfs 校验行完整，未被 watchdog 输出拆分。设备健康检查通过，服务端结果为 `success`。`fwctl status` 显示 deployment 1 已确认，`logctl verify-boot` 显示 R5 SPL、A53 SPL 和 U-Boot 三段日志均已验证。

发布 30 曾因 initramfs 调用 `pthread_cancel`，而精简目标系统缺少 `libgcc_s.so.1`，导致 PID 1 退出。设备 A/B 尝试耗尽后自动回滚，服务端记录 `rolled-back`。修正版使用原子停止标志并等待喂狗线程正常退出，发布 32 在实机验证成功。

## 构建产物与记录

固件标签保持 `v0.0.1`，完整固件 ID 为 `425cba2e7af145352eb452364b7d83485fc6e4a3d660545a5472c63c032d5ea4`。构建日志、OTA 包、构建身份和串口采集保存在忽略目录 `output/ota-validation/0.0.1-stage-logs-safe-handoff/`。
