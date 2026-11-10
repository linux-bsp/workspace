[[首页]] · [[案例索引]] · [[工具索引]] · [[03-内存与OOM/00-章节导航|章节导航]]

先按现象提出假设并完成练习，再核对定位、内核机制和参考修复。`verify` 验证镜像提供的参考实现。

[[03-内存与OOM/B-MM04-共享内存文件已删除却仍占用页/B-MM04：共享内存文件已删除却仍占用页#现象与原理|现象与原理]] · [[03-内存与OOM/B-MM04-共享内存文件已删除却仍占用页/B-MM04：共享内存文件已删除却仍占用页#练习任务|练习任务]] · [[03-内存与OOM/B-MM04-共享内存文件已删除却仍占用页/B-MM04：共享内存文件已删除却仍占用页#使用工具|使用工具]] · [[03-内存与OOM/B-MM04-共享内存文件已删除却仍占用页/B-MM04：共享内存文件已删除却仍占用页#定位方法|定位方法]] · [[03-内存与OOM/B-MM04-共享内存文件已删除却仍占用页/B-MM04：共享内存文件已删除却仍占用页#内核流程与汇编|内核流程与汇编]] · [[03-内存与OOM/B-MM04-共享内存文件已删除却仍占用页/B-MM04：共享内存文件已删除却仍占用页#修复与验收|修复与验收]]

## 现象与原理

**生产现场与异常现象。** 采集服务清理了临时文件名，Shmem 却不下降，重启服务后才恢复。

**原理与容易误判的地方。** 目录项、打开文件引用和映射引用分别维持对象生命。unlink 解除名字，不等同于释放仍被进程引用的数据页；memfd 还可能通过 IPC 转移给其他进程。

## 练习任务

设备端：运行“共享内存文件已删除却仍占用页”故障现场，记录输出中的实际结果目录与异常证据。

```sh
sadboard run memory-shmem
```

设备端：执行“共享内存文件已删除却仍占用页”的参考修复验收，核对终端结论及保存的结果契约。

```sh
sadboard verify memory-shmem
```

把下方路径替换为上一步打印的实际目录：

设备端：把路径占位符替换为本次实际现场目录，复核该次运行的证据完整性与验收约束。

```sh
sadboard check /srv/sadboard/实际目录
```

本例固定小负载，无额外参数；全部源文件安装在 `/usr/src/sadboard/src/`。实现入口为 [suite-memory.c](https://github.com/linux-bsp/sadboard-external/blob/93c81e82acfdf5d54155d1b9bb750e78645d384f/package/sadboard-labs/src/suite-memory.c)，公共调度器为 [suite.c](https://github.com/linux-bsp/sadboard-external/blob/93c81e82acfdf5d54155d1b9bb750e78645d384f/package/sadboard-labs/src/suite.c)。在 /dev/shm 创建本进程专属 8 MiB 文件，unlink 名字后通过 fd/mmap 实际持有页；参考版 close+munmap。不会清空全局 /dev/shm，观测后故障版也清理。

现场内 `memory-shmem-{bug,fixed}.out` 保存结构化度量，`.trace` 保存实际事件/资源计数，stderr/core/Valgrind 文件按案例保留。check 同时核对 trace 与摘要以及本例信号/业务契约，不会仅检查一个 passed 字符串。故障被限制在子进程或私有 namespace；run 返回的是取证控制器退出状态，真实异常信号要查看 observed/auxiliary 和 stderr，不能只看最外层 shell 的 `$?`。

**复现条件与故障注入。** 使用受控 memfd 或私有 tmpfs 文件写入 8 MiB，删除名字但保持 fd/映射，再逐步 close 和 munmap。严禁清空全局 /dev/shm。 操作前记录版本/构建 ID、boot ID、输入、资源上限和超时。取证对象必须是自己的实验进程，设计卡中的 PID 均指该子进程。

**面试/评审追问。** SCM_RIGHTS 传递的是路径还是引用？为什么 lsof 看见 deleted 并不意味着内存已释放？ 请提交：候选假设、可证伪实验、原始数据、关键源码分支、修复前后对照和未覆盖边界。只给一个参数调整或一个“修好了”的截图不算完成。

## 使用工具

通用原理、参数和使用边界见工具手册；具体命令与证据判断见本例定位方法。

[[工具手册/sadboard|sadboard]] · [[工具手册/Valgrind|Valgrind]] · [[工具手册/procfs|procfs]] · [[工具手册/cgroup-v2|cgroup-v2]]

## 定位方法

**定位分析流程。** 检查 /proc/PID/fd 中 deleted/memfd 条目与 maps；将 Shmem、cgroup memory.stat 的 shmem/file、业务引用计数关联起来。 对照上方工具手册逐项说明命令回答了什么问题；信号/退出码、资源计数、业务完成数和时间轴必须能互相验证。优化前后采用同输入，至少保留一次负例，排除“异常只是没有触发”。

参数查阅：[[工具手册/Valgrind|本方向基础工具参数与边界]]。

## 内核流程与汇编

**内核阅读入口。** [shmem.c](https://github.com/linux-bsp/linux-7.0/blob/1c04c52c72b0e67ad4b5deca464ea70bc6ebb718/mm/shmem.c)：shmem_get_folio、shmem_file_setup；[file_table.c](https://github.com/linux-bsp/linux-7.0/blob/1c04c52c72b0e67ad4b5deca464ea70bc6ebb718/fs/file_table.c)：文件引用释放。先确认用户态接口或信号，再向对应内核分支追踪；这些是本仓库 Linux 7.0 的源码入口，不是已经采集到的动态调用栈。

## 修复与验收

**修复方案与代价。** 统一共享内存对象的创建、发送、接收、取消和回收协议；文件名删除之外还要关闭全部 fd 并解除全部映射。

**量化验收与现场恢复。** 最后一个受控引用释放后，实验对象消失且对应内存回落；IPC 失败或消费者退出也能完成清理。 最后停止实验进程，释放私有文件、描述符或 namespace；保存证据再清理，不删除系统日志，不影响管理网络。

[[附录A-实验报告/00-章节导航|实验报告与复盘]] · [[00-实验准备与通用方法/01-构建与启动部署#固定源码与实机证据|匹配源码、固件与实测证据]]

[[03-内存与OOM/B-MM03-虚拟地址很大但RSS仍小/B-MM03：虚拟地址很大但 RSS 仍小|上一例 B-MM03]] · [[03-内存与OOM/B-MM05-外部SIGKILL被误判成cgroup-OOM/B-MM05：外部 SIGKILL 被误判成 cgroup OOM|下一例 B-MM05]]
