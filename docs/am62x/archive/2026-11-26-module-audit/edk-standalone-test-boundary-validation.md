# AM625 A7 测试装配边界与启动日志制品实板验收

2026-11-26，北京时间。最终 V6 通过；下列初次失败证据原样保留。E=`output/edk-standalone-test-boundary-20261126-104403/`。
[EDK 开发记录](../../../../edk/docs/archive/2026-11-26-module-audit/edk-standalone-test-boundary-validation.md)。

| 项目 | 实测 |
| --- | --- |
| 设备 | am625 / 192.168.10.211 / MAC 1c:63:49:22:c4:f7 / HWID 1010001000110000 |
| SSH | A5 物理串口核实 key，严格 known_hosts，E/board-known-hosts |
| 正式固件 | A5 full ID `403502c59347e139db86422e02308a2581493c73a5f201e1bbe31cae7a906dc3`，v0.0.1，B 槽 confirmed successful |
| boot ID | 34a43973-7489-478c-bfe1-7a2e8a47fb96 |
| 初次 V6 | 10:53:52 起，启动日志 handoff 实际检查失败，当时阶段开放 |

`ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=E/board-known-hosts root@192.168.10.211 "$(cat E/board-v6.sh)"`。
实际读身份、HWID、`fwctl version`/`ota-status`/`ota-check`/`health-check`、八 unit 和启动日志状态。
FWCHECK1 match、设备和健康断言均通过。`cat /sys/firmware/bootlog/state` 失败（exit 1），
追加 read-only `logctl verify-boot` 实际三个阶段 handoff unavailable，exit 1。`logctl status` storage persistent、sync-state ok。
E/board-v6.log、board-bootlog-diagnosis.log。不可忽略实机失败或把主机四个 U-Boot 模拟用例当作板上验证。

## 初次问题定位

- `dumpimage -l A5/images/release/kernel.itb`，`dumpimage -T flat_dt -p 2 -o E/a5-kernel-fdt.dtb ...`；
  `fdtget -t x E/a5-kernel-fdt.dtb /reserved-memory/bootlog@9c900000 reg` 返回 `0 9c900000 0 10000`，
  `fdtget E/a5-kernel-fdt.dtb /bootlog compatible` 返回 `bsp,bootlog-v1`。
- 读取实板 `/sys/firmware/devicetree/base/reserved-memory/bootlog@9c900000/reg` 和 `bootlog/compatible`
  的二进制属性，主机解码：`0x0 0x9c900000 0x0 0x10000` 和 `bsp,bootlog-v1`，与实际成功包相同。
  E/board-bootlog-reg.bin、board-bootlog-compatible.bin、board-bootlog-actual-dt.log。
- 正式源码 `linux/linux-7.0/arch/arm64/boot/dts/ti/k3-am625-alientek.dts` 已是 v2、reg 0x100000；
  U-Boot 和 Linux 的 `bsp_bootlog_layout.h` 一致，双 0x80000 bank；现有 `output/am625/build/linux-custom/...` DTS
  仍是 v1、reg 0x10000。此前 A5 复制了现有 boot artifacts 生成镜像；本阶段没有改变这些制品。
  需处理旧源副本/制品；如需 bootloader 更新须单独确认实际身份，不能仅按普通 kernel/rootfs OTA 证明。

## 其余断言

失败后继续其余只读检查（E/board-remainder.sh/log、board-package-compare.log）：实际 9 项 SHA
（A5 八制品及 logctl）全部与 A5 rootfs 逐项一致，BMC 三来源实际 Redfish、sequence=1014、失败0、last_status=0，
PMC 三来源最后状态正常，一来源累计失败1；不宣称永久零失败。健康、八 unit active、当前 Satellite 历史文件仍不存在。
本阶段测试装配改动 250/250 EDK 独立、10/10 BSP 产品集成通过，但当时既有启动日志实机异常尚未解决，
初查整体 V6 未通过；用户随后明确要求解决所有问题，按以下流程修复重验。初查仅指定 AM625 只读核对。


## 修复后正式验收（通过）

