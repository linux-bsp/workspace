# AM625 systemd 迁移

AM625 主 rootfs 使用 systemd 管理服务；独立 initramfs 仍由 `/init` 调用 `fwctl init`，完成分区验证、必要恢复与 `switch_root`。固件版本固定为 `v0.0.1`，每次构建以内容 SHA256 区分。分区布局与 A/B 元数据格式不变。

## 服务和职责

| 服务 | 职责 / 故障处理 |
| --- | --- |
| `bsp-data.service` | 挂载已有 data 文件系统，检查可写性与剩余空间；不自动格式化，失败时日志/缓存降级到 RAM |
| `systemd-networkd.service` | 配置 lo、eth0；不等待载波或管理服务器，静态地址由 `.network` 文件管理 |
| `bsp-can.service` / `pdm.service` | CAN 与 PDM 的依赖和反向停止顺序 |
| `psatellited.service` | 前台外设应用，主循环发送 READY/WATCHDOG；15 秒无心跳时由 systemd 终止并重启，限制重启频率 |
| `pdebug-web.service` | 前台运行 lighttpd；`ptelemetryd.service` 默认禁用 |
| `fwctld.service` | 前台 OTA 轮询；网络未就绪时延迟请求，传输失败不使本地健康检查失败 |
| `logctld.service` / `logctl-journal.service` | 保留 SPL/U-Boot/kernel 原有采集，journal 的 MESSAGE 文本接入 services 流，不附加 unit/时间等展示前缀 |
| `fw-health.service` | 评估本地健康策略；systemctl 子进程查询使用单调时钟、输出上限和 1 秒总期限 |
| `fw-confirm.service` | 连续六次健康检查通过后确认部署、记录启动事件，仍由 fwctld 向服务器报告 OTA 结果 |
| `fw-health-failure.service` | 记录关键健康失败，拒绝尚未确认的候选部署，并请求受控重启 |
| `device-shutdown-intent.service` | 服务停止前记录关机意图，辅助重启原因归因 |

PID 1 独占 `/dev/watchdog0`，运行及重启 watchdog 期限均为 60 秒。AM625 不再启动旧 `system_manager`，避免双重喂狗和双重进程监督。systemd 看门狗与应用心跳不是业务链路端到端健康的替代品；尚未加入的业务服务应定义自己的就绪条件、心跳及健康策略。

## 配置位置

- 板级 unit、网络、journal、watchdog、preset：`bsp-base-external/board/ti/am625/rootfs-overlay/`。
- `10-board-ethernet.link` 保留内核分配的 `eth0` 等网口名称，避免 udev 改名为 `end0` 后与恢复环境、OTA 和健康策略不一致。
- Device Manager 原生服务及前台启动脚本：`device-manager/integration/systemd/`。
- 必须健康的本地 unit/网卡：`/etc/device-manager/health.conf`。当前要求 networkd 和 lo/eth0 已配置 UP，不要求以太网载波或远端响应。
- `/etc/default/fwctld` 与 `/data/fwctld.conf` 保留 OTA 配置来源；禁用内置 timesyncd，继续使用 Device Manager 的可配置校时，显示 UTC+8。
- journal 使用有上限的 RAM 存储；logctld 负责 data 归档与 SOL 上报。禁用 systemd-pstore 自动搬移，避免抢先处理已有启动证据。

切换 init 系统应使用新的 Buildroot 输出目录。不要在旧 SysV target 目录上直接增量覆盖后发布。旧 SDK、dl 缓存可以复用。

```sh
BR2_EXTERNAL="$PWD/bsp-base-external" make -C buildroot O="$PWD/output/am625-systemd" alientek_am62x_defconfig
make -C buildroot O="$PWD/output/am625-systemd" all
```

板端检查：

```sh
cat /proc/1/comm
systemctl --failed
systemctl status fw-health fw-confirm fwctld logctld psatellited
journalctl -b -u fwctld -o cat
fwctl health-check
fwctl version
logctl status
```

`fw.rollback_test=1` 仍是明确启用的台架故障注入：未确认部署的健康检查被拒绝；已确认部署不受影响。该测试不能替代真实断电、介质故障和硬件 watchdog 验证。

