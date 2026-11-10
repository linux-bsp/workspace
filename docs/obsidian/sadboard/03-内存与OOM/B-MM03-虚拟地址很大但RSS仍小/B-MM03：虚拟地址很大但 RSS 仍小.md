[[README|首页]] · [[00-实验准备与通用方法/案例索引|案例索引]] · [[00-实验准备与通用方法/工具索引|工具索引]] · [[03-内存与OOM/00-章节导航|章节导航]]

先按现象提出假设并完成练习，再核对定位、内核机制和参考修复。`verify` 验证镜像提供的参考实现。

[[03-内存与OOM/B-MM03-虚拟地址很大但RSS仍小/B-MM03：虚拟地址很大但 RSS 仍小#现象与原理|现象与原理]] · [[03-内存与OOM/B-MM03-虚拟地址很大但RSS仍小/B-MM03：虚拟地址很大但 RSS 仍小#练习任务|练习任务]] · [[03-内存与OOM/B-MM03-虚拟地址很大但RSS仍小/B-MM03：虚拟地址很大但 RSS 仍小#使用工具|使用工具]] · [[03-内存与OOM/B-MM03-虚拟地址很大但RSS仍小/B-MM03：虚拟地址很大但 RSS 仍小#定位方法|定位方法]] · [[03-内存与OOM/B-MM03-虚拟地址很大但RSS仍小/B-MM03：虚拟地址很大但 RSS 仍小#内核流程与汇编|内核流程与汇编]] · [[03-内存与OOM/B-MM03-虚拟地址很大但RSS仍小/B-MM03：虚拟地址很大但 RSS 仍小#修复与验收|修复与验收]]

## 现象与原理

**生产现场与异常现象。** 进程 VIRT 增大几十 MiB，被误判成同量物理内存泄漏。

**原理与容易误判的地方。** 地址空间建立、按需缺页、物理页分配和回收是不同阶段。匿名映射可以先只占虚拟范围；读零页和写入私有页还可能走不同路径，因此只看 VIRT 不足以估算驻留工作集。

## 练习任务

设备端：运行“虚拟地址很大但RSS仍小”故障现场，记录输出中的实际结果目录与异常证据。

```sh
sadboard run memory-residency
```

设备端：执行“虚拟地址很大但RSS仍小”的参考修复验收，核对终端结论及保存的结果契约。

```sh
sadboard verify memory-residency
```

把下方路径替换为上一步打印的实际目录：

设备端：把路径占位符替换为本次实际现场目录，复核该次运行的证据完整性与验收约束。

```sh
sadboard check /srv/sadboard/实际目录
```

本例固定小负载，无额外参数；全部源文件安装在 `/usr/src/sadboard/src/`。实现入口为 [suite-memory.c](https://github.com/linux-bsp/sadboard-external/blob/93c81e82acfdf5d54155d1b9bb750e78645d384f/package/sadboard-labs/src/suite-memory.c)，公共调度器为 [suite.c](https://github.com/linux-bsp/sadboard-external/blob/93c81e82acfdf5d54155d1b9bb750e78645d384f/package/sadboard-labs/src/suite.c)。两版均映射 32 MiB，只触碰 4 MiB 的页，mincore 测得实际驻留。参考版解除未用的 28 MiB 映射，保留同样 4 MiB 数据与 checksum；解释地址空间和 RSS 的差异。

现场内 `memory-residency-{bug,fixed}.out` 保存结构化度量，`.trace` 保存实际事件/资源计数，stderr/core/Valgrind 文件按案例保留。check 同时核对 trace 与摘要以及本例信号/业务契约，不会仅检查一个 passed 字符串。故障被限制在子进程或私有 namespace；run 返回的是取证控制器退出状态，真实异常信号要查看 observed/auxiliary 和 stderr，不能只看最外层 shell 的 `$?`。

**复现条件与故障注入。** 受控进程 mmap 32 MiB 匿名区域，分别不触页、触碰 4 MiB、触碰全部区域，最后 munmap；每一步写阶段标记并暂停一秒便于观察。 操作前记录版本/构建 ID、boot ID、输入、资源上限和超时。取证对象必须是自己的实验进程，设计卡中的 PID 均指该子进程。

**面试/评审追问。** 为什么 calloc、malloc、mmap 的“成功”不能直接证明同量物理 RAM 已可用？ 请提交：候选假设、可证伪实验、原始数据、关键源码分支、修复前后对照和未覆盖边界。只给一个参数调整或一个“修好了”的截图不算完成。

## 使用工具

通用原理、参数和使用边界见工具手册；具体命令与证据判断见本例定位方法。

[[工具手册/sadboard|sadboard]] · [[工具手册/Valgrind|Valgrind]] · [[工具手册/perf|perf]] · [[工具手册/procfs|procfs]] · [[工具手册/cgroup-v2|cgroup-v2]]

## 定位方法

**定位分析流程。** 对齐各阶段的 VmSize、VmRSS、smaps_rollup、minor faults；perf stat -e page-faults,minor-faults 时先确认事件可用。对比映射数和 Anon/Pss。 对照上方工具手册逐项说明命令回答了什么问题；信号/退出码、资源计数、业务完成数和时间轴必须能互相验证。优化前后采用同输入，至少保留一次负例，排除“异常只是没有触发”。

参数查阅：[[工具手册/Valgrind|本方向基础工具参数与边界]]。

## 内核流程与汇编

**内核阅读入口。** [mmap.c](https://github.com/linux-bsp/linux-7.0/blob/master/mm/mmap.c)：do_mmap；[memory.c](https://github.com/linux-bsp/linux-7.0/blob/master/mm/memory.c)：do_anonymous_page、handle_mm_fault。先确认用户态接口或信号，再向对应内核分支追踪；这些是本仓库 Linux 7.0 的源码入口，不是已经采集到的动态调用栈。

## 修复与验收

**修复方案与代价。** 按业务工作集而非仅地址空间做容量规划；预留空间必须明确按需驻留策略，错误路径调用 munmap。

**量化验收与现场恢复。** 能解释每阶段地址空间与 RSS 的差异，解除映射后相关地址范围消失；不能把页缓存变化混入匿名页结论。 最后停止实验进程，释放私有文件、描述符或 namespace；保存证据再清理，不删除系统日志，不影响管理网络。

[[附录A-实验报告/00-章节导航|实验报告与复盘]] · [[00-实验准备与通用方法/01-构建与启动部署#源码与实机证据|匹配源码、固件与实测证据]]

[[03-内存与OOM/B-MM02-malloc返回空指针但并未发生OOM-kill/B-MM02：malloc 返回空指针但并未发生 OOM kill|上一例 B-MM02]] · [[03-内存与OOM/B-MM04-共享内存文件已删除却仍占用页/B-MM04：共享内存文件已删除却仍占用页|下一例 B-MM04]]
