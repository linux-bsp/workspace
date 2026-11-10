---
title: "TFTP-NFS 调试启动与编译开关"
type: "topic"
tags: ["sadboard/topic"]
chapter: "00-实验准备与通用方法"
---

# TFTP-NFS 调试启动与编译开关

[[首页]] · [[00-实验准备与通用方法/00-章节导航|章节导航]] · [[案例索引]] · [[工具索引]]


## 0.1.1 TFTP/NFS 调试启动与编译开关

这两个选项位于 U-Boot 的 AM625 A53 板级 Kconfig：

| `CONFIG_AM62X_BOOT_TFTP_KERNEL` | `CONFIG_AM62X_BOOT_NFS_ROOT` | 内核与设备树 | 根文件系统 |
| --- | --- | --- | --- |
| n | n | SD A/B 的已校验 FIT | FIT initramfs 验证并挂载 SD A/B rootfs（普通 AM625 默认） |
| y | n | TFTP `Image`＋DTB | 当前选中的 SD rootfs，直接挂载 SquashFS，供内核调试 |
| n | y | SD A/B 的已校验 FIT，跳过其中 initramfs | NFS，供文件系统调试 |
| y | y | TFTP `Image`＋DTB | NFS（SadBoard 默认） |

TFTP 与 NFS 是两种独立协议：U-Boot 用 TFTP 将内核、DTB 完整读入 RAM；Linux 的
内建网卡/NFS 客户端再通过 NFS 远程挂载主机目录。只有 TFTP 模式使用 `booti`，文件
必须是未压缩的 ARM64 `Image`；不要把 `Image.gz`、`vmlinux` 或 `kernel.itb` 改名冒充它。
仅 NFS 模式使用 `bootm FIT -` 跳过 FIT 内的 initramfs，否则 initramfs 会按生产策略切换到 SD。

SadBoard 的持久配置是
`sadboard-external/board/am625/uboot-netboot.config`，由
`BR2_TARGET_UBOOT_CONFIG_FRAGMENT_FILES` 合入 BSP U-Boot defconfig。普通 BSP 的
`am62x_alientek_a53_defconfig` 两项均关闭，不合入该调试片段。修改片段后执行：

```sh
make -C output/am625-debug-systemd uboot-reconfigure all
```

可以运行 `make -C output/am625-debug-systemd uboot-menuconfig` 临时选择，搜索上述
符号；需要长期保留时应写回片段。仅修改 U-Boot 无需重新构建工具链。已有板卡必须
安装新 U-Boot，单独发布 kernel/rootfs 不会更新它的 CONFIG 或默认环境。

### 主机服务与产物部署

本开发主机 IP 为 `192.168.10.246`，板卡 IP 为 `192.168.10.211`。先安装 NFS 服务；
TFTP 服务根目录必须与实际 tftpd 配置一致，本机已经是 `/srv/tftp/am625`：

```sh
sudo apt install nfs-kernel-server
```

```sh
sudo sadboard-external/scripts/deploy-netboot.sh \
  output/am625-debug-systemd/images
```

部署脚本校验 manifest 后，把 `rootfs.tar` 解压到 `/srv/nfs/sadboard-am625`，保留
root 属主/权限和符号链接；复制 Image/DTB 到 TFTP 根目录；在
`/etc/exports.d/sadboard.exports` 仅向指定板卡开放该根目录：

```text
/srv/nfs/sadboard-am625 192.168.10.211(rw,sync,no_root_squash,no_subtree_check)
```

可用 `--nfs-root`、`--tftp-root`、`--client` 指定路径和客户机 IP。脚本拒绝覆盖非空 NFS
根目录；更新时先让设备停止使用该导出目录，再归档旧目录并重新部署。不要直接导出
Buildroot 的 `target/`，其中的属主和设备文件尚未经过 fakeroot 最终处理。
同一导出目录只供一台板卡读写，避免多台设备共享 `/etc/machine-id` 等可变状态。

