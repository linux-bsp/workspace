# 案例：CPU 查找热点与 perf 火焰图

## 问题现场

难度：中级。查询结果正确，但同样一批数据处理耗时很长。任务是判断时间消耗在计算、
等待还是调度，找到占用 CPU 的具体函数，再验证优化没有偷减工作量。
源码：[cpu.c](../../sadboard-external/package/sadboard-labs/src/cpu.c)。

```sh
sadboard run cpu
sadboard verify cpu
```

默认参数为 4096 条记录、500000 次查询、随机种子 42。它是固定种子的伪随机输入，
不是随机触发的多个 bug。两版输出 items/queries/seed/checksum/cpu_ns/wall_ns。
进程 CPU 时间统计实际消耗的 CPU；墙钟时间还含被调度出去的时间。

## 原理与可证伪假设

故障版每次通过 `lookup_linear()` 扫描，近似 O(NQ)；参考版利用键连续且与数组下标
一致的契约直接索引，近似 O(Q)。两版初始化、查询序列、次数与校验和相同。
真实产品若允许稀疏键、删除或重复键，就不能盲目套用直接索引，应选哈希或其他索引。

本例主要在用户态执行。CPU 高不意味着内核忙，也不应为了“内核分析”硬把用户态算法
解释成内核缺陷。首先提出假设“线性扫描主导 CPU 时间”，再用采样和输入规模实验检验。

## 从业务量估算成本，而不是先猜 CPU 参数

令记录数为 N、查询数为 Q。线性查找成功位置分散时，每次平均比较次数近似随 N 增长，
累计约随 N×Q 增长；直接索引每次只做范围检查和一次访问，累计约随 Q 增长。这个模型
省略初始化、计时、分支、缓存和 CPU 频率，不承诺精确耗时，也不意味着所有输入等概率。

本程序把第 i 条记录设为 key=i、value=3i+7。伪随机状态使用 32 位无符号递推：
`state = state × 1664525 + 1013904223`，溢出按 2^32 回绕，查询 key=state%N。
输入种子固定，查询序列就固定；独立累加每次应得的 3×key+7，便能检查两版是否完成
相同业务。checksum 有碰撞可能，不能代替所有业务测试，但比只看两版输出相等更可靠。

改变一个变量建立预测：固定 Q/seed，N 翻倍时线性版成本预计上升，索引版变化较小；
N=1 时线性循环本来就极短，不能要求索引版仍提升很多倍。若实测偏离模型，先记录
编译、频率、温度、缓存和工作量，再提出新的假设，而不是强行修改数据配合结论。

## 输出中每个数字到底代表什么

| 字段或指标 | 读法 | 常见误判 |
| --- | --- | --- |
| cpu_ns | 程序测量区间内进程 CPU 时间，纳秒 | 不等于从 shell 启动到退出的总墙钟 |
| wall_ns | 同一区间的单调经过时间，纳秒 | 含被调度出去，不全是实际执行 |
| task-clock | perf 的被测任务执行时间口径 | 与内部计时窗口不完全相同 |
| cycles / instructions | 被测范围内的事件计数 | 单一计数不直接等于业务效率 |
| IPC | instructions/cycles | 高 IPC 的冗余循环仍然可能很慢 |
| context-switches | 上下文切换次数 | 次数多不自动证明每次切换很昂贵 |
| page-faults | 缺页事件 | 合法首次写触也会发生，不等于崩溃 |

先检查事件支持、统计范围和计数器是否 multiplex。多个硬件事件竞争有限 PMU 槽位时，
工具可能按时间轮换并缩放；程序相位不均匀会影响可比性。保存原始统计而不只留下 IPC。

## 第一步：统计成本

```sh
perf stat -r 3 -e task-clock,cycles,instructions,context-switches,page-faults -- \
  /usr/libexec/sadboard/cpu-bug 4096 500000 42
perf stat -r 3 -e task-clock,cycles,instructions,context-switches,page-faults -- \
  /usr/libexec/sadboard/cpu-fixed 4096 500000 42
```

`-r 3` 重复三次，`-e` 指定事件，`--` 之后是被测程序。先逐项确认 `perf list` 有支持，
再组合统计；不支持或 multiplex 比例很低时不要硬比较数值。指令数明显降低通常支持
减少算法工作量的解释，IPC 单独升高不能证明业务变快。

固定版本可能非常短，采样不足很正常；程序自带 CPU 时间和相同 checksum 的多次对照
更适合比较这一端。不要通过减少查询次数得到“修复后更快”的结论。

## 第二步：从函数占比追到代码

```sh
mkdir -p /data/sadboard/manual-cpu
perf record -F 99 -g -o /data/sadboard/manual-cpu/perf.data -- \
  /usr/libexec/sadboard/cpu-bug 4096 500000 42
perf report --no-inline --stdio -i /data/sadboard/manual-cpu/perf.data
perf script --no-inline -i /data/sadboard/manual-cpu/perf.data > /data/sadboard/manual-cpu/stacks.txt
```

`-F 99` 请求约 99 Hz，实际受 PMU、限流及运行时长影响。`-g` 记录调用链，默认 frame
pointer 方式依赖可展开的栈；源码构建保留 frame pointer 与函数边界。
`report` 的 self 表示叶子本身占比，children 包括后代，不能将累计占比相加当总时间。
热点 `lookup_linear` 应能追溯到 main 的查询循环。

`--no-inline` 关闭内联栈展开。此调试镜像没有目标端 addr2line，实测默认 inline 路径
尝试调用缺失的符号化器并导致 perf script 返回 141。案例本身禁用了内联，因此使用
该选项仍保留需要的函数调用链。真实内联程序如需展开，应先提供可用的符号化后端。

