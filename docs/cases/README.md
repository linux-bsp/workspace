# 案例学习手册

教材总入口见 [学习路线](../study-guide.md)；初次学习先读
[故障定位基础](../debugging-foundations.md)，再进入具体案例。

先按 [快速入门](../am625-quickstart.md) 构建、登录设备并确认固件健康，再按顺序学习。
每个案例先读“问题现场”，独立取证，再看根因与参考修复；不要只运行 `verify`。
希望先做题、后看答案时，使用 [分级练习册](../workbook.md)，并复制
[实验报告模板](../lab-report-template.md)。[内核阅读笔记](../kernel-reading-notes.md)
补充每条调用路径成立的条件及常见误读。

| 案例 | 重点能力 | 原理与源码 |
| --- | --- | --- |
| [应用崩溃](crash.md) | GDB、core、寄存器、反汇编 | ARM64 缺页异常、SIGSEGV、ELF core |
| [描述符泄漏与耗尽](fd-exhaustion.md) | strace、/proc/PID/fd、资源上限 | FD 表、打开文件对象、EMFILE、close/fput |
| [内存泄漏与 cgroup OOM](oom.md) | 内存趋势、cgroup、Valgrind | 按需分配、memcg 计费、回收与杀进程 |
| [CPU 查找热点](cpu.md) | perf stat/record、火焰图 | 算法复杂度、PMU、中断采样与调用链 |
| [持锁等待](lock.md) | 线程栈、strace、调度 trace | 用户态互斥锁、futex、睡眠与唤醒 |
| [网络延迟与丢包](network.md) | ping、iperf3、tcpdump、ss、tc | namespace、veth、qdisc、TCP 时延与重传 |
| [内核 panic 与启动恢复](kernel-panic.md) | 原始串口、栈解码、pstore、SOL | SysRq、panic、ramoops、跨启动关联 |

[工具手册](../debug-tools.md) 解释通用参数、符号准备与常见误判；各案例给出具体分析流程。
[场景管理](../scenario-lifecycle.md) 说明统一现场、参数、status/check/reset 和监督边界。
上述七个案例均已完成 AM625 实机验收；具体固件 ID、采样数据和启动日志结果见实机记录。

## 源码与证据约定

本手册的内核路径根据仓库 `linux/linux-7.0` 的固定提交
`1c04c52c72b0e67ad4b5deca464ea70bc6ebb718` 阅读整理，不直接套用其他内核版本的栈。
图中的箭头表示关键逻辑路径，省略异常入口、包装层和条件分支；**不是实机堆栈原文**。
程序自身运行在用户态，GDB 的用户栈也不会自动包含内核栈。

实验源代码在 `sadboard-external/package/sadboard-labs/src/`，设备副本在
`/usr/src/sadboard/src/`。每个固件的 `images/debug/` 保存配套源码、ELF、vmlinux、
配置及 SHA256 清单。仓库源码用于理解，镜像配套源码用于解释具体地址和行号。
实际执行结果集中记录于 [实机验证记录](../am625-debug-validation.md)；命令示例中
明确标为扩展练习的部分，不代表已经逐条完成实机验证。

## 每次实验要交付什么

1. 固件完整 ID、boot ID、输入、时间、命令与退出码。
2. 原始证据，以及对关键字段的解释。
3. 一个可以被证据推翻的根因假设；说明排除了哪些相近故障。
4. 故障版和修复版的同输入对照，检查业务正确性及资源消耗。
5. 清理过程与设备健康结果。

建议保存一次不看答案的分析笔记，再与手册比较。练习目标是建立证据链，
不能仅凭某条日志、一个热点函数或一次耗时就得出结论。
