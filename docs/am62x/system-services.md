# AM625 系统服务与健康检查

主 rootfs 使用 systemd；独立 initramfs 的 /init 调用 fwctl init，完成校验与切根后
启动正式系统。PID 1 独占 /dev/watchdog0，运行和重启期限均为 60 秒，避免双重喂狗。

## 服务职责

| 服务 | 职责 |
| --- | --- |
| bsp-data | 挂载已有 data，检查可写性；不自动格式化，失败时日志/下载可降级到 RAM |
| systemd-networkd | 配置 lo、eth0；不把载波或远端在线作为本地启动前提 |
| bsp-can / pdm | 板级 CAN、PDM 装载及停止顺序 |
| psatellited | 前台业务，READY/WATCHDOG 与有界重启 |
| pdebug-web | 前台 lighttpd；遥测 ptelemetryd 是否启用由 preset 配置 |
| fwctld | OTA 轮询、安装协调及结果上报，网络未就绪时等待 |
| logctld / logctl-journal | 启动证据、journal MESSAGE、持久归档与 SOL |
| timectld | 独立时间源、校准及 RTC，不依赖日志服务生命周期 |
| fw-health / fw-confirm | 本地健康观察与部署确认 |
| fw-health-failure | 记录关键失败、拒绝未确认候选并请求受控重启 |
| device-shutdown-intent | 在服务停止前记录软件重启意图 |

AM625 不启动可选的旧 system_manager。硬件 watchdog、服务心跳和端到端业务健康
各有不同边界，不能用一个进程存活替代实际业务验证。

## 配置位置

- 板级 unit、preset、网络、journal 和 watchdog：BSP board/ti/am625/rootfs-overlay。
- 管理服务模板和前台脚本：EDK user/integration/systemd。
- /etc/device-manager/health.conf：当前要求 networkd、lo、eth0 本地配置正常；
  不要求 carrier、BMC 或 OTA server 可达。
- /etc/default/fwctld、/data/fwctld.conf：OTA 默认值与持久覆盖。
- /etc/device-manager/time.conf、/data/timectl/source.conf：出厂与已持久化时间源。
- journal 使用有上限 RAM 存储，logctld 负责持久归档；不启用另一个服务抢先搬走 pstore。

fw-confirm 连续六次健康检查通过才确认部署；等待或锁争用会重置连续计数。
观察和子进程查询都有期限。控制操作和故障注入必须按明确维护流程进行。

## 板端检查

```sh
cat /proc/1/comm
systemctl --failed
systemctl status fw-health fw-confirm fwctld logctld timectld pdm
journalctl -b -u fw-health -u fw-confirm -u fwctld -o cat
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
