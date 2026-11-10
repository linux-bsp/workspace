---
title: "AM625 RAM 启动实验的共同操作方法"
type: "topic"
tags: ["sadboard/topic"]
chapter: "07-内核启动与恢复"
---

[[首页]] · [[07-内核启动与恢复/00-章节导航|章节导航]] · [[案例索引]] · [[工具索引]]

# AM625 RAM 启动实验的共同操作方法

B-BOOT02/03 在真实 AM625 执行。主机的 `scripts/sadboard-board.py` 仅控制串口、TFTP 和验收；设备上的 PID 1、动态加载器、内核挂载过程都是真实代码，没有使用 QEMU 或 PID namespace 替代整机故障。构建自动生成 `images/sadboard/`，正常 OTA 的 FIT/rootfs 不含这些故障副本。

先将本次正常固件经 SD A/B OTA 升级并确认，再部署配套 TFTP/NFS，保留 `tftp_kernel=1`、`nfs_root=1`。串口工具需要独占串口，关闭其他串口终端/采集程序；日志由工具自己保存。示例在 workspace 根执行，`--output` 必须是新目录：

主机端：在真实 AM625 上运行 RAM 缺库故障、超时保护与参考启动对照；先替换验收路径并确认串口可用。

```sh
python3 sadboard-external/scripts/sadboard-board.py boot-initlib \
  --images output/am625-debug-systemd/images --serial /dev/ttyACM2 \
  --known-hosts output/validation/STAGE/ssh-known-hosts \
  --output output/validation/boot-initlib-$(date +%Y%m%dT%H%M%S)
```

根挂载实验用同样参数，将 boot-initlib 改为 boot-root，并换一个 output。

工具校验工件 SHA256，记录基线，将 U-Boot 中的参数只改在 RAM 内，启动硬件 WDT，分别运行故障与参考副本。过程中不执行 saveenv、不写分区、不更新 SPL/U-Boot。若正常网络启动因 PHY/ARP/TFTP 重试退回 U-Boot，主机工具最多重试两次原有 fw_boot，记录重试次数；NFS 调试依赖主机服务，本地 SD 恢复另行实测。故障 kernel 的 `panic=3` 尝试三秒后复位；WDT 为后备。后续复位重新使用保存的正常网络启动配置。每次参考 SD 启动通过健康检查后，再回到正常 TFTP+NFS。当前 USB 串口不透传 BREAK，不依赖串口 SysRq 救援；RAM 参考 init 带独立 120 秒恢复守护，只有看到 PID 1 根目录下的健康确认才退出，卡在持续喂狗的 recovery 内也会强制复位。额外 guard 对照将此期限设为 10 秒，实测该路径再继续正常参考启动。`serial.log` 是完整原始串口，`bug-serial.log` / `fixed-serial.log` 是分段证据，`result.json` 记录对应启动与恢复。

缺库例中 `/init` 是一个依赖专用 `libsadboard-init.so` 的 ELF。故障副本仅缺这一个库；参考副本补齐后调用生产 `fwctl init`，完成 rootfs SHA256/dm-verity 校验与 switch_root。用 `readelf -lW images/sadboard/init` 查看解释器，`readelf -dW` 查看 DT_NEEDED/RUNPATH，再用交叉 `objdump -drS` 比较 main、库调用和 PLT。实际故障发生在 main 前的加载器阶段；exit_group(127) 最终进入 do_group_exit/do_exit 的全局 PID 1 保护并 panic。不要将它与普通业务进程 SIGSEGV 混为一谈。

根挂载例两版都不传 initramfs。故障只设不存在的 `/dev/mmcblk1p99`，并故意不加 rootwait，避免无限等待掩盖 VFS 错误。参考使用本次确认 deployment 对应的 rootfs 分区，带 rootwait、rootfstype=squashfs。同一个 Image 和绑定 rootfs 校验信息的 DTB 用于对照。沿 `kernel_init_freeable → prepare_namespace → mount_root` 阅读 `init/main.c`、`init/do_mounts.c`；实际函数与偏移以串口栈和匹配 vmlinux 为准。rootwait 解决异步设备发现，不能修正错误的设备号或文件系统类型。
