# AM625 系统服务与健康检查

主 rootfs 使用 systemd；独立 initramfs 的 /init 调用 fwctl init，完成校验与切根后
启动正式系统。PID 1 独占 /dev/watchdog0，运行和重启期限均为 60 秒，避免双重喂狗。

## 服务职责

| 服务 | 职责 |
| --- | --- |
| bsp-data | 挂载已有 data，检查可写性；不自动格式化，失败时日志/下载可降级到 RAM |
| systemd-networkd | 配置 lo、eth0；不把载波或远端在线作为本地启动前提 |
| bsp-can / pdm | 板级 CAN、PDM 装载及停止顺序 |
| psatellited / ptelemetryd | 星务接入与遥测执行，向 systemd 报告就绪与心跳 |
| fwctld | OTA 轮询、安装协调及结果上报，网络未就绪时等待 |
| logctld / logctl-journal | 启动证据、journal MESSAGE、持久归档与 SOL |
| timectld | 独立时间源、校准及 RTC，不依赖日志服务生命周期 |
| fw-health | 通过 `fwctl boot-health` 监测本地健康并确认部署 |
| fw-health-failure | 记录关键失败、拒绝未确认候选并请求受控重启 |
| bsp-netboot-confirm | 单独确认 NFS 启动及其构建标识 |
| device-shutdown-intent | BSP 在关机前设置标记，保留 PDM 和 CAN 到复位，并在日志工具可用时记录关机事件 |

systemd 负责硬件 watchdog、服务启动与重启。`fwctl` 负责板级健康策略和 A/B 确认。

## 配置位置

- 板级 unit、preset、网络、journal 和 watchdog：BSP board/ti/am625/rootfs-overlay。
- EDK 服务模板位于 `user/integration/systemd/`。
- `/etc/edk/system.conf` 的 `[health]` 段要求 networkd、遥测和星务单元就绪，以及 lo、eth0 在本机已启用。外部链路状态独立观察。
- OTA、日志和时间的板级默认配置分别位于 `/etc/edk/system.conf` 的 `[ota]`、`[logging]`、`[time]` 段。
- journal 使用有上限 RAM 存储，logctld 负责持久归档；不启用另一个服务抢先搬走 pstore。

`fwctl boot-health` 启动时读取一次配置，每轮对必需单元执行一次限时批量查询。
本地健康持续通过 30 秒后确认部署。服务重启、检查未通过或元数据锁忙会重置观察窗口。

## 板端检查

```sh
cat /proc/1/comm
systemctl --failed
systemctl status fw-health fwctld psatellited ptelemetryd logctld timectld pdm
journalctl -b -u fw-health -u fw-health-failure -u fwctld -o cat
fwctl version
fwctl health-check
logctl status
timectl status
```

日志上传或校时失败不应直接否决已有有效固件。辅助功能降级仍需保留具体原因。
变更健康策略时，先核对实际必需服务和网口，不默认要求 eth1 或 CAN 为平台链路。

历史 systemd 迁移与故障注入结果见
[历史验收](validation-history.md#systemd-migration)，最新版本见
[模块重构验收](edk-module-refactoring-validation.md)。
