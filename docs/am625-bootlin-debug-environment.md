# AM6254 Bootlin 调试实验环境

使用当前主机已构建的镜像开始实验，请先阅读 [快速上手](am625-quickstart.md)。本文侧重环境配置、构建方式和验证记录。

## 目标与边界

在现有 AM6254 BSP 上复现 Bootlin 的用户态调试、性能分析与系统跟踪流程。官方 BeaglePlay 实验使用定制 Buildroot、板端内核和 NFS 根文件系统；本项目借鉴这种组织方式，保留自己的 Linux 7.0、设备树和板级支持，不直接使用 BeaglePlay 镜像。

参考：[官方实验手册](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.pdf)、[官方 Buildroot 配置](https://github.com/bootlin/buildroot/blob/debugging-training-beagleplay/2025.02/configs/beagleplay_debugging_defconfig)。以下脚本和适配方案为 SadBoard 实现；课程内容归纳与 CC BY-SA 3.0 署名见 [课程指南](bootlin-linux-debugging-guide.md)。

## 配置组成

| 层次 | 路径 | 用途 |
| --- | --- | --- |
| 板级基线 | `bsp-base-external/configs/alientek_am62x_defconfig` | AM6254、设备树、基础服务和源码覆盖路径 |
| 用户态调试 | `sadboard-external/configs/debug-tools.config` | 调试符号、帧指针和分析工具 |
| 实验输出 | `sadboard-external/board/am625/debug.config` | 组合 overlay、内核片段，生成内核与 NFS rootfs |
| 内核基础 | `sadboard-external/kernel/debug.config` | ftrace、探针、perf、调度统计、PSI、core 与内核符号 |
| 可选诊断 | `kernel/kgdb.config`、`kernel/memory.config` | 串口 KGDB，或 lockdep/原子上下文检查/kmemleak |

基础工具包括 gdbserver、主机交叉 GDB（Python 支持）、strace、ltrace、Valgrind、perf、trace-cmd、procps-ng、sysstat、stress-ng、iperf3 和 tcpdump。保留全局 `-O2`，增加调试信息与帧指针，目标文件不剥离符号。课程示例按其 Makefile 使用 `-g3` 构建。

## 生成与构建

从新克隆的 workspace 根目录初始化源码子模块，进入 Buildroot 后直接使用标准 defconfig：

```bash
git submodule update --init --recursive
cd buildroot
BR2_EXTERNAL="../bsp-base-external ../sadboard-external" \
  make sadboard_am625_debug_defconfig && make all
```

主机应先准备 Buildroot 构建依赖。当前 `libbmc` 子模块仍使用内网 remote，需要能访问该仓库。默认包内并行度为 8；首次构建会独立编译交叉工具链，无需另一份工作区。

`configs/sadboard_am625_debug_defconfig` 已保存组合配置，使用者不需要先执行 Python。Buildroot 会在输出目录中记录 external 路径，所以第二条 `make all` 可以不再传 `BR2_EXTERNAL`。

**输出路径需要区分：**

- 上述不带 `O=` 的命令使用 `buildroot/.config` 和 `buildroot/output/`，镜像在 `buildroot/output/images/`。
- 本文后面的历史构建记录与上板示例使用 `workspace/output/am625-debug/`。新建相同布局时，从 workspace 根目录执行：

```bash
make -C buildroot O="$PWD/output/am625-debug" \
  BR2_EXTERNAL="$PWD/bsp-base-external $PWD/sadboard-external" \
  sadboard_am625_debug_defconfig
make -C output/am625-debug all
```

这组命令仅适用于新的输出目录。当前主机已有的 `output/am625-debug` 使用外部工具链，测试内部工具链方式请改用新的目录，例如 `output/am625-native-debug`，避免混用构建结果。后续增量构建直接执行相应目录中的 `make all`。

如上游下载缓慢，可在构建命令后追加 `BR2_PRIMARY_SITE=https://sources.buildroot.net`。需要日志时可用 `2>&1 | tee build.log`，并在 Bash 中先执行 `set -o pipefail` 以保留构建失败状态。

维护者修改 BSP 基线或调试片段后，用以下命令重新导出标准配置并审查差异；此步骤不属于普通构建流程：

```bash
regen_dir=$(mktemp -d)
python3 sadboard-external/scripts/configure-am625.py \
  --output "$regen_dir" --export-defconfig
git -C sadboard-external diff -- configs/sadboard_am625_debug_defconfig
```

这台主机首次验证采用已有工具链与下载缓存，首次配置时的等价命令为（已有 `.config` 时脚本会拒绝覆盖）：

```bash
python3 sadboard-external/scripts/configure-am625.py \
  --toolchain /home/guohao/am62x/workspace/buildroot/output/host \
  --dl-dir /home/guohao/am62x/dl
```

此加速方式只读取原工具链，下载缓存可被更新；该输出配置依赖上述绝对路径。独立部署时使用默认工具链方式，在新的输出目录重建。源码始终来自本 workspace 的固定子模块提交。外部工具链的 libc 调试信息取决于该工具链自身，关闭本次目标剥离并不会补回已缺失的 libc 符号。

构建成功后应检查：

- `output/am625-debug/images/Image.gz` 和 AM6254 DTB。
- `output/am625-debug/images/rootfs.tar`：可用于 NFS 的根文件系统。
- `output/am625-debug/build/linux-custom/vmlinux`、`.config`、`System.map`：保留与部署内核匹配的符号及配置。
- `output/am625-debug/host/bin/aarch64-buildroot-linux-gnu-gdb`：主机调试器。
- `output/am625-debug/staging/`：远程 GDB 的库与头文件。

本次另外保存了 `images/debug/`，其中包含 `vmlinux`、`System.map`、`kernel.config`、`buildroot.config` 和带源码状态/产物哈希的 `build-info.json`。修改后重新构建时，必须同步更新调试文件；不要把本次保存的副本用于分析另一版内核。

手动保存新一次构建的匹配符号：

```bash
mkdir -p output/am625-debug/images/debug
cp output/am625-debug/build/linux-custom/vmlinux output/am625-debug/images/debug/
cp output/am625-debug/build/linux-custom/System.map output/am625-debug/images/debug/
cp output/am625-debug/build/linux-custom/.config output/am625-debug/images/debug/kernel.config
cp output/am625-debug/.config output/am625-debug/images/debug/buildroot.config
```

上述复制命令不更新 `build-info.json`；重新构建后也应重新生成版本与哈希记录，避免保留过期记录。

`target/` 是构建中间目录，不能替代经过权限和设备文件处理的 `rootfs.tar`。本实验配置关闭 U-Boot、R5 Loader、ATF、OP-TEE 重建及产品后处理，复用板上已能工作的启动链。仍保留 TI 固件包供原 BSP 的 post-build 脚本安装运行时固件。

## NFS 与上板验证

调试符号和分析工具会增大镜像。产品 RAW A/B 布局的 rootfs 槽位为 128 MB，本环境不生成该布局的 SD 镜像。首次优先通过已有 U-Boot 加载调试内核，并使用 NFS 根文件系统。

主机需要 NFS 服务。下面仅提供手工部署步骤，本次未执行主机 NFS 服务配置或板卡启动。使用空的专用目录解包，保留所有者、权限和设备节点：

```bash
sudo mkdir -p /srv/nfs/sadboard-am625
sudo tar --numeric-owner -xpf output/am625-debug/images/rootfs.tar -C /srv/nfs/sadboard-am625
# 示例地址，必须改成实际实验板 IP。
BOARD_IP=192.168.0.100
sudo exportfs -o rw,sync,no_subtree_check,no_root_squash "$BOARD_IP:/srv/nfs/sadboard-am625"
```

该导出允许指定实验板的 root 用户访问根文件系统，适用于专用实验网络。临时导出不等于已配置永久服务；网络和服务安装方式以主机系统为准。

使用板上现有的加载内核/DTB方式，保留正确的串口参数。NFS 部分的参数模板为：

```text
root=/dev/nfs rw ip=<板IP>::<网关>:<掩码>:sadboard:eth0:off nfsroot=<主机IP>:<导出目录>,vers=3,tcp
```

不要直接使用占位符。实际网卡名、U-Boot 加载地址、启动命令与串口设备以本板为准；先临时启动验证，再决定是否持久化环境变量。`Image.gz` 是否可直接启动取决于现有 U-Boot 配置，必要时在主机解压为 `Image` 后加载。

NFS 启动后，先运行：

```sh
uname -a
sadboard-debug-check
cat /sys/kernel/tracing/available_tracers
perf stat -e task-clock -- sleep 1
```

`S99sadboard-debug` 只挂载 debugfs/tracefs，不开启跟踪，不启动压力负载。检查脚本报告工具和接口存在性；`perf stat` 进一步检查软件事件采样。真实 PMU、网卡吞吐和硬件中断仍需专项验证。

## 获取与编译官方实验

官方实验材料先保存在忽略的 `output/`，不作为 SadBoard 自有代码提交：

```bash
mkdir -p output/bootlin-reference
curl -fL https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.tar.xz \
  -o output/bootlin-reference/debugging-beagleplay-labs.tar.xz
sha256sum output/bootlin-reference/debugging-beagleplay-labs.tar.xz
tar -xf output/bootlin-reference/debugging-beagleplay-labs.tar.xz -C output/bootlin-reference
export CROSS_COMPILE="$PWD/output/am625-debug/host/bin/aarch64-buildroot-linux-gnu-"
LABS="$PWD/output/bootlin-reference/debugging-beagleplay-labs/nfsroot/root"
for lab in gdb ltrace valgrind heap_profile system_profiling app_profiling; do
    make -C "$LABS/$lab" CROSS_COMPILE="$CROSS_COMPILE"
done
```

2026-10-30 下载的归档 SHA-256 为 `2681da580f65efd21f3d2887457a87d273c942e28fd317dad386fad540279e2f`。官方 URL 未带版本号，未来内容可能改变，应记录实际哈希并复核差异。遵循各文件原始许可证；例如 `linked_list.c` 标注 GPL-2.0-only，不要统一改成文档许可。

把需要的实验目录复制到板端可写目录或 NFS 根目录中，例如 `/root/bootlin-labs/`。程序包含教学缺陷，需手动启动。

### GDB 与 core

在板上 `gdb` 实验目录启动：

```sh
gdbserver :2345 ./linked_list
```

主机运行交叉 GDB 打开同一次构建的 `linked_list`，随后设置：

```gdb
set sysroot /绝对路径/workspace/output/am625-debug/staging
target remote <板IP>:2345
break insert_name
continue
```

core 实验应先 `ulimit -c unlimited`，并把 `core_pattern` 指向板上可写且空间足够的目录。避免把 OOM 实验的 core、trace 数据写入 `/tmp`：BSP 的 `/tmp` 是 tmpfs，会额外消耗内存。GDB 端需要同版本可执行文件、库和 core。

### 跟踪与网络

```sh
strace -f -o /root/strace.log ./linked_list
LD_LIBRARY_PATH=. ltrace ./authent
trace-cmd record -o /root/trace.dat -e sched:sched_switch sleep 2
perf record -g -o /root/perf.data -- ./crc_random
```

分别在相应实验目录执行；NFS `/root` 可写时可保存结果。主机已在忽略的 `output/host-tools/FlameGraph` 中准备 FlameGraph，版本为 `41fee1f99f9276008b7cd112fca19dc3ea84ac32`。它不作为固件或项目源码的一部分；KernelShark 尚未安装。

板端执行 `perf script -i /root/perf.data > /root/perf.script`，把文本复制到主机后执行：

```bash
output/host-tools/FlameGraph/stackcollapse-perf.pl output/perf.script > output/perf.folded
output/host-tools/FlameGraph/flamegraph.pl output/perf.folded > output/perf.svg
```

在另一台主机准备同版本工具：

```bash
git clone https://github.com/brendangregg/FlameGraph.git output/host-tools/FlameGraph
git -C output/host-tools/FlameGraph checkout 41fee1f99f9276008b7cd112fca19dc3ea84ac32
```

网络测试用 `iperf3 -s` 与另一端的 `iperf3 -c <板IP>`，同时观察 CPU、IRQ、重传与抓包。NFS 根文件系统本身会产生网络流量；严谨的网络性能对照需要后续使用本地实验根文件系统。

## 可选内核诊断

```bash
python3 sadboard-external/scripts/configure-am625.py \
  --output output/am625-kgdb --kernel-extra kgdb
python3 sadboard-external/scripts/configure-am625.py \
  --output output/am625-memory --kernel-extra memory
```

用户态性能实验前，可以先运行 `debugctl status` 查看已有业务服务状态。确认实验允许暂停业务后，`debugctl start` 进入 BSP 的调试模式，`debugctl stop` 恢复业务。服务背景负载的开关状态应随测量结果记录。

KGDB 需要确认串口所有权和 watchdog 行为。`debugctl start` 不等同于关闭 watchdog：基础 BSP 的调试模式仍可能喂狗，内核被 GDB 暂停后喂狗也会停止，需另行安排。memory 配置开启 lockdep、原子上下文检查与 kmemleak，但 kmemleak 默认关闭，可用内核启动参数 `kmemleak=on` 开启。不要把这种诊断内核的性能结果与基础内核直接混用。

目前未接入 Bootlin 的故意破坏 watchdog 驱动补丁，未配置 BTF/eBPF、KASAN 或 kdump 捕获内核。kdump 还需独立捕获内核、内存预留与转储保存验证，不能仅通过启用一个配置项宣称完成。

## 本次验证记录

2026-10-30 至 2026-10-31，在当前 x86-64 主机完成以下验证：

- 使用已有 GCC 15/glibc 工具链与共享下载缓存，`make -C output/am625-debug BR2_PRIMARY_SITE=https://sources.buildroot.net` 完整构建成功，退出码为 0。未修改基础 BSP、Buildroot 或 Linux 源码。
- 默认内部工具链配置通过 Kconfig 检查，但未另行完整构建；本次实际产物来自外部工具链配置。
- 基础调试内核为 Linux `7.0.0`，Buildroot 实际内核配置保留了全部基础片段要求。可选 KGDB 和 memory 片段分别通过配置检查，尚未独立编译或上板。
- `rootfs.tar` 已核对 gdbserver、strace、ltrace、Valgrind、perf、trace-cmd、iperf3、tcpdump、stress-ng、ss、vmstat 和 iostat；检查脚本与启动脚本具有 root 所有权和可执行权限，内核模块目录为 `lib/modules/7.0.0/`。
- 新的交叉 GDB 验证了 Python 支持，能读取 `linked_list` 的源码/符号及保存的 `vmlinux` 中的 `panic` 符号。
- 官方 gdb、ltrace、valgrind、heap_profile、system_profiling、app_profiling 六个用户态示例均已交叉编译；未运行这些故障程序。
- 配置脚本拒绝覆盖已有 `.config`，Python/shell 语法、文档相对链接和 Git 空白检查通过。

| 产物 | 大小（字节） |
| --- | ---: |
| `images/Image.gz` | 9,665,893 |
| `images/k3-am625-alientek.dtb` | 56,205 |
| `images/rootfs.tar` | 356,167,680 |
| `images/rootfs.squashfs` | 133,763,072 |

SquashFS 已接近原 128 MiB 槽位容量，且本环境没有生成产品启动格式的整卡镜像，首次仍采用 NFS 验证。

构建日志为 `output/am625-debug/build.log`；官方实验编译日志为 `output/bootlin-reference/labs-build.log`。现有工具链、BSP 外部层和内核目录未被本任务修改；下载缓存新增了所需源码包。

**尚未验证**：AM6254 上电启动、SSH/串口连接、NFS 导出、真实 PMU 和网络性能、Valgrind 运行、KGDB、内核故障注入与 kdump。继续上板需要实际板卡连接及网络信息。

### 标准入口验证补充

已实际执行 `cd buildroot` 后通过环境变量传入两个 external，运行 `make sadboard_am625_debug_defconfig`。生成配置与原组合脚本的默认配置一致，仅 `BR2_DEFCONFIG` 的记录路径不同；入口可被 `make list-defconfigs` 列出。

后续不传 `BR2_EXTERNAL` 的 `make printvars` 与 `make show-info` 均成功，确认 external 路径被记住、所需调试工具和本地源码软件包进入构建依赖图。本次验证了标准入口及配置一致性，没有重新执行内部工具链方式的完整 `make all`。
