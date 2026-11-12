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


## 阶段 4：隔离网络与启动 panic（2026-11-09）

最终固件 `v0.0.1 / 7788272ef4d66cd5cae8746c0cfb94575953e32c4d8dc1cc8a6b61ebed32f323`，发布 123，设备 OTA success。
恢复后的 boot ID `debf4655-3f99-4e29-8920-22f15dbf0e5d`，当前仍使用同一固件、已确认部署，SSH 正常。

### 网络实测

- RTT：无故障 0.248 ms → 注入单向 100 ms 后
  100.284 ms → 移除后 0.244 ms。
- 100% 丢包阶段如期全部丢失；两次 TCP 测试各发送并接收 1048576 字节，无少传数据。
- pcap 为 2145666 字节、557 包，解析确认有 ICMP 和 TCP。
- 实验结束/取消后 namespace 清理通过，eth0 地址、MAC 和全局路由逐项比较未变。
- 1 MiB 短流的接收统计约 1 秒，包含测试和控制流程开销；该速率不代表真实网口带宽。

### 单一 panic、持久证据与 SOL

- 已确认固件额外正常重启，boot `ea4aa70e-995d-48ad-9e21-52477a1d0ea3` 在未封存窗口手动触发
  SysRq panic；串口打印原因、实验 marker、调用栈及 3 秒重启倒计时。
- 最终窗口没有附加的健康失败或 fw-confirm stop 事件；用 SIGSTOP/SIGCONT 暂停/恢复
  确认进程，避免 OnFailure 参与。配套 vmlinux 解码到 drivers/tty/sysrq.c:154、
  write_sysrq_trigger 等真实源行。
- 下一正常启动 `debf4655-3f99-4e29-8920-22f15dbf0e5d` 通过健康确认，boot-state 的前一 Linux boot
  匹配失败现场，previous_intent=operator，诊断为 linux-panic-observed。
- logctl 导出含 crash-ramoops 的 recovery.tar.gz，SHA256
  `565c4d7168a6b5c854900981a2847312ad3637f8c03abba41289c20f8c19b82c`。它是本次取证快照，不是内核内存 vmcore。
- SOL 服务器收到失败和恢复两条独立启动记录，并完成两份 RAM bank 确认清除：

| 记录 | Startup ID | R5 SPL | A53 SPL | U-Boot | Kernel |
| --- | --- | ---: | ---: | ---: | ---: |
| 异常启动 | ff388253-79cd-4981-837f-a63b235539a1 | 418 | 455 | 3029 | 26406 |
| 正常恢复 | c0be1c87-c603-45c5-aa74-aa1f7f0d1da7 | 418 | 455 | 3029 | 24967 |

表中大小单位为字节。异常 kernel 段包含对应实验 marker 和 panic 文本，四个阶段
均有实质内容。Startup ID 是启动缓冲的标识，和 Linux boot ID 不同，需要用
recovery-boot/boot-state 建立关联，不能直接把两个 UUID 当作同一字段。

