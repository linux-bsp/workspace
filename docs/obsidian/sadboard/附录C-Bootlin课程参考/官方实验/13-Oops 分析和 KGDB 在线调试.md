---
title: "Oops 分析和 KGDB 在线调试"
type: "topic"
tags: ["sadboard/topic"]
chapter: "附录C-Bootlin课程参考"
---

# Oops 分析和 KGDB 在线调试

[[首页]] · [[附录C-Bootlin课程参考/00-章节导航|章节导航]] · [[案例索引]] · [[工具索引]]


## C.3.13 Oops 分析和 KGDB 在线调试

**现场：在课程特制内核中操作 watchdog，触发内核 Oops。**

先分析 PC、调用栈、函数内偏移，使用匹配的 vmlinux、addr2line、decode_stacktrace.sh 和 GDB 反汇编，将现场关联到源码。

然后通过 KGDB 连接内核，检查变量。由于可疑的数据设置发生在启动早期，实验进一步配置 kgdbwait，在 watchdog_set_drvdata 处设置断点，追踪 driver_data 被错误覆盖的过程。另一个练习用 lx-symbols 加载模块符号，在模块代码中断点调试。

**学习产出：**从“崩溃点”继续追踪到“错误状态产生的位置”。实验中的现场修改可以验证假设，但真正修复仍需修改源码并重新验证。[手册第 29 至 32 页](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.pdf#page=29)