F=E/bootlog-repair/。从当前源码重新同步并构建 Linux、U-Boot/R5 和 EDK，
post-build 新增实际 DTB 与 V2 双 bank layout 校验；原 A5 真 DTB 被规则拒绝，新正式包通过。
本次正式 OTA **仅 kernel/rootfs**；先读回实际 6 个 bootloader 分区，A 为 11-03 V2 原 payload，
B 为 11-05 历史构建实际 payload，metadata 仍选中 B。更新后六分区完整读回全部逐字相同，
避免无必要的引导写入。新工厂 bootloader 制品已从当前源码重建但未实际安装，不声称新 bootloader V6。
F/bootloader-provenance.log、bootloader-preservation.log、board-boot-precheck.log。

| 项目 | 实测 |
| --- | --- |
| 发布 | `draft-3v0bSf`，2026-11-26 11:49:55+08:00，唯一设备 MAC/HWID /32 |
| firmware_id | `16f44b78e3915e830ae7bdcf2293ebc06738b1a187edead8d74aab3359b81730` |
| 版本 | 0.0.1 / packed version 1 |
| kernel | 12940588 bytes，`472e197eb3f8874e9bf5f9af2502b87b03771f396d6ef47aa1a82f119c2cc392` |
| rootfs | 30420992 bytes，`9fd537d46e5eae6ce9e89c8a1c1dc779d3b58dacf25221070291cc40351f0fdf` |
| 设备最终 success | 11:51:37+08:00，running=1，无 quarantine |
| boot ID | `8fb95921-66b5-431b-b5b5-1074e58148c3` |
| kernel/rootfs | A 槽 confirmed successful |
| 时间 | 11:59:00–11:59:04+08:00，最终 V6 |
| SSH key | 物理 USB/IP 串口核实 `SHA256:FwGx3XSb7Ex8dm3hFyAGwWFbX8Jg5mZdTqDT1TCks4U`，严格固定新 known_hosts |

命令 `ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=F/board-known-hosts-post-ota root@192.168.10.211 "$(cat F/board-v6.sh)"`。
实际设备身份、HWID、`fwctl version`/`ota-status`/`ota-check`（FWCHECK1 match）、health-check、八 active units、
无 failed unit，9 项实际制品摘要与本次新包一致；旧 Satellite 三文件仍不存在。实板真实 DTB binary
核对 compatible `bsp,bootlog-v2`、reserved-memory `0x9c900000/0x100000`，F/board-actual-dtb-check.log。
`cat /sys/firmware/bootlog/state`：startup-state=acknowledged、active-buffer=2、next-buffer=1；
`logctl verify-boot` 返回 0、`startup logs archived; both RAM buffers acknowledged`。

进一步只读查询本机 OTA/SOL server `GET /api/sol/devices`，当前 boot 的 healthy-current capture
`c959b47e-de7c-4df1-ab99-0ea53832a1df`、archive complete、buffer1/generation2；通过
`GET /api/sol/logs/<device>/<capture>/<stage>/0` 下载每段实际 bytes 验证：

| 段 | 字节数 | CRC32 | 状态 / dropped |
| --- | ---: | --- | --- |
| R5 SPL | 418 | c0d3dbaa | valid / 0 |
| A53 SPL | 455 | a83c48d8 | valid / 0 |
| U-Boot | 3027 | 415c0bb2 | valid / 0 |
| kernel | 24705 | ed6d3866 | valid / 0 |

四段实际归档长度、CRC32 均与 manifest 相同（F/archive-verified.log）。历史 V1 上次不完整记录
仍保留其 absent/corrupt 标志，不将其误作正常归档。当前三 BMC Redfish 和三 PMC pmcp 均 sequence=99、
累计失败0/last_status0，本次板端健康通过。F/board-v6.log、board-package-compare.log、board-final-status.log、
serial-key.log、ota-success.json、server-startup-devices.json、archive-*.json/bin。真正掉电、受控异常复位等非本次任务新验证范围。
本阶段独立 EDK 250/250、BSP 11/11、镜像/OTA 回归及最终 V6 全通过。
只有指定 AM625 执行正常 kernel/rootfs OTA，其他真实服务器仅只读测试。

## 提交与远端核验

- EDK `526fd2c54b8599c9bc829be3dd20b73b55743111`，origin/master 已核实 SHA 相同。
- BSP external `0fb4302eb7c640ac7c2a483fe3b2fc8d4e3c80db`，origin/master 已核实 SHA 相同。
- Linux/U-Boot 为已有固定提交，源码未修改；新构建和实际安装边界如上。
- 工作区只提交两个精确 gitlink 与本次板验记录，原有用户变更保持原样；自身提交和远端核验见 F/git-verification.log（提交后生成）。
