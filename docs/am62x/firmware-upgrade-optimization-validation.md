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

## 后续顺序

1. 移除健康系统启动路径中的备用 rootfs 长时间联网修复，改为有界后台维护。
2. 健康检查区分暂未就绪和确定失败，增加观察期限与明确结果。
3. 本地持久 OTA 事务和待上报队列，提交后的重启不依赖服务器 ACK。
4. 完善 Linux 命令参数、工厂初始化边界、状态输出及恢复接口说明。
5. 分区配置一致性检查、组件身份、服务端并发与剩余故障验收逐项推进。

本轮还观察到 data 可用空间约 31 MiB，已有存储策略因此降级到 RAM。
需检查缓存配额与清理策略；未格式化、扩分区或删除设备日志。

本地证据位于 `output/ota-validation/0.0.1-upgrade-01-download-errors/` 与
`output/ota-validation/0.0.1-upgrade-02-uboot-transactions/`，生成文件不提交 Git。
