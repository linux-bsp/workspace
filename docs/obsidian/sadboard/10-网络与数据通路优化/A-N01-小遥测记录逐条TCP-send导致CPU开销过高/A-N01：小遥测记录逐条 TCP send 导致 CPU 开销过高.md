[[首页]] · [[案例索引]] · [[工具索引]] · [[10-网络与数据通路优化/00-章节导航|章节导航]]

先按现象提出假设并完成练习，再核对定位、内核机制和参考修复。`verify` 验证镜像提供的参考实现。

[[10-网络与数据通路优化/A-N01-小遥测记录逐条TCP-send导致CPU开销过高/A-N01：小遥测记录逐条 TCP send 导致 CPU 开销过高#现象与原理|现象与原理]] · [[10-网络与数据通路优化/A-N01-小遥测记录逐条TCP-send导致CPU开销过高/A-N01：小遥测记录逐条 TCP send 导致 CPU 开销过高#练习任务|练习任务]] · [[10-网络与数据通路优化/A-N01-小遥测记录逐条TCP-send导致CPU开销过高/A-N01：小遥测记录逐条 TCP send 导致 CPU 开销过高#使用工具|使用工具]] · [[10-网络与数据通路优化/A-N01-小遥测记录逐条TCP-send导致CPU开销过高/A-N01：小遥测记录逐条 TCP send 导致 CPU 开销过高#定位方法|定位方法]] · [[10-网络与数据通路优化/A-N01-小遥测记录逐条TCP-send导致CPU开销过高/A-N01：小遥测记录逐条 TCP send 导致 CPU 开销过高#内核流程与汇编|内核流程与汇编]] · [[10-网络与数据通路优化/A-N01-小遥测记录逐条TCP-send导致CPU开销过高/A-N01：小遥测记录逐条 TCP send 导致 CPU 开销过高#修复与验收|修复与验收]]

## 现象与原理

**生产现场与现象。** 小消息转发服务吞吐达不到预期，链路利用率低，CPU 却偏高；增加 SO_SNDBUF 不一定有效。

**原理与因果关系。** 应用记录、系统调用、TCP segment、线上的包不是同一单位。批处理减少应用调用与复制/锁边界开销；GSO/TSO、Nagle 和调度仍可能改变实际分段。不能把 send 次数当作报文数。

## 练习任务

**受控复现设计。** tcp 在自有 netns loopback 上发送 8192 个 64 B 记录。故障版每条 send，参考版每批 64 条；两版均 TCP_NODELAY，接收端校验每字节和序号并处理任意短读。

**面试/评审追问。** 一个 send 是否对应一个 recv？TCP_NODELAY 为什么不等于每条业务消息一定是一个以太网包？

## 使用工具

通用原理、参数和使用边界见工具手册；具体命令与证据判断见本例定位方法。

[[工具手册/sadboard|sadboard]] · [[工具手册/strace|strace]] · [[工具手册/iperf3|iperf3]] · [[工具手册/tcpdump|tcpdump]] · [[工具手册/ss|ss]] · [[工具手册/tc|tc]] · [[工具手册/ip|ip]]

## 定位方法

**定位流程与工具。** strace -f -c 统计 sendto/recvfrom；CPU ns/字节、wall、send_calls 与 checksum 联合判断。tcpdump 分析分段时注明 loopback 与 offload，不把这个测试冒充真实千兆链路吞吐。

### A-N01 操作、协议与工具

源码：[tcp.c](https://github.com/linux-bsp/sadboard-external/blob/93c81e82acfdf5d54155d1b9bb750e78645d384f/package/sadboard-labs/src/tcp.c)、[run-tcp](https://github.com/linux-bsp/sadboard-external/blob/93c81e82acfdf5d54155d1b9bb750e78645d384f/package/sadboard-labs/run-tcp)。它测的是端点小记录发送路径，不是无线链路，也不模拟当前网卡的全部性能。

设备端：运行“小遥测记录逐条TCP-send导致CPU开销过高”故障现场，记录输出中的实际结果目录与异常证据。

```sh
sadboard run tcp 8192
```

设备端：执行“小遥测记录逐条TCP-send导致CPU开销过高”的参考修复验收，核对终端结论及保存的结果契约。

```sh
sadboard verify tcp 8192
```

设备端：检查 TCP 案例清理后的 namespace 列表，确认没有残留本次的 sb-tcp-* 空间。

```sh
ip netns list  # 完成后不应残留本次的 sb-tcp-*；不要删除其他人创建的空间
```

参数为 64～32768 条，每条 64 B。头 4 B 用网络字节序存序号，其余 60 B 由序号生成确定内容。默认有效业务数据为 `8192*64=524288 B`；最大 2 MiB。两版都建立真实 AF_INET/SOCK_STREAM 连接并设置 TCP_NODELAY，故障版每条一次 send，参考版最多把 64 条拼成 4096 B 再发送。监听使用 loopback 自动选择空闲端口，避免冲突；发送/接收设置短超时，入口有外层运行预算。

| 输出字段 | 学习重点 |
| --- | --- |
| `records/frame_bytes/completed/bytes/checksum` | 完整工作量和内容；接收方按流重组，不能假定 recv 刚好读一个记录 |
| `send_calls` | 实际 send 调用数，包括短写后的重试；通常 bug=记录数，fixed≈ceil(记录数/64) |
| `recv_calls` | 由流到达与调度决定，不能强制与 send_calls 相同 |
| `cpu_ns/wall_ns` | 进程双线程累计 CPU 与整体墙钟，不能把 CPU ns 当吞吐时长 |
| `tcp-interface-before/after.txt` | 私有 loopback 计数的对照；它不是管理 NIC 的线速抓包 |

接收端维护跨 recv 的半帧状态，检查每一帧序号和所有字节。循环必须处理 EINTR、短 send/recv、EOF 与错误；写满一批也不说明接收应用已经处理成功。要学习“业务确认”继续做 A-N03。

需要 strace 时先用较小输入，单独建立自己的命名空间，不能混入管理 eth0：

设备端：将本次 NFS/SD 模式的实际结果根目录保存为当前终端变量，供后续命令复用。

```sh
R=$(sadboard results)
```

设备端：创建本次 tcp 手工取证目录；确认成功后再写入跟踪文件。

```sh
mkdir -p "$R/manual-tcp"
```

设备端：创建本组专用网络命名空间；若名称已存在，先停止并核对归属。

```sh
ip netns add sb-manual-tcp
```

设备端：只启用新建实验命名空间中的 loopback，确认成功后再启动本组 TCP 负载。

```sh
ip -n sb-manual-tcp link set lo up
```

设备端：在私有命名空间中统计参考版系统调用次数，完成后再清理命名空间。

```sh
ip netns exec sb-manual-tcp strace -f -c -o "$R/manual-tcp/calls.txt" \
  /usr/libexec/sadboard/tcp-fixed 1024
```

设备端：删除本组自己创建的网络命名空间，确认没有残留实验进程。

```sh
ip netns del sb-manual-tcp
```

设备端：开放本次手工取证目录的主机读取权限，完成后到 NFS 导出路径查看产物。

```sh
sadboard share "$R/manual-tcp"
```

失败或按 Ctrl-C 后仍需删除**自己创建的** `sb-manual-tcp`，不能运行全局删除。自动入口的 trap/reset 处理自己的 `sb-tcp-结果目录名`。`-f` 跟踪 receiver 线程，`-c` 汇总各调用次数/耗时；在当前 libc 上 `send` 包装通常显示 `sendto`。耗时在 strace 影响下发生变化，不用于宣称优化倍率。

参数查阅：[[06-网络分析/B-NET01-netem延迟与丢包导致网络变慢或中断/B-NET01：网络延迟丢包与吞吐#定位方法|本方向基础工具参数与边界]]。

## 内核流程与汇编

**内核源码阅读。** [socket.c](https://github.com/linux-bsp/linux-7.0/blob/master/net/socket.c)：__sys_sendto → sock_sendmsg；[tcp.c](https://github.com/linux-bsp/linux-7.0/blob/master/net/ipv4/tcp.c)：tcp_sendmsg_locked、tcp_recvmsg_locked；[tcp_output.c](https://github.com/linux-bsp/linux-7.0/blob/master/net/ipv4/tcp_output.c)：TCP 输出分段与发送。从用户接口找到入口，检查配置/标志/失败分支，再画出本题的路径；这些链接不是实机完整调用栈。

### A-N01 内核路径与 ARM64 反汇编

源码流程示意：区分发送调用、TCP 缓冲/分段、接收队列和对端应用读取。

```text
用户 send → libc 包装 → __sys_sendto
  → sock_sendmsg → inet_sendmsg → tcp_sendmsg / tcp_sendmsg_locked
  → 建立/填充发送缓冲 → TCP push / IP 输出 → loopback（本例）
  → TCP 接收队列 → 唤醒等待接收者
用户 recv → __sys_recvfrom → sock_recvmsg → inet_recvmsg → tcp_recvmsg
```

这条箭头省略了协议回调、内联函数和可选分支，不是本例抓到的完整内核栈。完整名字以实际使用的内核源码为准；不要要求 GDB 用户回溯显示上述全部内核函数。读 `tcp_sendmsg_locked` 时区分复制到 skb、等待发送内存、push 和错误返回，读接收函数时解释“已有部分数据就返回”的条件。

在交叉 objdump 的 `main` 中观察两版循环调用 send 的位置与批量计数；ARM64 的 x0 是 fd、x1 是缓冲地址、x2 是字节数、x3 是 flags。GDB 在 send 调用前查看 x2，应能区分典型 64 B 和 4096 B 请求；x0 返回 ssize_t，必须先检查负值，不能当无符号长度。调用包装与内核 `svc` 位置可能位于共享 libc，使用本次 sysroot 解析。

本阶段同一固件 `tcp-fixed` 的发送重试循环实际包含：

参考版发送循环摘录：检查未发送长度、缓冲偏移、MSG_NOSIGNAL 和负返回值分支。

```asm
fa4: sub x2, x19, x27       // 待发批次总字节 - 已发送字节
fa8: add x1, x21, x27       // 缓冲起点 + 已发送偏移
fac: mov w0, w22            // client fd
fb0: mov w3, #0x4000        // MSG_NOSIGNAL
fb4: bl  send@plt
fb8: tbz x0, #63, f90       // ssize_t 非负则检查 0/累加；负值走错误路径
```

结合 f90 的零返回检查与 f94 的偏移累加理解 partial write。这里真实 flags 为 MSG_NOSIGNAL，因此连接异常通过错误返回处理，不依赖让 SIGPIPE 杀死进程；继续做基础 B-NET05 比较默认行为。反汇编不能证明接收完整，仍要检查接收方序号/字节验证。

## 修复与验收

**修复与工程取舍。** 在协议契约内批量写入，保留长度/序号、处理 partial send 和接收重组；生产还需最大批量等待时间与高优先级命令立即 flush。吞吐优化不能无限增加遥控延迟。

**量化验收与清理。** completed/bytes/checksum 完全一致，fixed send_calls 少于 bug；时延和 CPU 收益需要重复实测。结束后自建 namespace 消失，管理 eth0 配置不变。

**优化边界。** loopback 没有真实交换机、100 Mbps PHY、NIC DMA 与链路丢包；它证明批处理和正确重组的机制，不能直接导出 AM625 对外吞吐。生产应同时测控制消息 P99、每批最大等待时间和内存预算。`TCP_NODELAY` 不等于包边界开关；抓包还须考虑 GRO/GSO/TSO 的观察层。

**本阶段实测。** send 次数、逐字节一致性、CPU/墙钟和取消清理的结果见[验收档案](https://github.com/linux-bsp/workspace/blob/cb2b20ab8d17e68f4782dd96efe5a1253b64f035/docs/am625-debug-validation.md#production-cases)。

[[附录A-实验报告/00-章节导航|实验报告与复盘]] · [[00-实验准备与通用方法/01-构建与启动部署#源码与实机证据|匹配源码、固件与实测证据]]

[[10-网络与数据通路优化/A-N02-UDP突发超过接收队列，平均带宽却不高/A-N02：UDP 突发超过接收队列，平均带宽却不高|下一例 A-N02]]
