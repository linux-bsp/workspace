---
title: "Cachegrind 和 perf 分析 PNG 转换性能"
type: "topic"
tags: ["sadboard/topic"]
chapter: "附录C-Bootlin课程参考"
---

# Cachegrind 和 perf 分析 PNG 转换性能

[[首页]] · [[附录C-Bootlin课程参考/00-章节导航|章节导航]] · [[案例索引]] · [[工具索引]]


## C.3.7 Cachegrind 和 perf 分析 PNG 转换性能

**现场：png_convert 执行图像转换，需要分析其内存访问与计算成本。**

先用 Cachegrind 观察缓存访问问题，在 KCachegrind 中找出代价集中的函数，修改循环访问顺序，再次测量。随后用 Callgrind 查看调用关系与成本分布。

接着切换到真实系统上的 perf：用 perf list 检查硬件支持的事件，用 perf stat 比较缓存未命中，再通过 perf record 和 perf report 观察热点，最后增加调用栈采集以分析调用路径。

手册特别展示了 PMU 能力边界：目标处理器未暴露所需的 L1 数据缓存写未命中事件，因此实验改用支持的读未命中事件。不能假设所有处理器都支持同一组 perf 事件。

**学习产出：**能把“修改访问方式”与“缓存指标和运行表现变化”联系起来，并理解模拟分析与实机采样为什么可能不同。[手册第 17 至 19 页](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.pdf#page=17)
