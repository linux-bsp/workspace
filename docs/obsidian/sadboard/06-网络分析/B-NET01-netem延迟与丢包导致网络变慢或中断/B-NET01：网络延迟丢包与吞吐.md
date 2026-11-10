[[README|首页]] · [[00-实验准备与通用方法/案例索引|案例索引]] · [[00-实验准备与通用方法/工具索引|工具索引]] · [[06-网络分析/00-章节导航|章节导航]]

先按现象提出假设并完成练习，再核对定位、内核机制和参考修复。`verify` 验证镜像提供的参考实现。

[[06-网络分析/B-NET01-netem延迟与丢包导致网络变慢或中断/B-NET01：网络延迟丢包与吞吐#现象与原理|现象与原理]] · [[06-网络分析/B-NET01-netem延迟与丢包导致网络变慢或中断/B-NET01：网络延迟丢包与吞吐#练习任务|练习任务]] · [[06-网络分析/B-NET01-netem延迟与丢包导致网络变慢或中断/B-NET01：网络延迟丢包与吞吐#使用工具|使用工具]] · [[06-网络分析/B-NET01-netem延迟与丢包导致网络变慢或中断/B-NET01：网络延迟丢包与吞吐#定位方法|定位方法]] · [[06-网络分析/B-NET01-netem延迟与丢包导致网络变慢或中断/B-NET01：网络延迟丢包与吞吐#内核流程与汇编|内核流程与汇编]] · [[06-网络分析/B-NET01-netem延迟与丢包导致网络变慢或中断/B-NET01：网络延迟丢包与吞吐#修复与验收|修复与验收]] · [[06-网络分析/B-NET01-netem延迟与丢包导致网络变慢或中断/B-NET01：网络延迟丢包与吞吐#实机证据与反例|实机证据与反例]]

## 现象与原理

### 6.1 问题现场与拓扑

难度：中级。接口看起来正常、能连通，但请求明显变慢；另一个现场则全部丢包。
任务是区分链路未通、路由错误、排队延迟、丢包和 TCP 自身行为，找出故障所在的方向。
源码：[run-network](https://github.com/linux-bsp/sadboard-external/blob/93c81e82acfdf5d54155d1b9bb750e78645d384f/package/sadboard-labs/run-network)。

实验拓扑示意：确认左右网络命名空间、veth、netem 方向与 iperf3 服务端位置。

```text
实验左命名空间                        实验右命名空间
198.18.0.1/30 ── veth（左侧 netem）── 198.18.0.2/30
  ping / iperf3 client / tcpdump          iperf3 server :5207
```

两个端点都在专用 namespace 内，没有默认路由到业务网络。这个测试测量 Linux 网络栈
和故障模型，不代表 CPSW、PHY、交换机、网线或真实板间链路的极限吞吐。
实验不修改主机 namespace 的 eth0、地址、路由或 qdisc。

### 6.3 网络基础：连通、时延、吞吐和队列

ping 证明特定 ICMP 探测的往返情况，不证明某 TCP 端口开放、应用处理及时或大流量
吞吐足够。iperf 的测试时长、字节预算、并发数、协议和方向都改变测量含义。
本例固定 1 MiB，比较的首先是同字节传输能否完成及耗时，不能当物理网口极限吞吐。

RTT 是去程和回程的合计；只对一侧出口加 100 ms，通常只让其中一程增加约 100 ms。
qdisc 决定出口排队，tcpdump 的抓包点未必在实际出队之后，所以本机时间戳差值不能
直接等于线上的发送间隔。还要考虑协议处理、调度、拥塞控制和重传。

本项目把 netem 放进专用 namespace，veth 连接两个实验端点，eth0 保持管理通道。
namespace 有独立网络对象，但仍共享同一内核、CPU 和内存，不能用本实验代表独立物理
设备。结束必须回收进程及 namespace 引用；仅杀掉 iperf 并不保证网络对象都消失。

### 6.4 先建立分层模型：哪里正常，哪里仍未知

一次 TCP 请求大致涉及本地应用、socket、路由、邻居解析、出口队列、链路、对端协议
和对端应用。接口 UP 只能说明某一层状态；有 IP 不保证路由正确，路由正确不保证对端
端口监听，握手成功也不保证业务及时完成。把“网络不通”分成这些可验证的问题，才知道
下一条命令需要在哪个端点和哪个 namespace 执行。

本例两端在同一内核的隔离网络空间：每个空间有自己的接口、地址、路由和协议状态，
但共享物理 CPU/内存。veth 是虚拟配对链路，故这里可以稳定展示队列与协议行为，却不
覆盖 PHY 信号、CPSW DMA、外部交换机端口或网线质量。将来迁移到物理网络要补这些层。

| 问题 | 优先工具 | 观测成功后仍不能排除 |
| --- | --- | --- |
| 接口与地址是否正确？ | ip link / ip addr | 路由、端口、应用异常 |
| 去向与下一跳是什么？ | ip route / 邻居表 | 对端拒绝或丢弃 |
| ICMP 是否往返？ | ping | TCP/UDP 特定端口失败 |
| TCP 是否完成同样字节？ | iperf JSON | 实际业务应用慢 |
| 排队配置与计数？ | tc -s qdisc | 下游其他队列或主机负载 |
| 连接的协议状态？ | ss -ti | 所有历史报文的先后过程 |
| 报文实际经过抓包点？ | tcpdump / pcap | 另一个抓包点上的时刻与状态 |

### 6.5 两个数量关系：RTT 与在途数据

RTT 近似是去程各段延迟、对端处理和回程各段延迟的合计。只对左端出口加 D，通常只有
去程经过该延迟队列；不能因为名称叫“往返”就机械乘二。若 RTT 出乎预测，画出请求
与回复分别经过的接口及 qdisc，检查是否同时对两侧加了规则。

稳态下，为充分利用速率 B 的链路，常需要能容纳约 B×RTT 的在途数据。单位必须统一：
bit/s 与 byte、毫秒与秒不能混用。例如假设 100 Mbit/s、100 ms，乘积约 10 Mbit，
即 1.25 MB；这只是帮助理解的假设值，不是本机 veth 的实测带宽或调参建议。

实际吞吐还受拥塞窗口、接收窗口、拥塞算法、重传、应用发送与 CPU 限制。窗口/RTT
只提供某类约束的直觉，不是任何场景都精确等于它。尤其本例 1 MiB 短流包含建连、
启动与收尾，不能据此直接推算持续业务的长期性能。

### 6.7 机制：RTT、方向与 TCP

veth 将一侧发送的报文交给另一侧虚拟网卡。netem 排队规则位于左侧出口，在报文离开
该接口时施加延迟或丢弃，不会把整个系统所有流量都延迟。只有左侧加 100 ms 时，
ping 的往返增加量通常接近 100 ms，而不是必然 200 ms；反向也加才近似累加。

TCP 需要连接握手、ACK 和拥塞窗口推进。链路时延增大后，同样的在途窗口可能限制速率，
粗略关系是吞吐受 `窗口 / RTT` 约束；真实结果还受拥塞控制、接收窗口、CPU 和数据量
影响。1 MiB 短流包含握手和慢启动成本，不能直接外推为长连接带宽。
丢包可能引起重传和拥塞窗口变化，但 ping 不丢包不意味着 TCP 从不重传。

以下是**源码整理的关键路径**，省略 TCP/路由的分支；不是实机完整栈：

源码流程示意：从 TCP 发送追到出口 qdisc、netem 排队及 veth 对端接收。

```text
TCP connect → tcp_v4_connect → 建立控制流与路由
发送数据 → TCP/IP 输出 → __dev_queue_xmit
  qdisc 入队 → netem_enqueue → 等待计划发送时间
  netem_dequeue → veth 发送 → 对端接收 → IP/TCP/ICMP 处理
```

阅读 [tcp_ipv4.c](https://github.com/linux-bsp/linux-7.0/blob/master/net/ipv4/tcp_ipv4.c)、
[dev.c](https://github.com/linux-bsp/linux-7.0/blob/master/net/core/dev.c)、
[sch_netem.c](https://github.com/linux-bsp/linux-7.0/blob/master/net/sched/sch_netem.c)、
[veth.c](https://github.com/linux-bsp/linux-7.0/blob/master/drivers/net/veth.c)。重点看 netem 的 enqueue/dequeue、
定时唤醒与丢弃分支。softirq、NAPI、GRO 等路径会随配置及报文类型变化，不能假定每个
报文都有同一条调用栈；本案例不把软件 veth 路径写成物理网卡中断路径。

## 练习任务

### 6.2 独立练习任务与分级提示

**现场入口**：`sadboard run network` 或 `sadboard verify network`。

**任务**：确定故障方向，解释单向 100 ms 为何通常增加约 100 ms RTT，而非必然
200 ms。对比 ICMP 连通、TCP 完成字节、qdisc、抓包四类证据。

**必须提交**：network.info、三组 RTT、丢包对照、iperf JSON、pcap、host eth0
地址/路由未改变和 namespace 已清理的证明。

<details><summary>L1 提示：命令在哪个 namespace 中执行</summary>

先确认 network.info 的实际名字，再在该 namespace 内运行 tc/ss。不要在业务 eth0
注入故障。仅一个网卡 up 不能证明 ARP、路由、协议和应用都可用。

</details>
<details><summary>L2 提示：不同工具测量的是不同层</summary>

本地出口抓到报文的时间不一定是 netem 真正出队时间；短 TCP 流还含控制开销。
pcap 文件头非空也可能没有任何业务包，checker 会检查包记录边界和实验端点的 ICMP/TCP。
完整传输字节仍应从 iperf JSON 中核对。

</details>

**L3 对照**：解释“ping 正常、TCP 慢”“单流慢、多流汇总快”“抓包显示大包/校验和异常”
各需要哪些额外证据；指出本机 veth 的结果不能证明物理 PHY 极限吞吐。
参考：[[06-网络分析/00-章节导航|网络案例]]。

## 使用工具

通用原理、参数和使用边界见工具手册；具体命令与证据判断见本例定位方法。

[[工具手册/sadboard|sadboard]] · [[工具手册/iperf3|iperf3]] · [[工具手册/tcpdump|tcpdump]] · [[工具手册/ss|ss]] · [[工具手册/tc|tc]] · [[工具手册/ip|ip]]

## 定位方法

### 6.10 嵌入式工具裁剪和资源生命周期

实机初轮发现 BusyBox 即使 `FEATURE_FANCY_SLEEP/FANCY_PING=y`，在
`CONFIG_FLOAT_DURATION=n` 时仍拒绝 `sleep 0.1`、小数 ping 间隔。不能仅凭命令存在
或 fancy 选项开启就认为完整兼容主机用法。SadBoard 增加独立 BusyBox 片段启用浮点
时间，基础 BSP 保持原配置，并将最终 busybox.config 一并导出到调试符号清单。

另外，非交互 shell 启动的后台任务可能继承忽略 SIGINT；exec 不会把忽略的信号自动
改回默认，所以只对后台抓包进程发送 INT 可能无法结束它。本实现改为 TERM 并 wait，
先让 pcap 正常收尾，再删除 namespace。systemd 回收进程不等于 `ip netns` 的 bind
mount 自动删除；命名 namespace 还需要显式清理，这是 reset 要管理的另一类资源。

namespace 负责网络对象的隔离，cgroup 负责资源预算，二者不互相替代。本案例的
父监督器、业务进程、netns 绑定引用和 veth 是不同的生命周期对象。


### 6.6 复现与结果文件

设备端：将本次 NFS/SD 模式的实际结果根目录保存为当前终端变量，供后续命令复用。

```sh
SADBOARD_RESULTS=$(sadboard results)
```

设备端：运行“netem延迟与丢包导致网络变慢或中断”故障现场，记录输出中的实际结果目录与异常证据。

```sh
sadboard run network
```

设备端：执行“netem延迟与丢包导致网络变慢或中断”的参考修复验收，核对终端结论及保存的结果契约。

```sh
sadboard verify network
```

设备端：把路径占位符替换为本次实际现场目录，复核该次运行的证据完整性与验收约束。

```sh
sadboard check ${SADBOARD_RESULTS}/实际现场目录
```

run 在左侧出口增加 100 ms 延迟，记录 ping、固定 1 MiB TCP 传输、ss 和 pcap，
再留八秒供另一终端观察。verify 依次执行无故障基线、100 ms 延迟、100% 丢包、
删除 qdisc 后恢复连通。每次由独立 unit 限时，最后清理自己的 namespace。

| 文件 | 关注的证据 |
| --- | --- |
| network.info | 本次 namespace 和接口的实际名字，不能照抄另一次的名字 |
| baseline/delayed/restored.ping | 发收数量、丢包比例、min/avg/max RTT |
| baseline/delayed.iperf.json | error、发收字节、耗时、接收速率、重传等 |
| delayed/lost.qdisc | 实际 netem 参数、发送/丢弃计数及 backlog |
| baseline/delayed.sockets | 采样时刻的 TCP 状态、RTT/cwnd 等；短流可能已完成 |
| lost.ping / network.pcap | 完全丢包的对照，以及可离线重放的报文 |

### 6.8 定位流程

1. 先看 network.info，再在指定 namespace 内查看 `ip addr`、`ip route`、链路状态。
2. 对比基线与异常 RTT、丢包。RTT 高且稳定，先查出口排队和对端等待，不立即改 TCP 参数。
3. 查看双向 `tc -s qdisc`，确认实际规则和丢弃计数，定位注入的方向。
4. 使用同样数据量的 iperf3，对比完成时间与接收字节；同时看 ss 的 RTT、重传和窗口。
5. 通过 pcap 确认握手、ICMP 请求/应答、TCP 序列号与 ACK 的关系。
6. 只移除实验规则，再复测；如果没有恢复，原假设就不完整，继续查剩余路径。

假设 network.info 给出的名字为 LEFT 和 IFACE，手工替换它们：

设备端：查看本例 LEFT 命名空间的地址，核对 veth 与实验网段。

```sh
ip -n LEFT addr
```

设备端：查看同一命名空间的路由，核对测试流量走向。

```sh
ip -n LEFT route
```

设备端：替换实际接口名，查看本例 qdisc 的累计排队、丢包与发送统计。

```sh
ip netns exec LEFT tc -s qdisc show dev IFACE
```

设备端：查看本例 TCP 连接的内部状态，结合 RTT、重传和窗口分析。

```sh
ip netns exec LEFT ss -ti
```

`ip -n` 选择 namespace，`ip netns exec` 让其他工具在该 namespace 内运行。
不要把命令改成 `tc ... dev eth0` 在主 namespace 执行。
netem 参数及模型限制参见 [tc-netem 手册](https://man7.org/linux/man-pages/man8/tc-netem.8.html)。

## 内核流程与汇编

### 6.15 内核源码精读与关键分支

读 [sch_netem.c](https://github.com/linux-bsp/linux-7.0/blob/master/net/sched/sch_netem.c) 的入队、计划发送时间和出队，
再回到 [dev.c](https://github.com/linux-bsp/linux-7.0/blob/master/net/core/dev.c) 理解 qdisc 进入发送路径的位置。
抓包点不必等于出队点，不能把本机某接口的时间戳直接当作远端到达时间。

命名 namespace 被 bind mount 引用后，即使测试进程已结束仍可能存在；veth 也可能
随对应 namespace 引用保留。systemd 的 cgroup 回收进程，不能替代删除这些网络对象。
这也是网络案例同时检查 unit、namespace、pcap 与 host eth0 的原因。

### 6.16 详细内核流程：用户发送、出口队列、veth 与对端接收

网络路径需要分成多个阶段：写入 socket、进入协议发送队列、qdisc 排队、驱动发送、
对端协议处理和应用读取。它们可能发生在不同任务或 softirq 上下文，不是一条从应用
一路调用到对端应用再原路返回的同步 C 栈。

#### 6.16.1 从用户字节到 skb

源码流程示意：区分应用写入 socket、TCP 组装 skb 和出口发送阶段。

```text
应用 send/write/sendmsg 等接口（实际入口由本次调用决定）
  → socket 文件/系统调用适配 → sock_sendmsg
  → inet_sendmsg → tcp_sendmsg → tcp_sendmsg_locked
    处理连接状态、发送缓冲、用户数据复制或引用、组装 skb
  → 满足发送条件时，经 TCP 输出/拥塞控制路径
  → tcp_write_xmit / tcp_transmit_skb 等 → IP 输出
  → __dev_queue_xmit
```

这里的 skb 是内核网络包相关的数据结构，可能包含分片引用与分段信息，不要求每次
用户 write 恰好对应一个 skb，更不要求等于一个线上以太网帧。TCP 可以合并、拆分、
重传，GSO/GRO 也改变观测形态。send 成功首先说明相应数据被本地接口接受，不能直接
推出远端应用已经读取全部业务字节。

源码入口：[net/socket.c](https://github.com/linux-bsp/linux-7.0/blob/master/net/socket.c)、
[af_inet.c](https://github.com/linux-bsp/linux-7.0/blob/master/net/ipv4/af_inet.c)、
[tcp.c](https://github.com/linux-bsp/linux-7.0/blob/master/net/ipv4/tcp.c)、
[tcp_output.c](https://github.com/linux-bsp/linux-7.0/blob/master/net/ipv4/tcp_output.c)。发送缓冲不足等条件可能让
调用者等待，因而慢 send 也不一定是物理链路速率不足。

#### 6.16.2 netem 不会让发送线程持有整个链路忙等

| 阶段 | 关键动作 | 与本案例的关系 |
| --- | --- | --- |
| 选择发送路径 | __dev_queue_xmit 根据设备、队列与 qdisc 状态分派 | 部分路径可直接发送，不能假设每次必排队 |
| 注入模型 | netem_enqueue 根据延迟/丢包参数处理 skb | loss 可在此让包被丢弃 |
| 等待发送时刻 | 记录可出队时刻，netem_dequeue 检查条件 | 未到期时先不返回可发送 skb |
| 安排后续运行 | qdisc watchdog 组织到期调度 | 不是用 nanosleep 挂住每个应用请求 |
| 真正下发 | 出队后通过通用发送与 netdev 操作 | 才来到 veth_xmit 等设备路径 |

当前 netem_dequeue 可调用 `qdisc_watchdog_schedule_ns`，其封装最终进入
`qdisc_watchdog_schedule_range_ns`。这些是网络调度设施，和复位整机的硬件 watchdog
不是同一功能，不能仅因名字相同就联系到设备重启。

对本实验的常规发送路径，出口抓包 tap 可在 `dev_queue_xmit_nit` 看到，这个调用位于
接近驱动发送的 xmit 路径。因而包已经在此前的队列中花掉的时间，不必出现在“本地
抓到请求与回复”的差里；ping 从发起操作计时的 RTT 则包含该等待。定位时要查具体
抓包点，不用一对 pcap 时间戳直接替代应用 RTT。

读 [dev.c](https://github.com/linux-bsp/linux-7.0/blob/master/net/core/dev.c) 与
[sch_netem.c](https://github.com/linux-bsp/linux-7.0/blob/master/net/sched/sch_netem.c)，把 enqueue、到期检查、
watchdog、dequeue 和设备 xmit 分开，解释“配置了 100 ms”怎样对应到实际观测。

#### 6.16.3 veth 到接收协议与应用

源码流程示意：沿 veth 转发、接收组织、TCP 处理与应用唤醒理解接收数据通路。

```text
veth_xmit → 找 peer → veth_forward_skb
  → 根据 NAPI/GRO 等状态选择接收组织方式
  → 通用接收/IP 分派（可能后续在 softirq/NAPI 上下文）
  → 对 IPv4 TCP，可经 tcp_v4_rcv → tcp_v4_do_rcv → tcp_rcv_established
    更新序列/ACK、重传和接收队列，按条件唤醒等待者
  → 对端应用随后 recv/read，消费已排队的数据
```

接收侧并非每包都保证经过同一组可见函数，ICMP 请求也不走 TCP 已建立连接处理。
veth 的 use_napi 分支取决于实际接口特性；不要把它的行为直接外推到 AM625 CPSW
物理 DMA/NAPI/IRQ 路径。源码在 [veth.c](https://github.com/linux-bsp/linux-7.0/blob/master/drivers/net/veth.c)、
[tcp_ipv4.c](https://github.com/linux-bsp/linux-7.0/blob/master/net/ipv4/tcp_ipv4.c) 和
[tcp_input.c](https://github.com/linux-bsp/linux-7.0/blob/master/net/ipv4/tcp_input.c)。

TCP 协议收到 ACK、socket 数据可读、应用实际读取完成是不同事件。把 iperf 收发
字节、ss、qdisc 和 pcap 放在这些位置理解，才能解释“本地发送很快，远端完成却慢”。

### 6.17 汇编学习：函数指针、队列回调与异步时间

内核中的 netdev_ops、Qdisc_ops 和协议回调大量使用函数指针。反汇编可能显示 BLR
调用寄存器中的地址，或由编译优化变成某个直接 BL；grep 不到一个直接 `bl netem_enqueue`
不能据此断言它没有运行。静态调用关系、配置选择和动态事件必须分开取证。

同固件 vmlinux 的 netem_dequeue 中，存在这条真实调用：

内核反汇编摘录：识别 netem_dequeue 中安排 qdisc watchdog 到期处理的调用点。

```asm
ffff800080c5a674: 97ffecfd  bl ffff800080c55a68 <qdisc_watchdog_schedule_range_ns>
```

源码中较小封装可以内联，因此机器码的函数名可能比源码调用的外层名字更深。只看这
一行也不能证明某个包等待了 100 ms：还需证明本次走到此分支、参数取自哪次配置，
并把时间点和 RTT/抓包相联系。本教材没有把静态反汇编冒充新的动态网络栈采样。

练习：主机反汇编 veth_xmit 与 netem_dequeue，对照源码找回调、时间比较和错误分支；
再说明如果只得到一段 tcp_v4_rcv 的栈，为什么还不知道包此前排在哪个出口队列。
扩展跟踪先限定本实验 namespace/流量与有限窗口，不在管理 eth0 注入新故障。

## 修复与验收

### 6.12 修复、复位与练习

参考修复删除本实验的 netem，恢复同网段连通性；校验传输字节未减少，RTT 回落，
完全丢包阶段出现 100% loss，结束后两个 namespace 和 veth 均已清理。
`sadboard reset RUN` 停止本实验并删除按该 RUN 命名的残留 namespace，保留证据。

练习：比较 50/100 ms、单向/双向延迟、固定丢包/随机丢包；解释为何随机丢包要多次
重复而 100% 丢包适合做确定性验收。再分析如何把此流程迁移到真实 AM625 网口，
分别检查协商速率、MTU、驱动计数、IRQ/CPU 和交换机，但先保留可恢复的管理链路。

### 6.13 证据验收与分级练习

`check` 检查 pcap 文件头、完整包记录和实验 IP 对的 ICMP/TCP；只保存空文件头、
截断包体或无关流量不能通过。延迟要与 qdisc 和 RTT 一致，verify 还检查基线、
100% 丢包及恢复后的 5/5 回复。它不完整解析 iperf JSON，仍需手动核对 error、
sum_sent/sum_received 字节及耗时，不能把非空 JSON 当作成功传输。
任务见 [[06-网络分析/B-NET01-netem延迟与丢包导致网络变慢或中断/B-NET01：网络延迟丢包与吞吐#6.2 独立练习任务与分级提示|练习册]]，用
[[附录A-实验报告/00-章节导航|报告模板]] 关联命令所在 namespace 与抓包点。

## 实机证据与反例

### 6.14 从输出得出结论的顺序

先核对 JSON 没有 error，再比较发送/接收总字节和结束时间。发送快不等于接收已经
完成，TCP 发送端的缓存接收与对端应用读取也不是同一个事件。保存 sum_sent 与
sum_received，说明自己引用哪个速率口径，不能只截其中最大的数。

再把 ping 的发/收数与 qdisc 参数对应：完全丢包对照应有 3 发 0 收；恢复阶段应回到
5 发 5 收，RTT 接近基线。只有 RTT 回落而 TCP 没有完成时，不能宣布所有问题解决。
最后检查抓包完整且确有本例端点流量，并确认 namespace 清理、管理链路没有被修改。

某个包在本机看见、对端没看见，可以缩小故障范围，但必须保证两边抓包方向、过滤条件、
时间窗和丢包统计可比。抓包工具自己丢包、网卡卸载和时钟不同步，都可能制造表面矛盾。
证据冲突时先校验观测方法，不能选择性删除“不符合预期”的附件。

[[附录A-实验报告/00-章节导航|实验报告与复盘]] · [[00-实验准备与通用方法/01-构建与启动部署#源码与实机证据|匹配源码、固件与实测证据]]

[[06-网络分析/B-NET02-把TCP读取次数当成报文边界/B-NET02：把 TCP 读取次数当成报文边界|下一例 B-NET02]]
