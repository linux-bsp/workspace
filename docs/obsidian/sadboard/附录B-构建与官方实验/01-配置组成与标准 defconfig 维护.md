---
title: "配置组成与标准 defconfig 维护"
type: "topic"
tags: ["sadboard/topic"]
chapter: "附录B-构建与官方实验"
---

# 配置组成与标准 defconfig 维护

[[首页]] · [[附录B-构建与官方实验/00-章节导航|章节导航]] · [[案例索引]] · [[工具索引]]


## B.1 配置组成与标准 defconfig 维护

| 层次 | 输入 | 用途 |
| --- | --- | --- |
| 普通 BSP | `bsp-base-external/configs/alientek_am62x_defconfig` | 普通 AM625 板级构建入口 |
| SadBoard | `sadboard-external/configs/sadboard_am625_debug_defconfig` | 调试工具、systemd、overlay、包和构建 hook 的唯一配置入口 |
| 内核片段 | `sadboard-external/kernel/debug.config` | ftrace、perf、memcg、core 等 |
| BusyBox 片段 | `board/am625/busybox-debug.config` | 实验需要的 applet 与参数能力 |
| U-Boot 片段 | `board/am625/uboot-netboot.config` | TFTP、NFS 两个独立配置开关 |
| 可选诊断片段 | `kernel/kgdb.config`、`kernel/memory.config` | 独立诊断构建，不能混作性能基线 |

直接维护 Buildroot 的标准 defconfig，不再额外合成 Buildroot 配置快照。在独立输出目录
加载标准 defconfig 后使用原生菜单修改；保存共享配置时使用默认内部工具链配置，避免把本机 SDK
绝对路径、个人下载目录或临时诊断选项写入仓库：

主机端：用 Buildroot 原生菜单调整独立配置，保存后再导出共享 defconfig。

```sh
make -C output/am625-native-debug menuconfig
```

主机端：导出当前最小 defconfig，确认配置来源不包含不该共享的本机路径。

```sh
make -C output/am625-native-debug savedefconfig \
  DEFCONFIG="$PWD/sadboard-external/configs/sadboard_am625_debug_defconfig"
```

主机端：审阅刚导出的 defconfig 差异，确认只有计划内的配置修改。

```sh
git -C sadboard-external diff -- configs/sadboard_am625_debug_defconfig
```

BSP 使用 `cmake-package`、`host-cmake-package` 和 `kernel-module` 构建 EDK。
固件由原生 post-image hook、`host-fw-tools`、`mkimage` 和 `genimage` 生成；
独立 initramfs 使用内核自带的 `usr/gen_init_cpio`，无需 root 或执行目标 ELF。
自定义流程不调用 Python。上游包仍可以有 Buildroot 原生管理的主机 Python 依赖。

核对配置等价和差异后再提交。内部/外部工具链不能混入同一输出树；外部工具链中
原本缺失的 libc 符号不能通过给应用增加 `-g` 补回。
`target/` 是构建中间目录；制作 NFS 根文件系统应从处理权限后的 `rootfs.tar` 解包。