## 固件管理删除

固件列表末尾增加“删除”，并要求一次浏览器确认。相同 tag 与完整内容 ID 的重复上传一并移除，避免删除后旧副本重新出现在列表。当前发布和正在安装/等待重启/启动健康检查中的固件受保护；发布锁串行化删除和发布。

删除会彻底移除相同版本与完整内容 ID 的上传包、历史发布副本及回退副本，只保留审计元数据和设备升级记录。SQLite `firmware_deletions` / `firmware_removals` 保存完整固件 ID、tag、HWID、来源 IP、时间及请求/完成状态；先记录全部副本的删除意图，再清理负载。已删除的发布只供审计，下载、恢复及自动回退均不能选择；服务重启后继续完成中断的物理删除。保留的 `manifest` 不包含固件字节，也防止历史发布编号重复使用。

## 验证记录

构建及测试输出保存于 `output/systemd-tools/`；实机发布身份、串口日志和设备确认结果另存于唯一的 `output/ota-validation/` 发布目录。只有目标设备重启并报告对应内容 ID 的 success 后才提交、推送本阶段代码。

2026-11-05 实机验证，AM625 `192.168.10.211` / HWID `1010001000110000`：

- `v0.0.1 / a33d0aa63cd81f48c741847762034cd1001d5bb6500fbb4389ea92a2c6a50fce`：OTA 发布 81，重启后设备报告 success；PID 1 为 systemd，部署 1 已确认，kernel/rootfs 使用 B 槽。
- 所需服务 active，`systemctl --failed` 为零，`fwctl health-check` 返回 0；PID 1 持有 `/dev/watchdog0`，运行与重启超时均为 60 秒。未用暂停 PID 1 或物理掉电测试硬件复位期限。
- 对 psatellited 主进程发送 SIGSTOP：15 秒服务 watchdog 到期，systemd 终止并重启进程，NRestarts=1，随后服务恢复 active，整体健康检查通过。
- 临时阻断到管理服务器的路由 18 秒：本地健康检查仍通过，fwctld/logctld 保持运行；恢复路由后 SOL 补传成功。
- data 保持 persistent；设备时间显示 UTC+8；journal 测试消息 `SYSTEMD_JOURNAL_CAPTURE_OK` 已在服务器 SOL 的 services 流中收到。
- 再次执行正常重启：systemd 服务停止并重新启动，仍为同一固件 ID；健康检查、data 持久化、SOL 上报及 UTC+8 校时通过，失败 unit 为零。
- 首轮候选 `d5ea496e` 因网卡自动改名未通过本地健康检查，150 秒观察期限后被拒绝并回退。服务器记录 rolled-back、隔离异常固件并恢复上一正常版本；失败启动日志整包已上传。该候选没有作为成功版本提交。
- 独立 initramfs 的实际 AArch64 程序通过 QEMU 动态加载检查；恢复测试 6 项、EDK 测试 10 项，以及健康策略、OTA/SOL、删除 API 和 Chromium 页面操作测试通过。

成功发布的镜像、完整身份、设备上报与串口证据位于
`output/ota-validation/0.0.1-systemd-02/`；失败候选单独保留在
`output/ota-validation/0.0.1-systemd-01/`。这轮只通过 OTA 安装 kernel/rootfs，
不代表重新安装或验证了包外的 SPL/U-Boot。

管理端同时验证了固件删除、SOL 首次连接时间标题与启动状态，以及各页面优先用设备 IP
显示的行为。历史事务仍保留当时的 IP，稳定内部设备标识继续用于关联，不因地址变化拆分历史。

配置语义参考 systemd 官方的 [服务就绪通知与服务 watchdog](https://www.freedesktop.org/software/systemd/man/255/systemd.service.html) 和 [管理器硬件 watchdog](https://www.freedesktop.org/software/systemd/man/258/user.conf.d.html)。服务 watchdog 监督应用通知；RuntimeWatchdog 由 PID 1 喂硬件，两者失效边界不同。
