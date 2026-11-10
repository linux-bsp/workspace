[[README|首页]] · [[00-实验准备与通用方法/案例索引|案例索引]] · [[00-实验准备与通用方法/工具索引|工具索引]] · [[附录B-构建与官方实验/00-章节导航|章节导航]]

## B.3 获取与编译官方实验

官方实验材料先保存在忽略的 `output/`，不作为 SadBoard 自有代码提交：

主机端：创建忽略目录保存 Bootlin 原始实验材料。

```bash
mkdir -p output/bootlin-reference
```

主机端：下载官方实验归档，确认 curl 成功退出后再计算哈希和解压。

```bash
curl -fL https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.tar.xz \
  -o output/bootlin-reference/debugging-beagleplay-labs.tar.xz
```

主机端：记录实际下载归档的 SHA256，与下方历史记录核对差异。

```bash
sha256sum output/bootlin-reference/debugging-beagleplay-labs.tar.xz
```

主机端：解压已核对的实验归档，确认目录完整后再配置交叉编译变量。

```bash
tar -xf output/bootlin-reference/debugging-beagleplay-labs.tar.xz -C output/bootlin-reference
```

主机端：集中设置交叉编译器前缀和 Bootlin 实验路径，供后续各实验共用。

```bash
export CROSS_COMPILE="$PWD/output/am625-debug-systemd/host/bin/aarch64-buildroot-linux-gnu-"
LABS="$PWD/output/bootlin-reference/debugging-beagleplay-labs/nfsroot/root"
```

主机端：单独交叉编译官方 gdb 实验，确认成功后再处理下一项。

```bash
make -C "$LABS/gdb" CROSS_COMPILE="$CROSS_COMPILE"
```

主机端：单独交叉编译官方 ltrace 实验，确认成功后再处理下一项。

```bash
make -C "$LABS/ltrace" CROSS_COMPILE="$CROSS_COMPILE"
```

主机端：单独交叉编译官方 valgrind 实验，确认成功后再处理下一项。

```bash
make -C "$LABS/valgrind" CROSS_COMPILE="$CROSS_COMPILE"
```

主机端：单独交叉编译官方 heap_profile 实验，确认成功后再处理下一项。

```bash
make -C "$LABS/heap_profile" CROSS_COMPILE="$CROSS_COMPILE"
```

主机端：单独交叉编译官方 system_profiling 实验，确认成功后再处理下一项。

```bash
make -C "$LABS/system_profiling" CROSS_COMPILE="$CROSS_COMPILE"
```

主机端：单独交叉编译官方 app_profiling 实验，确认成功后再处理下一项。

```bash
make -C "$LABS/app_profiling" CROSS_COMPILE="$CROSS_COMPILE"
```

2026-10-30 下载的归档 SHA-256 为 `2681da580f65efd21f3d2887457a87d273c942e28fd317dad386fad540279e2f`。官方 URL 未带版本号，未来内容可能改变，应记录实际哈希并复核差异。遵循各文件原始许可证；例如 `linked_list.c` 标注 GPL-2.0-only，不要统一改成文档许可。

把需要的实验目录复制到板端可写目录或 NFS 根目录中，例如 `/root/bootlin-labs/`。程序包含教学缺陷，需手动启动。

## B.5 Bootlin 官方示例运行参考

以下针对另行下载、按其许可证编译的官方示例，不是 SadBoard 的 `sadboard run` 入口。
按对应实验目录执行，路径、端口、板 IP 与本机实际环境匹配。原初版只完成了这些示例
的交叉编译，不把下列所有扩展命令宣称为已逐条实机验证。

### B.5.1 GDB 与 core

在板上 `gdb` 实验目录启动：

设备端：在官方 linked_list 实验目录启动 gdbserver，等待主机连接。

```sh
gdbserver :2345 ./linked_list
```

主机运行交叉 GDB 打开同一次构建的 `linked_list`，随后设置：

主机 GDB：设置本次构建的完整 sysroot，先替换本机绝对路径。

```gdb
set sysroot /绝对路径/workspace/output/am625-debug-systemd/staging
```

主机 GDB：替换板卡 IP 后连接官方实验的 gdbserver，确认成功停止后再设断点。

```gdb
target remote <板IP>:2345
```

主机 GDB：在 insert_name 设置断点，核对断点是否解析到匹配源码。

```gdb
break insert_name
```

主机 GDB：继续执行到断点或信号，观察链表操作的实际停止位置。

```gdb
continue
```

core 实验使用子进程的 32 MiB 有界上限；BusyBox ash 中为 `ulimit -c 65536`，并确认 `core_pattern` 保存到可写且空间足够的目录。避免把 OOM 实验的 core、trace 数据写入 `/tmp`：BSP 的 `/tmp` 是 tmpfs，会额外消耗内存。GDB 端需要同版本可执行文件、库和 core。

### B.5.2 跟踪与网络

设备端：在官方实验目录跟踪 linked_list 的系统调用，并保存原始 strace 记录。

```sh
strace -f -o /root/strace.log ./linked_list
```

设备端：为当前 authent 实验指定本目录库路径，跟踪其库函数调用。

```sh
LD_LIBRARY_PATH=. ltrace ./authent
```

设备端：保存两秒调度事件，确认 trace.dat 实际生成且能读取。

```sh
trace-cmd record -o /root/trace.dat -e sched:sched_switch sleep 2
```

设备端：对官方 CRC 负载采样调用链，成功后使用对应符号分析 perf.data。

```sh
perf record -g -o /root/perf.data -- ./crc_random
```

分别在相应实验目录执行；NFS `/root` 可写时可保存结果。原准备记录中，主机在忽略的 `output/host-tools/FlameGraph` 中保存 FlameGraph，版本为 `41fee1f99f9276008b7cd112fca19dc3ea84ac32`，当时未安装 KernelShark。主机工具不作为固件或项目源码的一部分。

本镜像缺少目标端 addr2line，板端可先用 `perf script --no-inline -i /root/perf.data > /root/perf.script` 导出不含内联展开的文本，原理和边界见第 4 章。把文本复制到主机后执行：

主机端：折叠已有的 perf 调用栈文本，检查输出后再生成 SVG。

```bash
output/host-tools/FlameGraph/stackcollapse-perf.pl output/perf.script > output/perf.folded
```

主机端：把折叠结果绘成 SVG 火焰图，完成后在浏览器查看。

```bash
output/host-tools/FlameGraph/flamegraph.pl output/perf.folded > output/perf.svg
```

在另一台主机准备同版本工具：

主机端：下载 FlameGraph 工具源码，确认克隆成功后再固定版本。

```bash
git clone https://github.com/brendangregg/FlameGraph.git output/host-tools/FlameGraph
```

主机端：切换到记录的 FlameGraph 提交，确保不同练习使用一致的工具代码。

```bash
git -C output/host-tools/FlameGraph checkout 41fee1f99f9276008b7cd112fca19dc3ea84ac32
```

网络测试用 `iperf3 -s` 与另一端的 `iperf3 -c <板IP>`，同时观察 CPU、IRQ、重传与抓包。NFS 根文件系统本身会产生网络流量；严谨的网络性能对照需要后续使用本地实验根文件系统。
