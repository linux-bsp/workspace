---
title: "ltrace 和 strace 分析应用行为"
type: "topic"
tags: ["sadboard/topic"]
chapter: "附录C-Bootlin课程参考"
---

# ltrace 和 strace 分析应用行为

[[首页]] · [[附录C-Bootlin课程参考/00-章节导航|章节导航]] · [[案例索引]] · [[工具索引]]


## C.3.4 ltrace 和 strace 分析应用行为

**现场一：authent 程序报告认证失败。**使用 ltrace 找出失败的库函数，再编写实验用共享库，通过 LD_PRELOAD 替换该函数，观察行为变化。重点是认识动态链接边界和函数替换机制。

**现场二：只有 strace_me 二进制，需要理解其行为。**使用 strace 查出它打开的文件、read 调用次数、失败的 openat，以及系统调用总量。

**学习产出：**能区分库函数和系统调用两种观察层次，并从参数、返回值和调用序列提出可验证的判断。[手册第 13 至 14 页](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.pdf#page=13)
