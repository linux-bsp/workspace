[[README|首页]] · [[00-实验准备与通用方法/工具索引|工具索引]] · [[00-实验准备与通用方法/案例索引|案例索引]]

## 解决的问题

核对启动日志采集、重启原因、持久化和服务端归档确认。

## 工作原理与准备

启动接力缓冲、ramoops/pstore 与 /data 文件归档是不同层次。需要把失败启动和恢复启动的 ID、版本、重启意图及 ACK 关联起来。

## 参数与结果解释

| 参数/字段 | 含义与判断方法 |
| --- | --- |
| `boot-state` | 查看启动阶段与关联记录。 |
| `diagnostic-reason previous` | 查看上一次启动的诊断原因。 |
| `status` | 查看采集、存储、同步及上传/ACK 状态。 |
| `verify-boot` | 验证当前启动记录完整性。 |

## 操作步骤

设备端：先检查采集、持久化和上报状态。

```sh
logctl status
```

设备端：关联启动阶段与 boot 标识。

```sh
logctl boot-state
```

设备端：查看上一轮启动原因并与原始串口互证。

```sh
logctl diagnostic-reason previous
```

设备端：确认记录完整后再用于问题定位。

```sh
logctl verify-boot
```

## 判断边界

预留 RAM 的暖重启保留不代表完全断电仍保留。pstore 原目录为空也可能表示已归档消费；应同时检查持久目录和服务端确认。

## 使用场景

下面链接直达具体案例的定位章节。基础流程沿用实机验收，扩展工具观测不自动记作已执行。

| 案例 | 本工具的观测目标 |
| --- | --- |
| [[07-内核启动与恢复/B-BOOT01-内核panic触发后的启动日志取证与恢复/B-BOOT01：内核panic启动日志与恢复#定位方法\|B-BOOT01：内核panic启动日志与恢复]] | 关联失败与恢复启动的日志、原因及上报确认 |
| [[07-内核启动与恢复/B-BOOT02-initramfs动态加载器缺库导致PID1退出/B-BOOT02：initramfs 动态加载器缺库导致 PID 1 退出#定位方法\|B-BOOT02：initramfs 动态加载器缺库导致 PID 1 退出]] | 关联失败与恢复启动的日志、原因及上报确认 |
| [[07-内核启动与恢复/B-BOOT03-根设备或文件系统参数错误导致VFS启动失败/B-BOOT03：根设备或文件系统参数错误导致 VFS 启动失败#定位方法\|B-BOOT03：根设备或文件系统参数错误导致 VFS 启动失败]] | 关联失败与恢复启动的日志、原因及上报确认 |
| [[07-内核启动与恢复/B-BOOT04-内核Oops与panic策略的区别/B-BOOT04：内核 Oops 与 panic 策略的区别#定位方法\|B-BOOT04：内核 Oops 与 panic 策略的区别]] | 关联失败与恢复启动的日志、原因及上报确认 |
| [[07-内核启动与恢复/B-BOOT05-soft-lockup、RCU-stall与硬件watchdog复位归因/B-BOOT05：soft lockup、RCU stall 与硬件 watchdog 复位归因#定位方法\|B-BOOT05：soft lockup、RCU stall 与硬件 watchdog 复位归因]] | 关联失败与恢复启动的日志、原因及上报确认 |
