---
title: "kexec 和 kdump 事后分析"
type: "topic"
tags: ["sadboard/topic"]
chapter: "附录C-Bootlin课程参考"
---

# kexec 和 kdump 事后分析

[[首页]] · [[附录C-Bootlin课程参考/00-章节导航|章节导航]] · [[案例索引]] · [[工具索引]]


## C.3.14 kexec 和 kdump 事后分析

**现场：系统崩溃后，需要保留内核现场供离线分析。**

构建专门的捕获内核，为其预留 crashkernel 内存，设置 Oops 转为 panic 并加载捕获内核。触发故障后进入第二个内核，导出 /proc/vmcore，再将 vmcore 与对应的 vmlinux 一起交给 GDB 分析。课程大纲另列出 crash 工具，但这份手册的具体收尾步骤使用 GDB。

BeaglePlay 实验还展示了板级限制：崩溃后通过 kexec 进入的新内核，可能无法正确重新初始化部分外围设备，因此使用 SD 卡取回 vmcore，不能想当然地依赖网络导出。

**学习产出：**理解“捕获内核启动成功”“转储文件保存成功”“符号匹配并可分析”是三个分别需要验证的环节。[手册第 33 至 34 页](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.pdf#page=33)