防火墙需要放行板卡访问 TFTP、rpcbind、NFSv3 和 mountd。本机 TFTP 使用 UDP 69
及配置的传输端口范围；NFS 服务的实际端口可用 `rpcinfo -p` 查看。

### U-Boot 环境变量与运行时切换

编译选项分别映射到 `tftp_kernel=0/1`、`nfs_root=0/1`。串口中断自动启动后可直接调整，
例如：

```sh
printenv fw_boot_profile tftp_kernel nfs_root ipaddr serverip nfsroot
```

```sh
setenv ipaddr 192.168.10.211
```

```sh
setenv serverip 192.168.10.246
```

```sh
setenv gatewayip 192.168.10.1
```

```sh
setenv netmask 255.255.255.0
```

```sh
setenv tftp_kernel_file Image
```

```sh
setenv tftp_fdt_file k3-am625-alientek.dtb
```

```sh
setenv nfsroot /srv/nfs/sadboard-am625
```

```sh
setenv nfsopts vers=3,tcp
```

```sh
setenv tftp_kernel 1
```

```sh
setenv nfs_root 1
```

```sh
saveenv
```

```sh
run fw_boot
```

`nfs_root` 是开关，`nfsroot` 是主机导出路径。只改这两个开关即可选择表中的四种组合。
临时切换可以省略 `saveenv`。恢复 SD 完整校验启动：

```sh
setenv tftp_kernel 0
```

```sh
setenv nfs_root 0
```

```sh
saveenv
```

```sh
run fw_boot
```

新 U-Boot 会迁移启动脚本；当**编译出的组合**与保存的 `fw_boot_profile` 不同时，
自动更新两个开关。HWID、MAC、IP、NFS/TFTP 路径保留。相同编译组合下，手动保存的
开关继续有效；重新刷同一组合不会反复覆盖人工选择。编译片段内的 IP 是全新环境的
默认值，已有保存值需要显式 `setenv` 调整。不要执行 `env default -a` 清掉设备身份。

### 调试模式的边界与确认方式

任一网络开关启用都会添加 `sadboard.netboot=1`。这种模式保留 `blkdevparts`，因此
SD `/data` 仍用于设备日志、SSH 主机密钥和启动确认。NFS 根下的实验结果写入
`/srv/sadboard`；TFTP 单开时根仍在 SD，实验结果也继续写 SD。TFTP 单开时直接挂载本地 SquashFS，
不经过 initramfs/dm-verity；要验证生产完整性检查和网络恢复，应切回两个开关均关闭。
网络调试依赖主机/交换机可达，NFS 中断可能阻塞系统，不是独立运行的生产启动方式。

网络模式跳过 `fwctld` 自动安装、生产 A/B 健康确认和生产版本输出，不会将外部内核
误标为 SD 的某个 deployment。SadBoard 在本地服务、持久存储稳定后封存本次启动日志，
开放手动案例；`/run/fwctl-boot-confirmed` 在该模式写入 `netboot`，只表示调试启动就绪。
`fwctl status` 查询的仍是 SD 元数据，不代表正在运行的网络镜像；`fwctl ota-status`
要求生产 `fw.deployment`，网络启动下可能报无法识别，不能拿它判断网络镜像就绪状态。

```sh
cat /proc/cmdline
```

```sh
cat /proc/mounts
```

```sh
cat /run/fwctl-boot-confirmed
```

```sh
/usr/libexec/sadboard/boot-context
```

```sh
systemctl --failed --no-pager
```

```sh
sadboard run crash
```

网络实验的 `firmware-status.txt` 使用 `SBNET1`，`run.info` 标记
`boot_mode=network-debug`。完整参考构建 ID 由内核、DTB 和 rootfs 文件内容/权限生成，
用于将案例与构建资料对应；它不是 OTA 的 ITB 内容 ID，也不证明可写 NFS 根目录在
运行期间未被修改。修改 NFS 文件后应重新构建并保留改动记录，不能用旧 ID 断言镜像一致。
panic 用例还要求这一参考构建已经完成过一次正常网络启动，再重启进入未封存的启动窗口。
