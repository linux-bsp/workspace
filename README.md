# SadBoard

每块板子都有问题，找到原因是你的任务。

SadBoard 是一个面向嵌入式 Linux 的故障定位与分析练习项目。当前在真实 AM625 开发板上构造不同难度、不同现象的问题现场，让学习者从现象出发，完成证据收集、问题分类、根因定位、修复和验证。

名字表达的是“一块出了问题、等你修好的开发板”。希望借鉴 SadServers 的故障现场练习形式，围绕嵌入式 Linux 建立可以反复练习的场景库。

## 当前状态

已完成 AM6254 systemd 调试基线，支持 SSH、匹配符号、完整现场记录及参考修复，75 个案例均有实机验收记录。随机题库和通用自动评分尚未实现。学习内容全部在 [Obsidian 手册](obsidian-sadboard/README.md) 中按章节和案例管理，每个案例一篇完整详解；通用工具参数在独立工具手册中维护，案例与工具通过双向链接关联。固件身份与已执行的验证见 [实机验证记录](docs/am625-debug-validation.md)。

案例库现有 **75 例**：35 个基础、24 个进阶、8 个 A64 汇编、8 个内核子系统案例。73 例使用设备命令，2 例由主机串口工具控制真实 AM625 的 RAM 启动；均有实机验收记录，各批验证的固件与范围分别归档。学习顺序与完整入口见[案例索引](obsidian-sadboard/00-实验准备与通用方法/案例索引.md)，根因、取证任务和参考来源保存在各案例详解中。

教材面向有数年 BSP 经验、能阅读源码但尚未系统掌握原理的工程师。原有 59 例逐例补充
硬件/操作系统模型、状态变化、关键源码分支、可证伪的定位思路与递进追问；实际受控负载
和生产扩展目标分别说明。练习方法见[从项目经验建立原理解释](obsidian-sadboard/00-实验准备与通用方法/03-定位流程与工具选择.md)。

补充教材见 [ABI 与数据模型](obsidian-sadboard/附录C-体系结构与补充知识/01-ABI与数据模型.md) 和
[跨架构汇编与调试](obsidian-sadboard/附录C-体系结构与补充知识/02-汇编学习教材/00-学习导航.md)，
覆盖 x86、ARMv7/ARMv8、RV32/RV64，并区分静态编译验证与实机运行范围。

SadBoard 默认使用 **TFTP 加载内核/DTB、NFS 挂载根文件系统**，普通 AM625 BSP 保持 SD A/B 启动。两个独立的 U-Boot 配置项 `CONFIG_AM62X_BOOT_TFTP_KERNEL`、`CONFIG_AM62X_BOOT_NFS_ROOT` 支持四种组合；配置、主机部署和运行时切换见[网络调试启动](obsidian-sadboard/00-实验准备与通用方法/01-构建与启动部署.md)。NFS 下实验结果保存在板端 `/srv/sadboard`，主机可直接读取 `/srv/nfs/sadboard-am625/srv/sadboard`；本地启动仍使用 `/data/sadboard`。`sadboard results` 可查看当前路径。

网络启动由 `bsp-base-external` 公共层提供，使用 `bsp.netboot=1`、`BSPNET1` 和
`/usr/libexec/bsp/boot-context`，普通 BSP 也可独立使用。Windows 接入的远程串口可通过
USB/IP 导入 Debian 后用 tio 操作；连接、权限检查与日志采集见
[环境检查与登录](obsidian-sadboard/00-实验准备与通用方法/02-环境检查、登录与符号准备.md)。

构建后可运行 `sadboard-external/scripts/sync-artifacts.sh output/am625-debug-systemd/images`
同步 NFS 根目录、TFTP 内核/DTB 及实验载荷。脚本按需从仓库外的
`~/.config/.sudo.guo` 读取 sudo 密码；使用 `--check` 只校验产物。完整根目录同步前，
先让板卡使用本地根文件系统或关机。

## Workspace 分支与 Buildroot 扩展层

