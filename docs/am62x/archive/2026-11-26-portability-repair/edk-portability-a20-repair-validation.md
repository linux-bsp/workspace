# A20：AM625 所选构建清单及实际运行版本验收

2026-11-26 20:00:29+08:00 PASS。E=`output/edk-portability-a20-20261126-195335-GXMpg3/`，F=E/final/。[工程回归](../../../../edk/docs/archive/2026-11-26-portability-repair/edk-portability-a20-repair-validation.md)。

指定 AM625 固定先前可信 SSH key，MAC `1c:63:49:22:c4:f7`、HWID `1010001000110000`，Linux `7.0.0 #1 SMP PREEMPT Wed Mar 4 08:06:40 UTC 2026 aarch64`，boot `83613296-b1de-42c5-822d-11bd14637d11`、B 槽 confirmed successful=1、FWCHECK1 match。catalog 上次 `draft-V54AKR` 对应该运行完整 ID `0971e5b329bc717a96389b0f529a9e4da481b3faf45d224e67d0162086f79a13` success/running=1，8 unit active、0 failed、9/9 制品匹配。F/board-check.log、board-kernel.log、board-identity-check.log、catalog.json、board-package-compare.log。

| 证据 | 实际结果 |
| --- | --- |
| 所选构建配置 | 正式 Linux `output/am625/build/linux-custom/.config` SHA `937e4cc07ca2474738051bbff3a7d521a573ef0c153279a05a875dba34ecd122`（同实际 LINUX_DIR）；其他 7 个配置、实际源码 revision、target/host build-info 均核对匹配。F/manifest-verified.log。 |
| 两棵独立共存树 | 实际 Buildroot 传递的 BSP_FIRMWARE_LINUX_CONFIG 和 generator 随 A/B 切换，两个 SHA 不同，入清单正确。不以这个配置注释夹具冒充另一真实 Linux 版本。E/selection-*.log/json。 |
| 正式制品 | kernel 12940588 bytes `21f8facbea36c8f56d4b19b178a02c94c5780b50d52652686a0ce647b37a48c3`、rootfs 30425088 bytes `0d661e39187fae712a39e41ce7633752564face3a6b1ef829f914626e26bfe28`。四 ITB、initramfs、verity rootfs 与上次部署逐字相同；清单是侧车，本阶段不发 OTA。F/formal-content-match.log、images/release/build-manifest.json。 |
| bootlog | 真实 final gate 18 输入、FIT FDT 字节匹配；实机 persistent/sync ok、verify-boot 通过、RAM acknowledged；同 boot capture `784b65b0-a877-4f40-8f85-1db361e877c5`，r5 418/4c81b2d0，a53 455/e5ad50a2，uboot 3027/ff7b0455，kernel 24705/dc01cabb，四段 CRC 正确、dropped=0，早期本地 kernel absent 为有效前缀。F/archive-verified.log。 |

未操作其他真实设备，未安装 bootloader，阶段仅变更通用 BSP 打包清单及测试。原配置和唯一输出目录保留。

EDK 文档提交 `125a6189887286244dbdb57a6c1b499555bdd80e`、BSP 修复提交 `ae0c744b4e208efe5033143cdb05871b809c2c41` 已分别推送并核对 master；工作区记录相同 gitlink，E/git-verification.log。
