[[README|首页]] · [[00-实验准备与通用方法/案例索引|案例索引]] · [[00-实验准备与通用方法/工具索引|工具索引]] · [[05-锁与线程调度/00-章节导航|章节导航]]

先按现象提出假设并完成练习，再核对定位、内核机制和参考修复。`verify` 验证镜像提供的参考实现。

[[05-锁与线程调度/B-SYNC03-条件变量丢失唤醒/B-SYNC03：条件变量丢失唤醒#现象与原理|现象与原理]] · [[05-锁与线程调度/B-SYNC03-条件变量丢失唤醒/B-SYNC03：条件变量丢失唤醒#练习任务|练习任务]] · [[05-锁与线程调度/B-SYNC03-条件变量丢失唤醒/B-SYNC03：条件变量丢失唤醒#使用工具|使用工具]] · [[05-锁与线程调度/B-SYNC03-条件变量丢失唤醒/B-SYNC03：条件变量丢失唤醒#定位方法|定位方法]] · [[05-锁与线程调度/B-SYNC03-条件变量丢失唤醒/B-SYNC03：条件变量丢失唤醒#内核流程与汇编|内核流程与汇编]] · [[05-锁与线程调度/B-SYNC03-条件变量丢失唤醒/B-SYNC03：条件变量丢失唤醒#修复与验收|修复与验收]]

## 现象与原理

**生产现场与异常现象。** 工作队列明明有数据，消费者却偶尔睡到超时，重启或再来一个请求才恢复。

**原理与容易误判的地方。** 条件变量不保存事件计数；它配合共享谓词使用。signal 早于 wait、虚假唤醒或多个消费者竞争都要求在循环里重新检查谓词，而不是依赖“收到一次通知就有一条数据”。

## 练习任务

设备端：运行“条件变量丢失唤醒”故障现场，记录输出中的实际结果目录与异常证据。

```sh
sadboard run sync-condvar
```

设备端：执行“条件变量丢失唤醒”的参考修复验收，核对终端结论及保存的结果契约。

```sh
sadboard verify sync-condvar
```

把下方路径替换为上一步打印的实际目录：

设备端：把路径占位符替换为本次实际现场目录，复核该次运行的证据完整性与验收约束。

```sh
sadboard check /srv/sadboard/实际目录
```

本例固定小负载，无额外参数；全部源文件安装在 `/usr/src/sadboard/src/`。实现入口为 [suite-sync.c](https://github.com/linux-bsp/sadboard-external/blob/93c81e82acfdf5d54155d1b9bb750e78645d384f/package/sadboard-labs/src/suite-sync.c)，公共调度器为 [suite.c](https://github.com/linux-bsp/sadboard-external/blob/93c81e82acfdf5d54155d1b9bb750e78645d384f/package/sadboard-labs/src/suite.c)。先 signal 再等待，故障版忽略已经成立的 predicate，实际 timedwait 返回 ETIMEDOUT=110；参考版用 while 检查状态，消费相同值 42。

现场内 `sync-condvar-{bug,fixed}.out` 保存结构化度量，`.trace` 保存实际事件/资源计数，stderr/core/Valgrind 文件按案例保留。check 同时核对 trace 与摘要以及本例信号/业务契约，不会仅检查一个 passed 字符串。故障被限制在子进程或私有 namespace；run 返回的是取证控制器退出状态，真实异常信号要查看 observed/auxiliary 和 stderr，不能只看最外层 shell 的 `$?`。

**复现条件与故障注入。** 控制生产者先修改谓词并 signal，再让故障消费者无条件 wait；用有限 timedwait。参考版把谓词检查、wait 与状态更新置于同一 mutex 协议内。 操作前记录版本/构建 ID、boot ID、输入、资源上限和超时。取证对象必须是自己的实验进程，设计卡中的 PID 均指该子进程。

**面试/评审追问。** 为什么用 if 替代 while 有风险？条件变量和 eventfd/信号量的语义有何不同？ 请提交：候选假设、可证伪实验、原始数据、关键源码分支、修复前后对照和未覆盖边界。只给一个参数调整或一个“修好了”的截图不算完成。

## 使用工具

通用原理、参数和使用边界见工具手册；具体命令与证据判断见本例定位方法。

[[工具手册/sadboard|sadboard]] · [[工具手册/GDB|GDB]] · [[工具手册/strace|strace]] · [[工具手册/ftrace|ftrace]] · [[工具手册/trace-cmd|trace-cmd]]

## 定位方法

**定位分析流程。** 记录谓词、队列长度、wait/signal 顺序；GDB 中查看消费者栈和队列内容，strace 只能证明 futex 行为，不能替代业务谓词分析。 对照上方工具手册逐项说明命令回答了什么问题；信号/退出码、资源计数、业务完成数和时间轴必须能互相验证。优化前后采用同输入，至少保留一次负例，排除“异常只是没有触发”。

参数查阅：[[工具手册/trace-cmd|本方向基础工具参数与边界]]。

## 内核流程与汇编

**内核阅读入口。** [waitwake.c](https://github.com/linux-bsp/linux-7.0/blob/master/kernel/futex/waitwake.c)：futex_wait 的值检查与入队；[syscalls.c](https://github.com/linux-bsp/linux-7.0/blob/master/kernel/futex/syscalls.c)：futex 操作分派。先确认用户态接口或信号，再向对应内核分支追踪；这些是本仓库 Linux 7.0 的源码入口，不是已经采集到的动态调用栈。

## 修复与验收

**修复方案与代价。** while (!predicate) wait；状态变更和通知服从相同的锁协议，超时使用一致的单调时钟并正确退出。

**量化验收与现场恢复。** 通知先到、后到和虚假唤醒情况下都不丢业务；超时与取消后资源没有残留。 最后停止实验进程，释放私有文件、描述符或 namespace；保存证据再清理，不删除系统日志，不影响管理网络。

[[附录A-实验报告/00-章节导航|实验报告与复盘]] · [[00-实验准备与通用方法/01-构建与启动部署#源码与实机证据|匹配源码、固件与实测证据]]

[[05-锁与线程调度/B-SYNC02-ABBA锁顺序造成互相等待/B-SYNC02：ABBA 锁顺序造成互相等待|上一例 B-SYNC02]] · [[05-锁与线程调度/B-SYNC04-分开的检查与更新导致逻辑丢失/B-SYNC04：分开的检查与更新导致逻辑丢失|下一例 B-SYNC04]]
