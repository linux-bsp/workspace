# GDB

[[首页]] · [[工具索引]] · [[案例索引]]

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

## 判断边界

在线暂停会改变线程、超时和外部设备交互。core 是静态快照，无法继续执行。PIE/KASLR 的运行地址必须结合装载偏移解释；优化导致的 optimized out 与缺符号导致的 ?? 分开处理。

## 使用场景

下面链接直达具体案例的定位章节。基础流程沿用实机验收，扩展工具观测不自动记作已执行。

| 案例 | 本工具的观测目标 |
| --- | --- |
| [[01-应用崩溃/B-CR01-缺失记录未判空导致空指针崩溃/案例详解#定位方法\|B-CR01：缺失记录导致应用崩溃]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[01-应用崩溃/B-CR02-配置状态不一致触发SIGABRT/案例详解#定位方法\|B-CR02：配置状态不一致触发 SIGABRT]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[01-应用崩溃/B-CR03-堆越界写延迟破坏邻接对象/案例详解#定位方法\|B-CR03：堆越界写延迟破坏邻接对象]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[01-应用崩溃/B-CR04-递归或大栈数组耗尽工作线程栈/案例详解#定位方法\|B-CR04：递归或大栈数组耗尽工作线程栈]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[01-应用崩溃/B-CR05-mmap文件截断引发SIGBUS/案例详解#定位方法\|B-CR05：mmap 文件截断引发 SIGBUS]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[02-文件描述符/B-FD03-exec继承管道写端导致读者等不到EOF/案例详解#定位方法\|B-FD03：exec 继承管道写端导致读者等不到 EOF]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[04-CPU性能与火焰图/B-CPU04-错误订阅EPOLLOUT导致空转/案例详解#定位方法\|B-CPU04：错误订阅 EPOLLOUT 导致空转]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[05-锁与线程调度/B-SYNC01-持锁执行慢操作导致线程串行等待/案例详解#定位方法\|B-SYNC01：持锁等待与线程调度]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[05-锁与线程调度/B-SYNC02-ABBA锁顺序造成互相等待/案例详解#定位方法\|B-SYNC02：ABBA 锁顺序造成互相等待]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[05-锁与线程调度/B-SYNC03-条件变量丢失唤醒/案例详解#定位方法\|B-SYNC03：条件变量丢失唤醒]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[05-锁与线程调度/B-SYNC04-分开的检查与更新导致逻辑丢失/案例详解#定位方法\|B-SYNC04：分开的检查与更新导致逻辑丢失]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[05-锁与线程调度/B-SYNC05-退出路径等待一个永不完成的工作线程/案例详解#定位方法\|B-SYNC05：退出路径等待一个永不完成的工作线程]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[06-网络分析/B-NET03-长度字段端序错误放大内存请求/案例详解#定位方法\|B-NET03：长度字段端序错误放大内存请求]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[07-内核启动与恢复/B-BOOT01-内核panic触发后的启动日志取证与恢复/案例详解#定位方法\|B-BOOT01：内核panic启动日志与恢复]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[07-内核启动与恢复/B-BOOT02-initramfs动态加载器缺库导致PID1退出/案例详解#定位方法\|B-BOOT02：initramfs 动态加载器缺库导致 PID 1 退出]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[07-内核启动与恢复/B-BOOT03-根设备或文件系统参数错误导致VFS启动失败/案例详解#定位方法\|B-BOOT03：根设备或文件系统参数错误导致 VFS 启动失败]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[07-内核启动与恢复/B-BOOT04-内核Oops与panic策略的区别/案例详解#定位方法\|B-BOOT04：内核 Oops 与 panic 策略的区别]] | 检查业务调用栈、变量、寄存器或线程等待关系 |
| [[07-内核启动与恢复/B-BOOT05-soft-lockup、RCU-stall与硬件watchdog复位归因/案例详解#定位方法\|B-BOOT05：soft lockup、RCU stall 与硬件 watchdog 复位归因]] | 检查业务调用栈、变量、寄存器或线程等待关系 |

## 参考资料

[GDB 官方手册](https://sourceware.org/gdb/current/onlinedocs/gdb.html/)
