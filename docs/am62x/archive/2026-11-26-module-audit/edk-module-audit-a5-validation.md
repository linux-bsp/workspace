# AM625 A5 历史 Satellite 库清理实板验收

2026-11-26（北京时间）。本轮 AI 验证人。证据 E=`output/edk-module-audit-a5-20261126-0017/`。
[EDK A5 开发记录](../../../../edk/docs/archive/2026-11-26-module-audit/edk-module-audit-a5-validation.md)。

## 初审：A4 成功发布物（清理前）

| 项目 | 核对结果 |
| --- | --- |
| 设备 | am625 / 192.168.10.211 / aarch64 / MAC 1c:63:49:22:c4:f7 / HWID 1010001000110000 |
| SSH 身份 | 严格使用 A4 串口核实的 ED25519 指纹 `SHA256:3b6MDiZegQzAOwVdFWCw5AhJmVbRpanR4jI0NbblWZQ`，E/board-known-hosts |
| 运行制品 | A4 full ID `0e27a1546a308cb8d6a3844e6d937440318ddf367043b79717ffb323e526187c`，0.0.1，A 槽 confirmed/successful |
| boot ID | `35831c39-3102-45c7-87f1-71adf8c2b865` |
| 检查时间 | 00:19:45 初查；00:28:37–00:28:42 全四库只读复核 |
| 证据 | E/board-library-audit.log、board-client-audit.log、board-v6-readonly.log、board-package-compare.log、elf-consumers.log |

使用固定 known_hosts 的 `ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=E/board-known-hosts root@192.168.10.211`，
执行 hostname、MAC、HWID、boot ID、`fwctl version`、`fwctl ota-check 1 12913344 1655713575f3330c64af724041acd74b8e1b9b7640f6316b7f7b91d347f46e0d 30457856 2ca79d8131a6a20469129acffd77a400e6d50fd2ebe82a729b28eb51de0014bf`、
`fwctl health-check`、`ls -l /usr/lib/lib{bsl,pdi,server,satellite}.so*`（逐项通配符执行）、
六实体 `sha256sum`、各 PID `/proc/PID/maps` 读取、`systemctl is-active`、`systemctl --failed`、`ptelemetryd --query runtime-status`。

预期：与当前成功发布的 A4 rootfs 一致，现行消费者加载清单中的库，板端健康。
实际：FWCHECK1 match、健康退出 0；全部六个库实体与 A4 包摘要相同（6/6），
现行 bsl/pdi/server/satellite 链及两个历史 Satellite 实体、`.so.1` 链均与包相符；
只有 psatellited 映射 Satellite `.3.0.0.1`，未见两旧实体被映射。
八个服务 pdm/bsp-can/ptelemetryd/psatellited/fw-health/fwctld/logctld/timectld 均 active，
无 failed unit。早期 BusyBox `find -perm` 不支持，改为枚举外部目录常规文件
并读取 ELF 标识，仅发现两个历史 crash candidate.elf（无 Satellite 依赖）。
现有配置无旧库直接引用，仍不能排除板外产品客户的 ABI 兼容约定。

00:28:42 三 BMC 实际采样均 Redfish、三个 PMC 来源均 pmcp，全部 last_status=0、
consecutive_failures=0。节点1在此 boot 累计 9 次失败（sequence=175），
并非原持续失败循环；节点2/3 sequence=184、失败=0。
00:31:15/21 另读 journal/dmesg 与 runtime-status，过滤未见当前 WARN/ERROR，
不把该快照推断为节点1零超时。E/board-redfish-observation.log、board-warning-observation.log。

所有操作为指定 AM625 只读检查，未对板上旧文件做任何删除或替换，未对其他真实
服务器执行写入、部署或电源操作。A5 独立干净构建只作主机对照，未 OTA。
上述是清理前初审，不能替代最终 V6。用户随后确认“历史版本全部淘汰清理掉”，
按打包层定向清理并执行以下正式验收。


## 正式 A5 OTA 与 V6（通过）

最终证据 F=E/formal-final/，所有时间为北京时间。

