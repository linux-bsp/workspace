[[首页]] · [[案例索引]] · [[工具索引]] · [[08-性能与调度优化/00-章节导航|章节导航]]

先按现象提出假设并完成练习，再核对定位、内核机制和参考修复。`verify` 验证镜像提供的参考实现。

[[08-性能与调度优化/A-P04-独立计数器发生false-sharing/A-P04：独立计数器发生 false sharing#现象与原理|现象与原理]] · [[08-性能与调度优化/A-P04-独立计数器发生false-sharing/A-P04：独立计数器发生 false sharing#练习任务|练习任务]] · [[08-性能与调度优化/A-P04-独立计数器发生false-sharing/A-P04：独立计数器发生 false sharing#使用工具|使用工具]] · [[08-性能与调度优化/A-P04-独立计数器发生false-sharing/A-P04：独立计数器发生 false sharing#定位方法|定位方法]] · [[08-性能与调度优化/A-P04-独立计数器发生false-sharing/A-P04：独立计数器发生 false sharing#内核流程与汇编|内核流程与汇编]] · [[08-性能与调度优化/A-P04-独立计数器发生false-sharing/A-P04：独立计数器发生 false sharing#修复与验收|修复与验收]]

## 现象与原理

**生产现场与现象。** 多核数据采集增加线程后吞吐反而下降，锁统计却没有明显竞争。

**原理与因果关系。** 逻辑上独立的数据可能共享缓存一致性粒度，写入导致缓存行所有权反复转移。原子指令开销、真实共享与 false sharing 是三个假设，需布局及单核/双核对照排除。

## 练习任务

设备端：运行“独立计数器发生false-sharing”故障现场，记录输出中的实际结果目录与异常证据。

```sh
sadboard run perf-sharing
```

设备端：执行“独立计数器发生false-sharing”的参考修复验收，核对终端结论及保存的结果契约。

```sh
sadboard verify perf-sharing
```

把下方路径替换为完成后打印的实际目录：

设备端：把路径占位符替换为本次实际现场目录，复核该次运行的证据完整性与验收约束。

```sh
sadboard check /srv/sadboard/实际目录
```

本例为固定有界负载，无额外参数。源码 [suite-performance.c](https://github.com/linux-bsp/sadboard-external/blob/93c81e82acfdf5d54155d1b9bb750e78645d384f/package/sadboard-labs/src/suite-performance.c)；两个绑核线程各做 500000 次独立原子递增，比较同缓存行与相距 64 B。observed 是实际指针间距 8/64，completed/checksum=1000000；性能收益另看 CPU/wall 与 PMU，不作单次倍率保证。

`perf-sharing-{bug,fixed}.out/.trace` 分别保存摘要与原始事件，字段 observed/auxiliary 的含义以上述本例定义为准。摘要、trace 和完成数必须相符。与正常业务输出不同的故障结果会由本例契约明确识别；不能拿最外层退出0证明没有异常。性能题同时保留 cpu_ns/wall_ns，至少三次再评价时序，不只看资源上界或一次漂亮数字。

**实际复现负载。** 两个绑核线程各做 500000 次独立原子递增，比较同缓存行与相距 64 B。observed 是实际指针间距 8/64，completed/checksum=1000000；性能收益另看 CPU/wall 与 PMU，不作单次倍率保证。

**面试/评审追问。** padding 何时只增加内存却不提升速度？为什么共享只读数据不等同于 false sharing？

## 使用工具

通用原理、参数和使用边界见工具手册；具体命令与证据判断见本例定位方法。

[[工具手册/sadboard|sadboard]] · [[工具手册/strace|strace]] · [[工具手册/perf|perf]] · [[工具手册/火焰图|火焰图]] · [[工具手册/trace-cmd|trace-cmd]]

## 定位方法

**定位流程与工具。** 检查 sysfs 缓存行信息、对象地址和反汇编；perf stat 先列举支持的 cycles/instructions/cache 事件，不把不支持的远端 HITM 事件硬搬到 Cortex-A53。

参数查阅：[[工具手册/perf|本方向基础工具参数与边界]]。

## 内核流程与汇编

**内核源码阅读。** [atomic_t.rst](https://github.com/linux-bsp/linux-7.0/blob/master/Documentation/core-api/wrappers/atomic_t.rst)：内核原子语义，用户 C 原子仍按其语言标准；[arm_pmuv3.c](https://github.com/linux-bsp/linux-7.0/blob/master/drivers/perf/arm_pmuv3.c)：ARM PMUv3 事件支持。从用户接口找到入口，检查配置/标志/失败分支，再画出本题的路径；这些链接不是实机完整调用栈。

## 修复与验收

**修复与工程取舍。** 按写入所有权分片或分离热点字段，减少每条记录的原子更新。对齐增加内存和缓存占用，应解释收益来自布局还是减少工作量。

**量化验收与清理。** 最终计数完全相同；预热后至少三次记录 wall/CPU、cycles/op 与事件可用性，单核对照不应被当作多核一致性证据。

[[附录A-实验报告/00-章节导航|实验报告与复盘]] · [[00-实验准备与通用方法/01-构建与启动部署#源码与实机证据|匹配源码、固件与实测证据]]

[[08-性能与调度优化/A-P03-共享事件循环中的慢回调阻塞控制请求/A-P03：共享事件循环中的慢回调阻塞控制请求|上一例 A-P03]] · [[08-性能与调度优化/A-P05-高频日志格式化与系统调用放大/A-P05：高频日志格式化与系统调用放大|下一例 A-P05]]