SadBoard 在 [linux-bsp/workspace](https://github.com/linux-bsp/workspace) 的 `SadBoard` 分支中开发，复用已有的 Buildroot、Linux、U-Boot 和 BSP 子模块。原先独立的 BadBoard 仓库不再作为本工作区的开发入口。

- `bsp-base-external/`：板级支持、启动配置、镜像布局和基础软件包，external 名称保持 `LINUX_BSP`。
- `sadboard-external/`：独立的实验层子模块，external 名称为 `SADBOARD`，包含故障程序、调试配置和实验 overlay。
- `obsidian-sadboard/`：独立的 Obsidian 手册子模块，包含案例、工具手册及文档检查工具。
- `docs/`：实机验收、工具链操作及板级参考资料。

在 workspace 根目录初始化构建配置和手册子模块：

```bash
git submodule update --init -- buildroot bsp-base-external sadboard-external obsidian-sadboard
```

初始化目标板需要的源码子模块后，可直接使用标准配置：

```bash
cd buildroot
BR2_EXTERNAL="../bsp-base-external ../sadboard-external" \
  make sadboard_am625_debug_defconfig && make all
```

不指定 `O=` 时，产物位于 `buildroot/output/images/`。Buildroot 会记住本输出目录使用的两个 external；后续 `make all` 无需再次指定。默认独立构建工具链，配置输入保存在 Git 中，输出目录由构建生成。

构建使用 Buildroot 原生包框架、Kconfig/CMake 和 shell hooks；固件 JSON 由 host 工具生成 ITS/ITB。
设备程序和 Device Manager 均使用 C，自定义生产构建不调用 Python。
主机测试、文档检查、可选串口验收工具及上游 binman 等主机依赖仍可使用 Python。
固件打包职责见 [生成器说明](bsp-base-external/support/firmware/README.md)。

在新克隆的工作区中，先运行 `git submodule update --init --recursive`。`libbmc` 使用 `git@github.com:wanguo99/libbmc.git` 的 `master` 分支。`make list-defconfigs` 可以查看本实验入口。可选工具链、独立输出目录和详细构建步骤见 [环境指南](obsidian-sadboard/附录A-实验实践与构建/00-章节导航.md)。

`sadboard-external` 包含 AM6254 标准 defconfig、内核片段、原生构建 hooks、手动实验程序和目标端环境检查脚本，跟踪远端 `main` 分支。workspace 固定所有子模块的具体提交；复现实验时使用固定提交。`git submodule update --remote` 会尝试更新到跟踪分支的新提交。

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

## 运行平台与后续方向

当前可运行并完成实机验收的平台是 TI AM6254。i.MX6ULL 的硬件资料保留供板级开发参考，SadBoard 尚未提供对应配置。当前案例统一在真实 AM625 上验证。

内核和启动故障实验要求先验证硬件 WDT 与正常恢复路径；PMU、缓存、DMA、网卡中断和吞吐等结论以对应实机证据为准。

现阶段已建立 75 个手动案例及设备/串口入口、取证、参考修复和复位流程。后续可扩展随机抽题、兼容的多故障组合和更多板级问题；这些仍是项目方向，未记作已实现功能。

## 参考项目与学习资料

- [SadServers](https://sadservers.com/)：参考故障现场、提示和结果检查的练习形式。
- [Bootlin Linux 调试课程](https://bootlin.com/training/debugging/)：参考嵌入式调试知识体系与实验组织。
- [Linux Kernel Labs](https://linux-kernel-labs.github.io/refs/heads/master/)：补充内核与驱动学习。
- [LKDTM](https://docs.kernel.org/fault-injection/provoke-crashes.html) 与 [Linux Fault Injection](https://docs.kernel.org/fault-injection/fault-injection.html)：候选内核故障构造组件。
- [stress-ng](https://github.com/ColinIanKing/stress-ng)：背景负载工具。
- [tc netem](https://man7.org/linux/man-pages/man8/tc-netem.8.html)：网络异常模拟工具。

这些链接用于参考方法与上游资料；实际已集成的工具、案例及验证范围以教材和验收档案为准。

## 文档

- [Obsidian 手册入口](obsidian-sadboard/README.md)：打开 `obsidian-sadboard` 仓库，从 `README.md` 进入；第 00 章集中维护案例索引与工具索引，75 个案例各一篇完整笔记，工具手册通过双向链接关联。
- [AM625 实机验收档案](docs/am625-debug-validation.md)：各阶段固件 ID、真实执行结果及附件位置。
- [EDK libbmc 与 SadBoard 专利候选分析](docs/patent-candidate-analysis.md)：候选技术机制、源码依据、现有技术对照及公开时间与权属条件。
- [Workspace 目录与 AM62x SDK](docs/workspace-toolchain.md)：独立 SDK、共享下载缓存与工具链管理。
- [AM625 TFTP 服务](docs/am62x/tftp-server.md)、[电源接线与联调](docs/am62x/power-control.md)：当前开发环境的板级操作参考。
- [固件升级接口](edk/docs/device-manager/fwctl.md)、[设备管理架构](edk/docs/device-manager/architecture.md)：由 EDK 维护，与对应源码一起更新。
- [i.MX6ULL DTS 与硬件验证参考](docs/imx6ull/dts-guide.md)：独立的板级资料，不代表已支持该平台的 SadBoard 案例。

## 仓库

项目名称为 **SadBoard**，开发仓库为 [linux-bsp/workspace](https://github.com/linux-bsp/workspace)，开发分支为 `SadBoard`。实验层仓库为 [linux-bsp/sadboard-external](https://github.com/linux-bsp/sadboard-external)，独立手册仓库为 [linux-bsp/obsidian-sadboard](https://github.com/linux-bsp/obsidian-sadboard)，手册分支为 `master`。

## 资料署名

教材中对 Bootlin 实验手册的归纳和改编沿用 CC BY-SA 3.0，具体署名与来源见 [教材附录 B](obsidian-sadboard/附录B-Bootlin课程参考/00-章节导航.md)。项目设想不代表 Bootlin 官方课程安排，SadBoard 代码许可尚未确定。
