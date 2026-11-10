[[首页]] · [[案例索引]] · [[工具索引]] · [[07-内核启动与恢复/00-章节导航|章节导航]]

先按现象提出假设并完成练习，再核对定位、内核机制和参考修复。`verify` 验证镜像提供的参考实现。

[[07-内核启动与恢复/B-BOOT05-soft-lockup、RCU-stall与硬件watchdog复位归因/B-BOOT05：soft lockup、RCU stall 与硬件 watchdog 复位归因#现象与原理|现象与原理]] · [[07-内核启动与恢复/B-BOOT05-soft-lockup、RCU-stall与硬件watchdog复位归因/B-BOOT05：soft lockup、RCU stall 与硬件 watchdog 复位归因#练习任务|练习任务]] · [[07-内核启动与恢复/B-BOOT05-soft-lockup、RCU-stall与硬件watchdog复位归因/B-BOOT05：soft lockup、RCU stall 与硬件 watchdog 复位归因#使用工具|使用工具]] · [[07-内核启动与恢复/B-BOOT05-soft-lockup、RCU-stall与硬件watchdog复位归因/B-BOOT05：soft lockup、RCU stall 与硬件 watchdog 复位归因#定位方法|定位方法]] · [[07-内核启动与恢复/B-BOOT05-soft-lockup、RCU-stall与硬件watchdog复位归因/B-BOOT05：soft lockup、RCU stall 与硬件 watchdog 复位归因#内核流程与汇编|内核流程与汇编]] · [[07-内核启动与恢复/B-BOOT05-soft-lockup、RCU-stall与硬件watchdog复位归因/B-BOOT05：soft lockup、RCU stall 与硬件 watchdog 复位归因#修复与验收|修复与验收]]

## 现象与原理

**生产现场与异常现象。** 系统卡顿后重启，只有 watchdog 标签时难以知道是 CPU 死循环、调度阻塞还是喂狗链路失败。

**原理与容易误判的地方。** soft lockup、hard lockup、RCU stall 和硬件 watchdog 的检测对象与时钟不同。CPU 百分百的普通用户进程通常仍可被抢占，并不自动等于内核 soft lockup。

## 练习任务

**复现条件与故障注入。** 先在真实 AM625 验证硬件 WDT，随后由手动内核模块触发有界 soft lockup 与全 CPU 禁中断锁死，由 WDT 复位；必须核对检测器配置与真实日志。 操作前记录版本/构建 ID、boot ID、输入、资源上限和超时。内核/启动故障会影响整机；核对完整固件 ID、WDT 与保存的正常启动路径。

**面试/评审追问。** CPU 满载、任务 D 状态、RCU stall 和 watchdog 触发可以互相等价吗？ 请提交：候选假设、可证伪实验、原始数据、关键源码分支、修复前后对照和未覆盖边界。只给一个参数调整或一个“修好了”的截图不算完成。

## 使用工具

通用原理、参数和使用边界见工具手册；具体命令与证据判断见本例定位方法。

[[工具手册/sadboard|sadboard]] · [[工具手册/GDB|GDB]] · [[工具手册/objdump|objdump]] · [[工具手册/addr2line|addr2line]] · [[工具手册/logctl|logctl]]

## 定位方法

**定位分析流程。** 关联最早 stall/lockup 文本、每 CPU 栈、调度事件、最后业务心跳、boot/reset 记录和 pstore；单独的 reset cause 不足以确认具体软件根因。 对照上方工具手册逐项说明命令回答了什么问题；信号/退出码、资源计数、业务完成数和时间轴必须能互相验证。优化前后采用同输入，至少保留一次负例，排除“异常只是没有触发”。

参数查阅：[[07-内核启动与恢复/B-BOOT01-内核panic触发后的启动日志取证与恢复/B-BOOT01：内核panic启动日志与恢复#定位方法|本方向基础工具参数与边界]]。

## 内核流程与汇编

**内核阅读入口。** [watchdog.c](https://github.com/linux-bsp/linux-7.0/blob/master/kernel/watchdog.c)：soft lockup 检测；[tree_stall.h](https://github.com/linux-bsp/linux-7.0/blob/master/kernel/rcu/tree_stall.h)：RCU stall 检查；[watchdog_core.c](https://github.com/linux-bsp/linux-7.0/blob/master/drivers/watchdog/watchdog_core.c)：硬件 watchdog 设备框架。先确认用户态接口或信号，再向对应内核分支追踪；这些是本仓库 Linux 7.0 的源码入口，不是已经采集到的动态调用栈。

## 修复与验收

**修复方案与代价。** 修复长时间不可调度区间，设计健康评估与喂狗职责，并验证日志在复位前后的接力；不能只延长 watchdog 超时。

**量化验收与现场恢复。** 受控故障原因与复位证据对应，健康负载不误复位；检测器不可用、断电 RAM 不保留等边界单独标记。 最后核对恢复启动的固件身份、健康检查与日志归档；不清除系统历史记录。

[[附录A-实验报告/00-章节导航|实验报告与复盘]] · [[00-实验准备与通用方法/01-构建与启动部署#源码与实机证据|匹配源码、固件与实测证据]]

[[07-内核启动与恢复/B-BOOT04-内核Oops与panic策略的区别/B-BOOT04：内核 Oops 与 panic 策略的区别|上一例 B-BOOT04]]
