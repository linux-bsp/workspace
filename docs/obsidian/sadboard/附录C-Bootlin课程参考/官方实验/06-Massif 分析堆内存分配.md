---
title: "Massif 分析堆内存分配"
type: "topic"
tags: ["sadboard/topic"]
chapter: "附录C-Bootlin课程参考"
---

# Massif 分析堆内存分配

[[首页]] · [[附录C-Bootlin课程参考/00-章节导航|章节导航]] · [[案例索引]] · [[工具索引]]


## C.3.6 Massif 分析堆内存分配

**现场：heap_profile 程序具有不同阶段的内存分配行为。**

用 Massif 采集堆分配数据，通过 ms_print 或 massif-visualizer 查看峰值、分配过程和结束时的内存情况。手册还建议在主机上尝试 heaptrack。

需要特别注意，实验指定了 --time-unit=B，因此图中横轴按累计分配字节推进，不能直接解释为秒。堆使用曲线有助于提出泄漏假设，具体泄漏仍应结合内存检查和对象生命周期判断。

**学习产出：**能解释峰值来自哪里，区分瞬时峰值、持续增长与最终释放情况。[手册第 17 页](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.pdf#page=17)
