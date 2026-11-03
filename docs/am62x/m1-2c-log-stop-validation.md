# M1.2c：日志停止与 data 卸载顺序

日期：2026-11-03。修复上一子阶段发现的采集器尚未完成退出、data 已开始卸载的竞态。

## 实现

`S01logctld stop` 先确认目标 PID/可执行文件，发送停止信号并最多等待 10 秒退出；随后核对运行时快照中的 `collector-state=stopped` 和 `sync-state=ok`。只有退出和最终同步均确认才报告成功。超时保留 PID 文件并返回错误；同步失败、缺失状态或仍为 running 的过期状态也返回错误。不使用强制终止来冒充同步成功。

`logctld` 在最终采集及停止事件写入完成后，进入 stopped 状态并执行最终同步；该状态由 `logctl status` 展示。

## 验收

| 项目 | 结果 |
| --- | --- |
| 版本 / 内容 ID | `v0.0.1` / `94ca0506956bfcae991e3cc93b9ad17e981a6d1e28c8ad8da1b5350c91dceeb9` |
| 发布 / 设备 | #40 / `1c-63-49-22-c4-f7` |
| 构建 | `output/am625-m1_2c-stop`，package 与完整镜像成功 |
| 主机测试 | 日志回归 9 项、停止脚本 5 项、同步故障注入 2 组通过；真实 FIT 下载逐字节比较通过 |
| OTA | 自动下载安装、重启、健康确认；服务器 success |
| 专项正常重启 | OTA success 后执行一次正常 reboot，最终同步确认先于 ext4 卸载，停止区间无 logctld ERROR |
| 重启后 | 仍为同一固件；boot ID `9a0f88f5-fd55-4a0c-a8f3-38b11b67a518`，confirmed deployment；storage/data-state=persistent，collector-state=running，sync-state=ok，sync-errno=0 |

实机串口关键顺序：

```text
stopped /usr/sbin/logctld (pid 144)
[logctld] [INFO] collector stopped after final synchronization
[   61.443679] EXT4-fs (mmcblk1p15): unmounting filesystem ...
[   63.470142] reboot: Restarting system
```

证据和工件保存在 `output/ota-validation/0.0.1-m1-2c-stop/`，包含原始串口、正常停止片段、服务器与事务快照、测试/构建日志、文件校验和及源码快照。生成物不提交 Git。

## 边界

仅在实机验证正常停止和正常重启；超时、最终同步失败和过期快照分支通过主机夹具验证。停止超时会返回错误，但现有整体关机流程仍会继续，不能保证真实 I/O 永久挂起时保住全部数据。突然掉电、空间配额、容量耗尽及 eMMC 验收仍待后续阶段。
