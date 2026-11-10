---
title: "kmemleak 定位内核模块泄漏"
type: "topic"
tags: ["sadboard/topic"]
chapter: "附录C-Bootlin课程参考"
---

# kmemleak 定位内核模块泄漏

[[首页]] · [[附录C-Bootlin课程参考/00-章节导航|章节导航]] · [[案例索引]] · [[工具索引]]


## C.3.12 kmemleak 定位内核模块泄漏

**现场：kmemleak_test 模块卸载后仍有未正确释放的内存。**

通过启动参数开启 kmemleak，加载并卸载模块，触发扫描、读取结果，再使用模块加载地址与 addr2line 关联到代码。手册提醒，残留引用可能使泄漏不能在第一次扫描时立刻被报告。

**学习产出：**理解内核泄漏报告、符号地址和模块重定位的关系，避免把暂未报告解释为没有泄漏。[手册第 27 至 28 页](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.pdf#page=27)
