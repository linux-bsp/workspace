# A14–A18 复查问题修复：AM625 正式镜像与实机验收

2026-11-26 17:38:19+08:00，实板验收 PASS。
E=`output/edk-portability-remediation-20261126-171855-c5SbY4/`，F=E/final/。
[EDK/BSP 工程及回归记录](../../../../edk/docs/archive/2026-11-26-portability/edk-portability-remediation-validation.md)。

## 正式制品和 OTA 事务

| 项目 | 实际证据 |
| --- | --- |
| 固件版本 | `v0.0.1`，packed 1，VERSION 不变 |
| 新完整 firmware_id | `a8138ac180f13bb09ef40e2e07f247c76d0590b5fdf4d8dd7eff914bcf10c845` |
| OTA 包 SHA256 | `39c53e26fb86d981fc57627a119d7ddf87ae2cea1aff62e80d417d77733f285a` |
| kernel | 12940588 bytes，`4438deebae9c5cb4ef05bbbb23c95f224f4883105a06c67907354c6fdc647dc4` |
| rootfs (实际分区 payload) | 30425088 bytes，`f2119af6a42a21e6b912f15ac858ae8eb30179eef30f5d8f5c28826beb0f3563` |
| publication | `draft-wI7nZu`，17:36:18，唯一活动 channel 为目标 HWID |
| 设备事务 | 17:38:10 catalog `success`，`running=1`、`version=1`、未隔离 |
| 实际设备 | MAC `1c:63:49:22:c4:f7`，HWID `1010001000110000`，IP `192.168.10.211` |
| 运行状态 | A 槽 kernel/rootfs，confirmed successful=1，完整 ID 相符，FWCHECK1 match |
| boot ID | `c0d6ded6-c130-44fd-9776-43f07b0a487c`，不同于升级前的 `727e44b9-d1b1-47f8-b992-5be7ca25d7f3` |

源 SHA/快照、原 Buildroot 配置、两个包重建、完整镜像验证及真实 OTA 包 roundtrip 均于发布前通过。
发布脚本固定旧板 key、MAC/HWID/boot ID，核对单设备 catalog、仅该设备可达的本地 relay
和精确上传候选 ID/HWID，才向本地 catalog 发布。F/boot-input.sha256、release-files.sha256、
ota.sha256、live-source.sha256、publication.log、publication.json、server-draft-state.json、
ota-timeline.log、ota-success.json、device-transaction.json。
安装和 boot-testing 未视为成功；等到最终 `success`，经物理串口核对新 SSH key 与设备身份
（F/serial-key.log），再严格 key 校验只读验收。

## 指定板专项验收

- `fwctl version`、`fwctl ota-status`、`fwctl ota-check`、`fwctl health-check`：通过；
  8 个应运行服务 active、0 failed。9/9 板上文件与新 rootfs FIT 解出的真实运行制品
  SHA256 一致，包括 4 个库、PDM、两应用、fwctl 和 logctl。F/board-check.log、board-package-compare.log。
- 真实板的 AM625 旧路径检查（dmcli、bmc-test、system_manager、旧 init 和 service/socket）均不存在，
  `/data` 和 `/data/log/boots` 仍存在。F/board-cleanup.log；另一产品保留其自有文件由隔离真实通用 recipe 验证。
- 最新实际 FIT 的 FDT 与运行设备树：`bsp,bootlog-v2`、memory-region 0x3f、
  reserved-memory phandle 0x3f、reg 0x9c900000/0x100000 一致。实际 18 条 Kbuild DTB 输入、
  四对象、三端固定布局及最终 FIT gate 通过。F/packed-bootlog.log、board-verify.log、active-*.bin。
- `logctl status` 为 persistent/sync ok，`verify-boot` 成功，RAM 交接已 acknowledged。
  新 boot 的本地 manifest 与服务器独立归档实际字节校验，capture `606a86b7-98ac-4c82-a047-f750657d3566`：

| stage | 服务器 bytes | CRC32 | 对照本地 |
| --- | ---: | --- | --- |
| r5-spl | 418 | 256aab6c | 逐字相等 |
| a53-spl | 455 | f6ffc5d4 | 逐字相等 |
| uboot | 3027 | 0b9d210c | 逐字相等 |
| kernel | 24705 | fd3a1b93 | 本地早期 absent，0 byte 前缀匹配；最终 sealed CRC 正确 |

四段 dropped 均为 0；F/board-local.tar、archive-verified.log、archive-*.json/bin。
当前实板仍运行 v2 manifest 布局，旧三文件布局的 show/follow/普通 SOL 及重启迁移由隔离
真实 logctld/pmcd 端到端测试验证，未为验证旧布局而重刷 bootloader 或更改生产内核。
本次 kernel/rootfs OTA 不代表未安装的 bootloader 获得实机安装验证。没有操作其他真实设备。

验收后的唯一构建目录保持原样，常规 output/am625/images 镜像逐字同步，旧目录移至
F/previous-default-images。F/default-images-check.log、commit-source-check.log。

已在板验通过后依次提交、推送并核对两个子仓 `master`：
EDK `0c8a02197d5365a252499fe9d7df00460a55cf03`、
BSP `fc24ae9655ef09a72f8c1794dfe6d900fd2acdc7`。
工作区记录这两个精确 gitlink；E/edk-remote.txt、bsp-remote.txt、git-verification.log。
