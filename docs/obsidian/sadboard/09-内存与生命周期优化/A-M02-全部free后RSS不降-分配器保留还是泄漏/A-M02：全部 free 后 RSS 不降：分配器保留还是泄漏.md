[[README|首页]] · [[00-实验准备与通用方法/案例索引|案例索引]] · [[00-实验准备与通用方法/工具索引|工具索引]] · [[09-内存与生命周期优化/00-章节导航|章节导航]]

先按现象提出假设并完成练习，再核对定位、内核机制和参考修复。`verify` 验证镜像提供的参考实现。

[[09-内存与生命周期优化/A-M02-全部free后RSS不降-分配器保留还是泄漏/A-M02：全部 free 后 RSS 不降：分配器保留还是泄漏#现象与原理|现象与原理]] · [[09-内存与生命周期优化/A-M02-全部free后RSS不降-分配器保留还是泄漏/A-M02：全部 free 后 RSS 不降：分配器保留还是泄漏#练习任务|练习任务]] · [[09-内存与生命周期优化/A-M02-全部free后RSS不降-分配器保留还是泄漏/A-M02：全部 free 后 RSS 不降：分配器保留还是泄漏#使用工具|使用工具]] · [[09-内存与生命周期优化/A-M02-全部free后RSS不降-分配器保留还是泄漏/A-M02：全部 free 后 RSS 不降：分配器保留还是泄漏#定位方法|定位方法]] · [[09-内存与生命周期优化/A-M02-全部free后RSS不降-分配器保留还是泄漏/A-M02：全部 free 后 RSS 不降：分配器保留还是泄漏#内核流程与汇编|内核流程与汇编]] · [[09-内存与生命周期优化/A-M02-全部free后RSS不降-分配器保留还是泄漏/A-M02：全部 free 后 RSS 不降：分配器保留还是泄漏#修复与验收|修复与验收]]

## 现象与原理

**生产现场与现象。** 模型加载/卸载后业务对象数归零，但 RSS 仍较高，重复重启只能暂时改善。

**原理与因果关系。** free 归还给分配器，不保证每个空闲块立即解除映射。arena、碎片、线程缓存和仍活跃对象可能阻止页归还；真实悬挂引用则是另一类原因。

## 练习任务

设备端：运行“全部free后RSS不降-分配器保留还是泄漏”故障现场，记录输出中的实际结果目录与异常证据。

```sh
sadboard run memory-allocator
```

设备端：执行“全部free后RSS不降-分配器保留还是泄漏”的参考修复验收，核对终端结论及保存的结果契约。

```sh
sadboard verify memory-allocator
```

把下方路径替换为完成后打印的实际目录：

设备端：把路径占位符替换为本次实际现场目录，复核该次运行的证据完整性与验收约束。

```sh
sadboard check /srv/sadboard/实际目录
```

本例为固定有界负载，无额外参数。源码 [suite-advanced-memory.c](https://github.com/linux-bsp/sadboard-external/blob/93c81e82acfdf5d54155d1b9bb750e78645d384f/package/sadboard-labs/src/suite-advanced-memory.c)；8192 个 1 KiB 小对象使用进程内 mallopt 禁止自动 trim，全部正确释放；参考额外 malloc_trim。observed 为释放前记录的堆页面在 free/trim 后仍驻留的实际字节（逐页 mincore，已解除映射计零），auxiliary 为活跃分配字节；fordblks 和 RSS 另行记录。AArch64 glibc 的 malloc_trim 可以用 MADV_DONTNEED 回收 arena 内部页面而不缩小 fordblks，因此不能要求 fordblks 随 RSS 一起下降。相同 8192 次与 checksum=1044480，不把 allocator 保留说成丢失块。

`memory-allocator-{bug,fixed}.out/.trace` 分别保存摘要与原始事件，字段 observed/auxiliary 的含义以上述本例定义为准。摘要、trace 和完成数必须相符。与正常业务输出不同的故障结果会由本例契约明确识别；不能拿最外层退出0证明没有异常。性能题同时保留 cpu_ns/wall_ns，至少三次再评价时序，不只看资源上界或一次漂亮数字。

**实际复现负载。** 8192 个 1 KiB 小对象使用进程内 mallopt 禁止自动 trim，全部正确释放；参考额外 malloc_trim。observed 为释放前记录的堆页面在 free/trim 后仍驻留的实际字节（逐页 mincore，已解除映射计零），auxiliary 为活跃分配字节；fordblks 和 RSS 另行记录。AArch64 glibc 的 malloc_trim 可以用 MADV_DONTNEED 回收 arena 内部页面而不缩小 fordblks，因此不能要求 fordblks 随 RSS 一起下降。相同 8192 次与 checksum=1044480，不把 allocator 保留说成丢失块。

**面试/评审追问。** 为何线程退出可能改变 RSS？增加 arena 上限为什么可能改善并发却增加内存？

## 使用工具

通用原理、参数和使用边界见工具手册；具体命令与证据判断见本例定位方法。

[[工具手册/sadboard|sadboard]] · [[工具手册/Valgrind|Valgrind]] · [[工具手册/Massif|Massif]] · [[工具手册/procfs|procfs]] · [[工具手册/cgroup-v2|cgroup-v2]]

## 定位方法

**定位流程与工具。** Massif/Valgrind 记录活跃对象，smaps_rollup 看匿名驻留和映射；使用 glibc 分配统计时注明版本。RSS 单独不能区分 allocator 缓存与所有权泄漏。

参数查阅：[[工具手册/Valgrind|本方向基础工具参数与边界]]。

## 内核流程与汇编

**内核源码阅读。** [mmap.c](https://github.com/linux-bsp/linux-7.0/blob/master/mm/mmap.c)：brk、munmap 路径；[madvise.c](https://github.com/linux-bsp/linux-7.0/blob/master/mm/madvise.c)：madvise 丢弃页等路径。从用户接口找到入口，检查配置/标志/失败分支，再画出本题的路径；这些链接不是实机完整调用栈。

## 修复与验收

**修复与工程取舍。** 统一尺寸生命周期、复用池、避免跨线程随意交接，按峰值容量设计。malloc_trim 用作诊断对照，评估额外扫描和后续缺页成本后再决定策略。

**量化验收与清理。** 重复 N 轮后活跃字节/映射/RSS 是否进入平台期，业务数不减少；明确何种“高水位保留”可接受，而不是要求每次 RSS 回到一模一样的数。

[[附录A-实验报告/00-章节导航|实验报告与复盘]] · [[00-实验准备与通用方法/01-构建与启动部署#源码与实机证据|匹配源码、固件与实测证据]]

[[09-内存与生命周期优化/A-M01-慢消费者使有效队列挤爆内存/A-M01：慢消费者使有效队列挤爆内存|上一例 A-M01]] · [[09-内存与生命周期优化/A-M03-数据流水线多次复制和缓冲池生命周期错误/A-M03：数据流水线多次复制和缓冲池生命周期错误|下一例 A-M03]]
