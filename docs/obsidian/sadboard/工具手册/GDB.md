[[README|首页]] · [[00-实验准备与通用方法/工具索引|工具索引]] · [[00-实验准备与通用方法/案例索引|案例索引]]

## 解决的问题

应用崩溃、线程等待、变量与寄存器取证，以及匹配 ELF 的 core/反汇编分析。

## 工作原理与准备

主机交叉 GDB 解释目标架构、DWARF 和寄存器；设备 gdbserver 负责控制进程。sysroot 提供目标库/程序，substitute-path 提供编译时源文件，两者职责不同。

## 常用命令与参数

| 命令/参数 | 用途与使用时机 |
| --- | --- |
| `set sysroot ROOT` | 在 ROOT 下按目标的绝对路径查找库/程序；在线可用 staging，离线 PIE 分析优先使用完整目标根目录 |
| `set substitute-path OLD NEW` | 将 DWARF 中的编译源码前缀映射到本机源码副本，不替代 sysroot |
| `target remote IP:PORT` | 连接 gdbserver；已启动程序用 continue，而非另起 run |
| `break FUNC` / `break FILE:LINE` | 在函数或具体源行停住，缩小故障时间窗 |
| `ignore N COUNT` | 忽略编号 N 的断点前 COUNT 次命中 |
| `continue` / `next` / `step` | 继续执行、源码层越过函数、源码层进入函数 |
| `finish` / `return` | 前者执行到当前函数返回；后者强行返回，会修改行为，取证时慎用 |
| `bt full` / `frame N` | 看调用链及局部变量，再选择具体帧 |
| `info args` / `info locals` | 检查输入与当前帧的局部状态 |
| `print EXPR` / `print /x EXPR` | 按类型或十六进制读变量；不要随意解引用可疑指针 |
| `info registers` / `x/i $pc` | 将现场寄存器与出错机器指令对应 |
| `disassemble /s FUNC` | 混合源行与反汇编；优化构建可能不能逐行对应 |
| `info threads` / `thread N` | 选择线程；GDB 线程编号不同于 Linux TID |
| `thread apply all bt` | 同时查看线程的等待关系 |
| `set follow-fork-mode child` | fork 后优先跟踪子进程，适合 case-suite 的故障现场 |
| `set detach-on-fork off` | 同时保留父子进程的调试控制；需结合 inferior 状态管理执行与清理 |
| `info inferiors` | 检查 GDB 管理的进程；与线程列表不同，退出前确认实验进程已结束 |
| `core-file PATH` | 载入离线 core；不能在 core 上 continue |
| `set pagination off` / `--batch -ex CMD` | 关闭分页、自动化取证并保存输出 |

先看 frame 0，再看调用者如何产生错误状态。`<optimized out>` 可能来自编译优化；
`??` 可能来自缺符号或地址重定位失败；两者都不直接说明栈损坏。
GDB 的帧含义与回溯选项参见 [官方回溯说明](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Backtrace.html)。

## 操作步骤

主机端：从工作区根目录加载同次构建的故障 ELF。

```sh
output/am625-debug-systemd/host/bin/aarch64-buildroot-linux-gnu-gdb output/am625-debug-systemd/images/debug/labs/crash-bug
```

主机 GDB：批量设置库和源码路径，先替换本机绝对路径。

```gdb
set pagination off
set sysroot /path/to/SadBoard/output/am625-debug-systemd/staging
set substitute-path /usr/src/sadboard /path/to/SadBoard/output/am625-debug-systemd/images/debug/source
```

主机 GDB：连接已在板端等待的 gdbserver，确认停止位置后再继续。

```gdb
target remote 192.168.10.211:22345
```

主机 GDB：继续到断点或信号，记录实际停止原因。

```gdb
continue
```

主机 GDB：查看调用栈与局部量，先找到业务帧。

```gdb
bt full
```

主机 GDB：查看所有线程的等待关系。

```gdb
thread apply all bt
```

## 跟踪 case-suite 的故障子进程

