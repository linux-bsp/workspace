# addr2line

[[首页]] · [[工具索引]] · [[案例索引]]

## 解决的问题

把已正确换算的 ELF 地址映射到函数和源码位置。

## 工作原理与准备

依赖匹配的 ELF 与 DWARF。日志中的 func+offset 可结合符号起点计算；PIE、共享库和 KASLR 的绝对 PC 要先处理装载偏移。

## 参数与结果解释

| 参数/字段 | 含义与判断方法 |
| --- | --- |
| `-e ELF` | 指定精确匹配的符号文件。 |
| `-f` | 显示函数名。 |
| `-C` | 解释修饰名。 |
| `ADDRESS` | 提供该 ELF 的链接地址，不能直接混入其他构建的 PC。 |

## 操作步骤

主机端：先将 address 设置为本次 nm/objdump 确认的 ELF 链接地址，再查询源码。

```sh
output/am625-debug-systemd/host/bin/aarch64-buildroot-linux-gnu-addr2line -e output/am625-debug-systemd/images/debug/labs/crash-bug -f -C "$address"
```

## 判断边界

?? 可能由缺失调试信息、错误地址空间或版本不匹配导致。内核 func+offset 的批量解码流程见启动异常案例及 [[工具手册/GDB]]。

## 使用场景

下面链接直达具体案例的定位章节。基础流程沿用实机验收，扩展工具观测不自动记作已执行。

| 案例 | 本工具的观测目标 |
| --- | --- |
| [[01-应用崩溃/B-CR01-缺失记录未判空导致空指针崩溃/案例详解#定位方法\|B-CR01：缺失记录导致应用崩溃]] | 用匹配 ELF 解释已换算的函数/源码地址 |
| [[04-CPU性能与火焰图/B-CPU01-重复线性查找导致CPU热点/案例详解#定位方法\|B-CPU01：CPU热点与火焰图]] | 用匹配 ELF 解释已换算的函数/源码地址 |
| [[07-内核启动与恢复/B-BOOT01-内核panic触发后的启动日志取证与恢复/案例详解#定位方法\|B-BOOT01：内核panic启动日志与恢复]] | 用匹配 ELF 解释已换算的函数/源码地址 |
| [[07-内核启动与恢复/B-BOOT02-initramfs动态加载器缺库导致PID1退出/案例详解#定位方法\|B-BOOT02：initramfs 动态加载器缺库导致 PID 1 退出]] | 用匹配 ELF 解释已换算的函数/源码地址 |
| [[07-内核启动与恢复/B-BOOT03-根设备或文件系统参数错误导致VFS启动失败/案例详解#定位方法\|B-BOOT03：根设备或文件系统参数错误导致 VFS 启动失败]] | 用匹配 ELF 解释已换算的函数/源码地址 |
| [[07-内核启动与恢复/B-BOOT04-内核Oops与panic策略的区别/案例详解#定位方法\|B-BOOT04：内核 Oops 与 panic 策略的区别]] | 用匹配 ELF 解释已换算的函数/源码地址 |
| [[07-内核启动与恢复/B-BOOT05-soft-lockup、RCU-stall与硬件watchdog复位归因/案例详解#定位方法\|B-BOOT05：soft lockup、RCU stall 与硬件 watchdog 复位归因]] | 用匹配 ELF 解释已换算的函数/源码地址 |
