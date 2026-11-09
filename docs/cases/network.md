# 案例：隔离链路的延迟、丢包与吞吐分析

## 问题现场与拓扑

难度：中级。接口看起来正常、能连通，但请求明显变慢；另一个现场则全部丢包。
任务是区分链路未通、路由错误、排队延迟、丢包和 TCP 自身行为，找出故障所在的方向。
源码：[run-network](../../sadboard-external/package/sadboard-labs/run-network)。

```text
实验左命名空间                        实验右命名空间
198.18.0.1/30 ── veth（左侧 netem）── 198.18.0.2/30
  ping / iperf3 client / tcpdump          iperf3 server :5207
```

两个端点都在专用 namespace 内，没有默认路由到业务网络。这个测试测量 Linux 网络栈
和故障模型，不代表 CPSW、PHY、交换机、网线或真实板间链路的极限吞吐。
实验不修改主机 namespace 的 eth0、地址、路由或 qdisc。

## 复现与结果文件

```sh
sadboard run network
sadboard verify network
sadboard check /data/sadboard/实际现场目录
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

## 机制：RTT、方向与 TCP

veth 将一侧发送的报文交给另一侧虚拟网卡。netem 排队规则位于左侧出口，在报文离开
该接口时施加延迟或丢弃，不会把整个系统所有流量都延迟。只有左侧加 100 ms 时，
ping 的往返增加量通常接近 100 ms，而不是必然 200 ms；反向也加才近似累加。

TCP 需要连接握手、ACK 和拥塞窗口推进。链路时延增大后，同样的在途窗口可能限制速率，
粗略关系是吞吐受 `窗口 / RTT` 约束；真实结果还受拥塞控制、接收窗口、CPU 和数据量
影响。1 MiB 短流包含握手和慢启动成本，不能直接外推为长连接带宽。
丢包可能引起重传和拥塞窗口变化，但 ping 不丢包不意味着 TCP 从不重传。

以下是**源码整理的关键路径**，省略 TCP/路由的分支；不是实机完整栈：

```text
TCP connect → tcp_v4_connect → 建立控制流与路由
发送数据 → TCP/IP 输出 → __dev_queue_xmit
  qdisc 入队 → netem_enqueue → 等待计划发送时间
  netem_dequeue → veth 发送 → 对端接收 → IP/TCP/ICMP 处理
