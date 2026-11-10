---
title: "使用 libbpf 将跟踪工具部署到开发板"
type: "topic"
tags: ["sadboard/topic"]
chapter: "附录C-Bootlin课程参考"
---

# 使用 libbpf 将跟踪工具部署到开发板

[[首页]] · [[附录C-Bootlin课程参考/00-章节导航|章节导航]] · [[案例索引]] · [[工具索引]]


## C.3.10 使用 libbpf 将跟踪工具部署到开发板

**现场：BCC 原型依赖 Python、LLVM、Clang 等，直接放到嵌入式目标上不够方便。**

将原型移植到 libbpf：生成 vmlinux.h，编译 BPF 对象，理解 SEC、架构相关参数与 CO-RE，先用 bpftool 加载和检查程序，再生成 skeleton，编写用户态 C 程序管理加载与挂载。

随后将输出改成通过 BPF ring buffer 传给用户态，最后读取 task_struct 中的父进程信息，让工具能说明“哪个进程启动了这个程序”。涉及 BPF_MAP_TYPE_RINGBUF、bpf_ringbuf_output、ring_buffer__poll 和 BPF_CORE_READ 等接口。

**学习产出：**把临时跟踪脚本做成适合目标板部署的小工具，并理解 BTF、内核结构访问与架构依赖。[手册第 23 至 26 页](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.pdf#page=23)
