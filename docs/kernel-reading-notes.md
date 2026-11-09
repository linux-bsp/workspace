# 从案例读内核：关键分支与证据边界

对应 `linux/linux-7.0` 提交 `1c04c52c72b0e67ad4b5deca464ea70bc6ebb718`。
以下为源码阅读笔记，不是把所有函数拼成某次实机的完整调用栈。
先找入口和关键条件，再追辅助函数；不要从一个同名函数推断所有路径相同。

## 缺页异常不等于非法访问

读 [fault.c](../linux/linux-7.0/arch/arm64/mm/fault.c) 的 `do_page_fault`：

1. 识别 EL0/EL1、读/写/取指，决定需要什么 VMA 权限。
2. 根据地址查找有效 VMA；没有 VMA 与权限不符是不同的错误分支。
3. 合法 VMA 进入 `handle_mm_fault`，可能建立页表或处理写时复制，恢复后重试原指令。
4. 无法合法恢复才转入信号或内核异常处置；`VM_FAULT_OOM` 还有自己的处理分支。

再读 [memory.c](../linux/linux-7.0/mm/memory.c) 的 `handle_mm_fault`、
`do_anonymous_page`：合法首次写触可以分配匿名 folio、做 memcg 计费、建立 PTE。
因此“缺页数增加”“malloc 返回地址”“RSS 增加”是不同事件，不能混用。

对照实验：正常内存程序大量写触也会发生缺页，但应继续运行；crash 案例访问无效
记录，内核无法为它建立合法 VMA。用 GDB 的地址、指令和变量证明是哪一类。
SIGSEGV 还需区分 MAPERR/ACCERR，不能把所有访存异常都归为 NULL。

## FD 表、打开对象与资源所有权

从 [open.c](../linux/linux-7.0/fs/open.c) 的 do_sys_openat2 进入
[file.h](../linux/linux-7.0/include/linux/file.h) 的 FD_ADD。当前内核使用组合清理宏：
先取 FD 槽，成功后才求值文件打开表达式，再发布引用；打开失败则由清理规则归还资源。
宏名不一定成为栈帧，不能照搬旧内核中显式展开的源码来伪造当前调用栈。

读 [file.c](../linux/linux-7.0/fs/file.c) 的 alloc_fd：候选编号达到 end 时返回 EMFILE，
end 来自该进程的 RLIMIT_NOFILE。再读 close_fd 如何在锁保护下摘除表项，转入
filp_close 与文件引用释放。最后读 [file_table.c](../linux/linux-7.0/fs/file_table.c)
的 alloc_empty_file、fput、__fput，区分系统对象预算、FD 槽位、最后引用和延后清理。

本例只降低子进程的预算；进程退出回收不等于业务正确释放。将局部变量覆盖与 fdtable
引用生命周期分别画出来，就能解释为什么相同路径重复 open 也会耗尽描述符。
细节及真实 syscall 证据见 [FD 章节](cases/fd-exhaustion.md)。

## memcg 是先回收重试，再决定失败

读 [memcontrol.c](../linux/linux-7.0/mm/memcontrol.c) 的 `try_charge_memcg`：

- 计费是否能通过 page counter，首先决定是否需要慢路径。
- 无法阻塞的分配、特殊 GFP 标志与可回收的普通用户页，走法不同。
- 慢路径尝试组内回收、检查 margin、清空 stock 并重试，不是超过 max 就立即杀进程。
- 允许的重试耗尽后，某些分配可以进入 mem_cgroup_oom；其他路径可能只返回 ENOMEM。
- OOM 锁保证多个竞争者串行检查，取得锁后还会复查余量，不能把函数返回 true 简化成
  “必定新杀了一个进程”。

配合 [oom_kill.c](../linux/linux-7.0/mm/oom_kill.c) 读 victim 选择、组终止与后续回收。
把 `.limits`、oom/max/oom_kill、进程及时间连起来；新 check 要求组 oom 事件和 kill
事件共同存在。即使它通过，泄漏来源仍需分配栈和所有权分析来解释。

## futex 必须防止检查与睡眠之间丢失唤醒

读 [waitwake.c](../linux/linux-7.0/kernel/futex/waitwake.c) 的 `futex_wait_setup`：
先获取关联 key 和 hash bucket 保护，再读取用户态值并核对预期。值已改变时返回
EWOULDBLOCK；应用/libc 重新检查，而不是无条件睡眠。

如果先在用户态检查值、再无保护地排队，唤醒者可能在这两步之间修改值并完成唤醒，
随后等待者才入睡，造成 lost wakeup。关键是正确的状态与队列同步，不是简单的
“加个 sleep 等待对方”。继续读 `futex_do_wait` 与 wake 的队列操作，区分：

| 时刻 | 能观察到什么 | 尚不能推出什么 |
| --- | --- | --- |
| 应用拿不到锁 | libc 栈/源行 | 不一定已经进入内核等待 |
| futex 睡眠 | 系统调用、内核等待点 | 不能只据此确定哪个业务对象有错 |
| sched_wakeup | 变为可运行 | 不代表已经获得 CPU 或 mutex |
| sched_switch 到该线程 | 真正开始运行 | 仍可能需要再次竞争锁 |

锁案例的根因在应用持锁范围。修复应维持临界区数据契约；futex 是协助证明等待机制
的下一层，不是看到它出现就修改调度器。

## perf 的测量路径与业务热点是两条路径

读 [events/core.c](../linux/linux-7.0/kernel/events/core.c) 的 perf_event_open、
perf_event_overflow、perf_output_sample，以及 [ARM PMU](../linux/linux-7.0/drivers/perf/arm_pmuv3.c)。
配置事件、处理中断、展开/保存调用链属于测量机制；被采样的 lookup_linear 属于
业务工作。报告里两者可能同时出现，需要结合 self/children、事件类型和采样上下文。

采样频率、过滤范围、是否含内核、栈展开方式、缓冲大小、调试符号都会影响可见性。
没有样本不等于没有执行，unknown 不等于未知 bug，极短程序也不适合拿少量样本做精细比例。
使用程序自带计时和完整工作量作交叉证据；新 check 打印的一次比值仍需重复测量。

## 网络对象不等于进程生命期

读 [sch_netem.c](../linux/linux-7.0/net/sched/sch_netem.c) 的入队、计划发送时间和出队，
再回到 [dev.c](../linux/linux-7.0/net/core/dev.c) 理解 qdisc 进入发送路径的位置。
抓包点不必等于出队点，不能把本机某接口的时间戳直接当作远端到达时间。

命名 namespace 被 bind mount 引用后，即使测试进程已结束仍可能存在；veth 也可能
随对应 namespace 引用保留。systemd 的 cgroup 回收进程，不能替代删除这些网络对象。
这也是网络案例同时检查 unit、namespace、pcap 与 host eth0 的原因。

## panic 是终止决策，需要继续向调用者追因

读 [sysrq.c](../linux/linux-7.0/drivers/tty/sysrq.c) 与
[panic.c](../linux/linux-7.0/kernel/panic.c)：本例通过 SysRq 明确进入 panic，
不是演示未知内存踩踏。转到 [pstore](../linux/linux-7.0/fs/pstore/platform.c) 看日志 dump，
再分清内存保留、下次读取、落盘、上传和服务端确认是不同阶段。

只看 vpanic 不能确定根因；只看 reset 标签不能证明发生 panic；只看 SSH 恢复不能
证明启动日志已上传。用失败 boot、恢复 boot、startup 缓冲 ID、原始栈和内容 ID 关联。
最终因果解释必须与实际证据一致，而不是因为有恢复动作就宣称所有故障类型都已覆盖。
