# SadBoard AM6254 快速上手

当前使用流程是：启动 AM6254 调试系统 → 手动运行实验 → 使用工具定位问题。已经完成主机构建，尚未上板验证；随机出题、场景管理命令和自动评分尚未实现。

本文描述现有主机上的使用方式。`output/` 被 Git 忽略，新克隆的工作区不会包含镜像、工具链或下载的实验，需要先按 [环境搭建指南](am625-bootlin-debug-environment.md) 构建并准备实验材料。

## 新克隆工作区的首次构建

已安装 Buildroot 主机依赖、具备各子模块仓库访问权限时，从 workspace 根目录执行：

```bash
git submodule update --init --recursive
cd buildroot
BR2_EXTERNAL="../bsp-base-external ../sadboard-external" \
  make sadboard_am625_debug_defconfig && make all
```

默认自动构建交叉工具链，镜像生成在 `buildroot/output/images/`。下面的操作示例使用原主机的 `workspace/output/am625-debug/`，采用上述默认构建方式时需替换对应路径；也可以按 [环境指南](am625-bootlin-debug-environment.md) 使用 `O=` 指定独立输出目录。Bootlin 实验材料仍需按环境指南单独下载和编译。

## 1. 进入项目并检查已有产物

主机执行：

```bash
cd ~/SadBoard/workspace
```

| 路径 | 用途 |
| --- | --- |
| `sadboard-external/` | 调试工具、内核配置和环境检查脚本 |
| `output/am625-debug/images/Image.gz` | 调试内核 |
| `output/am625-debug/images/k3-am625-alientek.dtb` | AM6254 设备树 |
| `output/am625-debug/images/rootfs.tar` | 带调试工具的根文件系统 |
| `output/am625-debug/images/debug/` | 本次构建保存的匹配内核符号和配置 |
| `output/bootlin-reference/` | 已下载、编译的 Bootlin 实验 |

当前主机已有这些产物，无需重新构建。后续继续构建时执行：

```bash
make -C output/am625-debug
```

该输出目录已有 `.config`，不要再次对它运行配置生成脚本。当前构建使用原工作区的外部工具链；迁移到另一台主机时请按环境指南生成新的构建目录。重新构建内核后，需要同步更新保存的符号与版本记录。

## 2. 准备 NFS 根文件系统与实验

首次使用通过 NFS 挂载根文件系统，方便修改程序、保存日志和 core。以下命令要求主机 NFS 服务已经安装并启动；请使用专用空目录解包。

主机执行：

```bash
sudo mkdir -p /srv/nfs/sadboard-am625
sudo tar --numeric-owner -xpf \
  output/am625-debug/images/rootfs.tar \
  -C /srv/nfs/sadboard-am625

LABS="$PWD/output/bootlin-reference/debugging-beagleplay-labs/nfsroot/root"
DEST=/srv/nfs/sadboard-am625/root/bootlin-labs
sudo mkdir -p "$DEST"

for lab in gdb ltrace valgrind heap_profile system_profiling app_profiling; do
    sudo cp -a "$LABS/$lab" "$DEST/"
done
```

仓库默认板卡 IP 为 `192.168.18.246`。下面必须使用实际板卡 IP；导出仅供指定实验板的 root 用户访问实验根文件系统：

```bash
BOARD_IP=192.168.18.246
sudo exportfs -o rw,sync,no_subtree_check,no_root_squash \
  "$BOARD_IP:/srv/nfs/sadboard-am625"
```

这是临时导出，主机重启后的持久化配置需要根据实际 NFS 服务设置。

## 3. 使用现有 U-Boot 临时启动

主机需要有可用的 TFTP 服务。把内核和设备树放入该服务实际使用的根目录；以下 `/srv/tftp` 是示例路径：

```bash
TFTP_DIR=/srv/tftp

gzip -dc output/am625-debug/images/Image.gz |
  sudo tee "$TFTP_DIR/Image" >/dev/null

sudo cp output/am625-debug/images/k3-am625-alientek.dtb "$TFTP_DIR/"
```

进入板上 U-Boot，先检查实际环境和命令支持：

```text
printenv ipaddr serverip gatewayip netmask kernel_addr_r fdt_addr_r
help booti
```

仓库中 `am62x_raw_ab.env` 与 `ti_common.env` 的默认配置为：

| 参数 | 默认值 |
| --- | --- |
| 主机 IP | `192.168.18.245` |
| 板卡 IP | `192.168.18.246` |
| 网关 / 掩码 | `192.168.18.1` / `255.255.255.0` |
| 串口 | `ttyS2`，115200 |
| `kernel_addr_r` | `0x90000000` |
| `fdt_addr_r` | `0x88000000` |

