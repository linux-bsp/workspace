# AM625 固件升级与恢复操作

当前使用 `fwctl` 作为 U-Boot 和 Linux 的统一入口。设备守护进程 `fwctld`
负责发现、下载、安装和结果补报；服务器由 `device-server` 与 `ota-cli` 管理。
版本固定为 `v0.0.1`，完整 SHA256 决定内容身份，人工日志只显示前八位。

## 先识别运行环境与槽位

两种环境均支持：

```sh
fwctl help
fwctl capabilities
fwctl status
```

Linux 额外使用 `fwctl version` 查看实际启动的版本、内容 ID、kernel/rootfs 槽位和
确认状态。`capabilities` 不访问固件存储，区分 `runtime=uboot` 与 `runtime=linux`。

deployment 0/1 是一组组件选择，A/B 是每个组件的物理槽。它们不能互相替代：
某个 deployment 可以使用 bootloader B、kernel A、rootfs A。以状态输出为准，
不能从 deployment 编号推断物理槽。

## 日常 OTA

在管理界面上传包并发布到包内声明的 HWID，或使用 `ota-cli` 完成同样操作。
设备正常流程为：发现 → 下载/续传 → 完整校验 → 写备用槽并直接读回 → 重启 →
健康观察 → 确认 → 成功补报。只有最后一步才计升级成功。

下载缓存默认在 `/data/fwctld/HWID/`；事务和待补报事件独立保存在
`/data/fwctld-state/HWID/DEVICE/`。已完成写入的重启与启动确认不依赖服务器在线。
补报按顺序发送并取得 ACK 后才移除本地事件；有未补报结果时不开始下一次更新。

网络中断保留部分下载并重试，不隔离固件。内容校验错误、写入错误、启动失败和
设备存储异常分别记录具体原因，沿用服务器的停发、隔离与健康版本回退策略。
低空间时只下载缓存可降级到 RAM；本地事务存储不可用则拒绝新的自动写入。

完成包默认保留最近两份及 current 引用包。仅在系统确认、没有 pending 且结果已
ACK 时回收。日志、事务和未完成下载不参加回收，`FWCTLD_CACHE_KEEP=0` 可关闭。

## Linux 手动维护

先暂停 poller，避免它的校验读取与维护争用非阻塞介质锁：

```sh
/etc/init.d/S98fwctld stop
fwctl update /mnt/firmware/release.itb
fwctl status
reboot
```

命令只暂存，不自动重启；重启后 fwctld 随系统恢复。设备保持可启动的已确认源，
写入期间候选为 WRITING，所有负载读回成功才成为 READY。返回 EAGAIN 表示锁冲突，
未进入本次写入；EBUSY 可以表示当前启动尚未确认，或目标分区仍被挂载/映射占用。

单组件语法：

```sh
fwctl update kernel /mnt/firmware/release.itb
fwctl update rootfs /mnt/firmware/release.itb
```

两次暂存会保留同一 READY 候选中前次组件，重复暂存也不会切回已确认源的物理槽。
正常发布应使用完整包，确保内核绑定的 rootfs 摘要一致，并持久记录完整发布身份。
禁止组件或包内缺失组件的请求会在修改元数据之前拒绝。

## U-Boot 维护与恢复

U-Boot 的来源是 TFTP 或内存 FIT，Linux 的来源是文件或 URL，因此来源参数有所区别：

```sh
fwctl update tftp release.itb all
fwctl update tftp kernel.itb
fwctl update tftp rootfs.itb
fwctl recover-kernel
```

现有 `upa/upk/upr/upb` 是这些命令的快捷方式。单组件 ITB 与 release.itb 的用途不同，
请勿交换文件名。恢复仍匹配完整 HWID、版本和内容 ID，不盲目安装不确定的最新版本。

kernel 恢复在 U-Boot 执行；rootfs 校验、回退和精确恢复在独立 initramfs 执行。
`/init` 脚本调用 `fwctl init`，该入口只接受 PID 1，不用于初始化升级元数据。
正常根分区通过校验后尽快 switch_root；备用 rootfs 的检查与精确修复在健康确认后运行。

## 工厂元数据重建

两种环境使用相同命令：

```sh
fwctl factory-init a --force
```

`a` 也可改为 `b`。该操作丢弃原 deployment 历史，重建两份元数据，声明指定物理槽已
预置完整组件；它不写负载，也不代表验证过负载。只用于工厂或明确的元数据恢复。
缺少 `--force` 时不访问存储，旧的 `init a/b` 写法已移除。日常 OTA 不调用此命令。

## 布局、引导程序与验证边界

JSON 打包配置和设备启动配置独立维护；最终打包的布局门禁核对 Linux、A53/R5 DTB、
环境区、blkdevparts 和工厂布局，报告保存在 images/layout-validation.json。
该门禁不迁移运行设备分区，同 HWID 的已部署布局仍须固定。

当前 ROM 固定从 tiboot3 A 进入，常规远程 OTA 禁止 bootloader 更新。引导程序维护必须
另行确认实际安装、读回和执行，不能把 kernel/rootfs 的 OTA 成功算作引导程序验收。
当前验证以 AM625 SD 为准，真实断电、eMMC/NOR 实物与安全签名投产需专项验收。

具体测试、发布身份和实机证据见
[优化验收记录](firmware-upgrade-optimization-validation.md)，Linux 接口细节见
[fwctl 文档](../../edk/device-manager/docs/fwctl.md)，U-Boot 细节见
[命令文档](../../uboot/u-boot-2026.04/doc/usage/cmd/fw.rst)。