可用 `perf annotate --stdio -s lookup_linear -i ...` 看指令行热点（扩展练习）；缺源码
或符号时，先检查匹配 ELF、build ID、strip 和路径，不能把 `[unknown]` 当作根因。
若 frame pointer 调用链不完整，可尝试 `--call-graph dwarf,8192`，代价是更大的采样
数据和栈拷贝开销。详见 [perf record 参数](https://man7.org/linux/man-pages/man1/perf-record.1.html)。

## 第三步：生成并正确阅读火焰图

将 stacks.txt 拷到服务器，使用主机上的官方
[FlameGraph](https://github.com/brendangregg/FlameGraph) 脚本：

```sh
FlameGraph/stackcollapse-perf.pl stacks.txt > cpu.folded
FlameGraph/flamegraph.pl --title 'SadBoard CPU lookup' cpu.folded > cpu.svg
```

本次工具来源固定为 `41fee1f99f9276008b7cd112fca19dc3ea84ac32`，放在忽略的
`output/host-tools/FlameGraph/`；不需要安装到设备。图宽表示采样累计权重，纵向表示
调用关系，横轴不表示时间顺序，颜色默认也不是温度或严重程度。先找宽栈，再回到源码
解释循环和数据结构；不要只凭一张图决定替换函数。

## 采样背后的内核路径

以下是**源码路径**，不是 CPU 程序直接调用的栈：

```text
perf 用户程序 → perf_event_open 系统调用 → 事件分配/PMU 注册
硬件计数器溢出 IRQ
  armpmu_dispatch_irq → armv8pmu_handle_irq → perf_event_overflow
  采样处理 → perf_output_sample → mmap ring buffer → perf.data
```

读 [kernel/events/core.c](../../linux/linux-7.0/kernel/events/core.c) 的
`SYSCALL_DEFINE5(perf_event_open)/perf_event_overflow/perf_output_sample`，以及
[arm_pmu.c](../../linux/linux-7.0/drivers/perf/arm_pmu.c)、
[arm_pmuv3.c](../../linux/linux-7.0/drivers/perf/arm_pmuv3.c)。
`task-clock` 属于软件事件，定时采样可经过 `perf_swevent_hrtimer`，与 PMU IRQ 不同。
PMU 支持、权限、事件数及硬件计数器都是测量前提。

## 修复验收与迁移

检查同一查询序列的 checksum、完成数、CPU 时间和墙钟中位数；同时确认没有崩溃、
设备关键服务仍健康。记录温度/频率、负载、构建优化级别和 trace 开销，跨版本绝对
耗时不能脱离这些条件。trace-cmd 可解释调度干扰，但更高开销的跟踪应单独运行。

练习：保持 Q 不变把 N 从 1024 增至 4096，分析线性版与索引版扩展规律；分别解释
“单核满、多核空闲”“墙钟增大但 CPU 不变”“指令减少但 IPC 下降”。保留 perf.data、
stacks、SVG、配套 ELF 和输入后清理自己的采样进程及目录。

## 证据验收与分级练习

`check` 严格解析两版 JSON，核对记录参数，并独立生成同一查询序列重算 checksum；
不会因两版输出了同一个错误值而通过。截断、重复字段、查询数不符均拒绝。
单次时间比只供观察，标记 `samples=1 performance_verdict=manual`；重复实验、固定输入、
记录中位数和波动后才能给出性能结论，不要求所有规模都有固定提升倍数。
任务见 [练习册](../workbook.md#4-结果正确但完成很慢)，结果整理到
[报告模板](../lab-report-template.md)。

## 用一个采样例子理解 self、children 和火焰图

假设共采到 100 个有效样本，其中 80 个栈经过 main→lookup_linear，另 20 个落在其他
路径；这里的数字只是教学示意。lookup 的 self 可以很高，而 main 的 children 也会很高，
因为同一个样本既属于叶子，也属于其祖先累计路径。不能把两者相加得出“消耗 160%”。

一个宽函数只能说明它在所选事件和窗口中权重大。它可能是必要工作，也可能被调用过多，
或者由上游选择了不合适的数据结构。回到源码询问“每个请求做了多少次、为什么需要做”，
通常比机械改写最热的一条指令更有效。火焰图合并相同调用路径，不保存原始先后顺序；
需要时间顺序时应改用事件时间线，而不是从横坐标猜执行顺序。

如果程序墙钟长但 CPU 样本很少，先返回时间分类，考虑等待或调度。把采样频率提得很高
可能增加开销及丢样，不能凭此补出本来不在 CPU 上执行的时段。用锁等待章与本章交叉
对照，理解 on-CPU 证据和 off-CPU 时间各自解释什么。

## 本轮实机数据如何判读

2026-11-09，`v0.0.1 / 668ad82f`，N=4096、Q=500000、seed=42，一次独立对照：

| 版本 | checksum | cpu_ns | wall_ns |
| --- | --- | --- | --- |
| 故障版 | 3074743472 | 4192871610 | 4215696845 |
| 参考版 | 3074743472 | 8869525 | 8988905 |

先确认相同参数、次数和独立计算的 checksum，再把纳秒换成秒：故障 CPU 约 4.193 秒，
墙钟约 4.216 秒，二者接近，支持主要在计算而非长期睡眠。参考 CPU 约 0.00887 秒，
说明这个输入下工作成本显著减少；本次单次比值约 472.7，**不是通用提速承诺**。
仍需重复测量与热点/源码证据，尤其短版本很容易受计时窗口及缓存状态影响。
