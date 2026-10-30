# Bootlin Linux 调试课程详解与实验学习指南

Bootlin 的 Linux debugging, profiling, tracing and performance analysis 课程，覆盖从用户态崩溃、内存错误和应用性能，到系统跟踪、eBPF、内核 Oops 与崩溃转储的分析流程。对于嵌入式 Linux 故障训练项目，最值得借鉴的是“带缺陷的程序或模块 + 可观察现场 + 分步定位 + 修改验证”的实验组织方式。

整理日期：2026 年 10 月 30 日。课程主题依据官方大纲，实验细节以封面日期为 2026 年 10 月 23 日的 BeaglePlay 实验手册为主，并参考 STM32MP1 版本。本文为中文归纳与学习建议，非官方逐页翻译；后文的项目扩展建议单独列出。

## 课程定位与学习条件

课程面向需要排查 Linux 应用和系统问题的工程师。线下课程为 3 天、24 小时；线上为 4 个半天、16 小时。线下安排大量动手实验；线上实验主要由讲师演示，有对应硬件的学员可自行复现。所需基础包括 Linux 命令行、C 程序开发，以及内核与用户空间的基本关系。课件、实验手册和实验资料可免费获取。[课程主页](https://bootlin.com/training/debugging/)

官方实验平台提供 STM32MP157 Discovery 和 BeaglePlay 两种版本。课程方法可迁移到其他平台，但板卡启动参数、交叉编译器、串口、硬件性能事件和转储流程需要重新适配。官方这套调试实验不是开箱即用的通用 QEMU 镜像。[BeaglePlay 手册第 5 至 7 页](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.pdf#page=5)

## 课程知识结构

课程按以下顺序推进：Linux 运行机制与系统观测 → GDB 应用调试 → 应用调用跟踪 → 内存问题 → 应用性能 → 全系统跟踪 → eBPF 工具开发 → 内核调试。以下主题对应官方大纲，具体案例在下一节展开。[官方课程大纲第 3 至 4 页](https://bootlin.com/doc/training/debugging/debugging-agenda.pdf#page=3)

### Linux 运行机制和基础观测

理解进程与线程、ELF、堆栈和共享库映射、虚拟与物理地址、调度与上下文切换，以及内核线程、workqueue、中断和 softirq。使用 GNU 二进制工具，以及 procfs、sysfs、debugfs 和系统状态工具，把资源指标与运行机制联系起来。

### 应用调试和调用跟踪

GDB 覆盖在线调试、远程调试、core 离线分析、编译优化对调试的影响和 Python 扩展。strace 观察系统调用；ltrace 观察动态库调用；LD_PRELOAD 用于替换库函数行为。

### 内存与应用性能

分析越界、未初始化内存、泄漏等问题，涉及 Valgrind、vgdb、libefence、Massif 和 heaptrack。性能部分使用 Cachegrind、Callgrind、KCachegrind、perf 和火焰图，从内存访问、调用关系与实际采样三个角度理解成本。

### 系统跟踪和 eBPF

使用 perf、kprobes、ftrace、KernelShark、LTTng 等机制分析整个系统。eBPF 部分既讲工具和框架，也通过 BCC 与 libbpf 开发定制跟踪程序。

### 内核调试

理解 vmlinux、System.map、Oops 行为与崩溃转储；涉及 crash、KGDB、KDB、KASAN、UBSAN、kmemleak、lockdep 和调试配置。大纲中出现的工具不一定都有独立完整实验，实践深度应结合下面的手册案例判断。

## 官方实验逐项详解

以下页码均为 BeaglePlay 实验 PDF 的阅读器页码，从封面算第 1 页。

### 实验准备

**目标：构建一套方便交叉编译、部署、调试和回收数据的嵌入式环境。**

使用 Bootlin 的 Buildroot 分支构建工具链、内核、文件系统和调试工具。BeaglePlay 手册使用 debugging-training-beagleplay/2025.02 分支与 beagleplay_debugging_defconfig；STM32MP1 使用对应分支和配置。开发板从 SD 卡启动内核，根文件系统通过 NFS 提供，主机通过串口和 SSH 操作目标。

这一配置让主机编译出的实验程序直接出现在目标文件系统里，也便于在主机分析目标采集的 core、perf.data 和 trace 数据。后续实验还反复使用主机上的 sysroot、带符号的程序、vmlinux 和模块文件。

**学习产出：**能说明主机、目标板、工具链、符号文件和运行镜像分别承担什么角色，避免把目标板上裁剪过的二进制当成完整调试资料。[手册第 5 至 7 页](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.pdf#page=5)

### 系统状态观察

**现场：系统已经运行若干进程，并有 CPU 与 MMC I/O 背景负载。**

实验要求回答具体问题：有多少 CPU；dropbear 映射了哪些内存；PSS 多大；应用可用内存与空闲内存各是多少；是否发生交换；谁消耗 CPU；CPU0 在内核态花了多少时间；MMC 吞吐与发起 I/O 的进程是谁；中断主要落在哪个处理器。

使用 ps、top、procfs、pmap、vmstat、iostat 等工具，形成“先看系统资源，再定位进程或设备”的基本分析路径。

**学习产出：**提交一份有指标支撑的系统状态说明，而不是只给出“负载高”“内存少”。[手册第 8 页](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.pdf#page=8)

### GDB 定位应用崩溃

**现场：linked_list 程序从文件读取单词、构建链表，本应打印内容，却发生崩溃。**

实验先用 Compiler Explorer 观察 C 代码与优化后汇编的关系，再通过目标板 gdbserver 和主机 GDB 远程调试链表程序。排查涉及断点、单步、条件断点、watchpoint、结构体与链表宏，要求理解数据结构如何在运行中损坏。

随后开启 core dump，重新触发崩溃，在主机加载程序与 core，查看崩溃时的寄存器、内存和变量。core 是事后快照，不能继续执行或单步运行。

最后补全一个 GDB Python 脚本，遍历并格式化输出链表；附加练习将远程调试配置到 VS Code。

**学习产出：**能分别完成在线定位、离线定位和自定义数据结构检查，并正确设置目标 sysroot 与符号路径。[手册第 9 至 12 页](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.pdf#page=9)

### ltrace 和 strace 分析应用行为

**现场一：authent 程序报告认证失败。**使用 ltrace 找出失败的库函数，再编写实验用共享库，通过 LD_PRELOAD 替换该函数，观察行为变化。重点是认识动态链接边界和函数替换机制。

**现场二：只有 strace_me 二进制，需要理解其行为。**使用 strace 查出它打开的文件、read 调用次数、失败的 openat，以及系统调用总量。

**学习产出：**能区分库函数和系统调用两种观察层次，并从参数、返回值和调用序列提出可验证的判断。[手册第 13 至 14 页](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.pdf#page=13)

### Valgrind 和 vgdb 检测隐蔽内存错误

**现场：faulty_mem_app 看似可以运行，没有立即出现段错误，但内部存在内存问题。**

Valgrind 检出非法写入、使用未初始化内存与内存泄漏。接着通过 vgdb 连接主机 GDB，在检测到错误时停止，检查当时的程序状态并修复问题。

这个实验的价值在于：可见崩溃可能晚于真正的错误写入，程序没有崩溃也不代表内存访问正确。

**学习产出：**区分不同内存报告，定位错误发生的位置，并在修改后重新运行检查。[手册第 15 至 16 页](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.pdf#page=15)

### Massif 分析堆内存分配

**现场：heap_profile 程序具有不同阶段的内存分配行为。**

用 Massif 采集堆分配数据，通过 ms_print 或 massif-visualizer 查看峰值、分配过程和结束时的内存情况。手册还建议在主机上尝试 heaptrack。

需要特别注意，实验指定了 --time-unit=B，因此图中横轴按累计分配字节推进，不能直接解释为秒。堆使用曲线有助于提出泄漏假设，具体泄漏仍应结合内存检查和对象生命周期判断。

**学习产出：**能解释峰值来自哪里，区分瞬时峰值、持续增长与最终释放情况。[手册第 17 页](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.pdf#page=17)

### Cachegrind 和 perf 分析 PNG 转换性能

**现场：png_convert 执行图像转换，需要分析其内存访问与计算成本。**

先用 Cachegrind 观察缓存访问问题，在 KCachegrind 中找出代价集中的函数，修改循环访问顺序，再次测量。随后用 Callgrind 查看调用关系与成本分布。

接着切换到真实系统上的 perf：用 perf list 检查硬件支持的事件，用 perf stat 比较缓存未命中，再通过 perf record 和 perf report 观察热点，最后增加调用栈采集以分析调用路径。

手册特别展示了 PMU 能力边界：目标处理器未暴露所需的 L1 数据缓存写未命中事件，因此实验改用支持的读未命中事件。不能假设所有处理器都支持同一组 perf 事件。

**学习产出：**能把“修改访问方式”与“缓存指标和运行表现变化”联系起来，并理解模拟分析与实机采样为什么可能不同。[手册第 17 至 19 页](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.pdf#page=17)

### ftrace 和 KernelShark 分析调度干扰

**现场：crc_random 的 CRC 计算间隔不稳定，系统同时运行 mystery_program。**

使用 perf probe 为用户程序添加 uprobe，在 CRC 计算位置采集数据；再通过 trace-cmd 采集并发送到主机，在 KernelShark 中观察时间分布。发现执行间隔异常后，加入 sched_switch 事件，将应用行为与调度切换放到同一条时间线上分析。

附加实验使用 perf 与 FlameGraph 观察系统负载，并建议回到 png_convert 案例生成火焰图，对照之前的热点判断。

**学习产出：**能把“程序什么时候计算”与“线程什么时候得到 CPU”联系起来。火焰图适合聚合调用栈成本，调度时间线适合分析先后关系，两者回答的问题不同。[手册第 20 至 21 页](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.pdf#page=20)

### 使用 BCC 开发 eBPF 跟踪工具

**现场：怀疑系统中有未知程序被启动，希望记录程序执行活动。**

先在开发主机上用 Python 与 BCC 编写原型，把 eBPF 程序挂到 execve 对应的内核入口，输出 PID 与程序名。实验要求找到正确的入口与参数形式，并理解程序加载失败时 verifier 给出的信息。

**学习产出：**能完成一个简单的自定义跟踪工具，理解挂载点、事件字段、输出方式和程序生命周期。[手册第 22 页](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.pdf#page=22)

### 使用 libbpf 将跟踪工具部署到开发板

**现场：BCC 原型依赖 Python、LLVM、Clang 等，直接放到嵌入式目标上不够方便。**

将原型移植到 libbpf：生成 vmlinux.h，编译 BPF 对象，理解 SEC、架构相关参数与 CO-RE，先用 bpftool 加载和检查程序，再生成 skeleton，编写用户态 C 程序管理加载与挂载。

随后将输出改成通过 BPF ring buffer 传给用户态，最后读取 task_struct 中的父进程信息，让工具能说明“哪个进程启动了这个程序”。涉及 BPF_MAP_TYPE_RINGBUF、bpf_ringbuf_output、ring_buffer__poll 和 BPF_CORE_READ 等接口。

**学习产出：**把临时跟踪脚本做成适合目标板部署的小工具，并理解 BTF、内核结构访问与架构依赖。[手册第 23 至 26 页](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.pdf#page=23)

### 内核锁和睡眠错误

**现场：加载 locking_test 模块，内核报告锁或睡眠使用问题。**

使用已经启用 CONFIG_PROVE_LOCKING 与 CONFIG_DEBUG_ATOMIC_SLEEP 的内核，阅读 dmesg 中的诊断，理解并修复实验模块。

**学习产出：**识别锁依赖和不允许睡眠的执行上下文，从报告反推代码路径。此类检查会提供违反规则的证据，不必等系统完全失去响应才开始排查。[手册第 27 页](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.pdf#page=27)

### kmemleak 定位内核模块泄漏

**现场：kmemleak_test 模块卸载后仍有未正确释放的内存。**

通过启动参数开启 kmemleak，加载并卸载模块，触发扫描、读取结果，再使用模块加载地址与 addr2line 关联到代码。手册提醒，残留引用可能使泄漏不能在第一次扫描时立刻被报告。

**学习产出：**理解内核泄漏报告、符号地址和模块重定位的关系，避免把暂未报告解释为没有泄漏。[手册第 27 至 28 页](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.pdf#page=27)

### Oops 分析和 KGDB 在线调试

**现场：在课程特制内核中操作 watchdog，触发内核 Oops。**

先分析 PC、调用栈、函数内偏移，使用匹配的 vmlinux、addr2line、decode_stacktrace.sh 和 GDB 反汇编，将现场关联到源码。

然后通过 KGDB 连接内核，检查变量。由于可疑的数据设置发生在启动早期，实验进一步配置 kgdbwait，在 watchdog_set_drvdata 处设置断点，追踪 driver_data 被错误覆盖的过程。另一个练习用 lx-symbols 加载模块符号，在模块代码中断点调试。

**学习产出：**从“崩溃点”继续追踪到“错误状态产生的位置”。实验中的现场修改可以验证假设，但真正修复仍需修改源码并重新验证。[手册第 29 至 32 页](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.pdf#page=29)

### kexec 和 kdump 事后分析

**现场：系统崩溃后，需要保留内核现场供离线分析。**

构建专门的捕获内核，为其预留 crashkernel 内存，设置 Oops 转为 panic 并加载捕获内核。触发故障后进入第二个内核，导出 /proc/vmcore，再将 vmcore 与对应的 vmlinux 一起交给 GDB 分析。课程大纲另列出 crash 工具，但这份手册的具体收尾步骤使用 GDB。

BeaglePlay 实验还展示了板级限制：崩溃后通过 kexec 进入的新内核，可能无法正确重新初始化部分外围设备，因此使用 SD 卡取回 vmcore，不能想当然地依赖网络导出。

**学习产出：**理解“捕获内核启动成功”“转储文件保存成功”“符号匹配并可分析”是三个分别需要验证的环节。[手册第 33 至 34 页](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.pdf#page=33)

## 与你的四个重点方向的对应关系

以下覆盖程度根据官方大纲与实验手册判断，用于安排你的学习和项目范围。

| 方向 | 课程可直接借鉴的部分 | 项目还应补充的内容 |
| --- | --- | --- |
| 内核 panic | Oops 符号化、KGDB、锁检查、kmemleak、kexec 和 kdump | 更多触发机制与故障类型，例如 UAF、越界、soft lockup，以及保存串口现场 |
| OOM | 系统内存观察、用户态泄漏、堆分析、内核泄漏 | 独立设计全局 OOM 与 cgroup OOM，分析内存压力、回收、限制值和被杀进程 |
| 性能分析 | 缓存访问优化、perf、调用栈、火焰图、调度时间线、eBPF | 加入 CPU 限额、锁等待、I/O 延迟、吞吐和尾延迟的完整验证 |
| 网络优化 | 系统资源观测、系统调用、调度与可定制跟踪方法 | 独立设计 iperf3、抓包、丢包与重传、MTU、队列和网卡中断场景 |

**OOM 与网络优化需要专门补课。**在这份大纲与实验手册中，二者没有像 GDB、perf、KGDB 那样形成独立完整实验链。内存泄漏实验可以为 OOM 排查打基础，但不能替代 OOM 机制与现场分析；系统跟踪也不能替代 TCP 和网卡路径的专项训练。[官方大纲](https://bootlin.com/doc/training/debugging/debugging-agenda.pdf) [实验手册](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.pdf)

## 面向故障训练项目的学习安排建议

以下是基于你的项目目标提出的安排，不是 Bootlin 官方课程日程。

1. **系统观测与应用崩溃。**先完成系统状态、链表 GDB、core 和 strace 实验。交付两个场景：应用崩溃，以及应用因外部条件失败。

2. **内存与应用性能。**完成 Valgrind、Massif、PNG 转换与 perf 实验。交付隐藏内存错误、内存增长、缓存访问低效三个场景。

3. **调度与系统跟踪。**完成 CRC 间隔异常、KernelShark 和火焰图练习。交付一个只描述“偶发变慢”的盲测场景。

4. **内核故障分析。**依次完成锁检查、kmemleak、Oops、KGDB 和 kdump。每题都保留匹配的源码、配置、vmlinux、模块和现场日志。

5. **专项扩展。**补充 OOM 和网络题，先固定单根因和触发条件，再考虑随机延迟、参数变化与多故障组合。

每个场景建议保存六类内容：症状描述、触发方法、正常基线、关键证据、参考修复、验收条件。这样既能用于引导学习，也能隐藏答案用于盲测。

迁移到 QEMU 时，先移植用户态案例和不依赖具体设备的内核模块。watchdog 驱动案例、PMU 事件、串口 KGDB 与板级 kdump 流程需要替换或适配；缓存和网卡真实性能应在目标硬件上复核。

## 使用资料时的几个技术细节

- **版本和符号必须对应。**按手册实际使用的分支构建，不要把旧实验镜像与另一版本的源码、vmlinux 或共享库混在一起。

- **架构设置要复核。**BeaglePlay 版本以 ARM64 为目标，但部分命令片段仍出现 ARM 或其他板卡串口写法。应以实际工具链、内核架构和设备节点为准。

- **全系统 perf 采样要确认范围。**手册的附加实验描述为全系统采样，但示例命令未显式写出 -a；实施时应按 perf 版本确认采样范围，不能仅凭小节标题判断。

- **区分 BPF ring buffer 与 perf buffer。**libbpf 实验文字有混称，但列出的 BPF_MAP_TYPE_RINGBUF 和 bpf_ringbuf_output 对应 BPF ring buffer。

- **不要把演示步骤直接当成通用部署脚本。**启动参数、内存预留、串口名、模块地址和存储分区均与实验平台有关。

这些事项来自对应实验片段的交叉核对，可在改造成自动化题库时列入适配检查。[性能与跟踪实验](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.pdf#page=20) [libbpf 实验](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.pdf#page=25) [KGDB 实验](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.pdf#page=31)

## 官方资料入口与署名

- [课程主页](https://bootlin.com/training/debugging/)：课程定位、形式、平台和材料入口。

- [线下详细大纲](https://bootlin.com/doc/training/debugging/debugging-agenda.pdf)：三天课程安排。

- [完整讲义](https://bootlin.com/doc/training/debugging/debugging-slides.pdf)：理论学习配套材料。

- [BeaglePlay 实验手册](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.pdf)：本文主要实验参考。

- [BeaglePlay 实验资料包](https://bootlin.com/doc/training/debugging/debugging-beagleplay-labs.tar.xz)：实验代码与资料入口。

- [STM32MP1 实验手册](https://bootlin.com/doc/training/debugging/debugging-stm32mp1-labs.pdf)：另一平台的实施步骤。

- [STM32MP1 实验资料包](https://bootlin.com/doc/training/debugging/debugging-stm32mp1-labs.tar.xz)：对应平台实验资料。

- [Bootlin 教学材料源码](https://github.com/bootlin/training-materials)：课程材料维护仓库。

- [Bootlin Buildroot 仓库](https://github.com/bootlin/buildroot)：实验系统构建基础。

实验手册原作者为 Bootlin，版权标注为 © 2004–2026 Bootlin，按 [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) 发布。本文对实验部分进行了中文归纳、结构重组和解释，相关改编内容沿用该许可；项目扩展建议为新增内容。官方资料会更新，复现实验时应保存所使用的手册、代码版本和配置。
