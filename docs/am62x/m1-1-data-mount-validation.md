# M1.1：AM625 独立 data 挂载验证

日期：2026-11-03。阶段目标是让 `/data` 由板级启动负责挂载，并解除 `logctld` 作为挂载者的隐式职责。挂载失败时只降级持久化能力；启动过程不格式化、不改写分区。

## 实现

- `bsp-base-external/board/ti/am625/rootfs-overlay/etc/init.d/S00data` 在服务启动前读取板级 `storage.conf` 并挂载 `/dev/mmcblk1p15` 到 `/data`。
- `S01logctld` 只消费已经挂载的 `/data`；不可用时继续使用 `/run/logctl/boots`。
- 目标固件的 FIT 版本保持 `v0.0.1`，本次内容 ID 为 `d1f470d7cd77b9c174a8f596fefdc0c3a8057f99ebadf8d7a2cd1cdc5be982bd`。

## 构建和 OTA

- 独立 Buildroot 输出：`output/am625-m1`。
- OTA 工件和串口采集：`output/ota-validation/0.0.1-m1-data-mount/`。
- 服务器：`192.168.10.246:8090`，publication `#36`。
- 实机：`1c-63-49-22-c4-f7`，启动 ID `c27823cd-6adf-43d6-b292-72e848412e76`。

## 验收结果

串口显示 ext4 data 分区以 `r/w` 挂载，并在服务启动前输出 `[data] [INFO] persistent storage mounted on /data`。随后 `logctl` 读回前一启动 marker，输出 `storage=persistent cross-boot=verified`。OTA 状态已从 boot-testing 变为 success，设备执行了 `fwctl current deployment marked good`。

Buildroot `make all` 成功；BusyBox `ash -n` 检查通过；logging 组件 8 项测试通过；新源码构建的 OTA 真实固件下载完整性冒烟测试通过。OTA 全套测试的自动安装模拟和精确恢复用例仍有 11 项失败，需在相关阶段另行定位。固件引擎的 `fwctl_version_test` 当前也有既存断言失败。第一次 OTA 冒烟失败来自旧 host 工具，使用当前源码重建后通过。

## 范围限制

本子阶段只交付独立挂载和跨启动持久化验证。板卡日志显示 ext4 `Quota mode: none`；只读、低空间、I/O 错误、满盘、突然掉电和配额策略尚未验证。这些保留在 M1.2，不能据此声称 data 存储已具备完整故障保护。
