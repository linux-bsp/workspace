# AM625 SadBoard 调试验证记录

## 阶段 1：systemd 基线与 GDB/core

状态：已构建、OTA、实机验证通过。固件版本保持 v0.0.1。

基线提交：

| 组件 | 提交 |
| --- | --- |
| Buildroot | 89f5a1cf52 |
| BSP | cf5300a（c404bd1 基线上的测试夹具修复） |
| EDK | b7bb487f |
| Linux | 1c04c52c7 |
| U-Boot | 6d569284 |
| libbmc | a991991 |
| SadBoard 实验层 | 5bb4010 |

本机输出目录为 `output/am625-debug-systemd/`，使用共享 AArch64 GCC 15 SDK 和
`../dl` 缓存。旧 `output/am625-debug/` 产物保留，不用于本轮部署或符号分析。

验证工件放 `output/validation/stage1-debug/`。实际固件 ID、测试结果、设备启动 ID
和提交门禁将在通过后补充。本轮 OTA 只更新 kernel/rootfs，不更新板上 SPL/U-Boot。

## 实际结果（2026-11-09）

- 初版 f89b2b06（发布 114）正常完成 OTA 和 SSH/GDB 在线验证；离线 core 的 PIE
  加载地址恢复遇到 ELF 头部缺失，补齐调试内核配置后重新发布，未把该项记为通过。
- 最终内容 ID `aa51f9311088f2e146018e42721073fad86a7a2972a752593e018f2aeee6aba5`，发布 115，设备上报 success。
- 启动 ID `3619d3ed-f0a2-4688-8267-6e630c396f89`；零失败服务，双 rootfs 槽和当前 kernel/rootfs 完整 SHA256
  检查通过，日志持久化、启动归档确认与 UTC+8 校时通过。
- 所有调试能力检查通过；GDB 在线复现 SIGSEGV，显示 process_request、key=42、
  record=0x0 和源码。离线 core 为 278528 字节，SSH 传输后 SHA256
  `b0b8ab5a27b62e22acedca6dbaf25ae7c3dfcac62d5605977d6efa46edcddef3` 一致，匹配符号和完整 sysroot 下回溯正常。
- 参考修复保留正常输入 1 的 value=64，不存在的输入 42 返回 2。strace 捕获 write，
  ltrace 捕获 strtol/printf，Valgrind 零错误；perf task-clock、cycles/instructions
  实际可用；trace-cmd 成功保存四个 CPU 的调度事件。
- SSH 的 root 调试登录在升级后正常，使用升级前缓存的主机指纹校验通过。
  私钥只保存在设备 /data/ssh/host，不进入固件或仓库。
- 原生产 BusyBox 不包含 command 内建，能力检查改为按 PATH 检查可执行文件；
  在旧/新实机 shell 中均验证。Core 上限按 ash 的 512 字节单位设置为 32 MiB。
- 主机案例 4 项、配置快照等价性、实际 FIT 解析/恢复 4 项、ARM64 initramfs
  加载和真实包上传下载回归通过。BSP 恢复测试夹具由固定 32 MiB 改为按实际
  rootfs 大小对齐分配，实际 SD 布局保持不变。

工件：`output/validation/stage1-debug-elfcore/`；初版和对照实验保存在
`output/validation/stage1-debug/`。匹配符号自动导出并校验；只更新 kernel/rootfs，
未烧写工厂镜像或更新实机 SPL/U-Boot。案例手动运行，未在启动时注入故障。


## 阶段 2：内存与性能（2026-11-09）

- 最终固件 `v0.0.1 / 59d8d1a5db4746a5943a086fee524ffa4edb2ace612e7ff37105b19735c2d8ea`，发布 118，OTA success；
  boot ID `81bc87c9-a77e-4e66-bd48-3e1279ec42b0`。SSH 指纹仍与阶段 1 相同。
