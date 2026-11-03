# M1.2a：data 启动健康检查与服务降级

日期：2026-11-03。本子阶段交付启动时的只读、空闲空间和写入探测，以及日志与 OTA 服务对存储状态的消费。M1.2 的配额、同步错误传播、运行时故障和断电验收仍待完成。

## 实现

- `S00data` 在挂载后检查 `/proc/mounts` 的读写标记、`df -Pk` 的可用空间及临时文件写入。结果原子写入 `/run/device-manager/storage-state`，区分 `persistent`、`read-only`、`low-space`、`unavailable`。
- 板级 `storage.conf` 增加 `minimum_free_kib=32768`。这是本阶段的固定启动阈值；架构计划中的容量比例和 OTA 实际空间预算尚未实现。
- `S01logctld` 与 `S98fwctld` 仅在状态为 `persistent` 时使用 data，否则分别选择 RAM 日志目录和 OTA 缓存目录。启动时明确打印降级原因。
- `logctl status` 增加 `data-state` 字段。启动检查不格式化介质，不修改 A/B 分区布局。

## 构建与实机结果

| 项目 | 结果 |
| --- | --- |
| Buildroot 输出 | `output/am625-m1_2b`，target package 重建与完整镜像生成成功 |
| 版本 / 内容 ID | `v0.0.1` / `443a7372995915849de9f61b8d8b089e6d1f2a1c9052f5a950836f878460c905` |
| 发布 / 设备 | #38 / `1c-63-49-22-c4-f7` |
| 新启动 ID | `adacb97b-3dac-4f32-aba1-27d619d01359` |
| OTA 验收 | 自动下载、安装、重启；健康确认后服务端记录 `success` |
| 存储验收 | ext4 r/w 挂载；`data filesystem mounted read-write with sufficient free space` |
| 日志验收 | `storage=persistent cross-boot=verified`，前次 marker 可读 |
| 传输检查 | 真实 FIT 包在临时 feed 下载并逐字节比较通过 |

工件、原始串口、服务器状态、设备事务、文件 SHA256、Buildroot 配置、编译包源码和待提交源码差异保存在 `output/ota-validation/0.0.1-m1-2-data-health-fix/`。生成物不提交 Git。

## 修复过程与限制

先前发布 #37 的启动脚本使用了目标系统未提供的 `awk`，虽然设备通过 OTA 健康确认，存储状态却降级为 unavailable，因此不作为本阶段验收版本。#38 改用 shell 内建 `read` 解析挂载标记与 `df` 输出，实机启动未再出现该错误。

本阶段只验证 SD 卡正常启动路径。只读、低空间、满盘、I/O 错误、运行期间状态变化、RAM 缓存容量边界和突然掉电均未完成实机故障验收；ext4 日志仍显示 `Quota mode: none`。下一子阶段应实现有界空间预算、同步失败传播与故障夹具，再执行对应实机验证，不能将本次 success 解释为整个 M1.2 已完成。
