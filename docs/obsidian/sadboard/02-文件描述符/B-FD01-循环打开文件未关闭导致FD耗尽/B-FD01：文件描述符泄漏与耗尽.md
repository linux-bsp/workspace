[[首页]] · [[案例索引]] · [[工具索引]] · [[02-文件描述符/00-章节导航|章节导航]]

先按现象提出假设并完成练习，再核对定位、内核机制和参考修复。`verify` 验证镜像提供的参考实现。

[[02-文件描述符/B-FD01-循环打开文件未关闭导致FD耗尽/B-FD01：文件描述符泄漏与耗尽#现象与原理|现象与原理]] · [[02-文件描述符/B-FD01-循环打开文件未关闭导致FD耗尽/B-FD01：文件描述符泄漏与耗尽#练习任务|练习任务]] · [[02-文件描述符/B-FD01-循环打开文件未关闭导致FD耗尽/B-FD01：文件描述符泄漏与耗尽#使用工具|使用工具]] · [[02-文件描述符/B-FD01-循环打开文件未关闭导致FD耗尽/B-FD01：文件描述符泄漏与耗尽#定位方法|定位方法]] · [[02-文件描述符/B-FD01-循环打开文件未关闭导致FD耗尽/B-FD01：文件描述符泄漏与耗尽#内核流程与汇编|内核流程与汇编]] · [[02-文件描述符/B-FD01-循环打开文件未关闭导致FD耗尽/B-FD01：文件描述符泄漏与耗尽#修复与验收|修复与验收]] · [[02-文件描述符/B-FD01-循环打开文件未关闭导致FD耗尽/B-FD01：文件描述符泄漏与耗尽#实机证据与反例|实机证据与反例]]

## 现象与原理

### 2.1 先观察现象，不急着增加限制

难度：入门到进阶。服务按请求打开一个资源，开始正常，处理一段时间后报告
`Too many open files`。内存没有明显耗尽，系统没有重启，其他服务仍能运行。
你的任务是解释：哪一种资源耗尽了、限制作用于谁、为什么请求数越多越容易失败，
以及为什么增加上限只能推迟本案例的问题。

源码是 [fd.c](https://github.com/linux-bsp/sadboard-external/blob/93c81e82acfdf5d54155d1b9bb750e78645d384f/package/sadboard-labs/src/fd.c)。程序用 `/dev/null`
代表每次请求需要打开的资源；故障版漏掉 close，参考版每次处理后关闭。它不是模拟
磁盘装不下，也不向管理网口注入故障。实验进程自己将 NOFILE 软硬限制降至 64，
不改全局 file-max、不改 SSH 或其他服务的限制；延迟总预算不超过十秒。

#### 2.1.1 复现前提与命令

先等固件健康确认，确认 `/data` 持久化且至少有 64 MiB 空间。板端执行：

设备端：确认当前案例列表中存在 FD 实验入口，再启动故障现场。

```sh
sadboard list
```

设备端：运行“循环打开文件未关闭导致FD耗尽”故障现场，记录输出中的实际结果目录与异常证据。

```sh
sadboard run fd
```

设备端：紧接上一步保存退出码并立即打印，结合本例日志解释该状态。

```sh
rc=$?
printf 'exit=%s\n' "$rc"
```

默认 128 次请求、每次等待 20 ms，预期退出 24，表示**本程序主动把 EMFILE 错误值
作为返回码**；它不是 `128 + 信号`。复制输出中的实际现场目录，检查：

设备端：将本次 NFS/SD 模式的实际结果根目录保存为当前终端变量，供后续命令复用。

```sh
SADBOARD_RESULTS=$(sadboard results)
```

设备端：替换实际现场目录，查看该次任务的运行状态和记录。

```sh
sadboard status ${SADBOARD_RESULTS}/实际现场目录
```

设备端：把路径占位符替换为本次实际现场目录，复核该次运行的证据完整性与验收约束。

```sh
sadboard check ${SADBOARD_RESULTS}/实际现场目录
```

设备端：读取该现场的 FD 故障摘要，核对完成数、占用峰值、最终占用和错误码。

```sh
cat ${SADBOARD_RESULTS}/实际现场目录/fd-bug.out
```

设备端：读取同一现场的 stderr，查看资源上限、准备状态及实际失败信息。

```sh
cat ${SADBOARD_RESULTS}/实际现场目录/stderr.log
```

不要把其他 shell 中相同的退出数字自动解释为 EMFILE；系统调用返回值和程序逻辑
才是本例的依据。没有 SIGKILL、没有组 OOM 计数，是区分 OOM 的线索，仍应保留证据。

### 2.3 FD 到底是什么

#### 2.3.1 三层对象，不能混为一个“文件”

FD 是进程描述符表中的非负整数索引。打开普通文件、socket、管道、eventfd 等，
都可能消耗 FD；因此“我没有打开很多磁盘文件”不能排除描述符泄漏。

对象关系示意：区分进程 FD 编号、struct file 引用与底层 inode/设备对象。

```text
进程 files_struct / fdtable
  fd 0 ──> 标准输入的 struct file
  fd 1 ──> 标准输出的 struct file
  fd 2 ──> 标准错误的 struct file
  fd 3 ──> 一次 open 的 struct file ──> 路径 / inode / 设备操作
  fd 4 ──> 另一次 open 的 struct file ──> 可以仍然是同一个 /dev/null
```

FD 表项、打开文件描述对象和文件系统 inode 是三个层次。重复 open 同一路径通常创建
不同打开对象；dup 则可用另一个 FD 引用同一打开对象，共享相应偏移等状态。关闭一个
FD 不表示所有引用都消失，unlink 路径也不等于关闭已打开的引用。
接口定义见 [open(2)](https://man7.org/linux/man-pages/man2/open.2.html)。

#### 2.3.2 为什么 `/dev/null` 也能耗尽资源

/dev/null 不需要保存业务数据，但每次成功 open 仍要占用当前描述符范围内的槽位。
本例不断覆盖局部变量 fd，旧的整数值被遗忘；内核不会因为 C 变量离开作用域就自动
调用 close。直到进程退出，内核才统一释放它还持有的描述符。

因此重启服务会短暂恢复，但不修复泄漏。设备持续运行的时间越长，请求越多，越可能
再次撞上限制；本案例把限制缩小，是为了在几秒内稳定复现这个关系。

### 2.4 理解资源上限，再读错误信息

#### 2.4.1 soft、hard 与实际可分配范围

RLIMIT_NOFILE 的软限制控制本进程可分配的描述符编号范围，硬限制约束软限制可提升的
范围。此处限制为 64，新的 FD 应落在 0..63；已占用槽位会减少剩余容量。
一个通常有 0、1、2 三个描述符的进程，大致还能打开 61 个，但不能把这个数写死：
服务管理器、父进程继承或调试环境都可能使初始状态不同。
限制规则见 [getrlimit(2)](https://man7.org/linux/man-pages/man2/getrlimit.2.html)。

本程序记录实际 baseline，验收采用 `完成量 + baseline = 64`，而不是永远要求 61。
它不主动提高继承上限；若父环境给的软/硬限制不足 64，返回 75 表示前提不满足。
程序内部降限制只影响它自己，不会反向修改启动它的 shell。

#### 2.4.2 这些错误看起来相近，但处置不同

| 观测 | 主要含义 | 应补充的证据 |
| --- | --- | --- |
| open 返回 EMFILE | 本进程可分配 FD 范围耗尽 | 进程 limits、fd 表、open/close 配对 |
| open 返回 ENFILE | 系统打开文件对象资源限制相关失败 | file-nr/file-max、全局日志及权限条件 |
| open 返回 ENOENT | 路径或组件不存在 | 路径、挂载、namespace、名称 |
| open 返回 EACCES | 访问检查拒绝 | 权限、凭据、目录搜索权限等 |
| malloc 返回 NULL/ENOMEM | 某种内存或地址空间申请失败 | 分配上下文、限制、内存状态 |
| 进程被 SIGKILL | 终止方式，不能单独说明谁发送 | OOM、超时、管理员或监督器记录 |

错误名要从实际系统调用读出。不要为了验证 ENFILE 去降低整机 file-max 或耗尽全机
资源；本案例只用进程限制构造 EMFILE。内核全局打开对象限制对特权进程还有特例，
也不能简单认为 root 的每次失败都由同一限制引起。

## 练习任务

### 2.2 独立练习任务与分级提示

**入口**：`sadboard run fd`，对照 `sadboard run fd 4 0`，再运行 `sadboard verify fd`。

**任务**：区分 FD 耗尽、全局文件对象不足、内存不足和路径错误。解释为什么同一个
/dev/null 路径会占用多个槽，为什么小输入没有报错却仍存在泄漏。

**必须提交**：实际 NOFILE、baseline、完成/请求数、两次 FD 快照、openat/close
配对、EMFILE 返回和参考修复的完整 128 次处理。说明全局限制和其他服务未被更改。

<details><summary>L1 提示：先确认谁返回了错误</summary>

本例退出 24 是程序主动返回 EMFILE，不是信号。看 strace 的系统调用返回值；
limits 是该进程的约束，父 shell 的 ulimit 不会因子进程降限制而自动改变。

</details>
<details><summary>L2 提示：把对象生命期画出来</summary>

分别画局部整数 fd、fdtable 槽、struct file 和底层路径。C 变量被覆盖不等于内核
引用被关闭；CLOEXEC 也不等于请求结束自动 close。查错误和提前返回路径的所有权。

</details>

**L3 对照**：增加一个继承 FD，解释为什么不能把失败请求数写死为 61；解释 dup、
fork、exec 对引用的不同作用，以及 TIME_WAIT 为什么不等于进程仍持有 socket FD。
参考：[[02-文件描述符/00-章节导航|描述符章节]]。

## 使用工具

通用原理、参数和使用边界见工具手册；具体命令与证据判断见本例定位方法。

[[工具手册/sadboard|sadboard]] · [[工具手册/strace|strace]] · [[工具手册/ltrace|ltrace]] · [[工具手册/procfs|procfs]] · [[工具手册/readelf|readelf]] · [[工具手册/nm|nm]] · [[工具手册/objdump|objdump]]

## 定位方法

### 2.10 参数、复位与证据边界

统一入口默认 128/20，允许 `REQUESTS=1..4096`、`DELAY_MS=0..50`，乘积不超过
10000 ms；超预算/非法参数返回 64，继承限制不足返回 75，不能记作预期故障通过。
数字 24 只在本 Linux 案例约定下作为主动退出码使用。

进程退出即释放自身 FD；`sadboard reset RUN` 只停止所属实验并保留证据。无需重启板，
无需调整其他服务。保留 JSON、strace、limits 与两次 fd 快照后再删除自己的现场。
实测范围及真实值见 [验证记录](https://github.com/linux-bsp/workspace/blob/cb2b20ab8d17e68f4782dd96efe5a1253b64f035/docs/am625-debug-validation.md)，本章示意输出和进阶题
不代表全部逐条实机执行结果。


### 2.5 第一步取证：描述符是否持续增长

统一入口结束后目标进程已退出，`/proc/PID/fd` 不再存在；这时应读保存的 JSON 和
strace。为了观察增长，可以单独运行稍慢的同一负载。以下操作不会生成统一 run.info，
操作者应自行保存固件 ID、输入和结果；进程仍受内部 64 FD 与十秒预算约束。

设备端：将本次 NFS/SD 模式的实际结果根目录保存为当前终端变量，供后续命令复用。

```sh
SADBOARD_RESULTS=$(sadboard results)
```

设备端：创建本次 fd 手工取证目录；确认成功后再写入跟踪文件。

```sh
mkdir -p ${SADBOARD_RESULTS}/manual-fd
```

设备端：后台运行较慢的 FD 故障负载并立即保存 PID，然后尽快执行下面的进程快照。

```sh
/usr/libexec/sadboard/fd-bug 128 50 \
  > ${SADBOARD_RESULTS}/manual-fd/bug.json \
  2> ${SADBOARD_RESULTS}/manual-fd/bug.err &
pid=$!
```

设备端：查看刚才保存的 PID 的资源上限，确认观测的是同一个实验进程。

```sh
cat /proc/$pid/limits
```

设备端：采集该进程当前打开的 FD 与引用目标，记录第一次快照。

```sh
ls -l /proc/$pid/fd
```

设备端：等待一秒，让受控负载继续运行，再比较下一份快照。

```sh
sleep 1
```

设备端：对同一个 PID 再取一次 FD 快照，观察描述符是否增长。

```sh
ls -l /proc/$pid/fd
```

设备端：等待后台负载结束并立即打印其退出状态，避免被后续命令覆盖。

```sh
wait "$pid"
printf 'exit=%s\n' "$?"
```

`$!` 是后台负载 PID；`wait` 取得其退出结果。某次读取如果提示目录不存在，可能是
进程已结束，不能把空观测当作没有泄漏。刚启动时的第一次快照也可能早于 setrlimit，
应与 stderr 中的准备信息及后续快照核对。
`/proc/PID/fd` 的条目含义见 [proc_pid_fd(5)](https://man7.org/linux/man-pages/man5/proc_pid_fd.5.html)。

观察应集中于同一 PID、同一时间窗中 `/dev/null` 引用数量增长。不要只统计系统全部
进程 FD 的总和；那无法确定是谁泄漏。列目录的观察命令运行在另一个进程，不占用被
观察进程的 FD；而在目标内部调用 opendir 自查则需要额外槽位，耗尽后可能也失败。
程序为避免这个问题，用 fcntl(F_GETFD) 检查 0..63，不通过新开目录统计。

### 2.6 第二步取证：用 strace 找到未配对的生命周期

设备端：将本次 NFS/SD 模式的实际结果根目录保存为当前终端变量，供后续命令复用。

```sh
SADBOARD_RESULTS=$(sadboard results)
```

设备端：记录 openat、close 与资源上限调用，查找未配对的打开操作；跟踪结果只用于因果分析。

```sh
strace -f -tt -T -e trace=openat,close,prlimit64 \
  -o ${SADBOARD_RESULTS}/manual-fd/bug.strace \
  /usr/libexec/sadboard/fd-bug 128 0 \
  > ${SADBOARD_RESULTS}/manual-fd/traced-bug.json
```

本例以 openat/close 配对和实际 FD 上限为主要证据；参数含义及本例选择理由见 [[工具手册/strace#FD 案例的参数选择|strace 手册]]。

注意 glibc 的 open 接口在本环境可通过 openat 系统调用实现。只过滤 open 可能漏掉
真正发生的调用。开头动态加载器会打开并关闭库文件，不要将它们与业务循环混为一谈。
关注 `/dev/null` 路径及其返回的 FD，然后寻找匹配的 close。

下面是**说明格式的示意，不是某次实机原文**：

跟踪格式示意：观察 openat 返回的 FD 持续增长，最终到达 EMFILE；本块是说明性样例。

```text
openat(AT_FDCWD, "/dev/null", O_RDONLY|O_CLOEXEC) = 3
openat(AT_FDCWD, "/dev/null", O_RDONLY|O_CLOEXEC) = 4
...
openat(AT_FDCWD, "/dev/null", O_RDONLY|O_CLOEXEC) = 63
openat(AT_FDCWD, "/dev/null", O_RDONLY|O_CLOEXEC) = -1 EMFILE (...)
```

这里没有相应 close，FD 编号持续占用，最后分配失败。`O_CLOEXEC` 只在成功 exec 时
关闭带标志的 FD；本业务循环没有 exec，所以它不能替代每次请求结束后的 close。
strace 会改变时序，故本步骤用于证明调用关系，不能用它的总耗时作为无干扰性能值。

## 内核流程与汇编

### 2.7 从系统调用读到内核源码

内核阅读入口见 [[00-实验准备与通用方法/01-构建与启动部署#源码与实机证据|源码与实机证据]]，具体函数按实际内核核对。以下是**源码关键路径**，不是用户 GDB
能够直接打印的完整内核栈，也不是从其他旧内核照抄的函数列表：

源码流程示意：先分配受 RLIMIT_NOFILE 约束的 FD，再创建并发布打开文件对象。

```text
用户 open / libc 包装
  openat 系统调用
  fs/open.c: do_sys_open → do_sys_openat2
  build_open_flags 检查参数
  FD_ADD（include/linux/file.h 中的组合资源管理宏）
    get_unused_fd_flags → __get_unused_fd_flags → alloc_fd
      在 current->files 中寻找空槽
      若候选 fd >= RLIMIT_NOFILE，则返回 -EMFILE
    只有 FD 分配成功才求值 do_file_open，建立打开文件对象
    成功后 fd_publish → fd_install，把 struct file 发布到 fd 表
```

阅读 [open.c](https://github.com/linux-bsp/linux-7.0/blob/master/fs/open.c) 的 `do_sys_openat2`，再转到
[file.h](https://github.com/linux-bsp/linux-7.0/blob/master/include/linux/file.h) 的 `__FD_PREPARE_INIT`、`FD_ADD`，
最后读 [file.c](https://github.com/linux-bsp/linux-7.0/blob/master/fs/file.c) 的 `alloc_fd`。当前版本通过宏和清理
guard 表达先保留 FD、失败自动归还等规则；旧文章里直接写在 open.c 中的步骤不一定
仍以同样形式存在。不要把宏名字误认为一定会在实机栈中出现的普通函数。

`alloc_fd` 用 file_lock 保护表操作，检查 next_fd、位图和可扩展范围；达到 end 便
返回 -EMFILE。这个错误发生在描述符槽位分配阶段，不是 `/dev/null` 读写失败。
文件对象全局限制则读 [file_table.c](https://github.com/linux-bsp/linux-7.0/blob/master/fs/file_table.c) 的
`alloc_empty_file`：它检查资源条件，也可能有 ENOMEM 等不同失败；ENFILE 是另一条
资源分支，不应与进程 FD 范围混为一谈。

#### 2.7.1 close 为什么不只是把整数改成零

close 通过 `close_fd` 在表中摘除引用，归还 FD 号，再进入 `filp_close` 等引用释放
路径。文件对象若仍被 dup、fork 后的其他进程或其他内核引用持有，并不会立刻销毁。
最后引用的清理涉及 `fput/__fput`，某些上下文会延后处理，因此不要把表项移除、
引用计数归零和底层设备 release 当成同一时刻。

还有一个常见 bug：业务保存着旧 FD 整数，另一线程关闭后该编号被重用，再使用旧整数
可能访问另一个对象。因而修复不只是“某处加 close”，还要明确谁拥有描述符、谁能
借用、何时失效。不要在不分析多线程编号重用的情况下盲目重试失败的 close。

### 2.13 内核源码精读与关键分支

从 [open.c](https://github.com/linux-bsp/linux-7.0/blob/master/fs/open.c) 的 do_sys_openat2 进入
[file.h](https://github.com/linux-bsp/linux-7.0/blob/master/include/linux/file.h) 的 FD_ADD。当前内核使用组合清理宏：
先取 FD 槽，成功后才求值文件打开表达式，再发布引用；打开失败则由清理规则归还资源。
宏名不一定成为栈帧，不能照搬旧内核中显式展开的源码来伪造当前调用栈。

读 [file.c](https://github.com/linux-bsp/linux-7.0/blob/master/fs/file.c) 的 alloc_fd：候选编号达到 end 时返回 EMFILE，
end 来自该进程的 RLIMIT_NOFILE。再读 close_fd 如何在锁保护下摘除表项，转入
filp_close 与文件引用释放。最后读 [file_table.c](https://github.com/linux-bsp/linux-7.0/blob/master/fs/file_table.c)
的 alloc_empty_file、fput、__fput，区分系统对象预算、FD 槽位、最后引用和延后清理。

本例只降低子进程的预算；进程退出回收不等于业务正确释放。将局部变量覆盖与 fdtable
引用生命周期分别画出来，就能解释为什么相同路径重复 open 也会耗尽描述符。
细节及真实 syscall 证据见 [[02-文件描述符/00-章节导航|FD 章节]]。

### 2.14 详细内核流程：从 open64 到 FD 发布，再到关闭

#### 2.14.1 三套调用约定不能混用

本构建的应用反汇编调用 `open64@plt`，而实机 strace 显示 openat。这并不矛盾：
C 源接口、libc 导出符号、实际系统调用是三个层次。PLT 可能经动态链接跳板到 libc，
只有其内部的 SVC 才进入内核，不能把 `bl open64@plt` 本身称为内核异常入口。

源码流程示意：区分 open 的 C 接口、libc 包装、SVC 以及内核 openat 入口。

```text
C: open("/dev/null", O_RDONLY|O_CLOEXEC)
  → 应用 BL open64@plt → libc 系统调用包装
  → SVC，保存 pt_regs，按调用号分派
  → __arm64_sys_openat(pt_regs *)
    宏生成的参数提取/类型转换层（可能内联）
  → do_sys_open → do_sys_openat2
  → build_open_flags → FD_ADD
```

在应用的 C 调用入口，x0 是路径，x1/w1 是 flags；在 openat 系统调用入口，x0 是
目录描述符，x1 是路径，x2 是 flags；在 `__arm64_sys_openat` 的 C 包装入口，x0
又变成保存现场的 pt_regs 指针。脱离当前边界套用参数含义，很容易看错一个指针。
宏定义见 [syscall_wrapper.h](https://github.com/linux-bsp/linux-7.0/blob/master/arch/arm64/include/asm/syscall_wrapper.h)。

#### 2.14.2 先预留槽，再建立打开对象

| 步骤 | 当前内核入口 | 关键状态与失败 |
| --- | --- | --- |
| 检查参数 | build_open_flags | flags、mode 等不合法可在此拒绝 |
| 预留 FD | get_unused_fd_flags → __get_unused_fd_flags → alloc_fd | current->files、位图与 rlimit；无槽返回 EMFILE |
| 打开对象 | do_file_open | 文件名解析、VFS/权限、具体文件类型的打开操作 |
| 发布引用 | fd_publish → fd_install | 将已获得的 struct file 安装到预留槽 |
| 出错清理 | FD_PREPARE 对应清理规则 | 归还未发布槽和未移交的引用 |

这是一个有资源所有权转移的事务，不是将一个整数加一就结束。`alloc_fd` 的 end 来自
进程 NOFILE，候选编号达到 end 就失败；因此 EMFILE 可能在真正打开该路径之前产生。
同样路径若只是已经打开多次，并不会自动复用旧 FD 或替你执行 close。

FD_ADD 和清理 guard 位于 [file.h](https://github.com/linux-bsp/linux-7.0/blob/master/include/linux/file.h)，
打开入口位于 [open.c](https://github.com/linux-bsp/linux-7.0/blob/master/fs/open.c)，槽分配/发布位于
[file.c](https://github.com/linux-bsp/linux-7.0/blob/master/fs/file.c)。这里省略了路径解析内部的多层 VFS、LSM 与设备
回调；不同文件类型不应伪造成相同完整栈。

#### 2.14.3 errno 从哪里来，描述符什么时候能重用

内核原始 `-EMFILE` 在 64 位返回寄存器中可表示为 `0xffffffffffffffe8`。libc 按错误
约定将返回值变为 -1、errno 变为正 24；本教学程序随后主动返回 24。系统调用结果、
libc errno 和进程退出码是三次不同的转换，不能把十六进制负值当成巨大成功 FD。

关闭路径关键步骤为：

源码流程示意：沿 close 的编号回收、文件引用释放和延后清理追踪资源生命周期。

```text
close 的系统调用
  → close_fd
    → 在 file_lock 保护下 file_close_fd_locked
      从 fdtable 清除 struct file 指针，释放 FD 编号
    → filp_close → 文件引用释放
      → 最后引用时进入 __fput 或延后清理
```

释放 FD 表项之后，该编号可能被另一线程重新分配；底层 file 的最后引用与设备资源
释放却未必同步完成。线程往往共享 files_struct，多个 FD 还可指向同一个打开对象。
因此只保存一个旧整数、事后盲目重试关闭，可能误关新对象。业务需要明确所有权及移交
边界；本例单线程通过每次请求配对 open/close 验证基本规则。

### 2.15 汇编实战：打开符号、返回值与 pt_regs 包装

真实应用中，故障版在 0x1128 调用 `open64@plt`；参考版在 0x1168 调用同类入口，
并在 0x11bc 调用 close。两版地址不同，先按符号和路径比较，而不是逐地址对齐。

参考版反汇编摘录：核对 open64 与 close 都出现在请求处理路径中。

```asm
/* 参考版：下面两行来自 main，省略中间业务与计数 */
1168: 97fffe82  bl b70 <open64@plt>
11bc: 97fffe51  bl b00 <close@plt>
```

这只能证明该路径有相应调用指令，不能静态保证每个请求都走到 close；还要看分支、
错误出口和实机 trace。本轮已经独立记录了 128 次 open 与 128 次 close，形成动态对照。

再看同固件 vmlinux 的 `__arm64_sys_openat` 真实片段：

内核反汇编摘录：观察系统调用包装如何从 pt_regs 提取参数，并将返回值符号扩展。

```asm
/* 省略函数序言和 flags 整理，地址是 ELF 链接地址 */
ffff8000803ec130: f9400c04  ldr x4, [x0, #24]
ffff8000803ec134: a9408c01  ldp x1, x3, [x0, #8]
ffff8000803ec13c: b9400005  ldr w5, [x0]
ffff8000803ec174: 97fffeed  bl  ffff8000803ebd28 <do_sys_openat2>
ffff8000803ec178: 93407c00  sxtw x0, w0
```

这里开始的 x0 指向 pt_regs，按八字节布局提取已保存的寄存器。最后 SXTW 把 32 位
结果按符号扩展成 64 位，以保留负错误。注意 do_sys_open 在该构建中没有单独出现在
这个片段的调用链上：包装可被内联，源码流程中的一个名字不保证存在一条 BL。
练习：对照参数宏，解释被读出的四个参数分别在哪里；再检查 strace 中 EMFILE 前的
最后一次成功 FD。不要把 pt_regs 指针当成字符串给 GDB 强行打印。

## 修复与验收

### 2.8 参考修复与可验收结果

设备端：运行默认规模的 FD 参考修复验收，确认所有请求完成后描述符归还。

```sh
sadboard verify fd
```

设备端：用更小请求数复验 FD 案例，避免只在资源耗尽参数下判断修复。

```sh
sadboard verify fd 4 0
```

默认对照应表现为故障版在容量用尽时退出 EMFILE，参考版完成全部 128 次且最终 FD
数量回到 baseline。小输入 4 次时故障版可能退出 0，但 final_open 仍增加 4，说明
**未触及上限不等于没有泄漏**；这正是第二个对照的学习价值。

| JSON 字段 | 含义 | 应如何使用 |
| --- | --- | --- |
| limit | 本例 NOFILE=64 | 与进程真实限制/trace 核对 |
| requested / delay_ms | 业务量与每次延迟 | 与 run.info 参数一致 |
| baseline | 开始时 0..63 内已打开数量 | 不硬编码为 3 |
| completed | 成功打开并处理的请求数 | 默认修复版应为 128 |
| peak_open | 观察范围内的峰值 | 故障达到 64，修复至多 baseline+1 |
| final_open | 进程退出前的数量 | 修复回到 baseline，故障仍保留引用 |
| error | 最后一次操作错误 | 0 或本例 EMFILE=24，与 trace/退出匹配 |

`check` 严格核对参数、容量关系、完成量、峰值、最终值和各子进程退出码。JSON 是
业务证据，strace 与 `/proc` 是独立观测；不能只靠程序自报值就推断任意代码没有泄漏。
一个充分的修复还应覆盖成功、错误、提前返回、取消和对象移交路径的资源所有权。

## 实机证据与反例

### 2.9 容易混淆的情况与迁移

- 合理保留一个有上限的连接池，不等于泄漏；看规模是否有界、空闲回收和所有权。
- TCP TIME_WAIT 是协议连接状态，不等同于某个进程仍持有一个 socket FD。
- 日志轮转后显示 deleted 的文件仍可能由服务持有；unlink 不是 close，磁盘空间
  也可能因此尚未回收，需要检查对应 FD，而不是反复删除同一路径。
- 提高 NOFILE 可满足合理并发需求，但本例每请求泄漏一个，容量提高只延后失败。
- select 的可用范围与进程 NOFILE 不是同一个约束；不能提升限制后假设所有 API
  自动支持更多编号。真实服务要结合它使用的 I/O 模型单独分析。

扩展练习仅作源码与小规模观察，不要求耗尽系统资源：为错误返回路径增加一次未关闭
的 open；思考 socket/accept 和 fopen/fclose 应如何遵守相同所有权；解释 fork/exec
对描述符的不同影响。完成 [[附录A-实验报告/00-章节导航|报告模板]]，写出两条相近原因
如何被证据排除。

### 2.11 一次实机证据的完整判读

2026-11-09，AM625、固件 `v0.0.1 / 668ad82f`，默认统一入口故障版输出：

故障版实机摘要：核对 FD 上限、已完成请求数、最终占用和 error=24。

```json
{"limit":64,"requested":128,"delay_ms":20,"baseline":3,"completed":61,"peak_open":64,"final_open":64,"error":24}
```

先核对输入 128/20，再计算可分配容量 `64-3=61`，恰好等于 completed。最终占用
64 且 error=24，支持容量耗尽；仍需检查是否真的是业务 open 失败而不是程序自造错误。
另一次相同二进制的小延迟 strace 实机摘录为：

实机 strace 摘录：把 RLIMIT_NOFILE=64、FD 编号增长与最终 EMFILE 关联起来。

```text
926   16:12:45.518412 prlimit64(0, RLIMIT_NOFILE, {rlim_cur=64, rlim_max=64}, NULL) = 0 <0.000029>
926   16:12:45.522128 openat(AT_FDCWD, "/dev/null", O_RDONLY|O_CLOEXEC) = 3 <0.000104>
926   16:12:45.741985 openat(AT_FDCWD, "/dev/null", O_RDONLY|O_CLOEXEC) = 63 <0.000063>
926   16:12:45.745692 openat(AT_FDCWD, "/dev/null", O_RDONLY|O_CLOEXEC) = -1 EMFILE (Too many open files) <0.000032>
```

中间重复调用省略；这是 trace 的实际 PID/时间，不是要求每次都出现的常量。
该 trace 中业务成功 open 61 次，业务开始后没有 close。另一组在线观察中，对同一
存活 PID 两次读取 `/proc/PID/fd`，指向 /dev/null 的条目从 3 增至 24；这个计数包括
已有相同目标的引用，所以不把它当作“新泄漏请求数”，只用来证明增长趋势。

参考版同参数的 JSON 为：

参考版实机摘要：核对全部请求完成、final_open 回到 baseline 且 error=0。

```json
{"limit":64,"requested":128,"delay_ms":20,"baseline":3,"completed":128,"peak_open":4,"final_open":3,"error":0}
```

strace 独立确认业务 open 和 close 各 128 次；最终回到 baseline，且请求量没有减少。
对照 `run fd 4 0`，故障版 completed=4、final_open=7、error=0，证明错误是否出现取决于
是否撞到容量，而泄漏在更早就已经存在。最后核对父 shell 限制、全局 file-max 和管理
网口不变，以及设备健康确认仍正常，完成从现象到机制、修复和复位的证据链。

trace 开头还出现 `/etc/ld.so.cache` 的 ENOENT，随后 libc 正常打开并加载。这说明
“日志里有一个失败调用”不等于它就是根因：加载器可以有正常回退路径。要看失败后
是否恢复，以及业务真正终止处的错误。进程退出时内核自动释放剩余 FD，不要求 strace
出现每个资源的显式 close 调用；本例比较的是请求生命周期内是否主动归还。

[[附录A-实验报告/00-章节导航|实验报告与复盘]] · [[00-实验准备与通用方法/01-构建与启动部署#源码与实机证据|匹配源码、固件与实测证据]]

[[02-文件描述符/B-FD02-dup别名使文件描述符持续增长/B-FD02：dup 别名使文件描述符持续增长|下一例 B-FD02]]
