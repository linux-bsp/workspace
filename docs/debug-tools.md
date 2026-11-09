# SadBoard 调试工具使用手册

结合 [案例目录](cases/README.md) 使用。先提出问题，再选工具；完整跟踪会改变时序，
先取低开销指标，再对可疑路径做短时间细查。下面“主机”指构建服务器，“设备”指 AM625。

## 构建、符号和证据准备

在主机运行 `python3 sadboard-external/scripts/verify-debug.py output/am625-debug-systemd/images`，
确认配套文件 SHA256、固件 ID 和 DWARF。实验前在设备记录：

```sh
fwctl version
fwctl ota-status
uname -a
cat /proc/sys/kernel/random/boot_id
date '+%Y-%m-%dT%H:%M:%S%z'
df -k /data
sadboard-debug-check
```

`fwctl version` 的日志使用短 ID；公共机器接口 `ota-status` 的 FWOTA2 记录含完整 ID，
适合保留到原始证据，不能从短 ID 反推全值。保存精确命令、输入、stdout/stderr、
退出码，性能原始文件和对应 ELF。目标时区为 UTC+8；时间未同步时另记 boot ID 和 uptime。
`images/debug/build-info.json` 将源码、ELF、内核配置与固件关联起来。

不要把 `vmlinux`、压缩 Image.gz、kernel.itb 混为同一用途：vmlinux 是带符号的 ELF，
Image.gz 是启动内核载荷，ITB 是包含内核、initramfs、DTB 等的 FIT 容器。

## GDB 与 gdbserver

设备用 `gdbserver --once :22345 PROGRAM ARGS` 启动待调程序；主机使用本构建的
`host/bin/aarch64-buildroot-linux-gnu-gdb ELF`。`--once` 在连接结束后退出，
`:22345` 是调试监听端口；它不同于 SSH，运行期间不要让其他客户端抢占连接。

| 命令/参数 | 用途与使用时机 |
| --- | --- |
| `set sysroot ROOT` | 在 ROOT 下按目标的绝对路径查找库/程序；在线可用 staging，离线 PIE 分析优先使用完整目标根目录 |
| `set substitute-path OLD NEW` | 将 DWARF 中的编译源码前缀映射到本机源码副本，不替代 sysroot |
| `target remote IP:PORT` | 连接 gdbserver；已启动程序用 continue，而非另起 run |
| `break FUNC` / `break FILE:LINE` | 在函数或具体源行停住，缩小故障时间窗 |
| `ignore N COUNT` | 忽略编号 N 的断点前 COUNT 次命中 |
| `continue` / `next` / `step` | 继续执行、源码层越过函数、源码层进入函数 |
| `finish` / `return` | 前者执行到当前函数返回；后者强行返回，会修改行为，取证时慎用 |
| `bt full` / `frame N` | 看调用链及局部变量，再选择具体帧 |
| `info args` / `info locals` | 检查输入与当前帧的局部状态 |
| `print EXPR` / `print /x EXPR` | 按类型或十六进制读变量；不要随意解引用可疑指针 |
| `info registers` / `x/i $pc` | 将现场寄存器与出错机器指令对应 |
| `disassemble /s FUNC` | 混合源行与反汇编；优化构建可能不能逐行对应 |
| `info threads` / `thread N` | 选择线程；GDB 线程编号不同于 Linux TID |
| `thread apply all bt` | 同时查看线程的等待关系 |
| `core-file PATH` | 载入离线 core；不能在 core 上 continue |
| `set pagination off` / `--batch -ex CMD` | 关闭分页、自动化取证并保存输出 |

先看 frame 0，再看调用者如何产生错误状态。`<optimized out>` 可能来自编译优化；
`??` 可能来自缺符号或地址重定位失败；两者都不直接说明栈损坏。
GDB 的帧含义与回溯选项参见 [官方回溯说明](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Backtrace.html)。

## strace 与 ltrace

strace 观察系统调用、信号和进程状态边界，适合回答“程序在等什么”“哪个文件打开失败”；
ltrace 观察可见的动态库调用，适合追踪 libc API。内联、静态链接或不经过可跟踪跳板的
调用可能不出现在 ltrace 中；不能把“没看到”当作“没调用”。

```sh
strace -f -tt -T -s 128 -e trace=openat,read,write,futex \
  -o /data/sadboard/syscalls.txt /usr/libexec/sadboard/lock-bug 20 50000
ltrace -o /data/sadboard/libcalls.txt /usr/libexec/sadboard/crash-fixed 1
```

| 参数 | 含义 |
| --- | --- |
| `-f` | 跟踪新建线程/子进程；没有它可能只看到主线程等待 join |
| `-p PID` | 附加已有进程；先确认 PID 与程序，避免跟踪关键守护进程 |
| `-tt` / `-T` | 分别是时间戳与单次系统调用耗时，不是同一指标 |
| `-e trace=...` | 过滤指定调用；可用 `%file`、`%network` 等分类，实际版本以帮助为准 |
| `-s 128` | 字符串最多打印 128 字节，长路径/报文被截断时适当增加 |
| `-o PATH` | 原始证据落盘，避免与业务输出混在一起 |
| `-c` | 统计调用次数、错误与耗时摘要；摘要不能替代调用顺序 |
| `-yy` | 尽可能解析 FD 对应路径/端点，便于识别 socket 和文件 |