这些是源码默认值，不代表板上持久化环境一定相同。确认加载地址有效，按实际网络修改下面的 IP，并确认两次 TFTP 加载成功后启动：

```text
setenv ipaddr 192.168.18.246
setenv serverip 192.168.18.245
setenv gatewayip 192.168.18.1
setenv netmask 255.255.255.0

tftpboot ${kernel_addr_r} Image
tftpboot ${fdt_addr_r} k3-am625-alientek.dtb

setenv bootargs "console=ttyS2,115200n8 earlycon=ns16550a,mmio32,0x02800000 root=/dev/nfs rw nfsroot=${serverip}:/srv/nfs/sadboard-am625,vers=3,tcp ip=${ipaddr}:${serverip}:${gatewayip}:${netmask}:sadboard:eth0:off"

booti ${kernel_addr_r} - ${fdt_addr_r}
```

首次先验证临时启动，再决定是否保存环境变量。这里直接执行 `booti`：现有 `run fw_boot` 会重新设置产品启动参数，并从存储设备加载产品内核，覆盖上述 NFS 启动流程。

本环境没有生成产品 RAW A/B 整卡镜像，`rootfs.squashfs` 已接近原 128 MiB 槽位容量；不能把本指南当作原产品升级包的刷写流程。

## 4. 检查板端环境

板上执行：

```sh
uname -a
sadboard-debug-check
cat /sys/kernel/tracing/available_tracers
perf stat -e task-clock -- sleep 1
```

预期内核为 `7.0.0`。`sadboard-debug-check` 检查工具和接口存在性，不触发故障；`perf stat` 进一步检查软件事件采样。若报告 `MISSING` 或采样失败，先定位环境问题，再开始实验。

## 5. 完成第一个 GDB 实验

板上进入实验目录并启动服务：

```sh
cd /root/bootlin-labs/gdb
gdbserver :2345 ./linked_list
```

主机另开终端，使用同一次构建的程序和符号：

```bash
cd ~/SadBoard/workspace
output/am625-debug/host/bin/aarch64-buildroot-linux-gnu-gdb \
  output/bootlin-reference/debugging-beagleplay-labs/nfsroot/root/gdb/linked_list
```

GDB 中输入；按实际情况修改主机绝对路径和板卡 IP：

```gdb
set sysroot /home/guohao/SadBoard/workspace/output/am625-debug/staging
target remote 192.168.18.246:2345
break insert_name
continue
list
next
info locals
```

继续运行，程序异常停止后查看：

```gdb
bt
info locals
```

先熟悉断点、单步、变量与调用栈，再根据证据分析错误。此处不直接给出根因，保留动手练习过程。

## 6. 使用其他实验和工具

以下命令在板上执行，先进入 `/root/bootlin-labs/` 下对应的子目录。

| 练习 | 子目录 | 命令 |
| --- | --- | --- |
| 系统调用分析 | `gdb` | `strace -f -o /root/strace.log ./linked_list` |
| 动态库调用分析 | `ltrace` | `LD_LIBRARY_PATH=. ltrace ./authent` |
| 内存错误分析 | `valgrind` | `valgrind --leak-check=full --track-origins=yes ./faulty_mem_app` |
| 堆内存分析 | `heap_profile` | `valgrind --tool=massif ./heap_profile` |
| CPU 热点分析 | `system_profiling` | `perf record -g -o /root/perf.data -- ./crc_random` |
| 图像处理性能 | `app_profiling` | `perf stat ./png_convert tux.png result.png` |

`crc_random` 持续运行，采样一段时间后按 `Ctrl+C`，再查看：

```sh
perf report --stdio -i /root/perf.data
```

跟踪调度事件可单独执行：

```sh
trace-cmd record -o /root/trace.dat -e sched:sched_switch sleep 2
trace-cmd report -i /root/trace.dat
```

NFS 启动时可把结果保存在 `/root`。BSP 的 `/tmp` 使用 tmpfs，较大的 core 和采样数据写入其中会额外占用内存，影响 OOM 等实验。

火焰图、网络测试、可选 KGDB/内存诊断配置及验证记录见 [AM6254 环境指南](am625-bootlin-debug-environment.md)。课程实验顺序和分析方法见 [Bootlin 课程指南](bootlin-linux-debugging-guide.md)。

## 验证状态与下一步

主机已完成镜像构建、归档内容检查、六个用户态示例交叉编译，以及 GDB 的 Python/符号读取验证。本文中的 NFS/TFTP 配置、U-Boot 启动和板端实验尚未实际执行。

下一步先完成 NFS 启动和 `sadboard-debug-check` 上板检查，再逐项练习用户态调试、性能分析和内核诊断。当前没有完整的 panic/OOM 题库，KGDB、故障注入和 kdump 仍需要分别适配验证。
