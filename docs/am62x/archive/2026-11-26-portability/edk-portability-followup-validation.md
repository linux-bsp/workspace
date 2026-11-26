# A16/A18 二次复查修复：AM625 正式制品与实板验收

2026-11-26 18:05:37+08:00，正式镜像及板验 PASS。E=`output/edk-portability-followup-20261126-175112-8j2Mvf/`，F=E/final/。
[EDK/BSP 工程及回归记录](../../../../edk/docs/archive/2026-11-26-portability/edk-portability-followup-validation.md)。

## 发布与运行身份

| 项目 | 实际证据 |
| --- | --- |
| 固件版本 | `v0.0.1`，packed 1，VERSION 不变 |
| firmware_id | `0971e5b329bc717a96389b0f529a9e4da481b3faf45d224e67d0162086f79a13` |
| OTA 包 SHA256 | `ad19cf91aa9c0cb7750108e52bc37ac27858afe3fc541069c518a0c47e86d2dc` |
| kernel | 12940588 bytes，`21f8facbea36c8f56d4b19b178a02c94c5780b50d52652686a0ce647b37a48c3` |
| rootfs 分区 payload | 30425088 bytes，`0d661e39187fae712a39e41ce7633752564face3a6b1ef829f914626e26bfe28` |
| publication | `draft-V54AKR`，18:03:47+08:00；仅目标 HWID 的活动 channel |
| 设备事务 | 18:05:23 catalog `success`，running=1、version=1、未隔离 |
| 设备 | AM625，MAC `1c:63:49:22:c4:f7`，HWID `1010001000110000`，IP `192.168.10.211` |
| 实际运行 | B 槽 kernel/rootfs，confirmed successful=1，FWCHECK1 match |
| boot ID | `83613296-b1de-42c5-822d-11bd14637d11`，升级前 `c0d6ded6-c130-44fd-9776-43f07b0a487c` |

发布前核对旧 SSH key/板身份、仅指定板可达的 relay、唯一 catalog device/channel、候选完整 ID/HWID、
所有原生/集成、实际输入、完整镜像与 OTA roundtrip 验收。F/publication.log、publication-time.txt、
publication.json、server-draft-state.json、ota-timeline.log、ota-success.json、device-transaction.json。
设备安装、boot-testing 未视为成功；待最终 success，先从物理串口核对新 boot ID 和 SSH fingerprint，
然后固定新 key 只读核对实际身份、分区、制品及服务。F/serial-key.log、board-check.log、board-verify.log。

## 实板与独立移植专项

- `fwctl version`、`fwctl ota-status`、`fwctl ota-check`、`fwctl health-check` 通过；
  8 个预期服务 active、0 failed；9/9 运行制品与实际 rootfs FIT 解包文件 SHA256 相等，含 logctl。
  F/board-package-compare.log。`logctl show --stage typo` 实际返回 2，错误信息 `Unknown log stage: typo`，
  合法 r5-spl 实际启动日志读取成功。
- 使用新固件的实际 ARM64 `logctl` 在指定板 `/tmp` 独立夹具（自有 LOGCTL_RUN_DIR/BOOT_ID，退出清理）运行
  `show` 和 `follow`。原始 GOOD 快照仍可 show，损坏 WRONG 投影被省略且明确告警，正常阶段及同阶段普通日志继续；
  `follow --boot previous` 读取历史 raw-only 快照一次，不创建历史投影，两个原始及损坏证据摘要不变。
  不启动另一个 collector、不开新网络转发、不改真实生产日志目录。首次夹具使用的 BusyBox `sha256sum -c` 不支持，
  改为比较两次 `sha256sum` 完整输出后全部通过；F/board-legacy-cli-first.log、board-legacy-cli.log、board-legacy-cli.sh。
  真实服务端端到端旧布局实时/历史测试已在无外部路由的 native logctld/pmcd 夹具通过。
- 真实选定 Linux 的 DTC/fixdep 产生合法 CONFIG 依赖、变更注释的 DTB 与原字节一致；9 项负例拒绝。
  真实 post-image 将选定 Linux 移至 `linux-7.0` 且无 `linux-custom` 别名，initramfs 及三件 FIT 与正式包逐字一致。
  E/provenance.log、renamed-image-test.log。正式最终 FIT FDT 与活动 DT：compatible `bsp,bootlog-v2`，
  memory-region/phandle 0x3f，reservation 0x9c900000/0x100000 全部一致，原 boot inputs SHA 不变。

`logctl status` 为 persistent/sync ok，`verify-boot` 成功，两个 RAM buffer 已 acknowledged。
同一新 boot 的 capture `784b65b0-a877-4f40-8f85-1db361e877c5` 本地及服务器实际归档：

| stage | 服务器 bytes | CRC32 | 本地对照 |
| --- | ---: | --- | --- |
| r5-spl | 418 | 4c81b2d0 | 逐字相等 |
| a53-spl | 455 | e5ad50a2 | 逐字相等 |
| uboot | 3027 | ff7b0455 | 逐字相等 |
| kernel | 24705 | dc01cabb | 早期本地 absent，0 byte 前缀；sealed CRC 正确 |

四段 dropped=0。F/board-local.tar、archive-verified.log、archive-*.json/bin。实际启动链仍使用 V2 布局，
旧布局为上述独立夹具，不冒充另一物理板或已安装旧 bootloader；本次不安装 bootloader。
没有操作其他真实设备。原 Buildroot 配置与 VERSION 保持；唯一正式构建目录保留，常规 images 与其逐字相同，
旧目录移到 F/previous-default-images。F/default-images-check.log、commit-source-check.log。

板验后 EDK `2e20d803a72076781837eb9340964d6bd96b398b`、BSP
`d7e129a6cf44da8e6757eebfe802d48b80f51613` 依次提交、推送并核对各自 `master`；
工作区记录相同 gitlink。E/edk-remote.txt、bsp-remote.txt、git-verification.log。
