# AM625 固件升级优化记录

版本保持 `v0.0.1`；以下阶段均保留独立工件、源码快照、串口和服务端事务记录。

## 第一阶段：下载失败分类

- 内容 ID：`134ab5d63db1adfb244dc2abda084ba751f66e0af833cba1ab9ecf75801f80e9`。
- 发布 54 在设备 `1c-63-49-22-c4-f7` 重启、健康确认后上报 success。
- 网络中断报告 transport-error，保留已同步缓存并重试；不触发全局隔离。
- 缓存读写失败和内容 SHA256 错误分别报告设备异常、校验失败，继续停发。
- 26 项自动安装测试，以及网络、隔离、退出、真实 FIT 和 ARM64 loader 回归通过。

## 第二阶段：U-Boot 事务保护与命令统一

- 内容 ID：`cc9f8e1115470f2fdca84404a00afb76c38995281f1db97984f24ad65704aa38`。
- 发布 55 在同一设备重启、健康确认后上报 success；最终 kernel/rootfs 为 A 槽。
- U-Boot 对外命令改为 `fwctl`；默认环境 schema 8 同步迁移启动命令及
  `upa/upb/upk/upr`，实际读取保存环境已核对。
- 单独组件更新先保存 WRITING 状态并撤销候选启动，再写备用槽、读回、提交 READY。
  连续更新保留前次已暂存组件；重复更新始终选择已确认源的相反物理槽。
- WRITING deployment 不能被 boot-once、已选启动或 mark-good 当作可用系统。
- 11 项 U-Boot sandbox 元数据测试通过，包括模拟写入期间复位；真实 FIT、
  verity 参数解析、ARM64 initramfs loader 及 A53/R5 交叉编译通过。
- 独立维护部署新版 A53 SPL/U-Boot B 槽，三项引导负载读回 SHA256 与工件一致；
  U-Boot 实机单独更新 kernel 并读回成功，取消候选后正常启动。

维护过程先备份两槽引导、环境和元数据。仅通过受控元数据试启动既有 A 槽进行
维护，再使用显式允许 bootloader 的临时配置安装 B 槽；正式配置仍禁用远程
bootloader 更新。首级 `tiboot3_a`、`tispl_a`、`uboot_a` 全分区 SHA256 均与备份一致。
旧 A 槽引导不支持当前 HWID-only 包，维护启动经过包读回 CRC 与 bootm 的负载
SHA256 校验；不把该过程计为旧 A 槽自动恢复兼容性验收。新版 R5 仅交叉编译和
工件校验，本轮 ROM 仍执行原始 R5 A 槽。

## 第三阶段：启动交接、健康观察与介质校验

- 最终内容 ID：`230ff0b0c6b4a0aaaa6b5cf5a64d860c0b874ceac82f57232ed7c66cca9b9ee2`。
- 发布 57 已重启、健康确认并上报 success，当前 deployment 1、kernel/rootfs A 槽。
- initramfs 只校验本次根分区，尽快 switch_root；备用 rootfs 的检查和精确恢复移到
  健康确认后的后台维护，下载限时 60 秒，不重配网络、不接管看门狗。
- 健康检查区分退出码 75（暂未就绪）和 1（确定失败）。要求连续 6 次成功，最多
  观察 24 轮；失败候选被标坏并回到已确认部署，已确认系统失败则保留诊断入口。
- 备用分区修复校验完整内容身份、拒绝共享当前 rootfs 的槽和进行中的更新，持有
  内核独占分区 claim，拒绝已挂载分区和设备映射占用；已在实机验证只读挂载拒写。
- 故障注入额外发现整盘/分区页缓存别名：分区首字节损坏后，旧整盘缓冲读取误报
  match。最终块后端改为单独 O_DIRECT 校验读取，并在写入同步后通过该路径读回。
  实机对同一损坏同时观察到旧路径 match、新路径 different，恢复后完整校验 match。
- 发布 57 上再次破坏备用 B 槽，`fwctl recovery maintain` 从服务端取得旧发布 56
  对应的精确 rootfs，写入与直接读回成功。元数据仍为 active=1、pending=none，
  两个 deployment 的启动状态未被维护操作改写。

自动化通过：7 组 C 引擎/CLI 测试、8 项健康观察测试、26 项自动安装测试、6 项
恢复测试、4 项真实 FIT 测试、ARM64 loader 和 Linux→U-Boot→Linux 元数据互操作。
直接读取测试包含短头部、未对齐 FIT 尾部、512/4096 字节扇区、溢出及读错误。

同阶段的发布 56 正常启动成功，但后续故障注入暴露缓存问题，因此没有作为最终
源码提交依据；最终以修正后的发布 57 及专项验证为准。未执行真实断电或 eMMC/NOR
实物测试，不能把模拟中断、同步和直接读回当作物理掉电验收。

本阶段证据位于 `output/ota-validation/0.0.1-upgrade-03-boot-health/` 和
`output/ota-validation/0.0.1-upgrade-03b-fresh-read/`。

## 第四阶段：本地 OTA 事务与断网补报

