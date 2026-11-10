---
title: "ftrace 和 KernelShark 分析调度干扰"
type: "topic"
tags: ["sadboard/topic"]
chapter: "附录C-Bootlin课程参考"
---

# ftrace 和 KernelShark 分析调度干扰

[[首页]] · [[附录C-Bootlin课程参考/00-章节导航|章节导航]] · [[案例索引]] · [[工具索引]]


## C.3.8 ftrace 和 KernelShark 分析调度干扰

**现场：crc_random 的 CRC 计算间隔不稳定，系统同时运行 mystery_program。**

使用 perf probe 为用户程序添加 uprobe，在 CRC 计算位置采集数据；再通过 trace-cmd 采集并发送到主机，在 KernelShark 中观察时间分布。发现执行间隔异常后，加入 sched_switch 事件，将应用行为与调度切换放到同一条时间线上分析。

附加实验使用 perf 与 FlameGraph 观察系统负载，并建议回到 png_convert 案例生成火焰图，对照之前的热点判断。

**学习产出：**能把“程序什么时候计算”与“线程什么时候得到 CPU”联系起来。火焰图适合聚合调用栈成本，调度时间线适合分析先后关系，两者回答的问题不同。[手册第 20 至 21 页](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.pdf#page=20)
