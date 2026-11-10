[[README|首页]] · [[00-实验准备与通用方法/案例索引|案例索引]] · [[00-实验准备与通用方法/工具索引|工具索引]] · [[04-CPU性能与火焰图/00-章节导航|章节导航]]

先按现象提出假设并完成练习，再核对定位、内核机制和参考修复。`verify` 验证镜像提供的参考实现。

[[04-CPU性能与火焰图/B-CPU02-EAGAIN忙轮询耗尽一个CPU/B-CPU02：EAGAIN 忙轮询耗尽一个 CPU#现象与原理|现象与原理]] · [[04-CPU性能与火焰图/B-CPU02-EAGAIN忙轮询耗尽一个CPU/B-CPU02：EAGAIN 忙轮询耗尽一个 CPU#练习任务|练习任务]] · [[04-CPU性能与火焰图/B-CPU02-EAGAIN忙轮询耗尽一个CPU/B-CPU02：EAGAIN 忙轮询耗尽一个 CPU#使用工具|使用工具]] · [[04-CPU性能与火焰图/B-CPU02-EAGAIN忙轮询耗尽一个CPU/B-CPU02：EAGAIN 忙轮询耗尽一个 CPU#定位方法|定位方法]] · [[04-CPU性能与火焰图/B-CPU02-EAGAIN忙轮询耗尽一个CPU/B-CPU02：EAGAIN 忙轮询耗尽一个 CPU#内核流程与汇编|内核流程与汇编]] · [[04-CPU性能与火焰图/B-CPU02-EAGAIN忙轮询耗尽一个CPU/B-CPU02：EAGAIN 忙轮询耗尽一个 CPU#修复与验收|修复与验收]]

## 现象与原理

**生产现场与异常现象。** 机器人传感器断流或遥测连接空闲时，业务吞吐为零但单核接近满载。

**原理与容易误判的地方。** 非阻塞接口把等待策略交给调用者。不断重试仍会执行系统调用和用户循环；CPU 忙不一定代表做了有价值的计算。固定 sleep 也可能换成过大的响应延迟。

## 练习任务

设备端：运行“EAGAIN忙轮询耗尽一个CPU”故障现场，记录输出中的实际结果目录与异常证据。

```sh
sadboard run cpu-eagain
```

设备端：执行“EAGAIN忙轮询耗尽一个CPU”的参考修复验收，核对终端结论及保存的结果契约。

```sh
sadboard verify cpu-eagain
```

把下方路径替换为上一步打印的实际目录：

设备端：把路径占位符替换为本次实际现场目录，复核该次运行的证据完整性与验收约束。

```sh
sadboard check /srv/sadboard/实际目录
```

本例固定小负载，无额外参数；全部源文件安装在 `/usr/src/sadboard/src/`。实现入口为 [suite-cpu.c](https://github.com/linux-bsp/sadboard-external/blob/93c81e82acfdf5d54155d1b9bb750e78645d384f/package/sadboard-labs/src/suite-cpu.c)，公共调度器为 [suite.c](https://github.com/linux-bsp/sadboard-external/blob/93c81e82acfdf5d54155d1b9bb750e78645d384f/package/sadboard-labs/src/suite.c)。延迟生产者写入相同的 42；故障读者忙读并产生 EAGAIN，参考版 poll 后读取。completed/checksum 相同，observed 是实际 EAGAIN 次数，不用固定耗时断言判优。

现场内 `cpu-eagain-{bug,fixed}.out` 保存结构化度量，`.trace` 保存实际事件/资源计数，stderr/core/Valgrind 文件按案例保留。check 同时核对 trace 与摘要以及本例信号/业务契约，不会仅检查一个 passed 字符串。故障被限制在子进程或私有 namespace；run 返回的是取证控制器退出状态，真实异常信号要查看 observed/auxiliary 和 stderr，不能只看最外层 shell 的 `$?`。

**复现条件与故障注入。** 用非阻塞 socketpair 读取空输入，故障版遇到 EAGAIN 立即重试；参考版在 poll/epoll 等待。每版只运行一秒，禁止作用于管理连接。 操作前记录版本/构建 ID、boot ID、输入、资源上限和超时。取证对象必须是自己的实验进程，设计卡中的 PID 均指该子进程。

**面试/评审追问。** EAGAIN 与 EOF 如何区别？为什么降低 CPU 占用不一定意味着响应性能更好？ 请提交：候选假设、可证伪实验、原始数据、关键源码分支、修复前后对照和未覆盖边界。只给一个参数调整或一个“修好了”的截图不算完成。

## 使用工具

通用原理、参数和使用边界见工具手册；具体命令与证据判断见本例定位方法。

[[工具手册/sadboard|sadboard]] · [[工具手册/strace|strace]] · [[工具手册/perf|perf]] · [[工具手册/火焰图|火焰图]]

## 定位方法

**定位分析流程。** perf stat 看 task-clock 与工作量，strace -c 看 EAGAIN 与调用次数，perf report 区分业务函数和系统调用开销；给输入后测唤醒延迟。 对照上方工具手册逐项说明命令回答了什么问题；信号/退出码、资源计数、业务完成数和时间轴必须能互相验证。优化前后采用同输入，至少保留一次负例，排除“异常只是没有触发”。

参数查阅：[[工具手册/perf|本方向基础工具参数与边界]]。

## 内核流程与汇编

**内核阅读入口。** [read_write.c](https://github.com/linux-bsp/linux-7.0/blob/master/fs/read_write.c)：read 的系统调用路径；[eventpoll.c](https://github.com/linux-bsp/linux-7.0/blob/master/fs/eventpoll.c)：ep_poll、do_epoll_wait。先确认用户态接口或信号，再向对应内核分支追踪；这些是本仓库 Linux 7.0 的源码入口，不是已经采集到的动态调用栈。

## 修复与验收

**修复方案与代价。** 使用事件等待，并在可读时排空数据到 EAGAIN；保留取消和截止时间。不要仅通过更长 sleep 降低 CPU。

**量化验收与现场恢复。** 空闲 CPU 成本显著下降，输入到达后的处理延迟仍满足预算，业务完成量保持不变。 最后停止实验进程，释放私有文件、描述符或 namespace；保存证据再清理，不删除系统日志，不影响管理网络。

[[附录A-实验报告/00-章节导航|实验报告与复盘]] · [[00-实验准备与通用方法/01-构建与启动部署#源码与实机证据|匹配源码、固件与实测证据]]

[[04-CPU性能与火焰图/B-CPU01-重复线性查找导致CPU热点/B-CPU01：CPU热点与火焰图|上一例 B-CPU01]] · [[04-CPU性能与火焰图/B-CPU03-高频日志格式化与小写入放大开销/B-CPU03：高频日志格式化与小写入放大开销|下一例 B-CPU03]]
