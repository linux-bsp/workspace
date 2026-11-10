---
title: "Bootlin 官方示例运行参考"
type: "topic"
tags: ["sadboard/topic"]
chapter: "附录B-构建与官方实验"
---

# Bootlin 官方示例运行参考

[[首页]] · [[附录B-构建与官方实验/00-章节导航|章节导航]] · [[案例索引]] · [[工具索引]]


## B.5 Bootlin 官方示例运行参考

以下针对另行下载、按其许可证编译的官方示例，不是 SadBoard 的 `sadboard run` 入口。
按对应实验目录执行，路径、端口、板 IP 与本机实际环境匹配。原初版只完成了这些示例
的交叉编译，不把下列所有扩展命令宣称为已逐条实机验证。

### B.5.1 GDB 与 core

在板上 `gdb` 实验目录启动：

```sh
gdbserver :2345 ./linked_list
```

主机运行交叉 GDB 打开同一次构建的 `linked_list`，随后设置：

```gdb
set sysroot /绝对路径/workspace/output/am625-debug-systemd/staging
target remote <板IP>:2345
break insert_name
continue
```

core 实验使用子进程的 32 MiB 有界上限；BusyBox ash 中为 `ulimit -c 65536`，并确认 `core_pattern` 保存到可写且空间足够的目录。避免把 OOM 实验的 core、trace 数据写入 `/tmp`：BSP 的 `/tmp` 是 tmpfs，会额外消耗内存。GDB 端需要同版本可执行文件、库和 core。

### B.5.2 跟踪与网络

```sh
strace -f -o /root/strace.log ./linked_list
LD_LIBRARY_PATH=. ltrace ./authent
trace-cmd record -o /root/trace.dat -e sched:sched_switch sleep 2
perf record -g -o /root/perf.data -- ./crc_random
```

分别在相应实验目录执行；NFS `/root` 可写时可保存结果。原准备记录中，主机在忽略的 `output/host-tools/FlameGraph` 中保存 FlameGraph，版本为 `41fee1f99f9276008b7cd112fca19dc3ea84ac32`，当时未安装 KernelShark。主机工具不作为固件或项目源码的一部分。

本镜像缺少目标端 addr2line，板端可先用 `perf script --no-inline -i /root/perf.data > /root/perf.script` 导出不含内联展开的文本，原理和边界见第 4 章。把文本复制到主机后执行：

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
