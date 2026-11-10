[[首页]] · [[案例索引]] · [[工具索引]] · [[03-内存与OOM/00-章节导航|章节导航]]

先按现象提出假设并完成练习，再核对定位、内核机制和参考修复。`verify` 验证镜像提供的参考实现。

[[03-内存与OOM/B-MM05-外部SIGKILL被误判成cgroup-OOM/B-MM05：外部 SIGKILL 被误判成 cgroup OOM#现象与原理|现象与原理]] · [[03-内存与OOM/B-MM05-外部SIGKILL被误判成cgroup-OOM/B-MM05：外部 SIGKILL 被误判成 cgroup OOM#练习任务|练习任务]] · [[03-内存与OOM/B-MM05-外部SIGKILL被误判成cgroup-OOM/B-MM05：外部 SIGKILL 被误判成 cgroup OOM#使用工具|使用工具]] · [[03-内存与OOM/B-MM05-外部SIGKILL被误判成cgroup-OOM/B-MM05：外部 SIGKILL 被误判成 cgroup OOM#定位方法|定位方法]] · [[03-内存与OOM/B-MM05-外部SIGKILL被误判成cgroup-OOM/B-MM05：外部 SIGKILL 被误判成 cgroup OOM#内核流程与汇编|内核流程与汇编]] · [[03-内存与OOM/B-MM05-外部SIGKILL被误判成cgroup-OOM/B-MM05：外部 SIGKILL 被误判成 cgroup OOM#修复与验收|修复与验收]]

## 现象与原理

**生产现场与异常现象。** 服务退出 137，监控系统直接标注 OOM，实际是超时监督器发出的强制终止。

**原理与容易误判的地方。** 退出码 137 常表示进程被 SIGKILL，但信号来源可能是 OOM、操作员、systemd 超时或其他监督器。只有把信号、cgroup 事件、服务 Result 和内核日志结合才能归因。

## 练习任务

设备端：运行“外部SIGKILL被误判成cgroup-OOM”故障现场，记录输出中的实际结果目录与异常证据。

```sh
sadboard run memory-sigkill
```

设备端：执行“外部SIGKILL被误判成cgroup-OOM”的参考修复验收，核对终端结论及保存的结果契约。

```sh
sadboard verify memory-sigkill
```

把下方路径替换为上一步打印的实际目录：

设备端：把路径占位符替换为本次实际现场目录，复核该次运行的证据完整性与验收约束。

```sh
sadboard check /srv/sadboard/实际目录
```

本例固定小负载，无额外参数；全部源文件安装在 `/usr/src/sadboard/src/`。实现入口为 [suite-memory.c](https://github.com/linux-bsp/sadboard-external/blob/93c81e82acfdf5d54155d1b9bb750e78645d384f/package/sadboard-labs/src/suite-memory.c)，公共调度器为 [suite.c](https://github.com/linux-bsp/sadboard-external/blob/93c81e82acfdf5d54155d1b9bb750e78645d384f/package/sadboard-labs/src/suite.c)。故障版由父进程明确发送 SIGKILL=9，并保存 kill/wait 证据；参考版通过管道请求受控退出。它用于练习归因，不能仅凭退出 137 认定 OOM。

现场内 `memory-sigkill-{bug,fixed}.out` 保存结构化度量，`.trace` 保存实际事件/资源计数，stderr/core/Valgrind 文件按案例保留。check 同时核对 trace 与摘要以及本例信号/业务契约，不会仅检查一个 passed 字符串。故障被限制在子进程或私有 namespace；run 返回的是取证控制器退出状态，真实异常信号要查看 observed/auxiliary 和 stderr，不能只看最外层 shell 的 `$?`。

**复现条件与故障注入。** 用两个受控子实验对照：一个在独立 32 MiB cgroup 内分配触发 OOM，另一个只分配少量内存后由父进程发送 SIGKILL。保留同一套退出码与事件快照。 操作前记录版本/构建 ID、boot ID、输入、资源上限和超时。取证对象必须是自己的实验进程，设计卡中的 PID 均指该子进程。

**面试/评审追问。** 为什么只解析退出码会误报？systemd-oomd 的用户态选杀与内核 OOM 是否一定有相同计数？ 请提交：候选假设、可证伪实验、原始数据、关键源码分支、修复前后对照和未覆盖边界。只给一个参数调整或一个“修好了”的截图不算完成。

## 使用工具

通用原理、参数和使用边界见工具手册；具体命令与证据判断见本例定位方法。

[[工具手册/sadboard|sadboard]] · [[工具手册/Valgrind|Valgrind]] · [[工具手册/procfs|procfs]] · [[工具手册/cgroup-v2|cgroup-v2]]

## 定位方法

**定位分析流程。** 比较 memory.events 的 oom/oom_kill 增量、memory.peak、systemctl show 的 Result/ExecMainStatus 和 dmesg 时间；检查采样前基线，不能拿累积历史事件证明本次 OOM。 对照上方工具手册逐项说明命令回答了什么问题；信号/退出码、资源计数、业务完成数和时间轴必须能互相验证。优化前后采用同输入，至少保留一次负例，排除“异常只是没有触发”。

参数查阅：[[工具手册/Valgrind|本方向基础工具参数与边界]]。

## 内核流程与汇编

**内核阅读入口。** [memcontrol.c](https://github.com/linux-bsp/linux-7.0/blob/1c04c52c72b0e67ad4b5deca464ea70bc6ebb718/mm/memcontrol.c)：mem_cgroup_out_of_memory；[oom_kill.c](https://github.com/linux-bsp/linux-7.0/blob/1c04c52c72b0e67ad4b5deca464ea70bc6ebb718/mm/oom_kill.c)：oom_kill_process；[signal.c](https://github.com/linux-bsp/linux-7.0/blob/1c04c52c72b0e67ad4b5deca464ea70bc6ebb718/kernel/signal.c)：发送与处理信号。先确认用户态接口或信号，再向对应内核分支追踪；这些是本仓库 Linux 7.0 的源码入口，不是已经采集到的动态调用栈。

## 修复与验收

**修复方案与代价。** 让服务退出原因保留结构化证据；将 OOM、超时、人工取消分别记录，并验证报警规则。

**量化验收与现场恢复。** 两个实验均可得到 SIGKILL，但只有真正 OOM 的实验新增相应事件；报警原因和原始证据一一对应。 最后停止实验进程，释放私有文件、描述符或 namespace；保存证据再清理，不删除系统日志，不影响管理网络。

[[附录A-实验报告/00-章节导航|实验报告与复盘]] · [[00-实验准备与通用方法/01-构建与启动部署#固定源码与实机证据|匹配源码、固件与实测证据]]

[[03-内存与OOM/B-MM04-共享内存文件已删除却仍占用页/B-MM04：共享内存文件已删除却仍占用页|上一例 B-MM04]]
