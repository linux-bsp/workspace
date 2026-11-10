---
title: "GDB 定位应用崩溃"
type: "topic"
tags: ["sadboard/topic"]
chapter: "附录C-Bootlin课程参考"
---

# GDB 定位应用崩溃

[[首页]] · [[附录C-Bootlin课程参考/00-章节导航|章节导航]] · [[案例索引]] · [[工具索引]]


## C.3.3 GDB 定位应用崩溃

**现场：linked_list 程序从文件读取单词、构建链表，本应打印内容，却发生崩溃。**

实验先用 Compiler Explorer 观察 C 代码与优化后汇编的关系，再通过目标板 gdbserver 和主机 GDB 远程调试链表程序。排查涉及断点、单步、条件断点、watchpoint、结构体与链表宏，要求理解数据结构如何在运行中损坏。

随后开启 core dump，重新触发崩溃，在主机加载程序与 core，查看崩溃时的寄存器、内存和变量。core 是事后快照，不能继续执行或单步运行。

最后补全一个 GDB Python 脚本，遍历并格式化输出链表；附加练习将远程调试配置到 VS Code。

**学习产出：**能分别完成在线定位、离线定位和自定义数据结构检查，并正确设置目标 sysroot 与符号路径。[手册第 9 至 12 页](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.pdf#page=9)
