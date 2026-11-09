# 内存与性能单故障实验

这些程序只在手动调用时运行，不受关键业务服务的健康确认管理。先确认 OTA 成功，
再进行实验。所有输入都有工作量上限；默认结果保存到 `/data/sadboard/`。
`verify` 运行随镜像提供的参考修复，不能证明学习者任意修改后的程序正确。

## cgroup OOM 与内存泄漏

现象：程序持续分配内存后被杀死，退出码 137。

```sh
sadboard run oom
sadboard verify oom
dmesg | tail -80
```

启动器为实验进程创建独立叶子 cgroup：`memory.max=33554432`、
`memory.swap.max=0`；监督脚本留在组外。不能仅根据 137 判定 OOM，必须同时看到
保存的 `memory-bug.events` 中 `oom_kill>0`。`memory.peak`、退出码和输出一并保存。
程序退出后删除专用 cgroup；内存不足不会用于压测整个设备。

分级提示：先查看退出信号及内核记录，再比较 cgroup 的 `memory.events`；检查每次
处理完的数据是否仍被保留。用较小输入定位泄漏：

```sh
valgrind --leak-check=full --error-exitcode=99 /usr/libexec/sadboard/memory-bug 4 0
valgrind --leak-check=full --error-exitcode=99 /usr/libexec/sadboard/memory-fixed 4 0
```

根因是缺少 `free()`；修复版处理相同的 64 MiB 累计数据，释放已处理的缓冲区，
在同一 32 MiB 限制内完成且校验和为 532480。Valgrind 本身需要额外内存，因此不要
把它放进上述 32 MiB OOM 组。

## CPU 查找热点

```sh
sadboard run cpu
perf record -F 99 -g -o /data/sadboard/cpu.perf -- /usr/libexec/sadboard/cpu-bug 4096 500000 42
perf report --no-inline --stdio -i /data/sadboard/cpu.perf
sadboard verify cpu
```

现象是 CPU 忙、查询延迟高。先区分 CPU 时间与墙钟时间，再观察 `lookup_linear`
的采样占比。根因是每次查询都线性扫描。参考实现利用连续键做直接索引；输入、
查询数及结果校验和必须相同。比较多次执行的中位数；不要只看进程是否更早退出。
主机可以用同一构建的符号及 `perf script` 输出生成火焰图。

## 锁等待

```sh
strace -f -T -e futex,clock_nanosleep -o /data/sadboard/lock.strace /usr/libexec/sadboard/lock-bug 20 50000
sadboard verify lock
```

现象是 CPU 占用低但完成慢。可用 GDB `thread apply all bt` 观察一个线程睡眠、另一个
线程等待互斥锁，再分析 futex 的等待时间。根因是持锁模拟 I/O，把可并行等待串行化。
参考修复把等待移到锁外，仅保护计数更新；两版都完成 40 次更新，不能丢失工作。

## 复位与清理

案例均有限次工作及超时；OOM 组由监督脚本清理。保留所需证据后，可删除对应
`/data/sadboard/<案例>-*` 目录。不要清除系统全部日志、修改关键服务或重置 eth0。
若手动启动 GDB/perf/strace，请结束自己启动的进程后再复测。