| 项目 | 实测 |
| --- | --- |
| 发布 | `draft-i9L3Lp`，2026-11-26 09:34:58+08:00，唯一目标板及唯一 HWID channel |
| firmware_id | `403502c59347e139db86422e02308a2581493c73a5f201e1bbe31cae7a906dc3` |
| 版本 | v0.0.1 / packed version 1 |
| OTA 包 SHA256 | `71b8746aa195f5bb9f498e0bba1bbc8cdd2a184139ab5e4c67e05907ff750bb6` |
| kernel | 12913344 bytes / `85b89e0495ddba7a528b9a8a1e8deb5a8969406a586ff3e09583a9222bdee93f` |
| rootfs | 30420992 bytes / `07635f132a9fbc869f52c0c49aa497352144d1ed6c80743f7b76c0be5cdd9733` |
| 最终回报 | 09:36:31 success，running=1，未 quarantine |
| 启动/槽位 | `34a43973-7489-478c-bfe1-7a2e8a47fb96` / B 槽 confirmed successful |
| 实板时间 | 09:44:52–09:44:57+08:00 |

发布前 `F/publish.sh` 核对严格 SSH、MAC、HWID、旧 boot、健康、唯一 OTA channel，
OTA 转发进程绑定 `192.168.10.246:8090` 并限制 `192.168.10.211/32`。
保存了 draft、manifest 身份、发布响应及设备事务 events（installing 09:35:06、rebooting/boot-testing
09:35:45、success 09:36:31），F/board-prepublication.log、ota-peer-filter.log、server-*.json、
publication.json、ota-success.json、ota-timeline.log。新启动后首次串口读取密钥尚未生成；
Dropbear 按需生成，`ssh-keyscan` 后再次由实体串口核实 MAC/HWID/boot ID 和指纹
`SHA256:BrVgnZLS+2mVjHmJShyEHJltrWrunAoZbZXZGHbF5O0` 并固定 known_hosts，未关闭校验。
F/serial-key-before-lazy-generation.log、serial-key-paths.log、serial-key.log、board-post-ota-scan。

`ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=F/board-known-hosts-post-ota root@192.168.10.211 "$(cat F/board-v6.sh)" < F/board-probes.tar.gz`。
该脚本实际核对：

- 设备身份、不同 boot ID、`fwctl version`/`ota-status`/`ota-check`、健康；实际 B 槽版本 0.0.1、完整 ID、FWCHECK1 match。
- `ls -l`、`readlink`、`test ! -e` 与 `test ! -L`：所有三个历史名字（`libsatellite.so.1`、
  `libsatellite.so.0.0.1`、`libsatellite.so.2.0.0.1`）均不存在；其余四库现行软链精确一致，只有 ABI3 当前 Satellite 实体。
- `/proc/PID/maps` 实际加载当前 `.3.0.0.1`，SHA256 与此次真实包八项完全匹配（四库、PDM、ptelemetryd、psatellited、fwctl）。
  F/packaged-artifact-hashes.txt、board-package-compare.log。
- 原 M0 ABI3 已编译 consumer 及本次正式 SDK 重新编译 consumer 在板 `/tmp` tmpfs 上执行
  本地文件夹具；核对探针和夹具 SHA256、动态 loader 实际使用 `/usr/lib/libsatellite.so.3`，
  两组 BSL/PDI/server/Satellite 正反断言均 PASS，结束清理临时文件。历史 ABI1 不再支持。
- 八 unit active，无 failed unit，健康检查退出 0；三个 BMC 实际 Redfish 均 sequence=111、失败=0、last_status=0，
  三 PMC 来源同样正常。与此前 A4 偶发失败分开记录，不将一次快照推断为无限期无失败。

F/board-v6.log 末尾 `A5 final assertions: PASS`，退出 0，八制品对比 8/8。
仅指定 AM625 经正式 OTA 改变运行制品；没有直接删除运行板旧库，其他实际服务器无写入、电源操作或部署。
A5 具备提交关闭条件；bootloader 未安装，本次仅验收已安装 kernel/rootfs OTA。

## 子仓提交及推送核验

- EDK `386ac1daad7c41ca6ddccdf31f3bcc6e687f788c`，origin/master 实测相同。
- BSP external `144e109e07bd810151249681b96d318358539d6c`，origin/master 实测相同。
- 工作区仅提交上述两个精确 gitlink 及本阶段板验记录，用户原有改动不纳入。
  工作区自身提交 ID 与远端核验保存在 F/git-verification.log（提交之后生成）。