`case-suite` 的故障通常发生在子进程中，只观察最外层父进程可能看不到断言或信号。
以下用 [[01-应用崩溃/B-CR02-配置状态不一致触发SIGABRT/B-CR02：配置状态不一致触发 SIGABRT#定位方法|B-CR02 的 SIGABRT]] 演示；
完整交叉 GDB 运行在主机，设备仅运行 gdbserver。手工单步与受监督的 `sadboard run`
分开执行，先从工作区根目录加载这次构建的真实 ELF、库和源码。

设备端：查询当前结果根目录并保存到 R，后面的手工取证使用同一位置。

```sh
R=$(sadboard results)
```

设备端：创建手工 SIGABRT 现场目录，供远程调试子进程保存证据。

```sh
mkdir -p "$R/manual-abort"
```

主机端：加载本次构建的 case-suite 符号文件，准备跟踪故障子进程。

```sh
output/am625-debug-systemd/host/bin/aarch64-buildroot-linux-gnu-gdb \
  output/am625-debug-systemd/images/debug/labs/case-suite
```

主机 GDB：批量设置匹配的库/源码路径、跟随子进程，并保留父子进程的调试控制，随后再连接目标。

```gdb
set sysroot output/am625-debug-systemd/staging
set substitute-path /usr/src/sadboard output/am625-debug-systemd/images/debug/source
set follow-fork-mode child
set detach-on-fork off
```

主机 GDB：通过 SSH 管道启动远程 gdbserver。下面按 NFS 结果根目录示例，最后一个参数必须与设备端创建的目录一致；本地 SD 根改为 `/data/sadboard/manual-abort`。

```gdb
target remote | ssh -T root@192.168.10.211 gdbserver --once - /usr/libexec/sadboard/case-suite crash-abort bug /srv/sadboard/manual-abort
```

主机 GDB：在 fault_child 设置断点，确认实际解析的源码位置。

```gdb
break fault_child
```

主机 GDB：继续到断点或信号，先检查停止原因再解释断言。

```gdb
continue
```

主机 GDB：打印带局部变量的调用栈，沿配置状态不一致的业务路径回溯。

```gdb
bt full
```

stdio 通道不需要另开调试端口；SSH 主机指纹按现有环境核对。`set detach-on-fork off`
保留父子进程在 GDB 控制下，父进程停住期间不会由它的短实验计时器杀掉正在单步的子进程。
退出前用 `info inferiors` 检查并终止自己创建的 inferior，或让它们完整结束；此方法已在
AM625 实测跟进到 `fault_child`。

普通 CPU/memory/sync 流程可在 `suite_cpu/suite_mem/suite_sync` 设断点。网络/CLOSE_WAIT
手工单步只在自建 namespace 中运行 gdbserver，仍可用相同 SSH stdio 通道连接，结束后
删除自己的空间。PMTU/RPS/优先队列入口自动保存 pcap、qdisc 和对端证据；先用 tcpdump
离线分析，再按 `run-network-suite` 的拓扑复现。GDB、strace/Valgrind、原生性能基准
分开执行，手工结果用 `sadboard share 目录` 开放 host 读取。

## 判断边界

在线暂停会改变线程、超时和外部设备交互。core 是静态快照，无法继续执行。PIE/KASLR 的运行地址必须结合装载偏移解释；优化导致的 optimized out 与缺符号导致的 ?? 分开处理。

## 使用场景

下面链接直达具体案例的定位章节。基础流程沿用实机验收，扩展工具观测不自动记作已执行。

| 案例 | 本工具的观测目标 |
| --- | --- |
| [[01-应用崩溃/B-CR01-缺失记录未判空导致空指针崩溃/B-CR01：缺失记录导致应用崩溃#定位方法\|B-CR01：缺失记录导致应用崩溃]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[01-应用崩溃/B-CR02-配置状态不一致触发SIGABRT/B-CR02：配置状态不一致触发 SIGABRT#定位方法\|B-CR02：配置状态不一致触发 SIGABRT]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[01-应用崩溃/B-CR03-堆越界写延迟破坏邻接对象/B-CR03：堆越界写延迟破坏邻接对象#定位方法\|B-CR03：堆越界写延迟破坏邻接对象]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[01-应用崩溃/B-CR04-递归或大栈数组耗尽工作线程栈/B-CR04：递归或大栈数组耗尽工作线程栈#定位方法\|B-CR04：递归或大栈数组耗尽工作线程栈]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[01-应用崩溃/B-CR05-mmap文件截断引发SIGBUS/B-CR05：mmap 文件截断引发 SIGBUS#定位方法\|B-CR05：mmap 文件截断引发 SIGBUS]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[02-文件描述符/B-FD03-exec继承管道写端导致读者等不到EOF/B-FD03：exec 继承管道写端导致读者等不到 EOF#定位方法\|B-FD03：exec 继承管道写端导致读者等不到 EOF]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[04-CPU性能与火焰图/B-CPU04-错误订阅EPOLLOUT导致空转/B-CPU04：错误订阅 EPOLLOUT 导致空转#定位方法\|B-CPU04：错误订阅 EPOLLOUT 导致空转]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[05-锁与线程调度/B-SYNC01-持锁执行慢操作导致线程串行等待/B-SYNC01：持锁等待与线程调度#定位方法\|B-SYNC01：持锁等待与线程调度]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[05-锁与线程调度/B-SYNC02-ABBA锁顺序造成互相等待/B-SYNC02：ABBA 锁顺序造成互相等待#定位方法\|B-SYNC02：ABBA 锁顺序造成互相等待]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[05-锁与线程调度/B-SYNC03-条件变量丢失唤醒/B-SYNC03：条件变量丢失唤醒#定位方法\|B-SYNC03：条件变量丢失唤醒]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[05-锁与线程调度/B-SYNC04-分开的检查与更新导致逻辑丢失/B-SYNC04：分开的检查与更新导致逻辑丢失#定位方法\|B-SYNC04：分开的检查与更新导致逻辑丢失]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[05-锁与线程调度/B-SYNC05-退出路径等待一个永不完成的工作线程/B-SYNC05：退出路径等待一个永不完成的工作线程#定位方法\|B-SYNC05：退出路径等待一个永不完成的工作线程]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[06-网络分析/B-NET03-长度字段端序错误放大内存请求/B-NET03：长度字段端序错误放大内存请求#定位方法\|B-NET03：长度字段端序错误放大内存请求]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[07-内核启动与恢复/B-BOOT01-内核panic触发后的启动日志取证与恢复/B-BOOT01：内核panic启动日志与恢复#定位方法\|B-BOOT01：内核panic启动日志与恢复]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[07-内核启动与恢复/B-BOOT02-initramfs动态加载器缺库导致PID1退出/B-BOOT02：initramfs 动态加载器缺库导致 PID 1 退出#定位方法\|B-BOOT02：initramfs 动态加载器缺库导致 PID 1 退出]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[07-内核启动与恢复/B-BOOT03-根设备或文件系统参数错误导致VFS启动失败/B-BOOT03：根设备或文件系统参数错误导致 VFS 启动失败#定位方法\|B-BOOT03：根设备或文件系统参数错误导致 VFS 启动失败]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[07-内核启动与恢复/B-BOOT04-内核Oops与panic策略的区别/B-BOOT04：内核 Oops 与 panic 策略的区别#定位方法\|B-BOOT04：内核 Oops 与 panic 策略的区别]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[07-内核启动与恢复/B-BOOT05-soft-lockup、RCU-stall与硬件watchdog复位归因/B-BOOT05：soft lockup、RCU stall 与硬件 watchdog 复位归因#定位方法\|B-BOOT05：soft lockup、RCU stall 与硬件 watchdog 复位归因]] | 检查业务调用栈、变量、寄存器或线程等待关系 |

## 参考资料

[GDB 官方手册](https://sourceware.org/gdb/current/onlinedocs/gdb.html/)
