[[首页]] · [[案例索引]] · [[工具索引]] · [[10-网络与数据通路优化/00-章节导航|章节导航]]

先按现象提出假设并完成练习，再核对定位、内核机制和参考修复。`verify` 验证镜像提供的参考实现。

[[10-网络与数据通路优化/A-N05-MTU与PMTU黑洞造成小包正常、大包卡住/A-N05：MTU／PMTU 黑洞造成小包正常、大包卡住#现象与原理|现象与原理]] · [[10-网络与数据通路优化/A-N05-MTU与PMTU黑洞造成小包正常、大包卡住/A-N05：MTU／PMTU 黑洞造成小包正常、大包卡住#练习任务|练习任务]] · [[10-网络与数据通路优化/A-N05-MTU与PMTU黑洞造成小包正常、大包卡住/A-N05：MTU／PMTU 黑洞造成小包正常、大包卡住#使用工具|使用工具]] · [[10-网络与数据通路优化/A-N05-MTU与PMTU黑洞造成小包正常、大包卡住/A-N05：MTU／PMTU 黑洞造成小包正常、大包卡住#定位方法|定位方法]] · [[10-网络与数据通路优化/A-N05-MTU与PMTU黑洞造成小包正常、大包卡住/A-N05：MTU／PMTU 黑洞造成小包正常、大包卡住#内核流程与汇编|内核流程与汇编]] · [[10-网络与数据通路优化/A-N05-MTU与PMTU黑洞造成小包正常、大包卡住/A-N05：MTU／PMTU 黑洞造成小包正常、大包卡住#修复与验收|修复与验收]]

## 现象与原理

**生产现场与现象。** ping 小包与 TCP 握手正常，上传固件或大块遥测停住，重传不断。

**原理与因果关系。** 路径 MTU 发现依赖正确的大小约束和反馈；丢弃必要 ICMP 可使大数据重复失败。UDP 分片、TCP MSS、PMTU 与 offload 是不同层次，小 ping 正常不能证明全路径适合大包。

## 练习任务

设备端：运行“MTU与PMTU黑洞造成小包正常、大包卡住”故障现场，记录输出中的实际结果目录与异常证据。

```sh
sadboard run net-pmtu
```

设备端：执行“MTU与PMTU黑洞造成小包正常、大包卡住”的参考修复验收，核对终端结论及保存的结果契约。

```sh
sadboard verify net-pmtu
```

把下方路径替换为完成后打印的实际目录：

设备端：把路径占位符替换为本次实际现场目录，复核该次运行的证据完整性与验收约束。

```sh
sadboard check /srv/sadboard/实际目录
```

本例为固定有界负载，无额外参数。源码 [suite-advanced-network.c](https://github.com/linux-bsp/sadboard-external/blob/93c81e82acfdf5d54155d1b9bb750e78645d384f/package/sadboard-labs/src/suite-advanced-network.c)；三个私有 netns 构成真实 IPv4 路由，第一段 MTU1500、路由出口600。故障在本实验源入口丢弃 ICMP，64 B 探测可通而 1400 B DF 数据无返回；参考允许 ICMP，IP_RECVERR 得 EMSGSIZE=90、缓存 PMTU600，再按512 B分块恢复相同1400 B内容。保留 ingress 丢包统计、pcap 和接收端证明。

`net-pmtu-{bug,fixed}.out/.trace` 分别保存摘要与原始事件，字段 observed/auxiliary 的含义以上述本例定义为准。摘要、trace 和完成数必须相符。与正常业务输出不同的故障结果会由本例契约明确识别；不能拿最外层退出0证明没有异常。性能题同时保留 cpu_ns/wall_ns，至少三次再评价时序，不只看资源上界或一次漂亮数字。

**实际复现负载。** 三个私有 netns 构成真实 IPv4 路由，第一段 MTU1500、路由出口600。故障在本实验源入口丢弃 ICMP，64 B 探测可通而 1400 B DF 数据无返回；参考允许 ICMP，IP_RECVERR 得 EMSGSIZE=90、缓存 PMTU600，再按512 B分块恢复相同1400 B内容。保留 ingress 丢包统计、pcap 和接收端证明。

**面试/评审追问。** 为什么 SYN 成功而传大文件失败？MSS 与 MTU 是否总相差固定 40 字节？

## 使用工具

通用原理、参数和使用边界见工具手册；具体命令与证据判断见本例定位方法。

[[工具手册/sadboard|sadboard]] · [[工具手册/iperf3|iperf3]] · [[工具手册/tcpdump|tcpdump]] · [[工具手册/ss|ss]] · [[工具手册/tc|tc]] · [[工具手册/ip|ip]]

## 定位方法

**定位流程与工具。** 限定命名空间抓 ICMP/重传和 TCP MSS，比较多种负载大小；ss -ti 看 pmtu/mss。先确认 tcpdump 抓到的超大包是否 offload 视角。

参数查阅：[[06-网络分析/B-NET01-netem延迟与丢包导致网络变慢或中断/B-NET01：网络延迟丢包与吞吐#定位方法|本方向基础工具参数与边界]]。

## 内核流程与汇编

**内核源码阅读。** [route.c](https://github.com/linux-bsp/linux-7.0/blob/master/net/ipv4/route.c)：PMTU 更新；[tcp_input.c](https://github.com/linux-bsp/linux-7.0/blob/master/net/ipv4/tcp_input.c)：TCP 错误与 MSS/重传关联；[ip_output.c](https://github.com/linux-bsp/linux-7.0/blob/master/net/ipv4/ip_output.c)：IP 输出与分片。从用户接口找到入口，检查配置/标志/失败分支，再画出本题的路径；这些链接不是实机完整调用栈。

## 修复与验收

**修复与工程取舍。** 修复实验路径 MTU/ICMP 策略或端点配置，避免全局强制小 MSS 掩盖真正网络边界。考虑额外协议头，记录吞吐与有效载荷比例。

**量化验收与清理。** 小/大报文都正确到达、无异常持续重传；清除所有私有过滤与 namespace，验证管理连接仍正常。

[[附录A-实验报告/00-章节导航|实验报告与复盘]] · [[00-实验准备与通用方法/01-构建与启动部署#源码与实机证据|匹配源码、固件与实测证据]]

[[10-网络与数据通路优化/A-N04-epoll-ET未读空与单连接独占事件循环/A-N04：epoll ET 未读空与单连接独占事件循环|上一例 A-N04]] · [[10-网络与数据通路优化/A-N06-softirq与NAPI单核瓶颈限制多核吞吐/A-N06：softirq／NAPI 单核瓶颈限制多核吞吐|下一例 A-N06]]
