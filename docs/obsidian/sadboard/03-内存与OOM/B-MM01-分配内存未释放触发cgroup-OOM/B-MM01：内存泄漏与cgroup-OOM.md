[[README|首页]] · [[00-实验准备与通用方法/案例索引|案例索引]] · [[00-实验准备与通用方法/工具索引|工具索引]] · [[03-内存与OOM/00-章节导航|章节导航]]

先按现象提出假设并完成练习，再核对定位、内核机制和参考修复。`verify` 验证镜像提供的参考实现。

[[03-内存与OOM/B-MM01-分配内存未释放触发cgroup-OOM/B-MM01：内存泄漏与cgroup-OOM#现象与原理|现象与原理]] · [[03-内存与OOM/B-MM01-分配内存未释放触发cgroup-OOM/B-MM01：内存泄漏与cgroup-OOM#练习任务|练习任务]] · [[03-内存与OOM/B-MM01-分配内存未释放触发cgroup-OOM/B-MM01：内存泄漏与cgroup-OOM#使用工具|使用工具]] · [[03-内存与OOM/B-MM01-分配内存未释放触发cgroup-OOM/B-MM01：内存泄漏与cgroup-OOM#定位方法|定位方法]] · [[03-内存与OOM/B-MM01-分配内存未释放触发cgroup-OOM/B-MM01：内存泄漏与cgroup-OOM#内核流程与汇编|内核流程与汇编]] · [[03-内存与OOM/B-MM01-分配内存未释放触发cgroup-OOM/B-MM01：内存泄漏与cgroup-OOM#修复与验收|修复与验收]] · [[03-内存与OOM/B-MM01-分配内存未释放触发cgroup-OOM/B-MM01：内存泄漏与cgroup-OOM#实机证据与反例|实机证据与反例]]

## 现象与原理

### 3.1 问题现场与实验边界

难度：中级。程序周期处理数据，内存不断增长，最终没有普通错误返回就被终止。
需要证明终止原因，找到增长来源，再证明同等业务量能在资源预算内完成。
源码：[memory.c](https://github.com/linux-bsp/sadboard-external/blob/93c81e82acfdf5d54155d1b9bb750e78645d384f/package/sadboard-labs/src/memory.c)；
隔离脚本：[run-memory](https://github.com/linux-bsp/sadboard-external/blob/93c81e82acfdf5d54155d1b9bb750e78645d384f/package/sadboard-labs/run-memory)。

设备端：运行“分配内存未释放触发cgroup-OOM”故障现场，记录输出中的实际结果目录与异常证据。

```sh
sadboard run oom
```

设备端：紧接上一条实验读取退出状态，结合日志确认含义，不要先执行其他命令。

```sh
echo "$?"
```

设备端：执行“分配内存未释放触发cgroup-OOM”的参考修复验收，核对终端结论及保存的结果契约。

```sh
sadboard verify oom
```

设备端：查看最近的内核消息，结合本次 cgroup 记录寻找 OOM 或信号证据。

```sh
dmesg | tail -80
```

每次申请 1 MiB，写触每个 4 KiB 区间，共 64 次、间隔 50 ms。监督脚本留在 cgroup 外，
仅将实验子进程移入独立叶子组，限制 32 MiB、禁止 swap、20 秒兜底超时。
不要取消限制来“更真实地”压满设备；32 MiB 是实验预算，不是整机内存容量。

### 3.3 内存基础：地址、物理页、分配器和资源组

#### 3.3.1 malloc、虚拟地址、RSS 分别是什么

malloc 返回可用的虚拟地址范围，底层可能重用已有堆块，也可能扩展映射。首次写触
尚未驻留的合法页面时，内核可以分配物理页并建立页表，之后进程继续执行。因此虚拟
大小增长、RSS 增长、分配成功和物理内存已经实际消耗，不能视为同一时刻。

RSS 表示驻留页的一个观测口径；它不是所有 malloc 的简单总和，包含共享/映射因素，
与 cgroup 总计费也不必相等。free 把块交还给分配器，分配器可能保留页用于后续复用，
所以 free 后 RSS 未立即下降不能单独证明泄漏。要观察同样业务长期运行是否有界，
再结合所有权、分配栈与失去引用的内存块。

#### 3.3.2 合法缺页与 SIGSEGV

合法 VMA 的页尚未建立、写时复制等情形可能通过缺页处理恢复；没有对应 VMA 或权限
不允许时，则可能向用户进程发 SIGSEGV。本案例 NULL 字段访问属于后者。
MAPERR 与 ACCERR 用于区分地址映射与访问权限问题，仍需根据具体地址、指令和映射判断。

#### 3.3.3 cgroup 为什么在整机有空闲内存时 OOM

cgroup 将一组进程的资源计费和限制组织起来。本案例叶子组 memory.max 为 32 MiB、
swap.max 为 0；它可能达到自己的预算，而整机依然有可用内存。内核先进行允许的回收
和重试，再根据分配标志、余量和竞争状态决定失败或 OOM 处置，不是 max 加一就必杀。

`memory.events` 的 max、oom、oom_kill 是不同事件；组终止还可能出现对同一 PID 的
多次 kill 计数。应同时记录真实限制、计数、退出、时间及对应进程。精读条件分支见
[[03-内存与OOM/B-MM01-分配内存未释放触发cgroup-OOM/B-MM01：内存泄漏与cgroup-OOM#3.14 内核源码精读与关键分支|内核笔记]]。

### 3.4 先读负载：哪一步真正消耗内存

一次循环分配 1 MiB，再每隔 4096 字节写一个字节。当前 AM625 配置页大小为 4 KiB，
这些写触使各页实际参与计费；`volatile` 防止这些观察性写入被编译器删除。仅调用
malloc 而不触页，可能难以稳定复现同样的组内压力。

循环第 i 次把值 i+1 写入 256 个位置，参考版完整运行 64 次的业务校验和是
`256 × (1+2+…+64) = 532480`。这解释了为什么验收要看完整次数和 checksum，不能让
“只处理了一块但没有被杀”的程序假装修好了内存问题。该按页解释依赖当前 4 KiB 配置，
迁移到其他页大小时需要重新核对触页方式。

故障版局部变量 block 在下次循环被覆盖，旧分配地址不再被业务保存，也没有 free。
从所有权看是遗失了释放入口；从内核看则仍然是该进程的合法已映射页面。内核不知道
业务已经不需要它，因此不会自动替应用回收这块仍然映射的匿名内存。

### 3.5 为什么先查“谁杀的”，再查“谁泄漏的”

1. 退出 137 只提示 SIGKILL 的可能；先查本次 result、时间和监督器是否超时。
2. 对应 memcg 的 oom/oom_kill 和内核日志支持组内 OOM；限制从实际 `.limits` 读取。
3. 这仍不能说明是泄漏，业务确实需要的无界批量数据也可能 OOM。
4. 缩小输入，在不会触及组限制的条件下用分配栈与所有权分析证明 missing free。
5. 同样完整业务在参考版下有界完成，建立修复与资源行为的因果关系。

这条顺序把**终止机制**与**资源增长根因**分开。不要因为 Valgrind 找到某个泄漏，
就自动把设备过去所有进程消失归因于它；还需将具体一次退出与具体组计数关联。

### 3.6 原理：申请成功为什么仍然会被杀

glibc 的 malloc 管理用户堆，大申请可能通过 mmap 建立匿名 VMA，小申请可能扩展 brk，
具体阈值由 libc 和分配历史决定。获得虚拟地址不等于物理页已经驻留。写触匿名页时发生
缺页，内核分配 folio、对 memory cgroup 计费并更新页表。实验用 volatile 写操作确保
编译器不能把写触全部消除。

故障版循环结束前没有 free，已经处理的数据持续占据内存。组计费触及 memory.max 后，
内核尝试回收及重试；无法满足分配时进入该组 OOM 选择/终止流程。系统即使仍有大量
可用内存，组也可以 OOM；这正是需要同时看全局和组指标的原因。

以下为**内核源码关键路径**；不同页阶、重试和缓存路径会有变化：

源码流程示意：从匿名页写触、内存计费与回收失败追到 cgroup OOM 处理。

```text
用户态 malloc / 写触匿名地址
  ARM64 do_page_fault → handle_mm_fault → __handle_mm_fault
  do_anonymous_page → alloc_anon_folio → mem_cgroup_charge
  __mem_cgroup_charge → charge_memcg → try_charge_memcg
  page_counter_try_charge 失败 → 回收、重试
  mem_cgroup_oom → mem_cgroup_out_of_memory → out_of_memory
  oom_kill_process → __oom_kill_process → SIGKILL
```

阅读 [memory.c](https://github.com/linux-bsp/linux-7.0/blob/master/mm/memory.c) 的 `alloc_anon_folio/do_anonymous_page`、
[memcontrol.c](https://github.com/linux-bsp/linux-7.0/blob/master/mm/memcontrol.c) 的 `try_charge_memcg/mem_cgroup_oom`，
以及 [oom_kill.c](https://github.com/linux-bsp/linux-7.0/blob/master/mm/oom_kill.c)。这些路径是源码分析，
实际 OOM 的 dmesg 栈以实验归档为准；OOM 受害者也不必总是触发分配的进程。

## 练习任务

### 3.2 独立练习任务与分级提示

**现场入口**：`sadboard run oom`，读取现场 `memory-bug.*`；然后 `sadboard verify oom`。

**任务**：区分人工 SIGKILL、超时、全局 OOM 和组内 OOM；找出资源增长的所有权问题。
先证明“为何被杀”，再用小输入证明“何处分配后没有释放”。

**必须提交**：实际 memory.max/swap.max/oom.group、oom 与 oom_kill、峰值、退出码、
内核记录、Valgrind 分配栈；修复版应完成 64 次处理、checksum=532480。

<details><summary>L1 提示：看两层资源</summary>

全局 `/proc/meminfo` 不能代替该组的计费。32 MiB 是实验组限制，整机有空闲页也能
发生组 OOM。新记录的 `.limits` 保存实际读回的限制，不靠日志中写死的数字推断。

</details>
<details><summary>L2 提示：不要把所有计数都叫进程数</summary>

当前内核启用组终止时，对一个 PID 的处理可使 oom_kill=2；应结合 oom、日志和限制。
仅有正 oom_kill 不能证明是该组触及上限，全局 OOM 也可能杀死属于它的进程。

</details>

**L3 对照**：解释为何 malloc 可能先成功、写触时才触发压力；为什么 free 后 RSS
不立即回落不能单独证明泄漏？为什么 Valgrind 不应直接放进这个 32 MiB 组？
参考：[[03-内存与OOM/00-章节导航|OOM 案例]]。

## 使用工具

通用原理、参数和使用边界见工具手册；具体命令与证据判断见本例定位方法。

[[工具手册/sadboard|sadboard]] · [[工具手册/Valgrind|Valgrind]] · [[工具手册/Massif|Massif]] · [[工具手册/procfs|procfs]] · [[工具手册/cgroup-v2|cgroup-v2]]

## 定位方法

### 3.7 由结果倒推原因

1. 记录退出码；137 只是 SIGKILL 的线索，也可能来自人工 kill 或超时。
2. 检查现场 `memory-bug.events` 的 `oom` 与 `oom_kill`，并匹配内核时间、进程及 cgroup 名；从 `.limits` 核对实际组限制。
3. 对照 `memory-bug.peak` 与 33554432 上限，查看 fixed 对应文件。
4. 在小输入上使用 Valgrind 找分配来源，避免高开销诊断器自己触及 32 MiB 限制。
5. 修复后重跑相同 64 次处理，确认 checksum=532480、退出 0、oom_kill=0。

运行期间可在另一终端对专用组取样。组名含启动器 PID，应先从
`/sys/fs/cgroup/sadboard-oom-*` 查找，不能照抄另一次的名称：

设备端：读取全局内存统计，先区分系统余量与单个 cgroup 的内存预算。

```sh
cat /proc/meminfo
```

设备端：读取实验 cgroup 的当前内存占用，先将 PID 替换为实际现场值。

```sh
cat /sys/fs/cgroup/sadboard-oom-PID/memory.current
```

设备端：读取该组的匿名页、文件页等内存构成，判断增长来自哪类资源。

```sh
cat /sys/fs/cgroup/sadboard-oom-PID/memory.stat
```

设备端：检查该组的 max、oom、oom_kill 等事件增量，核对是否发生组 OOM。

```sh
cat /sys/fs/cgroup/sadboard-oom-PID/memory.events
```

设备端：查看该组 memory PSI，判断是否存在回收或内存等待压力。

```sh
cat /sys/fs/cgroup/sadboard-oom-PID/memory.pressure
```

短实验可能结束得比人工采样快；此时使用启动器保存的 events/peak，不要凭消失的目录
认定实验没有运行。若需延长观察，应在保持资源上限的前提下调整程序参数。

### 3.9 用 Valgrind 定位到申请点

设备端：将本次 NFS/SD 模式的实际结果根目录保存为当前终端变量，供后续命令复用。

```sh
SADBOARD_RESULTS=$(sadboard results)
```

设备端：创建本次 oom 手工取证目录；确认成功后再写入跟踪文件。

```sh
mkdir -p ${SADBOARD_RESULTS}/manual-oom
```

设备端：对故障版运行小规模 Valgrind 取证，检查未释放内存的分类及分配调用栈。

```sh
valgrind --leak-check=full --show-leak-kinds=all --num-callers=20 \
  --error-exitcode=99 --log-file=${SADBOARD_RESULTS}/manual-oom/leak.log \
  /usr/libexec/sadboard/memory-bug 4 0
```

设备端：在相同负载下检查参考版，比较内存是否归还以及错误计数是否清零。

```sh
valgrind --leak-check=full --error-exitcode=99 \
  /usr/libexec/sadboard/memory-fixed 4 0
```

这里处理 4 MiB，不需要触发 OOM。`definitely lost` 表示不再找到指向该块的指针；
`still reachable` 表示仍有引用，不能直接判泄漏。沿分配栈找到循环内 malloc，并检查
所有权及释放路径。SIGKILL 不允许程序执行退出清理，直接对 OOM 后的现场跑泄漏总结
会丢失信息，因此把“证明 OOM”和“定位泄漏”拆成两个互相支持的实验。

## 内核流程与汇编

### 3.14 内核源码精读与关键分支

读 [memcontrol.c](https://github.com/linux-bsp/linux-7.0/blob/master/mm/memcontrol.c) 的 `try_charge_memcg`：

- 计费是否能通过 page counter，首先决定是否需要慢路径。
- 无法阻塞的分配、特殊 GFP 标志与可回收的普通用户页，走法不同。
- 慢路径尝试组内回收、检查 margin、清空 stock 并重试，不是超过 max 就立即杀进程。
- 允许的重试耗尽后，某些分配可以进入 mem_cgroup_oom；其他路径可能只返回 ENOMEM。
- OOM 锁保证多个竞争者串行检查，取得锁后还会复查余量，不能把函数返回 true 简化成
  “必定新杀了一个进程”。

配合 [oom_kill.c](https://github.com/linux-bsp/linux-7.0/blob/master/mm/oom_kill.c) 读 victim 选择、组终止与后续回收。
把 `.limits`、oom/max/oom_kill、进程及时间连起来；新 check 要求组 oom 事件和 kill
事件共同存在。即使它通过，泄漏来源仍需分配栈和所有权分析来解释。

### 3.15 详细内核流程：写触、分配、计费、回收和终止

#### 3.15.1 malloc 成功不是所有物理页已经到位

malloc 可能重用分配器已有块，也可能通过 brk/mmap 建立或扩展映射；其选择取决于
libc、大小和状态，不把本例所有申请都写死成一种系统调用。返回虚拟地址之后，本例
每隔 4096 字节进行一字节写触，让当前 4 KiB 页配置下的页面实际参与驻留和计费。

源码流程示意：观察首次写触合法匿名地址时，缺页处理如何分配并计费物理页。

```text
用户 STRB 写尚未驻留的合法匿名区域
  → EL0 Data Abort → do_page_fault（此时 VMA 存在且允许写）
  → handle_mm_fault → __handle_mm_fault → handle_pte_fault
  → 对缺失匿名 PTE，经 do_pte_missing → do_anonymous_page
  → alloc_anon_folio
      基础页后备分支：folio_prealloc，分配 folio 并 mem_cgroup_charge
      大 folio/THP 等配置可走其他分支，不能假设永远一个基础页
  → 建立 PTE、更新反向映射/LRU 等状态 → 恢复并重试原写指令
```

这是与崩溃案例相同异常入口的**合法地址分支**，不是另一种 SIGSEGV。匿名读缺页还可能
先映射共享零页，写时再分配或 COW；本负载采用写触，不能用“读过同样范围”代替验证。
源码见 [memory.c](https://github.com/linux-bsp/linux-7.0/blob/master/mm/memory.c)。

#### 3.15.2 计费为何会进入慢路径

mem_cgroup_charge 的实际处理可进入：

源码流程示意：沿 memcg 计费、额度检查、回收和重试理解内存压力的形成。

```text
__mem_cgroup_charge
  → get_mem_cgroup_from_mm：关联到该 mm 的计费域
  → charge_memcg → try_charge → try_charge_memcg
    尝试使用本地 stock 或 page_counter 预算
    失败后调整批量、发出 max 事件、尝试组内回收、清空 stock、重试
    依据 GFP、余量、重试次数决定是否进入 mem_cgroup_oom
```

stock 是降低频繁全局计数操作的批量优化，意味着一次写一页不等于计数文件恰好逐页
同步增长。计费对象还包括其他合规资源，memory.current/peak 也不是 malloc 参数总和。
看到计数略有差异，先检查口径、批量和共享资源，而不是立即认为工具坏了。

| 条件或出口 | 为什么存在 | 取证时怎样区分 |
| --- | --- | --- |
| 回收后有足够 margin | 可继续执行，不必杀进程 | max 增长可以没有 oom_kill |
| 分配不允许阻塞或带特殊 GFP | 不能在任意上下文无限回收 | 可能返回 ENOMEM，并非必杀 |
| 已有其他任务正在释放内存 | 避免重复终止和无意义竞争 | OOM 函数成功返回不等于新杀一个 PID |
| 普通组预算持续不足 | 进入 memcg OOM 处置 | 结合组名、oom、kill、限制和日志 |
| 系统范围不足 | 全局 OOM 的另一种约束 | 不把进程所属组误当作触发预算的组 |

#### 3.15.3 从组 OOM 到 SIGKILL 与回收

源码流程示意：区分 OOM 记录、受害者选择、SIGKILL 与被杀进程的后续资源回收。

```text
mem_cgroup_oom
  → 记录 MEMCG_OOM，检查分配阶数和适用条件
  → mem_cgroup_out_of_memory：在 OOM 锁内重新检查余量
  → out_of_memory：按约束判断已有退出任务或选择 victim
  → oom_kill_process → __oom_kill_process：对受害者发 SIGKILL
  → memory.oom.group 策略可进一步处理组内任务
  → 受害任务在信号/退出路径释放 mm；OOM reaper 可协助解除相关映射
```

SIGKILL 不能由业务捕获来 free，因而最后清理依靠内核。此后其他分配者可能重试成功，
不应把“发送信号”当成“所有页已在此时释放”。group kill 的计数也不能直接解释成不同
受害进程数量。看 [memcontrol.c](https://github.com/linux-bsp/linux-7.0/blob/master/mm/memcontrol.c) 与
[oom_kill.c](https://github.com/linux-bsp/linux-7.0/blob/master/mm/oom_kill.c) 时，分别标出计费失败、victim 选择、
发信号、异步回收四段，不把它们画成一个不可分割动作。

### 3.16 汇编实战：一字节写入怎样触发整页成本

真实 memory-bug 的 main 中可看到字节存取和页步长。以下保持原指令，只省略中间行：

反汇编摘录：结合每页一次的访存与步长，理解虚拟分配何时转化为实际物理页压力。

```asm
e44: 39400000  ldrb w0, [x0]
e60: 11400400  add  w0, w0, #0x1, lsl #12
e70: 6b00003f  cmp  w1, w0
e74: 54fffd29  b.ls e18 <main+0x108>
```

写入端另有 STRB；LDRB 读回业务字节并累加校验。ADD 中 `#1,lsl #12` 是加 4096，
不是把整个结果再乘 4096。每次只存一字节，却可能首次触发一个页面的分配/计费；CPU
指令的访存宽度和虚拟内存管理的页粒度是两层不同概念。

从故障指令本身不能看见完整 OOM 调用链。通过合法 VMA、组限制、内核事件和进程退出，
才能解释它是正常缺页慢路径最终遇到资源限制；同一条 STRB 若地址已经越界，则可能走
第 1 章的非法访问路径。汇编相似不代表根因相同。

参考版在业务块处理后有 free 调用。静态看到一条 BL free 仍不足以证明长期有界，
须结合所有分支、完整 64 次处理和峰值对照。练习：找出 malloc、STRB、页步长、
checksum 累加、free 五类指令，分别说明谁负责用户分配器、谁可能引发内核缺页。

## 修复与验收

### 3.10 修复与扩展

参考实现在每块处理后 free，累计处理量不变。RSS 不立即下降不一定意味着 free 无效，
分配器可能缓存内存；用长期有界性、组峰值和分配器工具交叉验证。若工作本来需要保留
全部数据，应改为流式处理或明确容量预算，不能只靠增加 OOM 上限掩盖问题。

练习：区分内存泄漏、无界缓存、页缓存、碎片、memory.high 节流、RLIMIT_AS 限制
及全局 OOM。解释为何 `malloc == NULL`、退出 137、内核 panic 是三种不同结果。
脚本退出后应没有遗留的 `sadboard-oom-*` 组；保留证据后仅删除此次现场目录。

### 3.11 证据验收与分级练习

新现场保存 `memory-{bug,fixed}.limits`，从 cgroup 实际读回 memory.max、swap.max
和 oom.group。`check` 要求故障版退出 137 且 oom、oom_kill 均为正；参考版完成全部
64 次及 checksum=532480，未被 OOM 杀死。仅打印“被杀”或伪造一份正 kill 计数不够。
按 [[03-内存与OOM/B-MM01-分配内存未释放触发cgroup-OOM/B-MM01：内存泄漏与cgroup-OOM#3.2 独立练习任务与分级提示|练习册]] 区分信号、组内 OOM 与泄漏根因，
并用 [[附录A-实验报告/00-章节导航|报告模板]] 保存资源限制及分配栈。

## 实机证据与反例

### 3.8 指标如何解释

| 字段 | 含义及判断边界 |
| --- | --- |
| memory.current | 组当前计费，包含的资源不止单进程 RSS |
| memory.peak | 组计费峰值，不保证与限制或进程 RSS 完全相等 |
| memory.stat 中 anon/file | 区分匿名内存和文件缓存；不要把所有缓存增长叫泄漏 |
| memory.events max | 达到硬限制的事件；可能随后回收成功 |
| oom | 发生 OOM 分配处置，不等价于一定杀了进程 |
| oom_kill | OOM kill 计数；结合内核记录解释，不能当作唯一受害 PID 数量 |
| memory.pressure some/full | 因内存回收等压力产生的停顿比例，区别于容量计数 |

本案例是新建的无子组叶子，因此可以直接解释其 events。一般层级环境需要区分
`memory.events` 的层级统计与 `memory.events.local`。接口细节见
[当前内核的 cgroup 文档](https://github.com/linux-bsp/linux-7.0/blob/master/Documentation/admin-guide/cgroup-v2.rst)。

实机启用 `memory.oom.group=1` 后，日志显示对同一 PID 的初始选择和组终止，
`oom_kill` 为 2、`oom_group_kill` 为 1。判定应结合退出 137、正 oom 与 oom_kill、实际组限制，
不能把计数硬编码成 1，也不能据此声称两个不同程序被杀。

### 3.12 逐项判断常见观测

| 观测 | 可以支持什么 | 不能单独证明什么 |
| --- | --- | --- |
| VmSize 增长 | 虚拟地址空间规模变化 | 全部页已经驻留 |
| RSS/anon 增长 | 匿名页驻留/计费增加的线索 | 一定是泄漏而非正常工作集 |
| memory.events max 增加 | 有分配触及硬预算路径 | 已经杀了进程 |
| oom 增加、oom_kill 为零 | OOM 处置发生但未形成该计数的 kill | 系统一定正常或一定异常退出 |
| oom 与 oom_kill 正增量 | 结合组/PID/时间支持本次组内终止 | 恰好杀死几个不同进程 |
| free 后 RSS 不降 | 分配器可能保留页 | free 没有执行 |
| 小输入 definitely lost | 有分配块已失去可达引用 | 它一定解释本次 OOM 的全部内存 |

Valgrind 日志先看错误类别和块数量，再沿分配栈回到 malloc 所在循环。工具自身需要
额外内存，不能把它放进原来的 32 MiB 预算后再拿“很快 OOM”比较业务泄漏速率。
结束时仍可达、确定丢失、间接丢失和可能丢失的含义不同，需要结合保存引用的数据结构。

一般工程的修复还要覆盖 malloc 失败后已分配资源如何释放、缓存是否有上限、并发所有权
是否明确。调高 memory.max 可能是容量设计的一部分，但对每次请求都丢失引用的程序，
它只会让故障更晚发生，不改变长期无界增长。

[[附录A-实验报告/00-章节导航|实验报告与复盘]] · [[00-实验准备与通用方法/01-构建与启动部署#源码与实机证据|匹配源码、固件与实测证据]]

[[03-内存与OOM/B-MM02-malloc返回空指针但并未发生OOM-kill/B-MM02：malloc 返回空指针但并未发生 OOM kill|下一例 B-MM02]]
