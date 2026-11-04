# AM625 OTA 启动失败与异常日志实机验证

日期：2026-11-04。通过真实 OTA 故障包验证升级后无法启动、自动回退、日志补传及隔离重发，并恢复两槽正常固件。

## 结论

采集与上传链路通过：最后一次失败启动和恢复启动的 SPL、U-Boot、kernel 已进入服务器独立归档，八段 CRC 正确、dropped=0，网页可查看和导出。

OTA 详情附件链路存在缺口：异常事务记录了 `linux-panic-observed` 和 `rolled-back`，但按现有 Linux 异常“只上报原因”策略，事故接口是 `mode=reason-only, bytes=0`。启动缓存归档未与 OTA 事故附件建立关联。当前可在 SOL 查到真实失败日志，不能宣称 OTA 详情已有日志附件。

## 故障与恢复过程

- 正常基线：`v0.0.1 / 6fada4df`，发布 45，A 槽 deployment 0 已确认。
- 故障包：`v0.0.1 / eec785bd`，发布 46，完整 ID `eec785bdea671164bd09c7ef4685c54b66b3b384d9e5b234622b374fe1a09477`。
- 故障只在隔离工件中的 initramfs `/init`：挂载 proc/dev，写入测试标记，设置 panic 后 3 秒重启，PID 1 以 73 退出。正式源树没有加入故障代码，rootfs 与正常包逐字节相同，bootloader 没有升级。
- 使用正式打包器生成 initramfs、FIT、身份与 release；先通过实际上传/下载及字节对比，再上传发布。设备正常校验并写入备用 B 槽，随后重启。
- 物理串口观察到 3 次 `Attempted to kill init! exitcode=0x00004900`，均在正式 rootfs 运行之前。SPL 耗尽 3 次尝试，将 deployment 1 标记 failed，自动回退 deployment 0。
- 回退后启动 UUID `6ea6121b-cad1-4d9d-83f6-5c7359438f1e`，重新通过健康检查、联网校时，然后补传两组缓存。
- 后台收到 `rolled-back / linux-panic-observed`，自动隔离发布 46，并将正常内容 `6fada4df` 重新发布为 47；同一时间只有 47 生效。
- 保留异常归档后，用正常发布 47 强制修复 B 槽。设备在 B 槽重启并通过健康检查，服务器为 `success`；最终启动 UUID `e85943fb-a2ef-42e7-b035-47f439ab1b66`，两 deployment 都为 confirmed/successful，data 为 persistent，日志同步为 ok。

已核对故障包缓存 SHA256 与服务器工件一致，恢复正常固件后移除设备缓存中的三个故障 ITB，保留缓存元数据、服务器故障包和全部日志；data 恢复到约 92 MiB 可用。

## 实际收到的日志

服务器首次接收时间：`2026-11-04 10:58:24 +08:00`。该时间是归档接收时间，不冒充 panic 发生的 UTC 时间。

| 阶段 | 失败启动字节 | 恢复启动字节 | 完整性 |
|---|---:|---:|---|
| R5 SPL | 418 | 544 | CRC 正确，dropped=0 |
| A53 SPL | 322 | 322 | CRC 正确，dropped=0 |
| U-Boot | 3010 | 3010 | CRC 正确，dropped=0 |
| kernel | 20171 | 20606 | CRC 正确，dropped=0 |

失败 capture：`dab591db-9258-4a34-8d2f-ff37d3ee3fcc`，bank 0、generation 3，共 23921 字节。恢复 capture：`96c60157-9a6e-4080-830c-388fccb27832`，bank 1、generation 4，共 24482 字节。

失败原文包含故障固件 ID、B 槽 FIT 信息、启动命令行、PID 1、退出码、CPU、调用栈和重启信息，例如：

```text
[    1.476449] OTA_BOOT_FAILURE_TEST: initramfs PID1 exiting status=73 before rootfs
[    1.484081] Kernel panic - not syncing: Attempted to kill init! exitcode=0x00004900
[    1.491739] CPU: 1 UID: 0 PID: 1 Comm: init Not tainted 7.0.0 #15 PREEMPT
[    1.503672] Call trace:
...
[    1.522637]  do_exit+0x8e8/0x8f0
...
[    1.584487] Rebooting in 3 seconds..
```

服务端 API 原始字节与 SQLite BLOB、清单长度/CRC 和独立 SHA256 对比一致。浏览器收到完整原始字节，导出内容与终端文本一致；网页按终端语义处理 CR、换行和倒计时覆盖，因此导出不是逐字节物理 UART 镜像。

## 查看与工件

打开 Device Manager 的 SOL，在启动记录中选择 `2026-11-04 10:58:24 +08:00`、上次未确认启动 `dab591db`；选择“全部”可看 SPL 到 panic，选择 kernel 可直接定位调用栈。正常恢复记录为同秒的 `96c60157`。又一次正常 OTA 修复 B 槽后，两份旧归档仍可读取，SHA256 未变。

工件目录 `output/ota-validation/0.0.1-ota-boot-failure/`：

- `logs/2026-11-04_10-58-24+0800_startup_dab591db.log`：失败原始四阶段合并日志，另有每阶段文件。
- `logs/2026-11-04_10-58-24+0800_startup_96c60157.log`：回退恢复原始日志。
- `web-exports/`：与网页显示一致的可读导出。
- `panic-excerpt.log`、`full-physical-serial.log`：panic 摘录和服务器物理串口测试全过程。
- `archive-verification.json`：八段长度、CRC、SHA256、capture 与清单。
- `failure-state.json`、`ota-incident-evidence.json`、`restored-success-state.json`：失败、附件缺口、正常恢复回执。
- `browser-verification.json` 与截图：实际网页选择、导出和 OTA 详情只报原因的证据。
- `images/`、`scripts/`、`fault-definition.json`：隔离测试包及故障定义，不提交或合入正式固件。

## 边界与待优化

双缓冲覆盖最后两次未归档启动。本次连续 3 次失败后再恢复，服务器保存最后一次 panic 与正常恢复；前两次失败被轮换覆盖，只有外接物理串口工件保存了三次全过程。

本次没有模拟掉电、DDR 丢失、Linux console 注册前异常或 data 损坏；未接入的 ROM/TIFS/ATF 直接输出也不能由此机制保证保存。capture ID 与实际 Linux boot ID 不等同。

下一步应把有可靠身份、清单及回退关系的早期启动归档关联到 OTA 事故，并在异常详情提供查看/下载入口。现有 pstore 原因只是 observed，不应把恢复启动 UUID 当作发生 panic 的启动 UUID；关联失败时仍应保留可查询的 SOL 归档。
