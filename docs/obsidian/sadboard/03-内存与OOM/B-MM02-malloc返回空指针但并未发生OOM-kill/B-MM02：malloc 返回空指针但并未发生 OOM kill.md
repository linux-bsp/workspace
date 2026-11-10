[[README|首页]] · [[00-实验准备与通用方法/案例索引|案例索引]] · [[00-实验准备与通用方法/工具索引|工具索引]] · [[03-内存与OOM/00-章节导航|章节导航]]

先按现象提出假设并完成练习，再核对定位、内核机制和参考修复。`verify` 验证镜像提供的参考实现。

[[03-内存与OOM/B-MM02-malloc返回空指针但并未发生OOM-kill/B-MM02：malloc 返回空指针但并未发生 OOM kill#现象与原理|现象与原理]] · [[03-内存与OOM/B-MM02-malloc返回空指针但并未发生OOM-kill/B-MM02：malloc 返回空指针但并未发生 OOM kill#练习任务|练习任务]] · [[03-内存与OOM/B-MM02-malloc返回空指针但并未发生OOM-kill/B-MM02：malloc 返回空指针但并未发生 OOM kill#使用工具|使用工具]] · [[03-内存与OOM/B-MM02-malloc返回空指针但并未发生OOM-kill/B-MM02：malloc 返回空指针但并未发生 OOM kill#定位方法|定位方法]] · [[03-内存与OOM/B-MM02-malloc返回空指针但并未发生OOM-kill/B-MM02：malloc 返回空指针但并未发生 OOM kill#内核流程与汇编|内核流程与汇编]] · [[03-内存与OOM/B-MM02-malloc返回空指针但并未发生OOM-kill/B-MM02：malloc 返回空指针但并未发生 OOM kill#修复与验收|修复与验收]]

## 现象与原理

**生产现场与异常现象。** 服务打印 Cannot allocate memory，却没有 OOM 日志；工程师误以为内核漏报。

**原理与容易误判的地方。** 分配失败可以由地址空间限制、映射失败或资源策略造成，并不必然触发 OOM killer。malloc 成功与物理页真正驻留也不是同一时刻。

## 练习任务

设备端：运行“malloc返回空指针但并未发生OOM-kill”故障现场，记录输出中的实际结果目录与异常证据。

```sh
sadboard run memory-enomem
```

设备端：执行“malloc返回空指针但并未发生OOM-kill”的参考修复验收，核对终端结论及保存的结果契约。

```sh
sadboard verify memory-enomem
```

把下方路径替换为上一步打印的实际目录：

设备端：把路径占位符替换为本次实际现场目录，复核该次运行的证据完整性与验收约束。

```sh
sadboard check /srv/sadboard/实际目录
```

本例固定小负载，无额外参数；全部源文件安装在 `/usr/src/sadboard/src/`。实现入口为 [suite-memory.c](https://github.com/linux-bsp/sadboard-external/blob/93c81e82acfdf5d54155d1b9bb750e78645d384f/package/sadboard-labs/src/suite-memory.c)，公共调度器为 [suite.c](https://github.com/linux-bsp/sadboard-external/blob/93c81e82acfdf5d54155d1b9bb750e78645d384f/package/sadboard-labs/src/suite.c)。仅子进程设置 16 MiB RLIMIT_AS，再 mmap 64 MiB，实际返回 ENOMEM=12；故障版继续使用空指针产生 SIGSEGV，参考版处理失败。此处没有把 ENOMEM 当作 OOM kill。

现场内 `memory-enomem-{bug,fixed}.out` 保存结构化度量，`.trace` 保存实际事件/资源计数，stderr/core/Valgrind 文件按案例保留。check 同时核对 trace 与摘要以及本例信号/业务契约，不会仅检查一个 passed 字符串。故障被限制在子进程或私有 namespace；run 返回的是取证控制器退出状态，真实异常信号要查看 observed/auxiliary 和 stderr，不能只看最外层 shell 的 `$?`。

**复现条件与故障注入。** 只给子进程设置较小 RLIMIT_AS，再请求超过预算的私有分配；故障版不检查返回值，参考版返回明确 ENOMEM。不要修改整机 overcommit 策略。 操作前记录版本/构建 ID、boot ID、输入、资源上限和超时。取证对象必须是自己的实验进程，设计卡中的 PID 均指该子进程。

**面试/评审追问。** ENOMEM、SIGKILL、OOM 日志分别说明什么？为什么 dmesg 没有 OOM 不能证明分配一定成功？ 请提交：候选假设、可证伪实验、原始数据、关键源码分支、修复前后对照和未覆盖边界。只给一个参数调整或一个“修好了”的截图不算完成。

## 使用工具

通用原理、参数和使用边界见工具手册；具体命令与证据判断见本例定位方法。

[[工具手册/sadboard|sadboard]] · [[工具手册/strace|strace]] · [[工具手册/Valgrind|Valgrind]] · [[工具手册/procfs|procfs]] · [[工具手册/cgroup-v2|cgroup-v2]]

## 定位方法

**定位分析流程。** 保存 limits、进程 maps、strace 中 brk/mmap 的 ENOMEM，以及实验 cgroup 的 memory.events 前后差值。不要把单个错误字符串等同于内核选杀。 对照上方工具手册逐项说明命令回答了什么问题；信号/退出码、资源计数、业务完成数和时间轴必须能互相验证。优化前后采用同输入，至少保留一次负例，排除“异常只是没有触发”。

参数查阅：[[工具手册/Valgrind|本方向基础工具参数与边界]]。

## 内核流程与汇编

**内核阅读入口。** [mmap.c](https://github.com/linux-bsp/linux-7.0/blob/master/mm/mmap.c)：do_mmap、brk；[memory.c](https://github.com/linux-bsp/linux-7.0/blob/master/mm/memory.c)：handle_mm_fault；[oom_kill.c](https://github.com/linux-bsp/linux-7.0/blob/master/mm/oom_kill.c)：out_of_memory。先确认用户态接口或信号，再向对应内核分支追踪；这些是本仓库 Linux 7.0 的源码入口，不是已经采集到的动态调用栈。

## 修复与验收

**修复方案与代价。** 定义分配失败的降级路径和上游输入上限，检查尺寸计算；保证错误不会继续解引用空指针而变成第二个崩溃。

**量化验收与现场恢复。** 失败输入得到明确错误、无 SIGKILL、无新增 oom_kill；正常输入仍完成相同校验和。 最后停止实验进程，释放私有文件、描述符或 namespace；保存证据再清理，不删除系统日志，不影响管理网络。

[[附录A-实验报告/00-章节导航|实验报告与复盘]] · [[00-实验准备与通用方法/01-构建与启动部署#源码与实机证据|匹配源码、固件与实测证据]]

[[03-内存与OOM/B-MM01-分配内存未释放触发cgroup-OOM/B-MM01：内存泄漏与cgroup-OOM|上一例 B-MM01]] · [[03-内存与OOM/B-MM03-虚拟地址很大但RSS仍小/B-MM03：虚拟地址很大但 RSS 仍小|下一例 B-MM03]]
