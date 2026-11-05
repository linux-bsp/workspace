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
| `timectld.service` | 独立 NTP/HTTP 校时、RTC 和配置回报；与日志服务无生命周期依赖，不以网络校时成功作为启动门槛 |
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
- `/etc/default/fwctld` 与 `/data/fwctld.conf` 保留 OTA 配置来源；禁用内置 timesyncd，由独立 timectld 使用 `/etc/device-manager/time.conf` 和 `/data/timectl/source.conf` 管理校时，显示 UTC+8。
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
systemctl status timectld
timectl status
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

### 后续 OTA 暴露的锁竞争修复

基线 `a33d0aa6` 能正常启动，但进行下一次 OTA 时，更新进程占用固件元数据锁，
旧健康监督将 `Resource temporarily unavailable` 误判为本地故障并重启。
因此仅验证一次迁移启动还不够，必须验证迁移后的系统能继续安装下一固件。

`50147beb` 修复健康结果约定：0 为全部通过，75 为本地服务未就绪，76 为固件事务占锁，
其他错误为失败。76 不产生 READY，也不增加启动确认成功次数；运行监督最多容忍连续
180 秒忙状态，使用 `/proc/uptime` 单调时间。其他服务异常不能被占锁状态掩盖。
`fw-confirm` 同样允许暂时忙，仍要求六次连续成功，并保留总观察期限。

正式镜像实机持锁 22 秒期间监督保持 active，释放后健康恢复；部署已确认，失败 unit 为零。
首轮 OTA 的取消记录、临时修复过程及正式镜像验证均归档，未手动确认候选、关闭健康检查
或停止硬件看门狗。详见 [S5f 验收记录](space-software-assessment-and-plan.md)。

再次从该正式镜像自动 OTA 至 `v0.0.1 / c06cfb5d`（完整 ID
`c06cfb5dcd09d8e7d54fd5902ac662db40a8535eebc6175b073e5c4727ab0b4a`，发布 85），
设备安装、重启、健康确认及服务端 success 均通过；没有使用临时健康脚本。
最终部署 1、kernel/rootfs B 槽，备用 rootfs 校验通过，失败 unit=0。
串口和设备最终状态见 `output/ota-validation/0.0.1-reliability-s5f-04/`。

### 串口输出与尚存提示

PID 1、服务默认环境和调试控制台均使用 `TERM=dumb`，禁用颜色和 URL 转义；控制台固定
行列，避免串口和 SOL 捕获 OSC 会话标记、ANSI 颜色及光标位置查询。保持原有服务状态和
错误信息，不以降低全局日志级别隐藏问题。

- `watchdog already running` / `nowayout prevents watchdog being stopped`：U-Boot、
  initramfs 到 PID 1 接力时硬件仍在计时。实机确认 systemd 接管并持续服务，未关闭 nowayout。
- `Modifying watchdog hardware timeout is not supported`：RTI 驱动不支持重新设置已启动的
  watchdog，systemd 复用实际 60 秒期限；不能把配置请求值当成硬件已改变的依据。
- `pdm: loading out-of-tree module taints kernel`：PDM 为外置模块，属于内核调试状态标记。
- RTC 在本次暖重启早期显示 1970 年，随后 Device Manager 完成校时并写 RTC；设备显示
  UTC+8，RTC 保持 UTC。跨复位/断电保持能力仍待硬件及驱动验证，早期日志时间不视为可信。

配置语义参考 systemd 官方的 [服务就绪通知与服务 watchdog](https://www.freedesktop.org/software/systemd/man/255/systemd.service.html) 和 [管理器硬件 watchdog](https://www.freedesktop.org/software/systemd/man/258/user.conf.d.html)。服务 watchdog 监督应用通知；RuntimeWatchdog 由 PID 1 喂硬件，两者失效边界不同。

### 时间服务拆分验收（2026-11-05）

固件 `v0.0.1 / b3397bb3`，完整 ID
`b3397bb3c3b9b1a4de52f8306519890d4f3b35175c1672c9c0e05d245e086e02`，发布 86，
AM625 自动 OTA 至部署 0/A 槽，重启后健康确认并向服务器上报 success。

`timectld` 与 `timectl` 共用一个二进制，通过独立 systemd unit 和有界 Unix socket 管理。
日志程序移除设时实现与 `sync-time` 命令；校时配置不再依赖 sol.conf 或日志运行目录。
旧 `/data/log/time-source.conf` 成功导入新位置，原副本保留供固件回退。

- 停止 logctld：timectld 保持 active，`timectl sync` 成功，服务器持续收到时间状态。
- 停止 timectld：CLI 明确报服务不可用，logctld 仍采集并通过 SOL 上传测试消息；健康检查通过。
- 网页 API 下发临时 LAN NTP 源：设备完成 9 次 UDP 采样，手工同步及时间服务重启后配置恢复通过。
  这是使用主机真实 UTC 时间的临时协议夹具，不代表长期精度或外部授时系统验收。
- 测试结束恢复原来的 Device Manager HTTP 时间源，所有相关服务 active，失败 unit=0，
  health-check=0、data=persistent、archive-pending=0、sync-state=ok，UTC+8 显示正常。

20 项时间模块测试、26 项日志/启动记录测试、9 项时间 API 测试及实际 ARM64 加载检查通过。
服务启用链接在最终 SquashFS 中检查；Buildroot 在生成文件系统时执行 preset，原始 target
目录不能代替最终镜像的启用状态。证据在 `output/ota-validation/0.0.1-time-service/`。
本阶段保留原 SNTP/HTTP 算法，不引入 chronyd，不宣称解决 RTC 跨复位保时。