[异常启动原始四段日志](http://192.168.10.246:8090/api/sol/logs/1c-63-49-22-c4-f7/ff388253-79cd-4981-837f-a63b235539a1/all/0)
与 [正常恢复原始四段日志](http://192.168.10.246:8090/api/sol/logs/1c-63-49-22-c4-f7/c0be1c87-c603-45c5-aa74-aa1f7f0d1da7/all/0)
为服务器 JSON 接口；同时可在 SOL 页面按启动时间选择。

### 回归与中间问题

- 最终镜像回归六类现场；原有 crash/OOM/CPU/lock 的运行、参考修复、参数、取消、
  不完整记录和外部 reset 拒绝测试通过，零失败服务。
- 双 rootfs 槽检查、实际 kernel/rootfs 完整 SHA256、日志持久化/同步/归档确认、
  UTC+8 校时和 SSH 主机指纹检查通过。
- 原生 10 项、实际 FIT/恢复 4 项、真实 ARM64 initramfs 依赖执行检查通过；新 BusyBox
  配置已导出并验证 FLOAT_DURATION，生成的便携 defconfig 包含对应片段。
- 初轮 121 暴露 BusyBox 不支持小数时间、后台抓包继承忽略 INT。改为独立调试片段
  启用 FLOAT_DURATION、TERM+wait 收尾，并用本案例 reset 清理残留 namespace。
- 122 已捕获 panic 与恢复，但发现停止 fw-confirm 额外触发 OnFailure；改为暂停进程后
  重新发布 123，复测只包含预期 panic。中间结果均保留，未据此提前提交阶段完成。
- 终检脚本曾把准备阶段正常 reboot 的 stop 日志也计入故障窗口；更正为失败那次 kernel
  的窗口后重新核对现有原始证据，没有为修复脚本断言再次触发 panic。

最终工件：`output/validation/stage4-panic-isolated/`，包含 source snapshot、发布审计、
board/network/panic/lifecycle-validation、完整原始串口、pcap、服务端四段 JSON、
pstore 附件和 panic-decoded.log。前两轮分别保留在 stage4-network-panic/ 和
stage4-network-panic-final/。本轮不刷写 SPL/U-Boot，不修改分区，不增加自动启动故障。

## 教材与证据验收增强（2026-11-09）

固件保持 `v0.0.1`，内容 ID：
`b9ea672a957c8046b31440a201453eb83372ffc42813a1b7683933eca58f942a`。
发布 124 已实机升级并上报 success；启动 ID 为
`065d4e23-193c-413e-91f9-c0bb304c27e8`。固件实际内容、两份 rootfs、持久日志、
UTC+8 校时及关键服务检查通过。

本轮新增 C 证据检查器，强化完整 JSON、实际工作量、独立 checksum、ELF core 结构、
实际 cgroup 限制与 OOM 计数、pcap 包边界及网络恢复检查。主机 15 项回归通过；
原生 FIT 完整性 4 项通过。实机完成 crash/OOM/CPU/lock 故障与参考版、参数与元数据、
取消、缺结束记录、外部目录复位拒绝、cgroup 清理检查。

网络实测基线/延迟/恢复 RTT 为 0.322/100.312/0.210 ms；两次 TCP 均传输 1048576
字节，pcap 为 2139534 字节、482 包，含 ICMP/TCP。取消后 namespace 清理，eth0
地址和路由不变，启动窗口之外的 panic 请求被拒绝。
网络验证开始时短连接 SSH 握手两次超时，复用控制连接后全项通过；没有把连接失败
记录当成案例通过。没有重复注入 panic，其既有跨启动验证保持独立，不冒充本轮重测。

额外在实机备份并临时损坏本次证据：空 core、空 pcap、空业务 JSON、完成数错误、
缺少 oom 事件、修复版工作量不足、缺少恢复回复均被 check 拒绝；随后恢复原始附件，
重新检查通过。此项检验拒绝不完整现场，不是抵御恶意操作者伪造全部证据的认证机制。

工件位于 `output/validation/stage5-evidence/`，包含发布审计、原始串口、板端验收、
生命周期、网络与负例验证 JSON、源码快照及提交门禁。教材新增基础篇、学习路线、
L1～L3 任务书、内核关键分支笔记及实验报告模板；扩展练习与实测结果分别标注。

## 描述符案例与教材深化（2026-11-09）

固件 `v0.0.1`，完整内容 ID：
`668ad82f52bae589bcf1a74c08734e7b29c309ec1899d7e3169382a323dcecdf`。
发布 125，设备已上报 success，Linux boot ID 为
`af921040-2640-472b-a533-af8091ca092d`。关键服务、实际 kernel/rootfs 内容、两份
rootfs 校验、持久日志与 UTC+8 时间检查通过。主机 18 项案例回归、导出符号验证及
4 项 FIT 完整性检查通过。

新增 `sadboard run/verify fd [REQUESTS DELAY_MS]`，默认 128/20，只降低负载自己的
NOFILE 为 64，不修改全局限制。实测 baseline=3，故障版完成 61 次、最终占用 64、
返回 EMFILE=24；参考版完成 128 次，峰值 4、最终占用 3。小输入 4/0 时故障版
退出 0 但最终占用 7，参考版回到初始值。两次在线 /dev/null 引用快照为 3→24，
用于证明趋势，不将其直接等同新增泄漏量。

真实 ARM64 strace：故障版成功 open 61 次、业务开始后显式 close 为零，随后
openat 返回 EMFILE；参考版 open/close 均为 128 次且无 EMFILE。完成量损坏、
超预算和继承 NOFILE 不足被拒绝；取消记录为 130 且不通过 check；父 shell 上限、
全局 file-max 和管理 eth0 保持不变，实验后健康检查正常。

新固件上重复原有 crash/OOM/CPU/lock 的故障与参考版、取消、元数据和证据边界回归。
另对新 ARM64 core 用配套 ELF/sysroot 实际运行 GDB，得到 record=NULL、key=42，
`ldr w0,[x0,#4]`、x0=0、si_addr=0x4，栈和源行正确，已将解读加入教材。
CPU 单次默认对照两版 checksum=3074743472，CPU 时间约 4.193 秒与 0.00887 秒；
锁案例两版完成 40 次，墙钟约 2.004 秒与 1.002 秒。单次数据仅用于解释，不冒充
多次测量的普适性能结论。

网络基线/延迟/恢复 RTT 为 0.283/100.337/0.249 ms，两版均传输 1048576 字节，
pcap 2135240 字节、430 包，包含 ICMP/TCP。取消与 namespace 清理、管理网口不变、
晚期 panic 拒绝检查通过。本轮未重新注入 panic，沿用先前独立的暖重启与 SOL 证据。

工件位于 `output/validation/stage6-descriptors/`：source snapshot、release audit、
原始串口、board/lifecycle/network/fd/GDB 验证 JSON、strace 与 core 原件。
新增 FD 教材章节，并扩充六个已有案例的先修概念、计算模型、逐步取证、返回值判读、
反例和实测样例；学习路线与练习册同步整理为七个章节。


## 阶段 7：独立 TFTP/NFS 开关与网络调试（2026-11-09）

普通 AM625 的 U-Boot defconfig 关闭 `CONFIG_AM62X_BOOT_TFTP_KERNEL` 和
`CONFIG_AM62X_BOOT_NFS_ROOT`；SadBoard 片段默认同时启用。主机实际执行四组
Kconfig 配置及默认环境生成，得到 mmc、tftp-mmc、mmc-nfs、tftp-nfs 四种组合。
新 U-Boot 完整构建通过；运行实际迁移 C 函数的主机测试确认旧环境迁移、配置组合
变更、HWID/MAC/IP/自定义路径保留及同组合人工覆盖保持。网络相关主机回归 4 项、
原案例回归 18 项通过，调试 ELF/源码清单校验通过。

本次发布保持 `v0.0.1`：

- OTA 内容 ID：`725d715950319e9525990b97d235a711f2c727f1036708569b093ebaa914c998`。
- 发布 126，设备上报 success；本地 SD 根继续使用 initramfs、dm-verity 和原 A/B 布局。
- 网络参考构建 ID：`366c904b3c1b100fc1ccd0dbbdc1798a5d443fb822962d5b1c76ebbbc8fc18af`。
  它记录构建时内核、DTB、rootfs 的内容，区别于 OTA ITB 的身份；不证明可写 NFS 树未被修改。
- 主机 NFS 导出 `/srv/nfs/sadboard-am625`，只向 `192.168.10.211` 开放；
  TFTP 根为 `/srv/tftp/am625`，部署未压缩 Image 和独立 DTB，产物 manifest 校验通过。

**构建与刷写范围：新 U-Boot 二进制尚未刷入实机。** 生产配置仍禁止远程启动链更新，
本轮未解除。实机从新构建的 `u-boot-initial-env` 导出受控启动变量，经串口 TFTP 导入
现有 U-Boot，保留它的环境 schema 8，随后保存网络开关。新 schema 9 的 C 迁移逻辑
完成主机测试，没有冒充已在设备执行。备份启动区并读回比较，六个 SPL/U-Boot
分区字节均未改变；仅按操作保存环境变量，没有刷工厂镜像或格式化介质。

| 实机组合 | 实际验证 |
| --- | --- |
| 0 / 0 | 使用新环境脚本回到 SD FIT、initramfs、dm-verity、deployment 0；725d7159 已确认，零失败服务 |
| 1 / 0 | TFTP 加载 Image/DTB，直接挂载 SD SquashFS；调试启动就绪、SSH 和持久日志通过 |
| 0 / 1 | 校验并加载 SD FIT，`bootm FIT -` 跳过 initramfs；内核实际挂载 NFS，root 可读写 |
| 1 / 1 | TFTP Image/DTB＋NFS root；反复重启保持开关，SD data ext4 可读写，零失败服务 |

网络模式中 `fwctld`、生产健康观察和生产版本输出按条件跳过，SadBoard 独立确认
本次调试启动并封存日志，不把外部镜像写成 SD deployment 成功。实测 `/data` 持久，
NFS 写入从主机可见并清理；crash/FD/OOM 故障及 CPU/锁案例、网络参考流程和各参考
修复的现场检查通过。运行记录为 network-debug/SBNET1；前后 SD 元数据、管理 IP/MAC
和路由保持一致，案例结束没有残留 namespace，晚期 panic 请求被拒绝。

TFTP/NFS 模式额外完成一次主动 SysRq panic 和恢复：

- 失败 Linux boot：`da1da413-e0f9-411a-916a-639466b059c7`；恢复 boot：
  `641bbaff-0583-4e2e-9826-203e8c620de5`。
- `sadboard check` 确认前次启动、实际 panic 原因、相同参考构建和恢复健康通过。
- pstore/原始串口包含 SysRq panic；恢复附件 SHA256 为
  `1cb7257870dfa5c3602835c045771468ea76cebd06a5f0c972af428cfeacd297`。
- SOL 同时确认失败和恢复启动归档，两个归档均包含 r5-spl、a53-spl、uboot、kernel；
  缓冲区收到持久归档确认后正常清理。本次没有故意损坏 SD 分区或测试断电。

工件在 `output/validation/stage7-netboot/`，包含构建、四组 CONFIG、原始串口、源码快照、
发布审计、各模式验证、未改写启动区哈希、案例检查和 panic/SOL 附件。
操作方法统一见[教材网络启动章节](../obsidian-sadboard/00-实验准备与通用方法/01-构建与启动部署.md)。

## 阶段 8：NFS 实验产物共享（2026-11-09）

固件保持 `v0.0.1`，OTA 内容 ID 为
`b3eeb4443a652df34813f5f160eee7765a105e71f83aafdf399a205f21f1cb9c`，
发布 127，设备已上报 success。NFS 参考构建为
`82de782ae597dcfdc2bb35ea93a85ec273848cb71a6b3ebdd702645ea26f91a7`。
本次没有更新 SPL/U-Boot，也没有调整或格式化 SD 分区。

按实际根挂载类型选择实验目录：NFS 为 `/srv/sadboard`，本地根为 `/data/sadboard`。
`sadboard results` 查询路径，`SADBOARD_RESULTS` 可覆盖；空间门禁检查所选结果文件系统。
NFS 现场在运行时允许主机遍历/读取普通输出，完成时开放 core 等文件的读权限。
`sadboard share` 用于手工采集目录，限制在结果根目录的直接子目录，不跟随内部符号链接。
SD 模式保持私有权限；设备日志、OTA 缓存、启动确认仍使用 SD data。

实机与主机验证结果：

- 完整构建和调试清单校验通过；18 项原案例回归、4 项网络启动回归、4 项目录策略回归通过。
- 本地 OTA 后创建 crash 现场，结果仍在 `/data/sadboard`，目录 0700、core/元数据 0600，
  原始退出 139 与证据检查通过。
- 重新部署匹配 NFS 根目录后，crash、FD、OOM、CPU/锁参考对照、网络参考流程的
  结果均位于 `/srv/sadboard`。主机 UID 1000 直接读取 64 个现场文件，无需 sudo 或 SCP；
  core 可用配套交叉 GDB 还原 process_request/key=42，pcap 可读，管理网口保持正常。
- 手工 perf 文件初始 0600，普通主机用户无法读取；执行 share 后变为 0644，主机直接
  读取的 SHA256 与设备端一致，栈文本中保留 lookup_linear。
- 153 个旧 SD 条目复制到 NFS，逐个核对 1,201 个普通文件、25,464,691 字节的 SHA256，
  原 SD 文件保留。此前火焰图的 perf.data 已在共享目录可读。原 NFS 根也已完整另存。
- 工作区 `output/board-results` 链接到 `/srv/nfs/sadboard-am625/srv/sadboard`。
- NFS 目录下实际触发一次 panic：失败 boot 为 `b9894f23-19f0-4eab-9280-1c3f7cdf51ba`，
  恢复 boot 为 `c50b47a0-07d9-40d7-8997-297492c98467`。check、pstore、串口与 SOL
  的失败/健康两组四阶段日志验证通过。恢复附件为 0644，主机 UID 1000 可直接读取，
  SHA256 为 `eaba4f3dafefcd32532ccfee787e6a864d15f467fa7a9c418a7cb59b07da8c87`。

工件位于 `output/validation/stage8-shared-results/`，包含源码快照、构建与发布审计、
本地/NFS 权限检查、主机 GDB、旧现场复制清单及 panic/SOL 恢复证据。
教材的手工采集命令已统一通过 `sadboard results` 选择目录。

<a id="production-cases"></a>

## 阶段 9：案例库扩展与生产问题首批落地（2026-11-09）

本阶段案例设计共 **59 例**：崩溃、FD、内存/OOM、CPU、同步、网络、内核/启动各 5 例；性能、内存、网络进阶各 8 例。统一教材收录任务书、生产背景、原理、固定内核源码入口、定位流程、修复取舍、验收与评审题。**10 例有可运行实现并完成验证，其余 49 例是设计任务书，无统一命令、未上板。** 公开岗位和 issue 只作为课程设计的一手依据，不冒充企业事故的已证实根因或真实面试题。

最终固件保持 `v0.0.1`，内容 ID 为
`2e7850c3939178505badc32eda92b7285752a804d17ba2a622399a05aa0fda8c`，发布 129，设备上报 success。
NFS 参考构建为 `a3a9a46b13d41e1975a9c29cfe8a5b4896335d8273a10ebdda8e0a9c384e0818`。TFTP/NFS 调试根可变，参考 ID 不证明整个运行目录始终不变；本次核对了运行中的 17 个实验 ELF 与对应构建导出的 SHA256。
本次只更新 kernel/rootfs，未更新实机 SPL/U-Boot、覆盖工厂镜像或改变 SD 分区。

### 过程发现与构建修正

首次候选 `070dd0bf`（发布 128）能完成系统健康确认，但第一个案例执行失败：源码目录中的主机版 ELF 被 local 包同步保留，make 根据时间戳没有重新交叉编译。它没有被视为案例验收通过。
修复为每次构建实验包使用目标编译器强制重编译；原生测试只在临时目录构建。部署检查同时验证 ELF64、小端与 AArch64 machine，原错误产物被新门禁拒绝，补充 x86-64/ARM32/截断头/错误端序负例。最终 2e7850c3 重新发布并通过下列检查。

### 实机结果

- 主机 23 项实验回归、4 项网络启动回归、4 项结果目录策略回归通过；调试清单、架构、源码、符号与 SHA256 校验通过。
- 先在 SD A/B 模式完成 OTA，再在 SD 和匹配 TFTP/NFS 两种模式分别对 `deadline/backlog/tcp` 做三轮默认负载对照，同时验证 run、非默认参数及 `sadboard check`。
- 两种模式下原 crash、FD、OOM、CPU、lock、network 六类回归通过，管理 eth0 地址/路由与 namespace 状态前后相同。crash core 用匹配交叉 GDB 在 host 还原到 `process_request/key=42`。
- NFS 结果由 host UID 1000 直接读取，输出 SHA256 与设备相同；重新部署前完整归档旧 NFS 根，保留 1280 个既有现场普通文件并逐个核对 SHA256，未删除旧 SD/NFS 证据。
- 实机 strace 确认绝对定时标志；backlog 的 Valgrind 对照无丢失块且零错误；1024 条 TCP 记录的 strace 实际 sendto 次数为 1024 → 16。
- 截断原始时间 CSV、篡改 completed、篡改 TCP checksum 的复制现场均被拒绝。运行中 reset 返回取消状态，检查器不接受取消现场为通过，TCP namespace 清理正常。

下面是默认输入下 **三次中位数**，每格故障版 → 参考版。时序与 CPU 数值仅说明这块 AM625 在本负载下的结果，不作为硬实时保证，也不把 loopback 数据外推成网口线速。

| 观察量 | SD A/B | TFTP/NFS |
| --- | --- | --- |
| deadline：200 周期、10 ms 周期、2 ms 处理，释放误差 P99 / ms | 420.42 → 0.162 | 419.958 → 0.095 |
| deadline：最后一次相位误差 / ms | 424.678 → 0.063 | 424.268 → 0.063 |
| backlog：512 条×64 KiB，队列高水位 / 条 | 366 → 8 | 367 → 8 |
| backlog：有效载荷峰值 / KiB | 23488 → 576 | 23552 → 576 |
| backlog：进程 RSS 高水位 / KiB | 26108 → 3520 | 25484 → 3908 |
| tcp：8192 条×64 B，send 调用 / 次 | 8192 → 128 | 8192 → 128 |
| tcp：进程累计 CPU / ms | 217.612 → 8.722 | 214.556 → 8.627 |

三组参考版都完成相同工作与 checksum。backlog 最终载荷归零，队列最多 8 条、含消费者在途对象最多 9 块；背压节省峰值内存，没有伪装成提高下游吞吐。TCP 接收校验全部序号/字节；send 调用数不是线上包数。

### panic 与完整启动日志回归

在已经健康确认的 NFS 构建上额外重启，手动触发一次受控 SysRq panic：

- 失败 boot：`77ab26a5-b491-436a-ae6a-0da51339a940`；恢复 boot：`9948dca9-8138-4e70-a3dc-9a43d1313f33`。
- `sadboard check`、原始串口、pstore 与 SOL 均核对到 panic 和对应实验 marker；失败/正常两次归档各含 r5-spl、a53-spl、uboot、kernel。
- 恢复附件 SHA256：`439240362c98416e76e940fc7aee7dc54976712bd664258c4584f22ba7ba103c`；设备重新通过网络调试健康确认，零失败服务。未故意损坏分区、未进行断电试验。

最终工件位于 `output/validation/stage9-production-cases-arm64/`：源码快照、发布审计、SD/NFS 三轮 JSON/CSV、17 ELF 校验、GDB/strace/Valgrind、负例、中止清理和 panic/SOL 证据。首次失败与重建日志保留在 `output/validation/stage9-production-cases/`。两个目录均为本地主机验收附件，不提交大型构建文件。

## 阶段 10：24 个基础案例全部落地（2026-11-10）

最终固件 `v0.0.1 / 11146c22ffb0433b2b32d225c00128c20e2abcbda47edbcf53c64cd51f344843`，发布 131，AM625 实际 OTA success。新增的 B-CR/FD/MM/CPU/SYNC/NET 02～05 共 24 例均已有可运行故障版、参考版和证据契约；当前 34 例有代码，剩余 25 例继续实现。没有使用 QEMU。

- 主机 24 项回归通过；其中新增的一项遍历 24 例的故障/参考与伪造完成数、截断 trace 负例。原生测试不代替下面的 AM625 验收。
- 先回到 SD A/B 完成 OTA，19 项非 core 场景与原有 7 项参考对照通过；再部署匹配 TFTP/NFS，全部 24 个新基础案例及原有 7 项参考对照通过。
- SIGABRT、线程栈 SIGSEGV、mmap SIGBUS、ENOMEM 后误用指针的实际 core 均可在 host 用配套 `case-suite` 还原到 fault_child/stack_frame/suite_mem；主机 UID 1000 直接读取现场。
- 堆边界案例在设备 Valgrind 下实际报告 Invalid write，故障退出 99；参考版零内存错误。FD 引用增长、CLOSE_WAIT、丢唤醒、逻辑丢更新和 UDP 接收溢出均由真实计数/信号验证，没有用固定字符串伪造结果。
- 首次候选 8e133f79（发布 130）在栈场景被 ARM64 glibc 的 128 KiB 最小线程栈拒绝，未视为全部通过。修复为读取平台最小栈并设置足以触发保护页的有界递归后，重新构建发布 11146c22 并完整复验。
- 两种启动模式的管理 IP/路由及 namespace 前后相同；零失败服务。WDT 确认 active、timeout=60 秒。本阶段均为用户态故障，未主动令内核卡死、未损坏分区。
- 新基础案例在受限子进程或私有 netns 中运行，控制器正常退出只表示完成取证。JSON 中 observed/auxiliary 与 trace 保存真实子进程状态，检查器同时验证本例契约。实验完成会释放测试资源。

最终工件 `output/validation/stage10-basic-suite-arm64/`；首次候选与平台差异记录在 `output/validation/stage10-basic-suite/`，主机与构建日志在 `output/validation/remaining-cases/`。重新部署时保留旧 NFS 根和全部旧现场，逐文件核对 SHA256。此阶段未更新实机 SPL/U-Boot，未修改分区或使用工厂镜像。

## 阶段 11：20 个进阶应用场景全部实机验证（2026-11-10）

固件 **v0.0.1 / 8184926229677117b3ce2deaa53fa38ac6b8a7e091f668eecfd602718c164dbf**，发布 134，设备已回报 success。当前共 54 例有实现并通过 AM625 验证，剩余 CMA 与四项启动/内核实验继续开发。

- 主机 25 项回归通过；SD A/B OTA 后先验证 7 个依赖板端能力的代表案例，再部署同构建 TFTP/NFS，全部 20 个新增进阶案例通过。性能 7 例及网络优先级各做 3 轮，共 36 组进阶故障/参考对照。
- NFS 下全部 24 个基础案例、4 份真实 core 的配套 host GDB 还原通过；原 10 例回归通过，包括真实 OOM、网络测试和新一轮 panic/恢复。panic 的失败及健康启动均含 R5 SPL、A53 SPL、U-Boot、kernel，pstore 可查，恢复后零失败服务。
- 私有 CPU 配额实际出现约 12 次节流，参考无节流；PI 高优先级等待约 66 ms→6 ms；memory.high 记录实际回收事件而无 OOM kill；虚拟 veth 的接收 CPU 由 2→3；真实 PMTU 错误反馈 90/MTU600，1400 B 数据重试完整。这里只证明实验模型，不等同物理网卡 RSS 或生产实时指标。
- 发现并修正 ARM64 差异：CPUWeight 激活实验 cgroup CPU 控制器；malloc_trim 用 mincore 验证已释放堆页驻留而不假设 fordblks 清零；ET 未读长度改用 MSG_PEEK，另存 FIONREAD；tcpdump 等待真实监听就绪并启用 immediate-mode，避免短实验只留下空 pcap。
- 管理 IP/路由、namespace 和私有 cgroup 清理均通过，WDT active/60 秒。重新部署保留既有 NFS 证据并核对 SHA256。未改分区、未刷工厂镜像，实机 SPL/U-Boot 未更新。

完整证据：`output/validation/stage11-advanced-final/`。原候选与平台差异保留在 `stage11-advanced-suite/`、`stage11-advanced-controller/`；主机回归/构建日志在 `output/validation/remaining-cases/`。独立记录 SD 固件内容 ID 与 SBNET1 参考构建 ID，不能混为同一个哈希。

## 阶段 12：59 个案例全部完成 AM625 验证（2026-11-10）

固件 **v0.0.1 / 2d3b5221fe3822d001c05bb79242e9213ebde35af475a7d6f2b502bc3299e5f8**，设备 OTA 已回报 success。共 35 个基础、24 个进阶案例：57 个设备端入口，2 个主机 UART 控制的真实板端 RAM 启动实验。全程未使用 QEMU。

- 新增真实 CMA、内核 Oops、soft/hard lockup、PID 1 加载器缺库与 VFS 根挂载失败。内核模块手动加载、默认空闲，无开机自动注入。
- SD A/B 完成 OTA/健康确认，再做 7 个代表对照；在本地 SD 固件上分别完成真实硬件 WDT、Oops、全核 IRQ-off 锁死的自动复位与健康恢复。首次 SPL 延迟约 75.91 / 6.27 / 44.24 秒；WDT/锁死确认实际 ESM，soft lockup 实际报告 CPU#2 stuck for 4s。配置 timeout=60 与停喂命令到复位时间不等同，窗口喂狗细节见教材。
- NFS 全部 21 个新增进阶（37 组故障/参考对照）、24 个新增基础及原有 10 例回归通过。4 份实际 core 在匹配 host GDB 中还原；panic/pstore/SOL 原有恢复链再次通过。
- CMA 实际空闲 16440 页、maxchunk 463 页时，4096 页连续申请返回 ENOMEM/12；释放本例 DMA 块后同样请求成功，used 回到实验前的 200 页。所有资源均归还，没有用普通 malloc 失败替代 DMA/CMA 现场。
- RAM 缺库实际触发 exitcode=0x00007f00 的 PID 1 panic；独立守护的 10 秒期限实际复位；完整依赖副本完成 rootfs SHA256/dm-verity、switch_root 与 SD 健康确认。错误 p99 根设备不带 rootwait，实际 VFS panic；参考使用已确认 rootfs，并正常返回网络启动。
- 每项异常恢复核对失败/正常两份 R5 SPL、A53 SPL、U-Boot、kernel 的 SOL 归档；RAM 原始串口还保存加载器的直接输出。立即 Oops 可能快于 live 文件落盘，检查器从校验过的导出归档/pstore 补充证据，不拿空缺尾部当未触发。
- 最终保持 TFTP+NFS 1/1，WDT active，零失败服务。旧 NFS 现场逐文件 SHA256 核对保留。没有写坏分区、保存错误启动参数、刷新 SPL/U-Boot 或使用工厂镜像。

工件 `output/validation/stage12-final/` 保存 source snapshot、发布/验收 JSON、匹配符号、原始串口、pstore、SOL 四阶段日志及 RAM 正反工件。先前候选保留在 `stage12-kernel-board/` 与 `stage12-kernel-fixed/`：先后修正 CMA 传参、过早判 SSH 为健康、立即 Oops 的 live 日志缺尾判断；一次网络启动 ARP 超时由 UART 重试恢复，随后将破坏性恢复测试改为本地 SD，并为主机控制器增加最多两次正常网络启动重试。当前 USB UART 不透传 BREAK，RAM 参考 init 使用独立超时恢复子进程。

## 阶段 13：抓包就绪检查消除无效告警（2026-11-10）

最新固件 **v0.0.1 / 2e57ef243300cdbe07216336d4487054b7ed486b99ba073a9b48b1df63f70ff7**，已 OTA 并回报 success。异步启动 tcpdump 前先创建错误日志文件，避免父进程就绪检查抢在子进程重定向前读取不存在的文件。

SD 与配套 TFTP/NFS 模式分别实测 PMTU、RPS、网络优先级，每例各 3 次，共 18 次。结果契约、非空 pcap、管理 IP/路由与 namespace 清理通过；未再出现该 grep 告警，设备零失败服务，WDT active/60。内核、故障模块及 19 个实验 ELF 的 SHA256 与阶段 12 完全一致，完整 59 例基线沿用阶段 12，针对改动复验对应采集路径。

证据位于 `output/validation/stage13-capture-readiness/`，包括实际 ELF SHA256 对照、发布/验收与匹配调试产物；旧 NFS 现场继续完整保留。设备最终保持网络调试启动 1/1。

## 阶段 14：构建链移除自定义 Python（2026-11-10）

固件 **v0.0.1 / af2fdbd12be6b3e5759528f7f8dc9f3e9e06bc30918f3b355d70b542b991489b**，
服务器发布后，AM625 完成下载、写入非活动槽、自动重启、健康确认并上报 success。
实际 SD 启动 ID `ed071092-bead-48ea-9fcd-9ed7ea51b186`，deployment 1，kernel/rootfs 均使用 B 槽。
SD 验证及 OTA 重启时，仅在 U-Boot 内存中临时关闭 TFTP/NFS 开关，没有执行 saveenv；
正常默认仍是 TFTP＋NFS，网络调试启动不会参与生产 OTA 或修改 SD 健康确认。

- EDK target/host 构建使用 Buildroot `cmake-package` / `host-cmake-package`，PDM 使用
  `kernel-module`。配置、编译来源和 Web 资源嵌入改用原生 Kconfig/CMake。
- BSP 通过 Bash post-image、jq、CMake、原生 host-fw-tools、mkimage/genimage 和
  Linux gen_init_cpio 生成 JSON→ITS→ITB、initramfs、冗余元数据与工厂镜像。
  工厂 metadata 和环境的 CRC、标志及字节格式与旧实现对照一致。
- SadBoard 只维护标准 Buildroot defconfig；移除额外配置合成入口，符号导出、网络启动资料和
  RAM 实验打包改为 shell hooks，实验 ELF 由 Buildroot 目标编译器构建。
- 清理 EDK/host-edk、实验包和 host-fw-tools 的旧输出目录后，完整 `make all` 通过。
  目标目录没有 `.py`、`.pyc` 或 Python 解释器。上游主机 Python 依赖、主机测试、文档检查及
  可选串口控制器保留，不进入设备运行链。
- 52 项管理回归、原生构建框架、配置映射、HWID Web 嵌入检查通过；其中 HWID 回归补齐实际
  libubootenv 源码路径后复验通过。固件 14 项、布局 11 项、恢复 6 项、实际 FIT 4 项、
  案例 25 项、网络构建身份 4 项、结果目录 4 项通过。调试工件和 469 篇 Obsidian 笔记检查通过。
- SD 实机 initramfs→rootfs 切换、持久日志、SSH、全部调试能力检查、CPU/FD 对照案例通过，
  零失败服务，WDT active。服务器重载为本工作区新构建的原生 dmserver，Web 页面及上传发布验证通过。
- 配套 TFTP/NFS 参考构建 `ef776d37a682a24a92d47107faeb29b710771d7083c1101a2626c43eb19aba3d`
  正常启动；启动 ID `be63f0fb-26d2-4572-91fb-54bef4d899dc`。原 NFS 实验目录 5,786 个文件
  逐项 SHA256 核对保留，旧根文件系统另行归档。SBNET1 是可变 NFS 树的参考标识，与 SD 固件 ID 分开记录。
- 原生归档生成的 RAM 启动案例三组实机通过：缺库副本复现 PID 1 panic/exitcode 0x00007f00；
  完整副本的独立守护在约 10 秒期限复位；参考副本正常加载 fwctl、校验 rootfs 并切换到 SD 根。
  三组结束均恢复正常启动，最终返回配套网络调试环境。首次验收误用 TFTP 前缀 `am625/sadboard`
  导致文件不存在，控制器恢复正常启动后，改用本机 TFTP 根下的 `sadboard` 重新完成全部验收。
  最终启动 ID `68b7c2b5-f9ab-4a43-bfc0-0c99c10c8211`，网络 CPU/FD 对照复验通过；
  日志为 persistent、启动归档 acknowledged、archive-pending=0、WDT active、零失败服务。

工件位于 `output/validation/native-build/`，包括原生构建/回归日志、源码快照、发布审计、
OTA 前后状态、原始串口和部署校验。仅在线更新 kernel/rootfs；没有烧写工厂镜像、调整分区或更新 SPL/U-Boot。
本阶段不重复执行全部 59 例故障；完整基线仍见阶段 12，针对本次构建、加载和部署改动进行复验。

<a id="bootlin-build-history"></a>

## 早期 Bootlin/NFS 构建验证档案（2026-10-30～31）

以下保留当时的主机验证结果。文中的“本次”“尚未验证”指这个早期阶段；当前 systemd、OTA 和七个案例的实机结果见本文件前面的各阶段记录。当前操作统一使用 [调试教材](../obsidian-sadboard/00-实验准备与通用方法/00-章节导航.md)。


2026-10-30 至 2026-10-31，在当前 x86-64 主机完成以下验证：

- 使用已有 GCC 15/glibc 工具链与共享下载缓存，`make -C output/am625-debug BR2_PRIMARY_SITE=https://sources.buildroot.net` 完整构建成功，退出码为 0。未修改基础 BSP、Buildroot 或 Linux 源码。
- 默认内部工具链配置通过 Kconfig 检查，但未另行完整构建；本次实际产物来自外部工具链配置。
- 基础调试内核为 Linux `7.0.0`，Buildroot 实际内核配置保留了全部基础片段要求。可选 KGDB 和 memory 片段分别通过配置检查，尚未独立编译或上板。
- `rootfs.tar` 已核对 gdbserver、strace、ltrace、Valgrind、perf、trace-cmd、iperf3、tcpdump、stress-ng、ss、vmstat 和 iostat；检查脚本与启动脚本具有 root 所有权和可执行权限，内核模块目录为 `lib/modules/7.0.0/`。
- 新的交叉 GDB 验证了 Python 支持，能读取 `linked_list` 的源码/符号及保存的 `vmlinux` 中的 `panic` 符号。
- 官方 gdb、ltrace、valgrind、heap_profile、system_profiling、app_profiling 六个用户态示例均已交叉编译；未运行这些故障程序。
- 配置脚本拒绝覆盖已有 `.config`，Python/shell 语法、文档相对链接和 Git 空白检查通过。

| 产物 | 大小（字节） |
| --- | ---: |
| `images/Image.gz` | 9,665,893 |
| `images/k3-am625-alientek.dtb` | 56,205 |
| `images/rootfs.tar` | 356,167,680 |
| `images/rootfs.squashfs` | 133,763,072 |

SquashFS 已接近原 128 MiB 槽位容量，且本环境没有生成产品启动格式的整卡镜像，首次仍采用 NFS 验证。

构建日志为 `output/am625-debug/build.log`；官方实验编译日志为 `output/bootlin-reference/labs-build.log`。现有工具链、BSP 外部层和内核目录未被本任务修改；下载缓存新增了所需源码包。

**尚未验证**：AM6254 上电启动、SSH/串口连接、NFS 导出、真实 PMU 和网络性能、Valgrind 运行、KGDB、内核故障注入与 kdump。继续上板需要实际板卡连接及网络信息。

### 标准入口验证补充

已实际执行 `cd buildroot` 后通过环境变量传入两个 external，运行 `make sadboard_am625_debug_defconfig`。生成配置与原组合脚本的默认配置一致，仅 `BR2_DEFCONFIG` 的记录路径不同；入口可被 `make list-defconfigs` 列出。

后续不传 `BR2_EXTERNAL` 的 `make printvars` 与 `make show-info` 均成功，确认 external 路径被记住、所需调试工具和本地源码软件包进入构建依赖图。本次验证了标准入口及配置一致性，没有重新执行内部工具链方式的完整 `make all`。

## 2026-11-11：网络启动归入公共 BSP、USB/IP 串口文档

本轮将网络启动标记改为 `bsp.netboot=1`，参考记录改为
`BSPNET1 1 <SHA256>`，接口迁至 `/usr/libexec/bsp/boot-context`。
公共 overlay、健康确认、TFTP/NFS 导出与部署脚本均属于
`bsp-base-external`；SadBoard 只提供实验室 IP、案例依赖与 RAM 故障载荷。
普通 BSP 仍默认关闭 TFTP/NFS，SadBoard 默认开启两项。

最终构建：`v0.0.1 / 239b82b93d67d95111b57a7b07c7d178b233c31cffe7ec666af1e075e1a390d0`。
网络参考：`1e506637ec852571f38537d26814bfa24800e50891c0da736d1aa56556a2429a`。
OTA 服务已接收该固件的 `success` 上报；本地 SD 运行、健康确认、60 秒硬件看门狗正常。

| 模式 | 本轮实机结果 |
| --- | --- |
| 本地 FIT + 本地 rootfs | OTA 安装与启动健康确认通过，无失败服务 |
| TFTP Image/DTB + 本地 rootfs | 公共标记、BSPNET1、netboot 就绪、OTA/生产健康停用均通过 |
| 本地 FIT + NFS rootfs | 实机启动、公共健康确认、案例运行通过 |
| TFTP Image/DTB + NFS rootfs | 实机启动、公共健康确认、案例、perf 通过 |

TFTP/本地根模式运行 `sadboard-debug-check`、`sadboard verify crash`、
`perf stat -e task-clock -- sleep 1` 均通过。案例正确使用公共构建记录，结果仍写
本地 `/data/sadboard`。主机回归为公共网络启动 6 项、U-Boot 启动环境 11 项、
固件打包 14 项和案例 25 项，全部通过。另加载只含 BSP 的
`alientek_am62x_defconfig`，确认不依赖 SadBoard external 即包含公共 overlay/hooks。

U-Boot 二进制已重新构建，生成环境为 schema 10；**没有烧写新 U-Boot/SPL**。
板上仍运行 2026-11-05 的 U-Boot，验证时只更新了已有环境中的
`fw_set_net_bootargs`、`net_hostname` 和两个启动开关，原环境备份保留于设备
`/data/bsp-netboot-env-before.txt`。初次环境导入文件使用了不适用于本机 libubootenv
的空格分隔，公共标记未写入，触发调试健康拒绝与软件重启；已经串口恢复并改为
`name=value` 格式，读回确认后重新实测通过。增量构建还补做了
`sadboard-labs-rebuild`，避免沿用旧包中已删除路径的调用；最终固件包含新案例脚本。

工件：`output/validation/bsp-netboot-common/`，保存构建、回归、OTA 上报、原始串口、
串口恢复及 TFTP/本地根验收。NFS 根目录需要服务器 root 权限解包并更新导出配置；
后续已使用统一同步入口完成两种 NFS 模式实测，见本节末尾。

Obsidian 在现有“环境检查、登录与符号准备”一文中补充 Windows usbipd-win 共享、
Debian 13 的 usbip 导入、节点权限与 tio 参数/退出/日志留存，不新增零散笔记。
A 核控制台实测稳定路径为
`/dev/serial/by-id/usb-1a86_USB_Dual_Serial_5757005084-if02`；
`if00` 的 M 核归属仍待启动输出确认，不能把本机 STM32 的 `ttyACM0` 当作 AM625。
已安装 tio 3.9，核对了命令选项并实测本地 `Ctrl+T` 后 `q` 退出。
文档检查通过：117 篇笔记、2207 个有效 Wiki 链接、115 个源码路径。

### 部署预检修正

首次执行服务器部署时，Buildroot 的 host-jq 因构建参数 `--without-oniguruma`
不能执行 `test()` 正则函数。此前主机测试用了系统 jq，未覆盖这一实际差异。
已将两份部署脚本中的名称、哈希正则校验改为 Bash，jq 只处理 JSON 结构；新增
`--check` 可在非 root 会话验证全部 SHA256、构建记录和 rootfs.tar 内的参考记录，
不修改部署目录。缓存部署入口先完成这两项预检，随后才归档旧目录及变更 exports。

首次失败时，旧 NFS 根已备份到
`/srv/nfs/sadboard-am625-before-bsp-netboot-20261111-133924`，原 exports 内容在同名
`.exports` 文件；没有创建新根目录或写入板卡固件。设备继续运行已确认的 SD 固件
`v0.0.1 / 239b82b9`，可重试同一部署命令。

已用实际 Buildroot host-jq 对完整构建产物执行两份 `--check`，均通过。网络启动
回归增为 7 项，分别用系统 jq 与不含 Oniguruma 的 Buildroot host-jq 运行通过；
新增覆盖非空旧根目录、非法名称/哈希、文件缺失、构建记录不一致及损坏产物，
确认失败预检不改动旧根目录、不创建 TFTP 目录。本次修正只涉及主机部署与测试文档，
固件内容 ID 不变；后续已完成 NFS 部署及启动测试，见下节。

### 统一同步入口与实机验收收尾

临时 `/home/guohao/.cache/bsp-netboot-common/deploy.sh` 已移除。正式入口为
`sadboard-external/scripts/sync-artifacts.sh IMAGES`，默认 NFS/TFTP 路径和客户端来自
SadBoard 策略，可用参数覆盖。公共 BSP 提供 `--sync`：先在临时目录解包，再用
`rsync -aH --numeric-ids --checksum --delete` 同步；通用 `--preserve` 参数由 SadBoard
传入 `srv/sadboard`、`etc/machine-id`，保留实验记录及主机身份。同步入口不登录板卡、
不控制板卡重启或启动开关，同步前须由使用者让板卡使用本地根或关机。

sudo 优先使用已有授权，需要密码时从用户指定的仓库外
`~/.config/.sudo.guo` 读取；权限已设为 600。密码仅通过标准输入交给 `sudo -v`，
提升后的进程标准输入为 `/dev/null`。保留调用脚本进程避免 sudo 的 parent-PID
时间戳作用域变化。五项认证回归验证缓存授权、密码认证、失败终止、私有文件权限、
预检不申请授权及密码不进入日志/参数。

实际完整同步、重复同步均通过：NFS 根目录 inode 保持不变，过时探针文件删除，
实验记录和 machine-id 保留；一次实际 NFS 启动、回到 SD 后重复同步，再次 NFS
启动均正常。原有根目录备份保持原样。当前已完成四种模式的本轮验证，设备最终恢复
SadBoard 默认的 `tftp_kernel=1`、`nfs_root=1`，运行公共 `bsp.netboot=1` 模式。

两种 NFS 模式的案例均通过，最终现场为主机
`/srv/nfs/sadboard-am625/srv/sadboard/crash-20261111T140356-XXmwPnbI/`。
NFS 模式 `sadboard results` 为 `/srv/sadboard`，主机普通用户可直接读取共享证据。
`perf stat -e task-clock -- sleep 1` 成功，硬件 watchdog timeout=60，无失败 systemd
服务。生产 OTA/健康服务按公共条件停用，公共网络就绪服务正常完成。

网络模式前后两个 A/B 元数据区的合并 SHA256 均为
`b8f8a3c59a67a66fb549df23db5fe4bf39e43aabff64877456e69cc2636f3597`，
确认没有将网络镜像误确认为 SD deployment。正式固件保持已成功 OTA 的
`v0.0.1 / 239b82b9`；本次后续改动仅为主机同步工具，未生成不同内容的目标固件。
验证工件仍位于 `output/validation/bsp-netboot-common/`。

## 2026-11-11：补齐案例列表中的 01 编号

旧列表由 `case-suite --list` 和 shell 中的单独输出拼接；初期的十个入口已经存在，
但没有附带手册 ID，因此末尾的 `crash/oom/cpu/...` 看起来像未编号案例。
现在由现有原生 `case-suite --catalog` 统一输出 59 个正式案例及一个辅助项，按手册
章节、编号排序；`watchdog-probe` 的编号为 `-`。保留原命令入口与运行/验证语义，
不把外部 shell/串口案例注册为 case-suite 直接执行的负载。目标不依赖 awk/sort。

主机回归 25 项通过，现有入口测试增加对全部 35 个基础、24 个进阶 ID、顺序、
唯一入口及十个 01 映射的校验。原生 Buildroot `sadboard-labs-rebuild all` 和配套
符号/架构检查通过。固件版本维持 `v0.0.1`，内容 ID 为
`52745c9f8c9f1eb3800b0570e73cce97ba7c72e3af77be994f65e66501244a3a`；
OTA 发布事务 142 已收到 AM625 的 `success` 上报，SD 模式健康确认、零失败服务。

随后从 SD 启动状态运行正式 `sync-artifacts.sh` 同步配套 NFS/TFTP，恢复两个网络
启动开关。NFS 参考 ID 为
`97287f0095fc0836b876f2069460e8ef4bcfaa04da3c395f46b9af32d4870273`。
实机 SD 与 NFS 两次 `sadboard list` 输出逐字一致，59 个 ID 齐全且按手册排序；
NFS 下 `sadboard verify crash` 通过，无失败服务。板卡最终保持 TFTP＋NFS 启动。
未升级 SPL/U-Boot。工件保存在 `output/validation/case-list-ids/`。

## 2026-11-11：将看门狗前置检查独立展示

`watchdog-probe` 是 `kernel-lockup` 前的硬件恢复检查，不占 59 个正式案例编号。
现在从正式案例元数据表移出，在清单末尾独立的 `Auxiliary checks (not handbook cases)`
区域展示，不再使用 `-` 作为编号占位。手册提供了对应 B-BOOT05 的跳转链接。
现有目录回归更新为校验 59 个编号案例及独立辅助区域；针对该入口的主机回归通过。

原生构建与匹配符号检查通过，固件维持 `v0.0.1`，内容 ID 为
`e44eb18baa13ee36fddcb7e1aae2d34ad29820e624d2169f8846f9714a0cff5a`。
OTA 发布事务 143 已上报 success，SD 本地健康确认通过。随后同步 NFS/TFTP，
网络参考 ID 为
`221987529c140eebc5f7a37c5e8cc2b5ff40fdd4e4cd494b5aa5c477fc4a167c`。
SD 与 NFS 清单逐字一致，正式区域完整包含 59 个案例，辅助检查在独立区域，
NFS 健康确认通过、零失败服务，设备恢复 TFTP＋NFS 启动。
验证工件为 `output/validation/auxiliary-catalog/`。

## 2026-11-11：按案例编号前缀筛选与编号列前置

`sadboard list [ID_PREFIX]` 支持按编号的字面前缀筛选，如 `B-CR`、`B-MM`、`A-P`，
全量及筛选输出均为“编号、命令入口、说明”三列。无参数时仍展示 59 个正式案例及
独立辅助区域，带前缀时只展示匹配的正式案例。空前缀、无匹配项和多余参数返回 64；
筛选不会执行任何案例。现有目录入口回归覆盖十个单元、基础/进阶前缀、完整编号、
部分前缀及非法参数，通过。原生 Buildroot 重编译、固件符号与架构检查通过。

固件版本保持 `v0.0.1`，内容 ID 为
`3a231bdac1ecc2d5ff1937bb6a37c89e2f801031595214bb9d25ea7c1b898896`。
OTA 发布事务 144 已收到 AM625 的 success 上报。在本地 SD 模式实测全部十个单元
的筛选结果、59 个案例顺序、编号第一列及未知前缀返回值。随后同步 NFS/TFTP，
网络参考 ID 为
`6b346d2676a9276ead6f9c68b9ef4c3822428a229b3173a9de9162f9b4596609`。
NFS 与 SD 全量列表逐字一致，`B-CR` 均只列出 B-CR01～05，网络健康确认通过、
无失败 systemd 服务。设备最终保持 TFTP＋NFS 启动；未升级 SPL/U-Boot。
手册更新了字段顺序、单元前缀及示例。验证工件为 `output/validation/catalog-prefix/`。

## 2026-11-11：附录重组与 ABI、汇编教材验证

手册原附录 A/B 合并为实验实践与构建，Bootlin 课程参考顺移到附录 B；新增附录 C
保存 ABI 和跨架构汇编，24 篇工具说明迁入附录 D，移除两篇 i.MX6ULL 历史排错笔记。
原有保留内容的 517 个代码块逐字一致，案例、工具与导航链接同步更新。

教材七份手写 load_add 函数和统一 C 对照已用 Clang 19 编译、检查 ELF 并反汇编：
IA-32、x86-64、ARMv7-A A32/T32、AArch64、RV32IMAC、RV64IMAC 均通过；
另验证 A64 O0 与 RV64 关闭 C 扩展的对照。非 x86-64/AArch64 目标仅静态验证。

x86-64 主机与 AM625 均运行 ABI 测量程序，结果为 LP64、小端，示例结构体大小 16、
对齐 8、偏移 0/4/8。C 对照得到 load_add=12、wrapper=13、sum_array=31，
手写 x86-64/A64 函数得到 12。AM625 gdbserver 实测入口参数 inc=5、内存首值 7，
单步 ldr 后 w0=7、add 后 w0=12，ret 返回调用者并正常退出。

本轮只调整文档、校验工具与学习示例，没有构建或发布新固件；示例放在 NFS 共享的
`/srv/sadboard/`，设备继续 TFTP＋NFS 健康运行，无失败 systemd 服务。
主机编译日志、各架构反汇编、ABI 输出和 GDB 实机记录位于
`output/validation/appendix-textbook/`，学习程序位于 `output/learning/`。

## 2026-11-11：汇编教材按架构拆分

原跨架构长文拆为 10 篇笔记：学习导航、共同基础、x86、Arm 家族、ARMv7、ARMv8、
RV32、RV64、跨平台实验和工程分析。各架构补充数据流、调用边界、符号扩展、
分支推理与递进追问，面向有 BSP 经验但缺少系统原理训练的读者。
原教材全部代码块保留，标题独立编号并迁移链接；127 篇笔记、933 个标题、
2308 个双向链接及 120 个源码路径校验通过。本阶段为文档拆分，沿用上一节已验证的
静态编译与 AM625 单步结果；配套新练习在下一阶段实现并单独记录构建与实机结果。

## 2026-11-11：八个 A64 汇编与八个内核子系统实验

新增 L-ASM01～08：访存宽度、符号扩展、指针截断、有/无符号条件、调用者临时寄存器、
结构体布局、循环边界、callee-saved 寄存器。执行真实 A64 指令；错误指针只观察不解引用，
逻辑越界读取位于已分配哨兵内，被测 callee 的违规由外层探针保护 C 调用者。
非小端 AArch64 不模拟结果，返回 77。

新增 K-MM/VFS/IPC/TIME/PROC/NET/IO/SCHED01：私有 COW、rename 后旧 FD、eventfd 聚合、
timerfd 过期计数、僵尸回收、UDP 截断、管道短读和有效 CPU 亲和集合。
使用真实接口与私有资源，UDP 受管运行使用独立 namespace，不改管理 eth0。
故障和参考均回收实验子进程与资源；timerfd 数量按本次实际过期数检查，不编造固定 IRQ 次数。

主机原生回归 27 项通过，包含新子系统契约、双层证据篡改拒绝、非目标架构拒绝与 75 个目录项。
原生 Buildroot 构建、AArch64 ELF 和匹配符号校验通过。固件维持 v0.0.1，完整 ID 为
`81f22be540a73fe2c2118850e42e30b76add7abd4f0e4772e220664fc5cfaea6`，
OTA 发布 145 收到 success。AM625 本地 SD 与 TFTP＋NFS 分别完成新增 16 例 verify，
每例均独立调用 check，通过全部业务、资源和 trace/summary 契约。

NFS 参考 ID 为 `0fd5a423f9e30f4a81891cc8862462d25a2a6df2c8f01f99a83bcc9f39e9f4f5`。
设备最终保持网络调试启动，未升级 SPL/U-Boot。构建、回归、OTA、SD/NFS 每例原始输出与
独立检查保存在 `output/validation/assembly-course/`。手册增加两章共 16 个完整案例、
共同调试步骤与工具反向链接，原 59 例历史验证范围与本批分开记录。
另外实测手动 GDB 流程：在 sb_asm_width_bug 入口看到两个输入字段，单步 ldr x0 后
观察到 `0x1234567889abcdef`，进程正常结束；kernel-cow 的手动 strace 采集成功。
本次 A64 `.S` 源码同时保存在目标 `/usr/src/sadboard/src/` 与配套 `images/debug/source/src/`。

## 2026-11-11：原有 59 例的机制与定位教学深化

按有数年 BSP 经验、能读内核源码但缺少系统理论训练的读者定位，逐例扩充原有 35 个
基础和 24 个进阶案例。每例增加硬件/操作系统模型、状态与关键条件、证据到结论的推理、
反例和三项递进追问。保留原有命令与源码入口；源码逻辑路径不记为新增采集的动态栈。
学习导航补充从业务约定、对象、机制、分支、证据到修复边界的解释方法。

对照实际 C 实现，纠正 24 个基础扩展案例的负载描述，包括 pipe/socketpair、固定轮数、
消息长度、join/父控制器超时和内存触页范围。memory-residency 实际只触碰 4 MiB，
cpu-logging 实际为 memfd 上的 2048 条记录，net-endian 的长度是 1024；不再保留与
代码不符的设计设想。区分当前检查器能验证的契约与需要新增输入的生产扩展目标，
特别注明正常消费者退出与真正崩溃注入、本地代际模拟与实际迟到 IPC 的差别。

全部 59 例覆盖检查通过，原有 306 个 fenced 代码块逐字、按原顺序保留。
工作区及独立仓库两种文档检查均通过：145 篇笔记、1353 个连续编号标题、2587 个双链，
工作区额外检查 127 个源码路径；补丁空白检查通过。维护辅助脚本只保存在被忽略的
`output/validation/assembly-course/`，未加入生产构建或设备程序。

本阶段只改文档，未重新构建或发布相同固件，也未重复触发内核故障；新增 16 例的运行
结果沿用上一阶段单独记录的 SD/NFS 验收。只读检查确认 AM625 仍在 TFTP＋NFS 模式，
无失败 systemd 服务，WDT timeout=60、nowayout=1，两组新增案例清单完整；未占用串口。

## 2026-11-11：内核教材改为按子系统递进学习

移除把八个K-案例集中放在一个章节的组织方式，建立第12～20章：进程管理、进程调度、
内存管理、VFS与文件系统、并发同步与IPC、网络协议栈、时间与定时器、块设备与存储I/O、
启动与故障恢复。每章新增框架设计与核心原理，解释设计目标、对象、状态、关键控制路径、
并发/错误边界及源码阅读问题；导航逐例规定机制问题、实际证据、修复与深化任务。
进程、内存、VFS和同步章节另加入copy_mm、wait、匿名缺页、PTE重检查、fsync分派与
futex等待竞争的具体走读，源码位置已与当前工作区核对。

各章分别安排6/6/10/6/8/10/6/5/5个案例，合计62个学习安排复用50个独立实现；
不重复增加案例总数，正式目录仍为75例。八个K-笔记迁入所属子系统，原B-/A-案例保留
唯一详解并增加课程反链；工具反链、总索引和手动strace准备同步迁移。
驱动模型、中断、RCU、PM与块层故障的专用实现缺口单独列出，未计入本次已实现或已验证能力。

文档检查新增每章5～10个不同案例、逐例实训段落、框架入口及课程反链检查。
工作区与独立仓库校验通过：162篇笔记、9个子系统章节、1529个标题、2867个双链，
工作区检查136个源码路径。旧仓库778个代码块全部保留，75例中的469个代码块逐字且按
原顺序保留；8篇移动笔记的路径迁移检查通过。损坏章节、缺失框架及课程链接不足的负例被拒绝。

本阶段修改教材与主机文档检查，不修改目标程序、构建配置或固件，没有生成或发布内容相同
的OTA包，也未重复触发实机故障。沿用各独立案例已归档的AM625验证，明确区分课程源码
推导和此前的动态证据；特别不以NFS文件实验代替本地MMC块层验证。

## 2026-11-11：内核课程归入统一的二级目录

九个子系统章节由顶层12～20目录迁入 `obsidian-sadboard/12-内核子系统/`，内部按
`01-进程管理/` 至 `09-启动与故障恢复/` 编号。增加课程总导航，首页仅保留一个内核课程入口；
子系统、案例、工具反链、案例索引及工作区指南同步更新，案例ID、命令和课程顺序不变。

工作区与独立仓库文档检查通过：163篇笔记、9个子系统、62个学习安排、1533个标题、
2873个双链；工作区核对136个源码路径。迁移前162篇笔记全部保留，787个代码块逐字保留。
新增总导航对子系统入口的检查，并验证缺少入口时被拒绝。本轮仅整理文档，不生成新固件。

## 2026-11-11：汇编教材与AM625实验集中分组

将原第00章ARM64基础、附录C的跨架构汇编教材及AM625八个汇编案例集中到
`obsidian-sadboard/11-汇编与体系结构/`，按基础知识、x86、ARMv7、ARMv8、RV32、RV64、
编译反汇编与调试、AM625汇编实验八个二级目录管理。ABI与数据模型继续在补充知识附录
维护，通过课程导航引用。首页、案例索引、案例/工具反链和工作区指南同步更新。

共迁移20篇笔记；原163篇笔记全部保留，787个代码块逐字且按原顺序保留。
工作区与独立仓库文档检查通过：1533个标题、2876个双链、工作区核对136个源码路径。
检查器增加汇编分组、教材入口及AM625案例归属检查，缺失架构入口或教材的负例均被拒绝。
本次只整理文档与主机校验，不修改设备程序、不生成新固件；历史静态编译与AM625实测范围不变。

## 2026-11-11：操作系统与常用硬件基础教材

新增第13章操作系统原理，按执行保护、进程调度、内存、并发通信、文件与设备I/O、
时间可靠性、性能排队分为7篇正文。新增第14章常用硬件知识，15篇正文覆盖电平、
推挽/开漏/上下拉、时序与测量、常见元器件、电源时钟复位、UART/RS-485、I²C/SMBus、
SPI/QSPI、CAN/CAN FD、以太网、USB/PCIe、I²S/PWM/ADC/DAC、SoC/MMIO/DMA、
DDR/SD/eMMC/Flash及原理图到AM625 DTS的对应。每章有独立导航，44个原案例增加原理反链。

教学计算核对上拉电阻上下界、RC上升时间、灌电流、UART有效字节率、I²S时钟和ADC理想LSB；
数值仅对应文内假设，不作为当前板卡实测参数。开漏/低有效、电气层/协议层、软件枚举/波形测量、
SD既有验证/eMMC等其他介质能力分别说明；参考原厂协议、芯片与Linux文档。

共新增24篇笔记（22篇正文、2篇导航）。原有163篇笔记及787个代码块逐字且按原顺序保留；
工作区和独立仓库文档检查通过：187篇笔记、1702个标题、3117个双链，工作区核对160个源码路径。
两条主机DTS只读命令执行成功，补丁空白检查通过。辅助记录位于被忽略的
`output/validation/os-hardware-foundations/`。

本阶段只修改教材和维护说明，正式案例仍为75例；未改目标程序或构建配置，未发布内容相同的
OTA包，也未重新注入故障或采集电气波形。板端只读示例尚未在本轮执行，AM625功能验证沿用
此前各案例的独立记录；源码核对不代表新的硬件功能验证。

## 2026-11-12：教材逐章审校与机制推演补充

检查第00～14章和附录A～D共19个章节/附录，修订90篇现有笔记。保持原有187篇笔记、
75个案例及796个代码块；没有增加内容重复的计划文档或新的正式案例编号。
各章本轮补充如下，既有实机验收与本轮文档校验分开记录。

| 章节 | 审校与完善内容 |
| --- | --- |
| 00 实验准备 | 将泛化现象转换为请求、对象、时间窗与反证条件 |
| 01 应用崩溃 | SIGSEGV/ABRT、越界迟到破坏、栈与映射后备的区分 |
| 02 文件描述符 | FD表、打开对象、订阅与引用拥有关系 |
| 03 内存与OOM | 提前ENOMEM、驻留、引用保留、OOM与外部SIGKILL诊断表 |
| 04 CPU性能 | 算法、忙轮询、日志、EPOLLOUT与局部性的不同证据 |
| 05 锁与线程 | 锁等待、死锁、谓词、事务与可停止性 |
| 06 网络分析 | 字节流/数据报、端序、队列、截断与断连状态 |
| 07 启动恢复 | 失败阶段、首错、PID1语义和故障/恢复操作入口 |
| 08 性能优化 | 成本所在时间段、同输入结果与优化代价 |
| 09 内存优化 | 对象、allocator、内核内存、DMA与会话生命周期 |
| 10 网络优化 | 批量、背压、ET公平、PMTU、RPS、QoS和重连边界 |
| 11 汇编 | 数据宽度/扩展、架构状态、ABI、重定位与地址换算例子 |
| 12 内核子系统 | 九个框架逐一增加具体状态、条件分支与证据推演 |
| 13 操作系统 | 七篇补充系统调用、调度、分页、交错、持久性与排队推导 |
| 14 硬件 | 十五篇补充电路、时序、协议、器件、DMA与板级分析练习 |
| 附录A | 增量构建、配置/工件核对与诊断恢复条件 |
| 附录B | Bootlin方法迁移到AM625的适配验收表，保留来源及许可 |
| 附录C | 进程内ABI与跨设备二进制协议的不同责任 |
| 附录D | 24篇工具补充数据口径、丢记录、扰动和推断边界，精简重复说明 |

修正七个基础章节把已实现案例称作“新增设计”的旧描述，澄清super_block与挂载关系，
以及initramfs的/init已经是PID1、switch_root通常保持PID的语义。核对源码目录表的75项
入口：73项设备命令与2项主机RAM启动控制；启动五例去除通用verify歧义，补齐主机控制与
内核模块共同操作直链，明确run-only和重启后check，未改变原命令块或恢复门禁。

依据Linux接口/本地实现、原厂资料和ISA/ABI文档核对关键表述；重新计算21项教学数值，
包括RC系数/并联上拉与电流、分压与电容、SPI时序、CAN位时间、UART/I²S/ADC、
排队和地址换算。计算使用文内假设，不作为板卡实测参数。
工作区与独立手册校验均通过：187篇笔记、1852个连续编号标题、3138个双链；
工作区检查160个源码路径。补丁空白检查及全部原代码块保留检查通过，辅助审校记录位于
被忽略的 `output/validation/chapter-review/`。

本轮只修改文档，未改固件或构建配置，没有重新构建/发布OTA、触发整机故障或采集硬件波形。
原AM625运行结果仍以各案例历史验收为准；本轮的命令入口核对、数值检查与源码推演不冒充
新的实机验证或对全部生产边界的穷尽证明。

## 2026-11-12：多核SMP与异构系统课程

新增 `obsidian-sadboard/12-内核子系统/10-多核SMP与异构系统/`，包含导航与七篇正文：
框架与SMP/AMP/UMA/NUMA/SMT、Arm64次级CPU/PSCI/IPI与热插拔、运行队列/亲和/IRQ分流、
缓存一致性/内存序/per-CPU/锁、remoteproc/RPMsg及跨固件拥有权、AM625只读取证、故障定位与优化。
配套软件管理关系图、条件源码路径、自测和八个递进学习安排；复用K-SCHED01、A-P04、
B-SYNC04、B-SYNC02、A-P08、A-N06、A-M05、B-BOOT05，各案例增加反链。

内核总导航、案例索引、汇编/OS/SoC相关入口及工作区指南同步更新。课程扩展为十章、70个学习安排，
复用51个独立案例；正式案例总数仍75，未增加故障实现。检查器登记新章，保留每章5～10个案例、
逐例源码/证据任务和反链要求；缺失新章或案例反链的内存负例均被拒绝。

通过SSH逐条执行新取证篇的22条只读命令，全部成功。Linux 7.0.0，boot ID为
`678087b2-b3fa-437e-b77f-9a19dfa52de6`，网络调试参考ID为
`0fd5a423f9e30f4a81891cc8862462d25a2a6df2c8f01f99a83bcc9f39e9f4f5`。
possible/present/online及只读进程允许集合均0-3；CPU0的thread_siblings_list为0；
index0为L1 Data、64字节行、共享列表0，index2为L2 Unified、共享列表0-3。
取得各CPU IRQ/IPI与softirq计数，remoteproc/RPMsg设备目录为空。计数是累计快照，
不作为吞吐、延迟或CPU0瓶颈结论；管理mailbox中断也不证明远端业务RPMsg已连通。

核对当前板级DTS的M4F/R5F Linux节点disabled，以及构建树SMP/NR_CPUS/HOTPLUG_CPU等配置；
区分框架编译、Linux实例与早期R5管理固件。初探发现目标没有getconf，教材改用实际可读的
CPU集合/sysfs，未安装新工具。未占用串口、改变CPU在线或亲和设置、修改管理IRQ/RPS、
启停远端固件，也未注入故障或重新运行原八例。只读结果不替代热插拔、隔离、缓存一致性流量、
实际RPMsg或异构故障恢复验证。

工作区与独立手册检查通过：195篇笔记、1916个连续编号标题、3223个双链，工作区核对182个源码路径。
原187篇笔记及796个代码块完整保留，新增八篇笔记。辅助源码/取证/保留检查记录位于忽略目录
`output/validation/multicore-course/`。本轮只改教材及主机文档检查，不构建或发布内容相同的OTA固件。

## 2026-11-12：教材学习顺序、系统调试与优化分组及编译基础

手册顶层改为六个学习部分：01常用硬件知识、02操作系统原理、03汇编与体系结构、
04内核子系统、05实验准备与通用方法、06系统调试与优化。原基础和进阶的十个单元
归入 `06-系统调试与优化/`，集中管理原理、源码、工具应用、定位及优化；59个案例的
实现、编号和入口不变，16个A64/内核专用案例继续在所属课程维护唯一正文。

原附录C的ABI与数据模型并入操作系统章节，删除被总导航吸收的旧附录导航，工具手册由D顺延为C。
操作系统内部按ABI、编译、执行保护、调度、内存、并发、I/O、时间可靠性和排队排列；
新增三篇编译原理教材，覆盖预处理/词法语法/语义、AST/IR/SSA、后端、符号与重定位、
ELF/动态加载、BSP链接与裸镜像、优化/未定义行为/DWARF及交叉目标核对。
案例索引、工具反链、源码入口、前后章节导航和工作区指南同步更新，保留个人Obsidian配置。

逐条执行编译教材的32个shell代码块。主机使用GCC 14.2.0和Clang 19，普通链接、共享库及O2
三种变体均输出 `result=17`；确认直接链接版不依赖libcalc.so，共享库版的NEEDED包含该库、
RUNPATH保留字面 `$ORIGIN`；生成LLVM IR并核对目标信息。当前Buildroot工具链生成AArch64、
ELF64、小端目标文件，仅编译并检查ELF，未将其作为本轮AM625执行证据。
diff返回1表示两份汇编存在差异，按预期解释，不作为失败。

独立手册和工作区检查通过：198篇笔记、1950个连续编号标题、3281个有效双链，工作区核对
182个源码路径；75例覆盖与十章70个内核学习安排不变。迁移前195篇中194篇保留，
一篇无代码块的冗余导航被吸收；逐篇核对821个原有代码块，内容和顺序全部保留。
新增四篇为系统调试总导航及三篇编译正文，硬件15篇、操作系统11篇正文。
检查记录与主机练习输出在忽略目录 `output/validation/curriculum-order/`，产物在
`output/learning/compiler-basics/`。补丁空白、当前目录引用及Obsidian设置保留检查通过。

本轮只整理和补充教材，未改设备程序、构建配置或固件内容，未触发新的整机故障、
重新验收原75例或发布相同内容的OTA；历史档案中的旧目录名仍表示各次验证当时的结构。

## 2026-11-12：独立编译构建课程、交叉编译练习与案例导航命名

编译课程从操作系统中移出，独立为 `03-编译原理与构建系统/`，保留原三篇编译/链接/优化教材，
增加总导航及交叉编译、Buildroot、Yocto三篇教程。顶层依次为硬件、操作系统、编译构建、
汇编、内核、系统调试与优化；实验准备及两个索引移入第6章的 `00-实验准备与通用方法/`。
十个基础/进阶子类保留自己的导航，文件名与目录同名，例如 `01-应用崩溃/01-应用崩溃.md`，
没有合并到一份大导航；原现象区分与学习检查保留，所有双链与前后章路线同步更新。

交叉编译教程补齐build/host/target、sysroot/rootfs/DESTDIR、SDK环境、Make/CMake、
Autotools与pkg-config、ELF/动态依赖及设备执行验收。实际按正文执行28个shell代码块，
另有一个可选SDK环境source步骤没有混入测试终端；检查三份产物均为AArch64、ELF64、小端。
直接GCC版、Make版和CMake版分别上传AM625自己的临时目录执行，均输出
`toolchain-demo: pointer=8 value=17` 并退出0，随后只清理本次临时文件。
设备boot ID仍为 `678087b2-b3fa-437e-b77f-9a19dfa52de6`，没有重启或注入新故障。

Buildroot篇覆盖原生配置、external注册、包框架、host/target/staging、重建阶段、
rootfs/打包、SDK和复现边界。在独立ignored输出树完成标准defconfig解析、help和
savedefconfig导出；另将文内教学external/Config.in/.mk原样落地到ignored练习目录，
用原生defconfig选择示例包，确认框架解析的SITE_METHOD=local及LICENSE=NOASSERTION。
没有完整重建该示例包、板级镜像或SDK，不将配置解析当作这些构建成功的证据。

Yocto篇以5.0.13/Scarthgap教学标签为基线，讲layer、recipe、任务、依赖、包/镜像、sstate、
标准SDK与当前BSP适配边界。远程核对官方tag，提交为
`f16cffd030d21d12dd57bb95cfc310bda41f8a1f`；核对对应genericarm64配置是SystemReady/EFI参考平台，
不是当前ALIENTEK板BSP。该系列支持列表未列当前Debian 13，文内要求按其支持环境准备，
不声明完成BitBake元数据解析、Yocto包/镜像/SDK构建或本板Yocto启动，不使用QEMU。

文档检查通过：202篇笔记、1987个连续编号标题、3315个有效双链和182个本地源码路径；
原75例及十章70个内核学习安排不变。逐篇核对原198篇、854个代码/证据块内容和顺序完整保留，
新增三篇教程的67个shell块通过bash语法检查；十个子类导航均与目录同名，个人Obsidian配置未改。
主机配置、源码核对和运行日志保存在ignored的 `output/validation/toolchain-course/`；
所有练习输入与产物放在 `output/learning/`。本轮没有修改设备固件或产品构建配置，
没有发布重复内容的OTA，原案例的历史实机验收范围继续按各自档案解释。

## 2026-11-12：导航文件命名整理收尾

复核原十个案例子类导航已经与目录同名，继续将其他课程、十个内核子系统、实验准备、
汇编实验及附录中的21个旧导航统一为目录同名文件；全部31个导航采用相同规则，
不再保留 `00-章节导航.md`。更新全库双链、工作区入口、贡献指南与文档检查器，
没有移动案例正文或修改设备实现。历史验证档案中的旧名称仍表示当时结构。

工作区与独立手册检查通过：202篇笔记、1987个编号标题、3315个双链和182个源码路径；
75例及内核学习安排不变。逐篇检查原命令/证据块内容与顺序、31项同名导航、旧链接残留和
个人Obsidian配置，记录位于ignored的 `output/validation/navigation-names/`。
本次仅文档结构收尾，未构建或发布相同固件。完成提交推送后继续进阶课程第一阶段。

## 2026-11-12：进阶教程第一阶段——启动主线、驱动模型与自己的修复验收

教材定位为约三年BSP经验、能够阅读源码但需要形成机制解释与诊断体系的工程师。
增加AM625从ROM、R5/A53 SPL、ATF、U-Boot到本地FIT/initramfs或TFTP/NFS、systemd及业务就绪的
正常启动主线；明确实际路线、阶段输入与交接条件，不把不同启动分支拼成一次调用栈。
新增第11章设备模型与驱动核心，按匹配、固件属性、延迟探测、probe失败回收、remove异步停用
组织K-DRV01～05，附条件源码路径、对象/资源账本、反证、修复和适用边界。

五例使用手动加载的独立sadboard-driver模块、真实platform总线及自有设备，命令为
driver-match/property/defer/unwind/remove。保存初始/最终JSON、modalias/uevent、sysfs绑定、
deferred列表、内核片段及清理状态；公共入口沿用健康确认、受管unit、资源预算和共享实验flock。
匹配使用平台名字，属性使用软件节点，defer使用显式ready门与核心重试；没有以此证明真实DT
外设、clock/regulator供应者、IRQ或电气已验证。失败保留仅96字节且有最终回收者，remove案例
仅观察模块保留对象上的迟到回调，未制造无界泄漏或真实UAF，也没有卸载网卡、MMC等管理驱动。

新增 `sadboard evaluate crash /绝对路径/程序`，运行学习者候选ELF快照，保存SHA256、十项输入表、
原始stdout/stderr与摘要。分别约束正常输入、缺失记录、无效参数，带CPU/文件输出/core及外层unit
预算；check复算快照hash并核对原始证据。当前仅覆盖B-CR01十输入契约，不是恶意代码沙箱或
全部案例的通用自动评分。实机发现BusyBox不支持sha256sum -c，已改成基础计算与直接比较。
教材给出独立源码目录、原生Makefile/交叉编译、匹配符号、临时上传、候选验收和归档流程。

原生回归28项和结果目录策略4项通过；Buildroot sadboard-labs-rebuild及all完成，AArch64 ELF、
模块、源文件、调试段及全部清单hash检查通过。发布固件保持v0.0.1，内容ID为
`f50301694c4ae38131a4bd5b4f510790ecaa8cc86e75af94430ce3692b2820da`。
只上传/发布release、kernel、rootfs三个ITB；OTA服务记录成功1、升级失败0、设备异常0。

先在旧NFS系统的独立临时目录完成五例verify/check、修复候选通过与原故障拒绝，以及篡改快照hash
或modalias证据后拒绝通过、恢复原证据后通过。这部分只证明暂存程序，不冒充新整机启动验证。
之后经UART切到正常本地A/B模式，暂存网络开关为0以保证OTA重启仍走本地；升级后boot ID为
`78f486e4-2dde-4f12-9591-d68bd64af97c`，kernel/rootfs使用A槽、部署0已confirmed。
运行镜像内五例verify/check、crash与fd回归，以及候选修复成功/原故障失败，均符合契约。
WDT active，systemd失败服务0，SOL同步正常、启动缓冲已确认归档、archive-pending=0。
未刷factory镜像、未调整分区，未升级SPL/U-Boot二进制。

板卡使用本地根时，以现有sync-artifacts脚本部署匹配TFTP文件与rootfs.tar，保留NFS实验结果及
machine-id；随后恢复保存的tftp_kernel=1、nfs_root=1。网络启动boot ID为
`6e08b923-d469-44e0-a2b4-d82bf89b8b71`，参考构建ID为
`50f557e82033bd4a4459829861a0593665a458c6c54e69264b5d5bf9c621c54f`，确认标记netboot。
再次通过五例verify/check、五例run/check/reset；按教材原生Make流程构建的候选通过evaluate/check。
主机普通用户可直接读取NFS结果与候选快照，三个新程序/模块的设备hash与构建target逐一匹配，
结束后实验模块、平台设备与owner标记均清理。生产OTA在网络调试模式继续停用。

真实只读观察确认CPSW设备对应am65-cpsw-nuss驱动和运行OF节点；采集当前FDT并以host dtc解析。
新增十篇笔记，补充dmesg独立手册及双向场景链接；原202篇的929个命令/证据块内容与顺序保留，
新笔记97个shell块通过语法及前置说明检查。全库212篇、2072个连续编号标题、3394个有效双链、
193个本地源码路径检查通过；案例增至80个，内核十一章75个学习安排复用56个独立案例。
旧75例继续按历史批次解释，没有声明本轮重跑全部破坏性案例或完成真实外设依赖/IRQ/RCU/PM课程。

构建、候选、篡改反证、两种启动模式、OTA服务回执及原始UART记录位于ignored的
`output/validation/advanced-phase1/`；匹配源文件、配置、vmlinux和模块另保留在该目录的debug副本。
当前正式产物与学习符号仍位于 `output/am625-debug-systemd/images/`。

## 2026-11-12：进阶教程第二阶段——内核并发与异步执行

新增第12章“中断与异步执行”，配套五个手动内核案例：K-ASY01 async-coalesce验证重复pending的work
不会替业务保存16个事件；K-ASY02 async-ordered验证慢工作阻塞同一有序队列中的控制工作；
K-ASY03 async-predicate区分等待队列通知与业务谓词；K-ASY04 async-reference验证创建者与回调的
kref交接；K-ASY05 async-stop验证等待谓词缺少停止条件会让kthread等到超时才退出。

使用独立sadboard-async模块、真实workqueue/waitqueue/kref/kthread及共享实验flock，不接触管理网卡、
存储驱动、MMIO、CPU在线状态或物理IRQ。引用故障通过隔离对象观察逻辑释放，全部回调退出后才真正free，
未制造真实UAF。工作与线程有有限等待和统一清理；性能结论以因果关系为准，不将门控交错或超时粒度
写成真实业务截止时间。实际物理IRQ、RCU和lockdep专项继续列为覆盖缺口。

每个变体保存20字段摘要、单调ns/事件/value/CPU/PID/上下文CSV、独立模块函数ftrace和每CPU丢记录统计。
trace使用私有instance、mono时钟、每CPU64KiB及模块过滤，保留实际filter后清理自己的实例。
check同时核对结果、原始因果、回调入口及overrun/dropped events。实机默认函数输出不带模块名，
已用独立filter与函数入口共同核对，避免将格式差异误判为未执行。

在旧NFS系统独立目录暂存运行五例verify/check通过；有序队列证据中的控制事件值篡改、非零overrun、
缺失函数trace均被拒绝，恢复原始文件后通过。此部分记录旧网络参考50f557e8及暂存模块，不冒充新镜像。
原生回归28项通过；Buildroot包重建与all完成，AArch64程序/模块、匹配源文件、调试段及清单hash检查通过。

发布固件保持v0.0.1，完整内容ID为
`15b46b0796c06822f5568bcce2bd5cc29cbca62c190f3f34d706c16eb834b0eb`。
只发布release/kernel/rootfs ITB，经正常本地OTA升级至部署1、kernel/rootfs B槽并confirmed；
启动ID为 `6e960224-6ab1-41ed-aa19-7a036d3ec7a1`。服务端确认成功1、升级失败0、设备异常0。
运行镜像内五例verify/check、driver-remove与crash回归均通过。另用自己的canary trace实例验证
其内容、开关和全局tracer在实验前后不变；主动reset运行中的async-stop后，模块/owner/trace清理完成，
现场标记cancelled=1，check正确拒绝将不完整实验当成通过。

板卡仍用本地根时同步匹配TFTP/NFS产物，保留原NFS结果与machine-id，恢复保存的两个网络开关为1。
网络启动ID为 `1ebdf6af-d6a9-4f55-aabf-09d4f5e1bc17`，参考构建为
`cf5527d8ef32d554fcc82c625b546b35088a517b3baa56c5a59e40509ff72224`，确认标记netboot。
五例run与verify分别通过check/reset，主机普通用户可读取JSON、CSV和函数trace；设备check-result、
run-async及模块SHA256与构建target逐一匹配。结束时无实验模块、owner或trace实例，WDT active、
systemd失败服务0、SOL同步正常且archive-pending=0。未更改分区、刷factory或更新SPL/U-Boot二进制。

七篇新笔记包含框架、同名导航和五例完整教材；补充GIC/IRQ domain/handler到线程处理的条件源码地图、
等待发布、引用交接、退出协议及真实函数trace解读，并分别注明已执行范围。全库219篇、2143个编号标题、
3456个有效双链、199个本地源码路径检查通过；原212篇的1029个代码/证据块保留，新75个shell块语法与
前置说明检查通过。案例增至85个，其中83个目标命令、2个主机UART入口；内核十二章80个学习安排复用
61个独立案例，没有把复用、只读IRQ统计或理论说明重复算成新故障场景。

匹配debug副本、固件包、原始串口、暂存/本地/NFS测试、取消反证、trace隔离与OTA回执保存在ignored的
`output/validation/advanced-phase2/`。其余案例沿用各自历史批次，未声明本轮重跑全部破坏性场景。