- 固件保持 v0.0.1，正常验证发布 58：`c52d1bd7`；断网专项发布 59：
  `e7f62c95640bd95a98d01319452856c814d5c26c3aaafe420bd9d4d793565a53`。
- 小型事务与有序事件队列独立存放在 `/data/fwctld-state/HWID/DEVICE/`，
  不随下载缓存降级到 RAM。事件先同步落盘，再原子更新快照；重启扫描恢复尚未
  更新快照的有效事件。CRC 保护记录封装，固件身份仍使用完整 SHA256。
- 写入完成后先持久化 rebooting，再重启，不依赖 HTTP ACK。启动确认和回滚
  判定在网络就绪判断之前执行；服务恢复后校对发布的完整身份再有序补报。
- 缺失或损坏的状态存储拒绝自动写入并保留证据；停止 agent 记为取消，
  不误隔离固件。下载后、写入前再次检查当前发布与隔离策略。
- 实机在写入开始后关闭 8090 服务，设备独立重启并确认健康。串口读取 data
  快照证实本地 success、3 条未 ACK 事件；此时服务器仍为 installing。
  恢复服务后，升级历史内 events 依次为 installing、rebooting、boot-testing、
  success，设备队列清空。当前 deployment 1、kernel/rootfs A，bootloader 未改。
- 自动化：35 项自动升级、12 项启动脚本，状态日志的崩溃窗口/同步失败/损坏/
  队列上限，以及网络、隔离、历史、上下文、停止、真实 FIT 和 ARM64 loader。

证据：`output/ota-validation/0.0.1-upgrade-04-offline-proof/`。本轮验证服务端
离线和重启持久化，不等同于物理断电验收。恢复后的 8090 服务继续无凭据调试。

## 第五阶段：下载缓存保留与持久化空间恢复

- 发布 60、v0.0.1，内容 ID：
  `cf647820da44fab5d72132e4036ac78000118b00cf325f70d4c56d329ae38adf`。
- 回收在健康确认、无 pending 且补报已 ACK 后执行，默认保留最近两份完成包和
  current 引用包。RAM 降级时仍保留原持久目录的引用，因此可以释放旧包占用。
- 只清理有效 HWID manifest 与大小相符的三个普通负载文件。数字目录以外的
  下载暂存、事务、日志、未知内容和链接均不删除；中断的 `.gc-*` 可续清理。
- 7 项回收边界测试、36 项升级、12 项启动脚本、事务/目录测试、FIT 和 loader 通过。
- 实机从六份完成包回收到两份，释放 124262 KiB；可用空间从 31252 KiB 增至
  155528 KiB。再次正常重启，storage-state 为 persistent、health-check 为 0，
  日志目录仍保留。当前 deployment 0、kernel/rootfs B，未改分区或格式化。

证据：`output/ota-validation/0.0.1-upgrade-05-cache-retention/`。

## 第六阶段：手动升级参数、组件事务与分区拒写

- 发布 61、v0.0.1，内容 ID：
  `ca3573b64fd974b7d71fde0efdffaefc43ea142809a1d424c3ee6386bda7b53b`。
- `fwctl update kernel /path/release.itb` 等两参数形式可用，参数错误在打开介质前
  拒绝。缺失组件和禁止的 bootloader 请求不再先改 metadata。
- 单组件事务保留 READY 中已暂存组件，重复更新也始终写已确认源的相反物理槽。
  写入前持久化不可启动状态，读回后才提交；WRITING 不允许 mark-good。
- 实际块设备/MTD 的更新入口要求当前启动源等于已确认 active；块负载写入持有
  目标分区的独占 claim，阻止挂载或 dm holder 使用中的分区被覆盖。
- 实机在新系统尚未确认时更新被 EBUSY 拒绝。确认后暂停 poller，连续 kernel、
  kernel、rootfs 暂存到 B；运行 A 的直接 SHA256 校验始终 match。挂载 B rootfs
  后更新被 EBUSY 拒绝，WRITING 候选确认被拒绝。最后完整包重建身份并启动 B，
  health-check=0、两项负载直接校验 match，fwctld 随启动恢复。
- 7 组 C 引擎/CLI 测试、36 项自动升级、8 项健康观察、FIT、ARM64 loader 和
  Linux/U-Boot 元数据互操作通过。MTD 入口保护只做源码/构建验证，没有 NOR 实物验收。

证据：`output/ota-validation/0.0.1-upgrade-06-manual-transactions/`。CLI 与 poller
共用非阻塞存储锁；手动维护宜先停止 poller，锁冲突返回 EAGAIN 时不发生写入。

## 后续顺序

1. 保留独立配置，增加构建时分区一致性检查。
2. 工厂初始化边界、状态输出及恢复接口说明。
3. 组件身份、服务端并发与剩余故障验收逐项推进。

原 data 低空间问题已由第五阶段的受控缓存保留修复；仍需保留空间监控，
不能把有限存储视作无限归档。未格式化、扩分区或删除设备日志。

本地证据位于 `output/ota-validation/0.0.1-upgrade-01-download-errors/` 与
`output/ota-validation/0.0.1-upgrade-02-uboot-transactions/`，生成文件不提交 Git。
