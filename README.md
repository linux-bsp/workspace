# SadBoard

每块板子都有问题，找到原因是你的任务。

SadBoard 是一个面向嵌入式 Linux 的故障定位与分析练习项目。计划在 QEMU 和实体 Linux 开发板上构造不同难度、不同现象的问题现场，让学习者从现象出发，完成证据收集、问题分类、根因定位、修复和验证。

名字表达的是“一块出了问题、等你修好的开发板”。希望借鉴 SadServers 的故障现场练习形式，围绕嵌入式 Linux 建立可以反复练习的场景库。

## 当前状态

已完成 AM6254 systemd 调试基线和六个手动案例的实机验证：GDB/core、受限 OOM、CPU 热点、锁等待、隔离网络、启动 panic 与恢复取证。支持 SSH、匹配符号、完整现场记录及参考修复。随机题库和通用自动评分尚未实现。学习入口为 [案例学习手册](docs/cases/README.md) 和 [调试工具参数手册](docs/debug-tools.md)，入口与结果管理见 [场景生命周期](docs/scenario-lifecycle.md)。具体进度见 [开发计划](docs/sadboard-development.md) 和 [实机验证记录](docs/am625-debug-validation.md)。

## Workspace 分支与 Buildroot 扩展层

SadBoard 在 [linux-bsp/workspace](https://github.com/linux-bsp/workspace) 的 `SadBoard` 分支中开发，复用已有的 Buildroot、Linux、U-Boot 和 BSP 子模块。原先独立的 BadBoard 仓库不再作为本工作区的开发入口。

- `bsp-base-external/`：板级支持、启动配置、镜像布局和基础软件包，external 名称保持 `LINUX_BSP`。
- `sadboard-external/`：独立的实验层子模块，external 名称为 `SADBOARD`，后续添加故障程序、调试配置和实验 overlay。
- `docs/`：学习资料与参考分析；原 workspace 操作说明保存在 [workspace-guide.md](docs/workspace-guide.md)。

在 workspace 根目录初始化所需的三个子模块：

```bash
git submodule update --init -- buildroot bsp-base-external sadboard-external
```

初始化目标板需要的源码子模块后，可直接使用标准配置：

```bash
cd buildroot
BR2_EXTERNAL="../bsp-base-external ../sadboard-external" \
  make sadboard_am625_debug_defconfig && make all
```

不指定 `O=` 时，产物位于 `buildroot/output/images/`。Buildroot 会记住本输出目录使用的两个 external；后续 `make all` 无需再次指定。默认独立构建工具链，配置输入保存在 Git 中，输出目录由构建生成。

在新克隆的工作区中，先运行 `git submodule update --init --recursive`。`libbmc` 使用 `git@github.com:wanguo99/libbmc.git` 的 `master` 分支。`make list-defconfigs` 可以查看本实验入口。可选工具链、独立输出目录和详细构建步骤见 [环境指南](docs/am625-bootlin-debug-environment.md)。

`sadboard-external` 包含 AM6254 配置生成脚本、Buildroot/内核配置片段、手动实验程序和目标端环境检查脚本，跟踪远端 `main` 分支。workspace 固定所有子模块的具体提交；复现实验时使用固定提交。`git submodule update --remote` 会尝试更新到跟踪分支的新提交。

开发时应先提交并推送子模块改动，再在 workspace 提交更新后的子模块指针。构建输出统一放在 `output/`，不提交生成文件。

## 为什么做这个项目

学习调试工具时，经常能够找到命令说明，却缺少适合动手分析的问题现场。真实故障可能很久才出现一次，也不一定适合反复触发、修改和对照。

SadBoard 希望提供一组可重复练习的现场，帮助学习者回答：

- 面对“程序消失了”“系统卡住了”“网络很慢”，应该先观察什么？
- 如何区分应用错误、内核问题、资源不足、配置错误和外部环境异常？
- 当前证据支持什么判断，还需要什么证据才能排除其他原因？
- 怎样找到根因，并证明修改解决了问题？

核心目标是练习分析过程。每个场景需要有明确的因果关系、可解释的证据和修复验收条件。

## 重点学习方向

| 方向 | 拟覆盖的问题 | 计划练习的工具与方法 |
| --- | --- | --- |
| 内核故障 | Oops、panic、内存访问错误、锁错误、卡死 | 串口日志、GDB、KGDB、符号化、kdump、crash、KASAN、lockdep |
| 内存与 OOM | 用户态和内核泄漏、内存压力、全局 OOM、cgroup OOM | procfs、内存统计、Valgrind、Massif、kmemleak、OOM 日志 |
| 性能分析 | CPU 热点、忙循环、缓存访问低效、锁竞争、调度延迟、I/O 阻塞 | perf、火焰图、strace、ftrace、trace-cmd、KernelShark、eBPF |
| 网络优化 | 吞吐不足、延迟抖动、丢包、重传、接收端处理慢 | iperf3、ss、tcpdump、tc netem、系统负载与调度分析 |
| 用户态调试 | 崩溃、越界、未初始化内存、死锁、文件描述符泄漏 | GDB、gdbserver、core dump、strace、ltrace、Valgrind |

工具按具体场景选用。比如网络吞吐低，原因也可能在应用锁等待或 CPU 饱和，需要结合多个层次的证据分析。

## 故障现场的构造方式

最初的设想是：运行一个包含若干 bug 的程序，允许指定要学习的 bug，也允许随机选择 bug 数量和触发时间。

为了覆盖用户态、内核和网络问题，计划用统一入口管理三类场景：

- **用户态故障程序**：包含泄漏、越界、忙循环、锁等待、低效算法等可控缺陷。
- **内核实验模块与故障注入**：构造内核错误路径、锁问题、内存错误和崩溃现场。
- **系统与网络环境配置**：通过资源限制、背景负载、延迟或丢包等条件制造异常。

故障来源也包括配置和环境问题。学习者需要根据现场判断问题发生在哪一层。

## 练习模式

| 模式 | 提供的信息 | 训练目的 |
| --- | --- | --- |
| 引导模式 | 指定故障类别，提供分级提示和参考分析 | 学习工具与基本排查方法 |
| 盲测模式 | 只给出可见现象，隐藏根因 | 练习判断方向、选择工具和建立证据链 |
| 综合模式 | 组合多个经过验证的故障，可能存在因果关系 | 练习复杂现场的拆解与修复顺序 |

指定场景适合专项学习；随机抽题适合复习和自测。难度可以通过线索多少、触发条件、干扰负载、涉及层次和故障组合来调整。

## 随机性与可复现性

计划先建立稳定的单故障场景，再引入随机参数、触发时间和故障组合。

- 保存场景版本、随机种子、参数、负载和触发记录，便于再次分析同一组条件。
- 固定随机种子用于重现抽题和参数选择；多线程竞态还需要单独设计可控的触发机制。
- 为故障组合建立兼容性规则，避免一个故障提前终止程序或系统，遮蔽其他问题。
- 提供复位机制，让学习者可以回到相同起点，比较修复前后的表现。

题库也应包含“同一现象、不同根因”的练习。例如服务消失可能是进程崩溃，也可能是 OOM；响应变慢可能来自计算热点、锁等待或网络异常。

## 每个场景应包含什么

1. **现场描述**：从使用者角度描述异常现象，按模式决定是否公开故障类别。
2. **环境要求**：架构、内核版本、配置、工具、内存和设备条件。
3. **正常基线与触发方式**：说明正常表现，以及如何产生负载或触发异常。
4. **分级提示**：从观察方向逐步引导到工具和关键证据。
5. **参考分析**：解释因果链，说明如何排除其他可能原因。
6. **修复与验收**：提供参考修复，并在相同工作负载下验证功能和指标。
7. **复位与现场保存**：保留日志、core、vmcore、采样数据或抓包，支持重复练习。

性能和网络题需要定义吞吐、延迟、错误率等验收指标，防止仅因减少实际工作量而看似“优化成功”。验收应允许合理的不同修复方案。

## 首批候选场景

首个应用崩溃案例已完成实机闭环，其余按开发计划逐项推进。表中方向不代表全部已实现。

| 可见现象 | 候选根因 | 预期练习 |
| --- | --- | --- |
| 程序启动或处理特定输入后崩溃 | 链表操作错误或非法内存访问 | GDB 在线调试与 core 分析 |
| 服务运行一段时间后被终止 | 持续内存增长触发 OOM | 内存趋势、OOM 日志与分配来源分析 |
| CPU 很高但吞吐很低 | 忙循环或低效算法 | perf 热点、调用栈和火焰图 |
| CPU 不高但请求很慢 | 锁等待或 I/O 阻塞 | 线程栈、系统调用与等待分析 |
| 周期任务偶发延迟 | 背景负载造成调度干扰 | ftrace 与调度时间线 |
| 网络吞吐下降 | 丢包或接收端处理能力不足 | iperf3、抓包与系统资源联合分析 |
| 内核出现 Oops | 实验模块中的错误内存访问 | 日志解码、源码定位与 KGDB |
| 系统崩溃后需要离线分析 | 已知内核故障触发 panic | kdump 现场保存与转储分析 |

## 运行平台与实施顺序

先复用现有 Buildroot 与 BSP 工作区，在已有 TI AM6254、i.MX6ULL 开发板环境上逐步接入实验配置，优先选定一块板完成少量场景的完整流程。QEMU 作为后续便于复现和分发的运行平台，具体架构与配置尚待实现。

QEMU 计划用于验证分析流程、逻辑故障和场景复现。依赖真实 PMU、缓存、DMA、网卡中断或实际吞吐的实验，需要单独适配并在对应硬件上验证。

拟定实施顺序：

1. 准备可启动、可调试、可恢复的实验环境。
2. 完成约 6～8 个单根因场景，覆盖用户态、内存、性能、网络和内核问题。
3. 打通“启动现场 → 排查 → 修复 → 验证 → 复位”的流程。
4. 增加统一入口、场景描述格式、分级提示和结果检查。
5. 加入随机抽题、参数变化及兼容的多故障组合。
6. 补充 QEMU 适配，扩展板级性能和设备相关问题。

## 参考项目与学习资料

- [SadServers](https://sadservers.com/)：参考故障现场、提示和结果检查的练习形式。
- [Bootlin Linux 调试课程](https://bootlin.com/training/debugging/)：参考嵌入式调试知识体系与实验组织。
- [Linux Kernel Labs](https://linux-kernel-labs.github.io/refs/heads/master/)：补充内核与驱动学习。
- [LKDTM](https://docs.kernel.org/fault-injection/provoke-crashes.html) 与 [Linux Fault Injection](https://docs.kernel.org/fault-injection/fault-injection.html)：候选内核故障构造组件。
- [stress-ng](https://github.com/ColinIanKing/stress-ng)：候选背景负载工具。
- [tc netem](https://man7.org/linux/man-pages/man8/tc-netem.8.html)：候选网络异常模拟工具。

这些项目是参考资料或候选组件，当前仓库尚未集成。

## 文档

- [Workspace 目录与 AM62x SDK](docs/workspace-toolchain.md)：独立 SDK 配置、原生 `make sdk`、手动解压重定位和共享工具链。

- [AM6254 快速上手](docs/am625-quickstart.md)：使用已有镜像、NFS/TFTP 启动、环境检查和第一个 GDB 实验。

- [AM6254 Bootlin 调试环境](docs/am625-bootlin-debug-environment.md)：配置生成、构建、NFS 启动与实验验证。

- [Bootlin Linux 调试课程详解与实验学习指南](docs/bootlin-linux-debugging-guide.md)：课程主题、官方实验、资料链接，以及与 SadBoard 目标的对应关系。

## 仓库

项目名称为 **SadBoard**，开发仓库为 [linux-bsp/workspace](https://github.com/linux-bsp/workspace)，开发分支为 `SadBoard`。实验层仓库为 [linux-bsp/sadboard-external](https://github.com/linux-bsp/sadboard-external)。

## 资料署名

课程文档中对 Bootlin 实验手册的归纳和改编沿用 CC BY-SA 3.0，具体署名与来源见文档末尾。本文的项目设想不代表 Bootlin 官方课程安排。项目代码许可将在开始实现时另行确定。
