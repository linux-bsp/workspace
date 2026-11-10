[[README|首页]] · [[00-实验准备与通用方法/案例索引|案例索引]] · [[00-实验准备与通用方法/工具索引|工具索引]] · [[09-内存与生命周期优化/00-章节导航|章节导航]]

先按现象提出假设并完成练习，再核对定位、内核机制和参考修复。`verify` 验证镜像提供的参考实现。

[[09-内存与生命周期优化/A-M07-总空闲足够却申请不到连续DMA缓冲/A-M07：总空闲足够却申请不到连续 DMA 缓冲#现象与原理|现象与原理]] · [[09-内存与生命周期优化/A-M07-总空闲足够却申请不到连续DMA缓冲/A-M07：总空闲足够却申请不到连续 DMA 缓冲#练习任务|练习任务]] · [[09-内存与生命周期优化/A-M07-总空闲足够却申请不到连续DMA缓冲/A-M07：总空闲足够却申请不到连续 DMA 缓冲#使用工具|使用工具]] · [[09-内存与生命周期优化/A-M07-总空闲足够却申请不到连续DMA缓冲/A-M07：总空闲足够却申请不到连续 DMA 缓冲#定位方法|定位方法]] · [[09-内存与生命周期优化/A-M07-总空闲足够却申请不到连续DMA缓冲/A-M07：总空闲足够却申请不到连续 DMA 缓冲#内核流程与汇编|内核流程与汇编]] · [[09-内存与生命周期优化/A-M07-总空闲足够却申请不到连续DMA缓冲/A-M07：总空闲足够却申请不到连续 DMA 缓冲#修复与验收|修复与验收]]

## 现象与原理

**生产现场与现象。** 长时间运行后摄像或 DMA 缓冲申请失败，free 显示仍有可用 RAM。

**原理与因果关系。** 连续物理页需求与普通虚拟连续 malloc 不同。碎片、不可迁移页、CMA 区域及设备地址限制会导致申请失败；compaction 也可能制造时延。

## 练习任务

**受控复现设计。** 通过本项目专用模块在 AM625 手动持有有界 DMA 缓冲，制造真实 CMA 交错空洞并释放恢复；默认不加载、不触发，接口只释放本例持有的对象。

**面试/评审追问。** 为什么增加 swap 不能保证连续 DMA 内存？IOMMU 与物理连续性、设备地址宽度有什么关系？

## 使用工具

通用原理、参数和使用边界见工具手册；具体命令与证据判断见本例定位方法。

[[工具手册/sadboard|sadboard]] · [[工具手册/Valgrind|Valgrind]] · [[工具手册/procfs|procfs]] · [[工具手册/cgroup-v2|cgroup-v2]]

## 定位方法

**定位流程与工具。** 保存 buddyinfo、pagetypeinfo、CmaTotal/CmaFree、驱动失败日志及可用 tracepoint；区分用户分配 ENOMEM、DMA 映射限制与 CMA 连续区失败。

### A-M07：真实 CMA 连续内存实验操作

正常确认启动后执行 `sadboard verify memory-cma`。案例要求单一实际 CMA 区域、4 KiB 页、足够空闲 RAM；不满足就失败，不能把普通 malloc ENOMEM 当通过。控制器使用 dummy platform device 的真实 dma_alloc_coherent API，持有最多 128 MiB 的 1 MiB 连续 DMA 块；校验 DMA 地址都在 CMA 物理范围内，拒绝 CMA 外的普通页分配回退。按物理地址排序后释放交错块，再向 CMA debugfs 请求 16 MiB。

故障证据必须同时满足：总 CMA 空闲至少 4096 页，maxchunk 少于 4096 页，真实 alloc 写入返回 ENOMEM。随后释放本例仍持有的块，以完全相同的 16 MiB 请求成功作为参考，并释放本例刚申请的 debugfs 块。trace/JSON 保留实际计数：completed=1 表示本次申请实验已取证，checksum=4096 是请求页数，不是 DMA 数据哈希。内核内部可记录 EBUSY/-16，但 cma_debug 的 NULL 分配结果向 write 调用返回 ENOMEM/12，二者来自不同层。异常退出由 runner 释放自己的 DMA 块。没有数据写入分区，也没有模拟硬件 DMA 传输。

阅读 `kernel/dma/direct.c`、`kernel/dma/contiguous.c`、`mm/cma.c`、`mm/cma_debug.c`，把 DMA 地址限制、CMA bitmap 空洞、迁移/压实和普通虚拟连续 malloc 区分开。用 `cat /proc/meminfo`、`buddyinfo`、`pagetypeinfo`、debugfs 的 count/used/maxchunk 与可用 cma tracepoint 建立证据链。修复不是盲目扩大 CMA；生产设计应在启动时预算并复用缓冲池、按驱动能力选连续 DMA 或 SG，并审查 pinned 页的释放时机。

参数查阅：[[工具手册/Valgrind|本方向基础工具参数与边界]]。

## 内核流程与汇编

**内核源码阅读。** [cma.c](https://github.com/linux-bsp/linux-7.0/blob/master/mm/cma.c)：cma_alloc；[compaction.c](https://github.com/linux-bsp/linux-7.0/blob/master/mm/compaction.c)：try_to_compact_pages；[page_alloc.c](https://github.com/linux-bsp/linux-7.0/blob/master/mm/page_alloc.c)：__alloc_pages_slowpath。从用户接口找到入口，检查配置/标志/失败分支，再画出本题的路径；这些链接不是实机完整调用栈。

## 修复与验收

**修复与工程取舍。** 启动阶段预算并复用固定缓冲池，审查可迁移性和映射生命周期，必要时使用驱动支持的 scatter-gather；不能只增加 CMA 而不评估留给其余系统的 RAM。

**量化验收与清理。** 硬件条件满足时按预定帧池规模多轮申请/释放并校验数据，无泄漏且尾延迟满足预算；当前仅设计，缺失条件明确标为未验证。

[[附录A-实验报告/00-章节导航|实验报告与复盘]] · [[00-实验准备与通用方法/01-构建与启动部署#源码与实机证据|匹配源码、固件与实测证据]]

[[09-内存与生命周期优化/A-M06-socket与slab增长被误判为用户堆泄漏/A-M06：socket 与 slab 增长被误判为用户堆泄漏|上一例 A-M06]] · [[09-内存与生命周期优化/A-M08-线程扩张带来的栈、TLS与调度预算失控/A-M08：线程扩张带来的栈、TLS 与调度预算失控|下一例 A-M08]]
