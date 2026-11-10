[[README|首页]] · [[00-实验准备与通用方法/工具索引|工具索引]] · [[00-实验准备与通用方法/案例索引|案例索引]]

## 解决的问题

检查实际生成的机器指令、调用顺序和函数内偏移。

## 工作原理与准备

反汇编说明编译产物里有哪些指令；是否实际走过某个分支仍须寄存器、断点、采样或跟踪证据。

## 参数与结果解释

| 参数/字段 | 含义与判断方法 |
| --- | --- |
| `-d` | 反汇编代码节。 |
| `-S` | 尽可能混排源码，需要匹配调试信息。 |
| `-r` | 显示重定位信息，模块/目标文件分析常用。 |
| `--disassemble=FUNC` | 限定到目标函数，减少无关输出。 |

## 操作步骤

主机端：定位故障版字段读取指令。

```sh
output/am625-debug-systemd/host/bin/aarch64-buildroot-linux-gnu-objdump -d --disassemble=process_request output/am625-debug-systemd/images/debug/labs/crash-bug
```

主机端：用同次构建的参考 ELF 比较检查分支。

```sh
output/am625-debug-systemd/host/bin/aarch64-buildroot-linux-gnu-objdump -d --disassemble=process_request output/am625-debug-systemd/images/debug/labs/crash-fixed
```

## 判断边界

函数内 offset 与绝对 PC 分开。模块运行地址需要本次装载基址；跨版本比较优先按控制流和符号，不逐地址硬对齐。

## 使用场景

下面链接直达具体案例的定位章节。基础流程沿用实机验收，扩展工具观测不自动记作已执行。

| 案例 | 本工具的观测目标 |
| --- | --- |
| [[01-应用崩溃/B-CR01-缺失记录未判空导致空指针崩溃/B-CR01：缺失记录导致应用崩溃#定位方法\|B-CR01：缺失记录导致应用崩溃]] | 把故障机制对应到真实指令与分支 |
| [[02-文件描述符/B-FD01-循环打开文件未关闭导致FD耗尽/B-FD01：文件描述符泄漏与耗尽#定位方法\|B-FD01：文件描述符泄漏与耗尽]] | 把故障机制对应到真实指令与分支 |
| [[04-CPU性能与火焰图/B-CPU01-重复线性查找导致CPU热点/B-CPU01：CPU热点与火焰图#定位方法\|B-CPU01：CPU热点与火焰图]] | 把故障机制对应到真实指令与分支 |
| [[07-内核启动与恢复/B-BOOT01-内核panic触发后的启动日志取证与恢复/B-BOOT01：内核panic启动日志与恢复#定位方法\|B-BOOT01：内核panic启动日志与恢复]] | 把故障机制对应到真实指令与分支 |
| [[07-内核启动与恢复/B-BOOT02-initramfs动态加载器缺库导致PID1退出/B-BOOT02：initramfs 动态加载器缺库导致 PID 1 退出#定位方法\|B-BOOT02：initramfs 动态加载器缺库导致 PID 1 退出]] | 把故障机制对应到真实指令与分支 |
| [[07-内核启动与恢复/B-BOOT03-根设备或文件系统参数错误导致VFS启动失败/B-BOOT03：根设备或文件系统参数错误导致 VFS 启动失败#定位方法\|B-BOOT03：根设备或文件系统参数错误导致 VFS 启动失败]] | 把故障机制对应到真实指令与分支 |
| [[07-内核启动与恢复/B-BOOT04-内核Oops与panic策略的区别/B-BOOT04：内核 Oops 与 panic 策略的区别#定位方法\|B-BOOT04：内核 Oops 与 panic 策略的区别]] | 把故障机制对应到真实指令与分支 |
| [[07-内核启动与恢复/B-BOOT05-soft-lockup、RCU-stall与硬件watchdog复位归因/B-BOOT05：soft lockup、RCU stall 与硬件 watchdog 复位归因#定位方法\|B-BOOT05：soft lockup、RCU stall 与硬件 watchdog 复位归因]] | 把故障机制对应到真实指令与分支 |
