---
title: "status、check 与 reset"
type: "topic"
tags: ["sadboard/topic"]
chapter: "00-实验准备与通用方法"
---

# status、check 与 reset

[[首页]] · [[00-实验准备与通用方法/00-章节导航|章节导航]] · [[案例索引]] · [[工具索引]]


## 0.10 status、check 与 reset

复制入口打印的实际目录替换下面的 RUN：

```sh
SADBOARD_RESULTS=$(sadboard results)
```

```sh
sadboard status ${SADBOARD_RESULTS}/RUN
```

```sh
sadboard check ${SADBOARD_RESULTS}/RUN
```

```sh
sadboard reset ${SADBOARD_RESULTS}/RUN
```

`status` 显示元数据与结束记录；缺结束记录明确显示 incomplete，不报告通过。
`check` 通过私有工具 `check-result` 核对实际输入与证据；不依赖 Python，也不执行记录中的代码。
数值 JSON 必须完整、字段唯一、类型及范围正确，拒绝空文件、重复字段和截断内容。

| 案例 | 具体检查 |
| --- | --- |
| crash | 缺失记录退出 139，core 是本架构 ELF64 ET_CORE，段边界完整且有 CORE/NT_PRSTATUS；正常输入及参考修复输出符合契约 |
| oom | 退出 137，实际限制为 32 MiB、禁用 swap、组终止，oom 和 oom_kill 均为正；参考版完成 64 次、checksum=532480、没有被 OOM 杀死 |
| fd | 实际限制、初始占用、请求/完成数、峰值/最终占用与退出相符；小输入仍检查泄漏，参考版回到初始占用 |
| cpu | 两版参数与记录一致，根据查询序列独立重算 checksum，检查非零墙钟时间 |
| lock | 每线程次数一致、完成总量为两倍次数，墙钟时间符合该版最低等待预算 |
| network | pcap 结构及实验端点的 ICMP/TCP，延迟与 qdisc 一致；verify 还核对基线、100% 丢包和恢复 |

core 检查只是结构与线程 note 的最低要求，具体崩溃信号、地址、线程栈仍需 GDB。
网络自动检查未完整解析 iperf 的嵌套 JSON，传输字节与错误字段须另行核对。
CPU/锁只打印单次时间比值并标记 `performance_verdict=manual`，不设置通用提升倍数。
历史现场应配合其固件的工具与文档读取；旧现场缺少新证据时不会被补成“通过”。
**故障复现检查通过与问题已修复是两个概念**，性能提升仍需读采样及同输入时序数据。

`reset` 只停止该目录所属、本次 boot 的实验 unit，并保留证据；不会重置系统服务、
清除其他日志或删除现场。其他目录、符号链接、伪造的 unit 名会被拒绝。跨启动的现场
可读、可分析，但不会使用旧记录去停止本次启动的进程。
