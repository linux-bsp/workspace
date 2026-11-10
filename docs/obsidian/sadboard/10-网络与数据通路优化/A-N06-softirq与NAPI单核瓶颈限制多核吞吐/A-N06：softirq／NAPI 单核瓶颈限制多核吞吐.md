[[首页]] · [[案例索引]] · [[工具索引]] · [[10-网络与数据通路优化/00-章节导航|章节导航]]

先按现象提出假设并完成练习，再核对定位、内核机制和参考修复。`verify` 验证镜像提供的参考实现。

[[10-网络与数据通路优化/A-N06-softirq与NAPI单核瓶颈限制多核吞吐/A-N06：softirq／NAPI 单核瓶颈限制多核吞吐#现象与原理|现象与原理]] · [[10-网络与数据通路优化/A-N06-softirq与NAPI单核瓶颈限制多核吞吐/A-N06：softirq／NAPI 单核瓶颈限制多核吞吐#练习任务|练习任务]] · [[10-网络与数据通路优化/A-N06-softirq与NAPI单核瓶颈限制多核吞吐/A-N06：softirq／NAPI 单核瓶颈限制多核吞吐#使用工具|使用工具]] · [[10-网络与数据通路优化/A-N06-softirq与NAPI单核瓶颈限制多核吞吐/A-N06：softirq／NAPI 单核瓶颈限制多核吞吐#定位方法|定位方法]] · [[10-网络与数据通路优化/A-N06-softirq与NAPI单核瓶颈限制多核吞吐/A-N06：softirq／NAPI 单核瓶颈限制多核吞吐#内核流程与汇编|内核流程与汇编]] · [[10-网络与数据通路优化/A-N06-softirq与NAPI单核瓶颈限制多核吞吐/A-N06：softirq／NAPI 单核瓶颈限制多核吞吐#修复与验收|修复与验收]]

## 现象与原理

**生产现场与现象。** 多核板整体 CPU 没满，一个核却持续忙于收包；增加应用线程收效有限。

**原理与因果关系。** RSS 硬件分流、RPS 软件分流、NAPI poll budget 与应用亲和性共同影响局部热点；单流哈希不一定跨核，软件分流还增加 IPI/缓存代价。

## 练习任务

设备端：运行“softirq与NAPI单核瓶颈限制多核吞吐”故障现场，记录输出中的实际结果目录与异常证据。

```sh
sadboard run net-rps
```

设备端：执行“softirq与NAPI单核瓶颈限制多核吞吐”的参考修复验收，核对终端结论及保存的结果契约。

```sh
sadboard verify net-rps
```

把下方路径替换为完成后打印的实际目录：

设备端：把路径占位符替换为本次实际现场目录，复核该次运行的证据完整性与验收约束。

```sh
sadboard check /srv/sadboard/实际目录
```

本例为固定有界负载，无额外参数。源码 [suite-advanced-network.c](https://github.com/linux-bsp/sadboard-external/blob/93c81e82acfdf5d54155d1b9bb750e78645d384f/package/sadboard-labs/src/suite-advanced-network.c)；在 AM625 的私有 veth 上真实设置 RX rps_cpus=0/8，发送进程绑 CPU2，参考分流到 CPU3；接收端从 SO_INCOMING_CPU 报告实际协议接收 CPU。两版完整传输262144 B、checksum=11010048。它验证软件 RPS，不冒充物理 CPSW RSS 能力或线速。

`net-rps-{bug,fixed}.out/.trace` 分别保存摘要与原始事件，字段 observed/auxiliary 的含义以上述本例定义为准。摘要、trace 和完成数必须相符。与正常业务输出不同的故障结果会由本例契约明确识别；不能拿最外层退出0证明没有异常。性能题同时保留 cpu_ns/wall_ns，至少三次再评价时序，不只看资源上界或一次漂亮数字。

**实际复现负载。** 在 AM625 的私有 veth 上真实设置 RX rps_cpus=0/8，发送进程绑 CPU2，参考分流到 CPU3；接收端从 SO_INCOMING_CPU 报告实际协议接收 CPU。两版完整传输262144 B、checksum=11010048。它验证软件 RPS，不冒充物理 CPSW RSS 能力或线速。

**面试/评审追问。** 为何增加 RPS 可能降低吞吐？单流、多个五元组与应用多线程之间有什么区别？

## 使用工具

通用原理、参数和使用边界见工具手册；具体命令与证据判断见本例定位方法。

[[工具手册/sadboard|sadboard]] · [[工具手册/perf|perf]] · [[工具手册/iperf3|iperf3]] · [[工具手册/tcpdump|tcpdump]] · [[工具手册/ss|ss]] · [[工具手册/tc|tc]] · [[工具手册/ip|ip]]

## 定位方法

**定位流程与工具。** 逐核 perf/softirq 时间、IRQ 增量、网卡 drops 与单流/多流对照；先核实网卡队列和驱动能力，再解释“多核未利用”。

参数查阅：[[06-网络分析/B-NET01-netem延迟与丢包导致网络变慢或中断/B-NET01：网络延迟丢包与吞吐#定位方法|本方向基础工具参数与边界]]。

## 内核流程与汇编

RSS/RPS/RFS/XPS 术语可对照 [内核网络扩展文档](https://docs.kernel.org/networking/scaling.html)；
具体路径以以下固定版本的源码为准，不能把当前硬件不具备的多队列能力当成已验证方案。

**内核源码阅读。** [dev.c](https://github.com/linux-bsp/linux-7.0/blob/1c04c52c72b0e67ad4b5deca464ea70bc6ebb718/net/core/dev.c)：net_rx_action、NAPI poll；[gro.c](https://github.com/linux-bsp/linux-7.0/blob/1c04c52c72b0e67ad4b5deca464ea70bc6ebb718/net/core/gro.c)：GRO 聚合；[scaling.rst](https://github.com/linux-bsp/linux-7.0/blob/1c04c52c72b0e67ad4b5deca464ea70bc6ebb718/Documentation/networking/scaling.rst)：RSS/RPS/RFS/XPS。从用户接口找到入口，检查配置/标志/失败分支，再画出本题的路径；这些链接不是实机完整调用栈。

## 修复与验收

**修复与工程取舍。** 在测试 NIC 范围调整队列/亲和性/应用布局，评估吞吐与控制 P99；不盲目增大 budget，也不承诺 AM625 所有硬件都支持 RSS。

**量化验收与清理。** 仅在具备测试链路时报告吞吐、每核 CPU、丢包与尾延迟，保存并恢复配置；当前硬件未执行的部分明确标为条件性实验。

[[附录A-实验报告/00-章节导航|实验报告与复盘]] · [[00-实验准备与通用方法/01-构建与启动部署#固定源码与实机证据|匹配源码、固件与实测证据]]

[[10-网络与数据通路优化/A-N05-MTU与PMTU黑洞造成小包正常、大包卡住/A-N05：MTU／PMTU 黑洞造成小包正常、大包卡住|上一例 A-N05]] · [[10-网络与数据通路优化/A-N07-大文件与遥控共用队列产生队头阻塞/A-N07：大文件与遥控共用队列产生队头阻塞|下一例 A-N07]]