优先看实际返回值：`ENOENT`、`EACCES`、`ENOMEM` 含义不同；`EINTR` 可能正常，
`EAGAIN` 对非阻塞 I/O 或 futex 条件竞争也可能正常。ptrace 停顿会影响性能与超时，
不要拿 strace 期间的吞吐量当正式基线。工具原理见 [strace 项目说明](https://strace.io/)。

## Valgrind Memcheck

```sh
valgrind --tool=memcheck --leak-check=full --show-leak-kinds=all \
  --num-callers=20 --error-exitcode=99 --log-file=/data/sadboard/memcheck.txt \
  /usr/libexec/sadboard/memory-bug 4 0
```

`--tool=memcheck` 选择内存检测器（也是默认工具）；`--leak-check=full` 输出泄漏分配栈；
`--show-leak-kinds=all` 展示所有分类；`--num-callers=20` 保留更深调用链；
`--error-exitcode=99` 使被判为错误的检查结果影响退出码；`--log-file` 单独保存报告。
发现未初始化值时可加 `--track-origins=yes`，通常会更慢。

Memcheck 用地址/有效值的影子信息检测非法访问，并在结束时扫描可达性。先修复最早的
非法写，再看后续错误，避免追逐连锁现象。泄漏分类中 definitely lost 是明确失去引用，
indirectly lost 是依赖已丢对象的分配，possibly lost 常涉及内部指针，still reachable
需要结合所有权判断。它不会替你证明业务算法、所有并发交错或整个内核的正确性。
以 [官方 Memcheck 手册](https://valgrind.org/docs/manual/mc-manual.html) 为分类依据。

## perf stat、record、report、script

stat 统计总量，record 采样并存档，report 聚合，script 展开原始样本。

| 参数/事件 | 用法与限制 |
| --- | --- |
| `-e cycles,instructions` | 硬件 CPU 周期/指令；确认 PMU 支持，关注 multiplex 比例 |
| `-e task-clock` | 任务 CPU 时间的软件事件，帮助区分计算与等待 |
| `-e context-switches,page-faults` | 切换与缺页计数；缺页包含正常按需分配，不能直接判异常 |
| `stat -r 3` | 重复统计，保留每次业务输出并比较一致性 |
| `record -F 99` | 请求采样频率；采样数据少时不能过度解读百分比 |
| `record -g` | 保存调用链，frame pointer 展开依赖构建选项 |
| `--call-graph dwarf,8192` | 捕获用户栈以 DWARF 展开，8192 为每样本栈大小预算 |
| `-p PID` / `-a` | 指定进程或全系统；入门案例优先限定进程 |
| `record -o FILE` / `report -i FILE` | 指定采样输出和分析输入 |
| `report --stdio` | 文本报告，适合无显示器设备及归档 |
| `--no-inline` | report/script 不展开内联帧；当前镜像缺少目标 addr2line，案例禁用内联时使用此项 |
| `script -i FILE` | 展开样本时间/线程/调用链，供火焰图等进一步分析 |

权限错误先检查配置和 `perf_event_paranoid`；PMU 不支持和权限不足是不同问题。
频率变化、热限频、后台负载与测量开销都要记录。火焰图只反映采样权重，不表示时间线。

## ftrace 与 trace-cmd

ftrace 是内核跟踪框架，tracefs 暴露控制与缓冲区。trace-cmd 负责配置、录制和解码，
不是另一个内核跟踪实现。SadBoard 的准备服务挂载 debugfs/tracefs，不自动开全量跟踪。

```sh
cat /sys/kernel/tracing/available_tracers
cat /sys/kernel/tracing/available_events | head -20
trace-cmd record -o /data/sadboard/sched.dat -e sched:sched_switch -- sleep 1
trace-cmd report -i /data/sadboard/sched.dat
```

`record` 录制，`-e SUBSYSTEM:EVENT` 选择事件，`-o` 保存二进制，`report -i` 解码。
`sched_switch` 说明谁让出/获得 CPU，`sched_wakeup` 说明何时变成可运行；把两者和 TID
联系起来才能区分睡眠与唤醒后的调度延迟。

扩展练习可以读 `current_tracer`、`tracing_on`、`trace`、`trace_pipe`、
`set_ftrace_filter`：前者选择 tracer，tracing_on 控制写缓冲，trace 是快照式读取，
trace_pipe 消费流式记录，filter 限定函数。函数跟踪需先筛选，避免全局高频跟踪冲掉
证据或改变系统行为。写这些文件会影响同一 tracing instance 的其他使用者；
优先使用独立 instance 并恢复自己的配置。接口见
[当前内核 ftrace 文档](../linux/linux-7.0/Documentation/trace/ftrace.rst)。

## 工具选择与练习验收

| 问题 | 首选证据 | 深入工具 |
| --- | --- | --- |
| 程序崩溃 | 信号、core、配套 ELF | GDB 寄存器/调用链、反汇编、Valgrind |
| 进程被杀 | cgroup events、内核 OOM 记录、退出信号 | 内存趋势、Valgrind、分配源码 |
| CPU 忙 | 同输入 CPU/墙钟、perf stat | perf record/report、火焰图、算法分析 |
| CPU 闲却慢 | 线程状态、墙钟/CPU 比、strace | GDB 全线程栈、调度事件时间线 |

独立完成“现象 → 假设 → 证据 → 源码机制 → 修复 → 同输入验收”，并记录一个能推翻
原假设的结果。不要用没有错误日志、进程提前退出或某个单独命令返回 0 代替完整验收。