- 零失败服务，关键服务健康；双 rootfs 检查、实际 kernel/rootfs 完整 SHA256、
  持久日志与跨启动记录、UTC+8 校时通过。
- 独立 32 MiB cgroup 复现 OOM：退出 137，oom_kill>0，组结束后已删除。
  故障峰值 33554432 字节，修复峰值 1310720 字节；参考版完成相同 64 次处理和 checksum=532480。
- Valgrind 小输入显示 4194304 字节/4 块 definitely lost，修复后全部释放、零错误。
- CPU 案例三次对照的 CPU 时间中位数：4.189 秒 → 0.009385 秒；
  两版 checksum 均为 3074743472，查询数均为 500000，不能外推为所有工作负载的提升比例。
- 锁案例墙钟中位数：2.004 秒 → 1.002 秒；两版均 completed=40、低 CPU 占比。
  strace 捕获 FUTEX_WAIT 和 clock_nanosleep；GDB 同时观察到 worker 的睡眠与锁等待。
- perf 获得 lookup_linear 调用链并在主机生成 cpu.svg；实际采样和 SVG 保存在工件目录。
  参考版 CLI 重复验收后健康检查仍通过。
- 主机 8 项案例回归、实际 FIT 完整性/恢复 4 项通过；镜像符号清单覆盖全部 8 个 ELF。

本阶段发现并修正/记录：

1. 实机 data 文件系统约 230 MiB，调试包与两份历史 OTA 缓存使启动时空间低于
   32 MiB 阈值，日志退回 volatile。SadBoard 改为保留当前完成包，旧缓存由现有
   fwctld 清理；重新发布后实测 persistent。没有更改分区或格式化。
2. 此内核的组 OOM 对同一 PID 可使 oom_kill=2；验收改为正增量并结合日志，
   不把计数写死为 1，不将 137 单独解释为 OOM。
3. perf 默认内联展开尝试调用不存在的目标 addr2line，script 失败；本案例禁用
   编译内联，report/script 使用 --no-inline 后正确提取调用链。此项也进入教学文档。

发布 116、117 是上述问题的中间验证，未据此提交“阶段通过”。最终工件：
`output/validation/stage2-memory-performance-final/`，包含 release-audit、board-validation、
performance-validation、原始串口、Valgrind、strace、GDB 及火焰图。固件版本仍为 0.0.1。


## 阶段 3：统一现场与生命周期（2026-11-09）

- 固件 `v0.0.1 / 9baf48a7511a5ec72bb08663d07210ee41e0dfa499dd4c8a347428c19e957959`，发布 120，OTA success；
  boot ID `7c4347bf-4e83-472f-9d0d-6e7cbc56b50c`，SSH、持久日志、双槽及完整载荷校验、校时和服务健康通过。
- 四类案例的 run/verify 均实测；默认和自定义参数、完整固件 ID、boot ID、UTC+8
  时间、命令和结果落盘正常。crash 返回 139 且 core 可见，OOM 返回 137 且 events 有证据。
- CPU 零记录输入返回 64，check 拒绝；缺少 result 的现场拒绝通过；外部目录 reset 被拒绝。
- 正在运行的 lock 和 OOM 均能 reset，取消标记为 1，场景返回 130，check 拒绝通过，
  监督原始返回码另存。结束后没有遗留 OOM 组，零失败服务，健康检查通过。
- 10 项原生回归包含“负载直接返回 0 但没有业务输出”反例，参考检查正确拒绝。
- 预检发现 systemd-run 对信号退出可返回 1，正常停止 unit 可返回 0；通过负载层保留
  信号对应退出值、取消状态独立记录并统一返回 130，避免将监督命令状态误作业务成功。
- 发布 119 完成初轮验证，取消状态的返回码完善后重新发布 120，再完成全套实机验收。

工件：`output/validation/stage3-lifecycle-final/`，包含 source snapshot、发布审计、
board-validation、lifecycle-validation 和逐项日志。初轮保留在 `stage3-lifecycle/`。
