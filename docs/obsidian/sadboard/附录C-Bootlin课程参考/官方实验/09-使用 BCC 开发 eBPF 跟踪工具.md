---
title: "使用 BCC 开发 eBPF 跟踪工具"
type: "topic"
tags: ["sadboard/topic"]
chapter: "附录C-Bootlin课程参考"
---

# 使用 BCC 开发 eBPF 跟踪工具

[[首页]] · [[附录C-Bootlin课程参考/00-章节导航|章节导航]] · [[案例索引]] · [[工具索引]]


## C.3.9 使用 BCC 开发 eBPF 跟踪工具

**现场：怀疑系统中有未知程序被启动，希望记录程序执行活动。**

先在开发主机上用 Python 与 BCC 编写原型，把 eBPF 程序挂到 execve 对应的内核入口，输出 PID 与程序名。实验要求找到正确的入口与参数形式，并理解程序加载失败时 verifier 给出的信息。

**学习产出：**能完成一个简单的自定义跟踪工具，理解挂载点、事件字段、输出方式和程序生命周期。[手册第 22 页](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.pdf#page=22)
