[[README|首页]] · [[00-实验准备与通用方法/案例索引|案例索引]] · [[00-实验准备与通用方法/工具索引|工具索引]] · [[08-性能与调度优化/00-章节导航|章节导航]]

先按现象提出假设并完成练习，再核对定位、内核机制和参考修复。`verify` 验证镜像提供的参考实现。

[[08-性能与调度优化/A-P08-CPU-quota周期性节流被误认成算法抖动/A-P08：CPU quota 周期性节流被误认成算法抖动#现象与原理|现象与原理]] · [[08-性能与调度优化/A-P08-CPU-quota周期性节流被误认成算法抖动/A-P08：CPU quota 周期性节流被误认成算法抖动#练习任务|练习任务]] · [[08-性能与调度优化/A-P08-CPU-quota周期性节流被误认成算法抖动/A-P08：CPU quota 周期性节流被误认成算法抖动#使用工具|使用工具]] · [[08-性能与调度优化/A-P08-CPU-quota周期性节流被误认成算法抖动/A-P08：CPU quota 周期性节流被误认成算法抖动#定位方法|定位方法]] · [[08-性能与调度优化/A-P08-CPU-quota周期性节流被误认成算法抖动/A-P08：CPU quota 周期性节流被误认成算法抖动#内核流程与汇编|内核流程与汇编]] · [[08-性能与调度优化/A-P08-CPU-quota周期性节流被误认成算法抖动/A-P08：CPU quota 周期性节流被误认成算法抖动#修复与验收|修复与验收]]

## 现象与原理

**生产现场与现象。** 容器化边缘服务每隔一段时间出现整段停顿，主机整体 CPU 仍有空闲。

**原理与因果关系。** CFS 带宽预算耗尽后即使机器其他核有空闲，该组也可能等待下个补充窗口。亲和性、cpufreq/温度和 IRQ 压力会有相似现象，必须按证据区分。

## 练习任务

设备端：运行“CPU-quota周期性节流被误认成算法抖动”故障现场，记录输出中的实际结果目录与异常证据。

```sh
sadboard run perf-quota
```

设备端：执行“CPU-quota周期性节流被误认成算法抖动”的参考修复验收，核对终端结论及保存的结果契约。

```sh
sadboard verify perf-quota
```

把下方路径替换为完成后打印的实际目录：

设备端：把路径占位符替换为本次实际现场目录，复核该次运行的证据完整性与验收约束。

```sh
sadboard check /srv/sadboard/实际目录
```

本例为固定有界负载，无额外参数。源码 [suite-performance.c](https://github.com/linux-bsp/sadboard-external/blob/93c81e82acfdf5d54155d1b9bb750e78645d384f/package/sadboard-labs/src/suite-performance.c)；仅自建 cgroup 的子进程运行相同 30000000 次 32 位 LCG，cpu.max 为 25000/100000 或 max。observed/throttled_usec 来自 cpu.stat；checksum=213978538。子进程设置父死亡 SIGKILL，组有独立 memory/pids 上限，完成/取消清理归属本现场的组。

`perf-quota-{bug,fixed}.out/.trace` 分别保存摘要与原始事件，字段 observed/auxiliary 的含义以上述本例定义为准。摘要、trace 和完成数必须相符。与正常业务输出不同的故障结果会由本例契约明确识别；不能拿最外层退出0证明没有异常。性能题同时保留 cpu_ns/wall_ns，至少三次再评价时序，不只看资源上界或一次漂亮数字。

**实际复现负载。** 仅自建 cgroup 的子进程运行相同 30000000 次 32 位 LCG，cpu.max 为 25000/100000 或 max。observed/throttled_usec 来自 cpu.stat；checksum=213978538。子进程设置父死亡 SIGKILL，组有独立 memory/pids 上限，完成/取消清理归属本现场的组。

**面试/评审追问。** CPUQuota=25% 是否等于固定一个核的 25%？平均 CPU 与预算补充周期为什么都会影响长尾？

## 使用工具

通用原理、参数和使用边界见工具手册；具体命令与证据判断见本例定位方法。

[[工具手册/sadboard|sadboard]] · [[工具手册/strace|strace]] · [[工具手册/perf|perf]] · [[工具手册/火焰图|火焰图]] · [[工具手册/trace-cmd|trace-cmd]]

## 定位方法

**定位流程与工具。** 保存实验 cgroup 的 cpu.max、cpu.stat 的 nr_throttled/throttled_usec 增量和 PSI；perf 采样仅看到正在执行的部分，不能单凭火焰图解释停顿。

参数查阅：[[工具手册/perf|本方向基础工具参数与边界]]。

## 内核流程与汇编

**内核源码阅读。** [fair.c](https://github.com/linux-bsp/linux-7.0/blob/master/kernel/sched/fair.c)：CFS bandwidth 与 throttle_cfs_rq；[cgroup-v2.rst](https://github.com/linux-bsp/linux-7.0/blob/master/Documentation/admin-guide/cgroup-v2.rst)：cpu.max、cpu.stat、cpu.pressure。从用户接口找到入口，检查配置/标志/失败分支，再画出本题的路径；这些链接不是实机完整调用栈。

## 修复与验收

**修复与工程取舍。** 按真实 CPU 预算设计任务、调节该服务配额或分解工作；先证明节流是瓶颈，不把全局关闭节流当作修复。

**量化验收与清理。** 同输入吞吐、响应 P99、节流增量可关联；解除实验配额后恢复基线，记录其他进程是否受影响。

[[附录A-实验报告/00-章节导航|实验报告与复盘]] · [[00-实验准备与通用方法/01-构建与启动部署#源码与实机证据|匹配源码、固件与实测证据]]

[[08-性能与调度优化/A-P07-冷启动缺页导致首帧长尾/A-P07：冷启动缺页导致首帧长尾|上一例 A-P07]]