```

阅读 [tcp_ipv4.c](../../linux/linux-7.0/net/ipv4/tcp_ipv4.c)、
[dev.c](../../linux/linux-7.0/net/core/dev.c)、
[sch_netem.c](../../linux/linux-7.0/net/sched/sch_netem.c)、
[veth.c](../../linux/linux-7.0/drivers/net/veth.c)。重点看 netem 的 enqueue/dequeue、
定时唤醒与丢弃分支。softirq、NAPI、GRO 等路径会随配置及报文类型变化，不能假定每个
报文都有同一条调用栈；本案例不把软件 veth 路径写成物理网卡中断路径。

## 定位流程

1. 先看 network.info，再在指定 namespace 内查看 `ip addr`、`ip route`、链路状态。
2. 对比基线与异常 RTT、丢包。RTT 高且稳定，先查出口排队和对端等待，不立即改 TCP 参数。
3. 查看双向 `tc -s qdisc`，确认实际规则和丢弃计数，定位注入的方向。
4. 使用同样数据量的 iperf3，对比完成时间与接收字节；同时看 ss 的 RTT、重传和窗口。
5. 通过 pcap 确认握手、ICMP 请求/应答、TCP 序列号与 ACK 的关系。
6. 只移除实验规则，再复测；如果没有恢复，原假设就不完整，继续查剩余路径。

假设 network.info 给出的名字为 LEFT 和 IFACE，手工替换它们：

```sh
ip -n LEFT addr
ip -n LEFT route
ip netns exec LEFT tc -s qdisc show dev IFACE
ip netns exec LEFT ss -ti
```

`ip -n` 选择 namespace，`ip netns exec` 让其他工具在该 namespace 内运行。
不要把命令改成 `tc ... dev eth0` 在主 namespace 执行。
netem 参数及模型限制参见 [tc-netem 手册](https://man7.org/linux/man-pages/man8/tc-netem.8.html)。

## iperf3 参数与测量契约

```sh
ip netns exec RIGHT iperf3 -s -1 -p 5207
ip netns exec LEFT iperf3 -c 198.18.0.2 -p 5207 -n 1M -J
```

| 参数 | 含义 |
| --- | --- |
| `-s` / `-c ADDRESS` | 服务端与客户端；两边端口必须一致 |
| `-1` | 服务端处理一次测试后退出，避免留下长期监听进程 |
| `-p 5207` | 本实验端口，位于隔离 namespace 内 |
| `-n 1M` | 按固定字节量测试；与按秒跑的 `-t` 不同 |
| `-J` | 输出 JSON，保留字节量、时间及 error 等原始字段 |
| `-R` | 反向传输，用于检查方向不对称（扩展练习） |
| `-P N` | 多并行流；可以改变总吞吐，不能当作单流问题已解决 |
| `-u -b RATE` | UDP 和发送速率预算，适合独立研究丢包/抖动；不具有 TCP 的可靠重传语义 |

本案例实测命令使用 TCP、固定量、单流。其他选项是扩展练习，不要同时开启所有优化
后只比较一个汇总带宽。参数以设备 `iperf3 --help` 及
[iperf3 官方手册](https://software.es.net/iperf/invoking.html) 为准。

## 嵌入式工具裁剪和资源生命周期

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

## tcpdump 与 ss 的证据解读

脚本用 `tcpdump -U -n -i IFACE -w FILE`：`-U` 及时写包、`-n` 禁用名称解析、
`-i` 指定实验接口、`-w` 保存原始 pcap。完成后可以离线读：

```sh
tcpdump -nn -tttt -r /data/sadboard/RUN/network.pcap
```

`-nn` 同时避免地址和端口名称替换，`-tttt` 显示可读时间戳，`-r` 读文件而非实时抓包。
同一侧抓包时间与 netem 出队/对端接收时刻不等价，不能仅凭本地两个包的间隔就认定
线路传播延迟。需要定位单向时延时，应两端抓包并确认时钟误差。
GSO/GRO 与校验和卸载可能影响看到的分段和校验和，不能直接把抓到的“大包”判为协议违规。

`ss -ti` 中 RTT、rttvar、cwnd、retrans 等属于 TCP 状态观察值，不是全链路根因结论。
若短流已结束，快照为空是可能的；pcap 和完整 iperf JSON 仍应保留。

## 修复、复位与练习

参考修复删除本实验的 netem，恢复同网段连通性；校验传输字节未减少，RTT 回落，
完全丢包阶段出现 100% loss，结束后两个 namespace 和 veth 均已清理。
`sadboard reset RUN` 停止本实验并删除按该 RUN 命名的残留 namespace，保留证据。

练习：比较 50/100 ms、单向/双向延迟、固定丢包/随机丢包；解释为何随机丢包要多次
重复而 100% 丢包适合做确定性验收。再分析如何把此流程迁移到真实 AM625 网口，
分别检查协商速率、MTU、驱动计数、IRQ/CPU 和交换机，但先保留可恢复的管理链路。

## 证据验收与分级练习

`check` 检查 pcap 文件头、完整包记录和实验 IP 对的 ICMP/TCP；只保存空文件头、
截断包体或无关流量不能通过。延迟要与 qdisc 和 RTT 一致，verify 还检查基线、
100% 丢包及恢复后的 5/5 回复。它不完整解析 iperf JSON，仍需手动核对 error、
sum_sent/sum_received 字节及耗时，不能把非空 JSON 当作成功传输。
任务见 [练习册](../workbook.md#5-接口正常但请求延迟高)，用
[报告模板](../lab-report-template.md) 关联命令所在 namespace 与抓包点。
