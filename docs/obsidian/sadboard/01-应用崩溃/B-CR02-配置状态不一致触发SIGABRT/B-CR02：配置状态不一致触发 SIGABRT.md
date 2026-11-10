[[首页]] · [[案例索引]] · [[工具索引]] · [[01-应用崩溃/00-章节导航|章节导航]]

先按现象提出假设并完成练习，再核对定位、内核机制和参考修复。`verify` 验证镜像提供的参考实现。

[[01-应用崩溃/B-CR02-配置状态不一致触发SIGABRT/B-CR02：配置状态不一致触发 SIGABRT#现象与原理|现象与原理]] · [[01-应用崩溃/B-CR02-配置状态不一致触发SIGABRT/B-CR02：配置状态不一致触发 SIGABRT#练习任务|练习任务]] · [[01-应用崩溃/B-CR02-配置状态不一致触发SIGABRT/B-CR02：配置状态不一致触发 SIGABRT#使用工具|使用工具]] · [[01-应用崩溃/B-CR02-配置状态不一致触发SIGABRT/B-CR02：配置状态不一致触发 SIGABRT#定位方法|定位方法]] · [[01-应用崩溃/B-CR02-配置状态不一致触发SIGABRT/B-CR02：配置状态不一致触发 SIGABRT#内核流程与汇编|内核流程与汇编]] · [[01-应用崩溃/B-CR02-配置状态不一致触发SIGABRT/B-CR02：配置状态不一致触发 SIGABRT#修复与验收|修复与验收]]

## 现象与原理

**生产现场与异常现象。** 消费级网关配置热更新或车载服务重新初始化后，进程退出码变为 134；最后的 libc 栈容易掩盖最早的状态不变量失败。

**原理与容易误判的地方。** assert 失败走 libc 的 abort 路径，SIGABRT 默认动作可能产生 core。它是主动拒绝不一致状态，不等于 CPU 访问了非法地址；删除 assert 会把问题推迟成更难定位的错误。应先判断状态由谁、在哪个事务阶段修改。

## 练习任务

设备端：运行“配置状态不一致触发SIGABRT”故障现场，记录输出中的实际结果目录与异常证据。

```sh
sadboard run crash-abort
```

设备端：执行“配置状态不一致触发SIGABRT”的参考修复验收，核对终端结论及保存的结果契约。

```sh
sadboard verify crash-abort
```

把下方路径替换为上一步打印的实际目录：

设备端：把路径占位符替换为本次实际现场目录，复核该次运行的证据完整性与验收约束。

```sh
sadboard check /srv/sadboard/实际目录
```

本例固定小负载，无额外参数；全部源文件安装在 `/usr/src/sadboard/src/`。实现入口为 [suite-fault.c](https://github.com/linux-bsp/sadboard-external/blob/93c81e82acfdf5d54155d1b9bb750e78645d384f/package/sadboard-labs/src/suite-fault.c)，公共调度器为 [suite.c](https://github.com/linux-bsp/sadboard-external/blob/93c81e82acfdf5d54155d1b9bb750e78645d384f/package/sadboard-labs/src/suite.c)。实际子进程触发 SIGABRT=6；参考版对不合法状态返回 2。用 GDB 的 set follow-fork-mode child 跟进 fault_child，定位业务断言。

现场内 `crash-abort-{bug,fixed}.out` 保存结构化度量，`.trace` 保存实际事件/资源计数，stderr/core/Valgrind 文件按案例保留。check 同时核对 trace 与摘要以及本例信号/业务契约，不会仅检查一个 passed 字符串。故障被限制在子进程或私有 namespace；run 返回的是取证控制器退出状态，真实异常信号要查看 observed/auxiliary 和 stderr，不能只看最外层 shell 的 `$?`。

**复现条件与故障注入。** 建立只有两个合法状态的私有服务，故障版先应用新配置再检查旧对象，执行 assert(state == READY)；参考版先完成校验和对象替换。只终止实验子进程，保留有效/无效配置两个输入。 操作前记录版本/构建 ID、boot ID、输入、资源上限和超时。取证对象必须是自己的实验进程，设计卡中的 PID 均指该子进程。

**面试/评审追问。** SIGABRT 与 SIGSEGV 的证据区别是什么？为什么栈顶在 libc 并不证明 libc 有 bug？ 请提交：候选假设、可证伪实验、原始数据、关键源码分支、修复前后对照和未覆盖边界。只给一个参数调整或一个“修好了”的截图不算完成。

## 使用工具

通用原理、参数和使用边界见工具手册；具体命令与证据判断见本例定位方法。

[[工具手册/sadboard|sadboard]] · [[工具手册/GDB|GDB]] · [[工具手册/gdbserver|gdbserver]] · [[工具手册/strace|strace]]

## 定位方法

**定位分析流程。** 用 strace -f -e signal 捕获信号，用 GDB 的 bt full、frame、info args 找到第一个业务帧；对比 stderr 中断言位置、$_siginfo 和配置事务日志。 对照上方工具手册逐项说明命令回答了什么问题；信号/退出码、资源计数、业务完成数和时间轴必须能互相验证。优化前后采用同输入，至少保留一次负例，排除“异常只是没有触发”。

单步时需跟进 `fault_child`，避免只停在取证父进程。创建结果目录、匹配符号、通过 SSH
连接 gdbserver 和跟踪 fork 的完整步骤见 [[工具手册/GDB#跟踪 case-suite 的故障子进程|GDB 子进程调试流程]]。
在断言处停止后，沿第一个业务帧检查配置状态及修改顺序，再与参考修复对照。

## 内核流程与汇编

**内核阅读入口。** [signal.c](https://github.com/linux-bsp/linux-7.0/blob/1c04c52c72b0e67ad4b5deca464ea70bc6ebb718/kernel/signal.c)：get_signal、do_coredump 的调用条件；[coredump.c](https://github.com/linux-bsp/linux-7.0/blob/1c04c52c72b0e67ad4b5deca464ea70bc6ebb718/fs/coredump.c)：do_coredump。先确认用户态接口或信号，再向对应内核分支追踪；这些是本仓库 Linux 7.0 的源码入口，不是已经采集到的动态调用栈。

## 修复与验收

**修复方案与代价。** 把校验、构建新对象、发布指针和销毁旧对象作为完整生命周期；对可恢复的配置错误返回错误码，对破坏状态的不变量保留明确诊断。

**量化验收与现场恢复。** 无效配置被拒绝且旧配置仍可用；有效配置成功生效。保留原始退出 134/core 证明，确认修复没有把错误静默吞掉。 最后停止实验进程，释放私有文件、描述符或 namespace；保存证据再清理，不删除系统日志，不影响管理网络。

[[附录A-实验报告/00-章节导航|实验报告与复盘]] · [[00-实验准备与通用方法/01-构建与启动部署#固定源码与实机证据|匹配源码、固件与实测证据]]

[[01-应用崩溃/B-CR01-缺失记录未判空导致空指针崩溃/B-CR01：缺失记录导致应用崩溃|上一例 B-CR01]] · [[01-应用崩溃/B-CR03-堆越界写延迟破坏邻接对象/B-CR03：堆越界写延迟破坏邻接对象|下一例 B-CR03]]
