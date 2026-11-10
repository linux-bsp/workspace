[[README|首页]] · [[00-实验准备与通用方法/案例索引|案例索引]] · [[00-实验准备与通用方法/工具索引|工具索引]] · [[07-内核启动与恢复/00-章节导航|章节导航]]

先按现象提出假设并完成练习，再核对定位、内核机制和参考修复。`verify` 验证镜像提供的参考实现。

[[07-内核启动与恢复/B-BOOT02-initramfs动态加载器缺库导致PID1退出/B-BOOT02：initramfs 动态加载器缺库导致 PID 1 退出#现象与原理|现象与原理]] · [[07-内核启动与恢复/B-BOOT02-initramfs动态加载器缺库导致PID1退出/B-BOOT02：initramfs 动态加载器缺库导致 PID 1 退出#练习任务|练习任务]] · [[07-内核启动与恢复/B-BOOT02-initramfs动态加载器缺库导致PID1退出/B-BOOT02：initramfs 动态加载器缺库导致 PID 1 退出#使用工具|使用工具]] · [[07-内核启动与恢复/B-BOOT02-initramfs动态加载器缺库导致PID1退出/B-BOOT02：initramfs 动态加载器缺库导致 PID 1 退出#定位方法|定位方法]] · [[07-内核启动与恢复/B-BOOT02-initramfs动态加载器缺库导致PID1退出/B-BOOT02：initramfs 动态加载器缺库导致 PID 1 退出#内核流程与汇编|内核流程与汇编]] · [[07-内核启动与恢复/B-BOOT02-initramfs动态加载器缺库导致PID1退出/B-BOOT02：initramfs 动态加载器缺库导致 PID 1 退出#修复与验收|修复与验收]]

## 现象与原理

**生产现场与异常现象。** OTA 后 Run /init 紧接 loader error，随后 Attempted to kill init；表面是 kernel panic，根因可能在打包。

**原理与容易误判的地方。** 内核执行 /init 后动态加载器先工作；缺库时业务 main 可能尚未运行。真正的系统 PID 1 退出会进入 do_exit 的特殊保护并 panic。该链路与 init 程序自己发生空指针不同。

## 练习任务

**复现条件与故障注入。** 在 AM625 的 RAM-only initramfs 副本移除专用 DT_NEEDED 库，保留健康副本；用 WDT 与保存的正常网络启动配置恢复，不写坏 SD 分区，不以 PID namespace 替代整机 panic。 操作前记录版本/构建 ID、boot ID、输入、资源上限和超时。内核/启动故障会影响整机；核对完整固件 ID、WDT 与保存的正常启动路径。

**面试/评审追问。** 为什么 /init 存在仍可能 ENOENT？ELF 解释器缺失与共享库缺失的表现有什么区别？ 请提交：候选假设、可证伪实验、原始数据、关键源码分支、修复前后对照和未覆盖边界。只给一个参数调整或一个“修好了”的截图不算完成。

## 使用工具

通用原理、参数和使用边界见工具手册；具体命令与证据判断见本例定位方法。

[[工具手册/sadboard|sadboard]] · [[工具手册/GDB|GDB]] · [[工具手册/readelf|readelf]] · [[工具手册/nm|nm]] · [[工具手册/objdump|objdump]] · [[工具手册/addr2line|addr2line]] · [[工具手册/logctl|logctl]]

## 定位方法

**定位分析流程。** 按时间保存最早 loader 错误，readelf -l/-d 核对解释器与 DT_NEEDED，解包 initramfs 核对文件/符号链接/架构。不要只解码最后的 panic 栈。 对照上方工具手册逐项说明命令回答了什么问题；信号/退出码、资源计数、业务完成数和时间轴必须能互相验证。优化前后采用同输入，至少保留一次负例，排除“异常只是没有触发”。

参数查阅：[[07-内核启动与恢复/B-BOOT01-内核panic触发后的启动日志取证与恢复/B-BOOT01：内核panic启动日志与恢复#定位方法|本方向基础工具参数与边界]]。

## 内核流程与汇编

**内核阅读入口。** [exec.c](https://github.com/linux-bsp/linux-7.0/blob/master/fs/exec.c)：bprm_execve；[binfmt_elf.c](https://github.com/linux-bsp/linux-7.0/blob/master/fs/binfmt_elf.c)：load_elf_binary；[exit.c](https://github.com/linux-bsp/linux-7.0/blob/master/kernel/exit.c)：do_exit；[panic.c](https://github.com/linux-bsp/linux-7.0/blob/master/kernel/panic.c)：panic。先确认用户态接口或信号，再向对应内核分支追踪；这些是本仓库 Linux 7.0 的源码入口，不是已经采集到的动态调用栈。

## 修复与验收

**修复方案与代价。** 构建时递归检查依赖闭包，在真实 AM625 的 RAM 副本实际启动 /init；不要用从另一版 rootfs 拷贝单个 so 的方式形成混合 ABI。

**量化验收与现场恢复。** 缺库故障在真实设备稳定可复现，完整副本可启动；依赖检查在打包阶段拒绝缺失文件。 最后核对恢复启动的固件身份、健康检查与日志归档；不清除系统历史记录。

[[附录A-实验报告/00-章节导航|实验报告与复盘]] · [[00-实验准备与通用方法/01-构建与启动部署#源码与实机证据|匹配源码、固件与实测证据]]

[[07-内核启动与恢复/B-BOOT01-内核panic触发后的启动日志取证与恢复/B-BOOT01：内核panic启动日志与恢复|上一例 B-BOOT01]] · [[07-内核启动与恢复/B-BOOT03-根设备或文件系统参数错误导致VFS启动失败/B-BOOT03：根设备或文件系统参数错误导致 VFS 启动失败|下一例 B-BOOT03]]
