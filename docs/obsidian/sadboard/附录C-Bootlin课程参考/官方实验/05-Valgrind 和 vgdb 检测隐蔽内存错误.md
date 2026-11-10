---
title: "Valgrind 和 vgdb 检测隐蔽内存错误"
type: "topic"
tags: ["sadboard/topic"]
chapter: "附录C-Bootlin课程参考"
---

# Valgrind 和 vgdb 检测隐蔽内存错误

[[首页]] · [[附录C-Bootlin课程参考/00-章节导航|章节导航]] · [[案例索引]] · [[工具索引]]


## C.3.5 Valgrind 和 vgdb 检测隐蔽内存错误

**现场：faulty_mem_app 看似可以运行，没有立即出现段错误，但内部存在内存问题。**

Valgrind 检出非法写入、使用未初始化内存与内存泄漏。接着通过 vgdb 连接主机 GDB，在检测到错误时停止，检查当时的程序状态并修复问题。

这个实验的价值在于：可见崩溃可能晚于真正的错误写入，程序没有崩溃也不代表内存访问正确。

**学习产出：**区分不同内存报告，定位错误发生的位置，并在修改后重新运行检查。[手册第 15 至 16 页](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.pdf#page=15)
