[[README|首页]] · [[00-实验准备与通用方法/案例索引|案例索引]] · [[00-实验准备与通用方法/工具索引|工具索引]] · [[06-网络分析/00-章节导航|章节导航]]

先按现象提出假设并完成练习，再核对定位、内核机制和参考修复。`verify` 验证镜像提供的参考实现。

[[06-网络分析/B-NET05-对端退出时SIGPIPE、EOF和复位处理错误/B-NET05：对端退出时 SIGPIPE、EOF 和复位处理错误#现象与原理|现象与原理]] · [[06-网络分析/B-NET05-对端退出时SIGPIPE、EOF和复位处理错误/B-NET05：对端退出时 SIGPIPE、EOF 和复位处理错误#练习任务|练习任务]] · [[06-网络分析/B-NET05-对端退出时SIGPIPE、EOF和复位处理错误/B-NET05：对端退出时 SIGPIPE、EOF 和复位处理错误#使用工具|使用工具]] · [[06-网络分析/B-NET05-对端退出时SIGPIPE、EOF和复位处理错误/B-NET05：对端退出时 SIGPIPE、EOF 和复位处理错误#定位方法|定位方法]] · [[06-网络分析/B-NET05-对端退出时SIGPIPE、EOF和复位处理错误/B-NET05：对端退出时 SIGPIPE、EOF 和复位处理错误#内核流程与汇编|内核流程与汇编]] · [[06-网络分析/B-NET05-对端退出时SIGPIPE、EOF和复位处理错误/B-NET05：对端退出时 SIGPIPE、EOF 和复位处理错误#修复与验收|修复与验收]]

## 现象与原理

**生产现场与异常现象。** 服务器升级期间设备客户端直接退出，或忙重连而失去原请求的最终状态。

**原理与容易误判的地方。** 正常关闭、复位、临时不可写是不同状态。写已关闭的流可能触发 SIGPIPE；MSG_NOSIGNAL 只抑制信号，不能把失败改成发送成功。

## 练习任务

设备端：运行“对端退出时SIGPIPE、EOF和复位处理错误”故障现场，记录输出中的实际结果目录与异常证据。

```sh
sadboard run net-disconnect
```

设备端：执行“对端退出时SIGPIPE、EOF和复位处理错误”的参考修复验收，核对终端结论及保存的结果契约。

```sh
sadboard verify net-disconnect
```

把下方路径替换为上一步打印的实际目录：

设备端：把路径占位符替换为本次实际现场目录，复核该次运行的证据完整性与验收约束。

```sh
sadboard check /srv/sadboard/实际目录
```

本例固定小负载，无额外参数；全部源文件安装在 `/usr/src/sadboard/src/`。实现入口为 [suite-network.c](https://github.com/linux-bsp/sadboard-external/blob/93c81e82acfdf5d54155d1b9bb750e78645d384f/package/sadboard-labs/src/suite-network.c)，公共调度器为 [suite.c](https://github.com/linux-bsp/sadboard-external/blob/93c81e82acfdf5d54155d1b9bb750e78645d384f/package/sadboard-labs/src/suite.c)。分别观测真实 TCP FIN→EOF、SO_LINGER 复位→ECONNRESET=104，以及独立流写入已关闭端触发 SIGPIPE=13；参考 MSG_NOSIGNAL 返回 EPIPE=32。SIGPIPE 子实验使用 AF_UNIX，避免把 TCP 首次写入时序当作确定事实。

现场内 `net-disconnect-{bug,fixed}.out` 保存结构化度量，`.trace` 保存实际事件/资源计数，stderr/core/Valgrind 文件按案例保留。check 同时核对 trace 与摘要以及本例信号/业务契约，不会仅检查一个 passed 字符串。故障被限制在子进程或私有 namespace；run 返回的是取证控制器退出状态，真实异常信号要查看 observed/auxiliary 和 stderr，不能只看最外层 shell 的 `$?`。

**复现条件与故障注入。** 私有 loopback 连接中分别模拟 FIN 正常关闭和有意 RST，故障客户端忽略返回值；参考版处理 EOF、EPIPE、ECONNRESET 和部分写入，连接数有固定上限。 操作前记录版本/构建 ID、boot ID、输入、资源上限和超时。取证对象必须是自己的实验进程，设计卡中的 PID 均指该子进程。

**面试/评审追问。** 为什么重连成功不能证明上一次写入没有被对端执行？ 请提交：候选假设、可证伪实验、原始数据、关键源码分支、修复前后对照和未覆盖边界。只给一个参数调整或一个“修好了”的截图不算完成。

## 使用工具

通用原理、参数和使用边界见工具手册；具体命令与证据判断见本例定位方法。

[[工具手册/sadboard|sadboard]] · [[工具手册/strace|strace]] · [[工具手册/iperf3|iperf3]] · [[工具手册/tcpdump|tcpdump]] · [[工具手册/ss|ss]] · [[工具手册/tc|tc]] · [[工具手册/ip|ip]]

## 定位方法

**定位分析流程。** strace -f -e signal,sendto,recvfrom,close 记录调用结果；私有接口抓包分辨 FIN/RST，保留应用请求 ID 和重试次数。 对照上方工具手册逐项说明命令回答了什么问题；信号/退出码、资源计数、业务完成数和时间轴必须能互相验证。优化前后采用同输入，至少保留一次负例，排除“异常只是没有触发”。

参数查阅：[[06-网络分析/B-NET01-netem延迟与丢包导致网络变慢或中断/B-NET01：网络延迟丢包与吞吐#定位方法|本方向基础工具参数与边界]]。

## 内核流程与汇编

**内核阅读入口。** [tcp.c](https://github.com/linux-bsp/linux-7.0/blob/master/net/ipv4/tcp.c)：tcp_close、tcp_sendmsg_locked；[tcp_input.c](https://github.com/linux-bsp/linux-7.0/blob/master/net/ipv4/tcp_input.c)：FIN/RST 接收处理；[signal.c](https://github.com/linux-bsp/linux-7.0/blob/master/kernel/signal.c)：信号生成与默认动作。先确认用户态接口或信号，再向对应内核分支追踪；这些是本仓库 Linux 7.0 的源码入口，不是已经采集到的动态调用栈。

## 修复与验收

**修复方案与代价。** 统一连接状态机，限定退避重试，给请求设计去重和结果确认；断线重连不自动保证一次且仅一次执行。

**量化验收与现场恢复。** 三类关闭原因可区分，服务不被意外信号结束，业务重试不重复执行且资源回到基线。 最后停止实验进程，释放私有文件、描述符或 namespace；保存证据再清理，不删除系统日志，不影响管理网络。

[[附录A-实验报告/00-章节导航|实验报告与复盘]] · [[00-实验准备与通用方法/01-构建与启动部署#源码与实机证据|匹配源码、固件与实测证据]]

[[06-网络分析/B-NET04-UDP接收队列溢出而非链路丢包/B-NET04：UDP 接收队列溢出而非链路丢包|上一例 B-NET04]]
