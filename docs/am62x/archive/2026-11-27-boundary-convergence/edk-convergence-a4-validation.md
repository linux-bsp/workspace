# A4：AM625 Kconfig 模式及最终正常候选实机验收

E=`output/edk-convergence-a4-20261126-214421-nn8tCz/`，F=E/final/。[工程与本轮四阶段边界复核](../../../../edk/docs/archive/2026-11-27-boundary-convergence/edk-convergence-a4-validation.md)。

- 指定板可信 SSH，MAC `1c:63:49:22:c4:f7`、HWID `1010001000110000`、boot `fba8a8cf-97fa-42f5-8376-bf992e784687`，slot A，`v0.0.1` packed 1，完整 firmware ID `8472924c9470022a7ae05db552e5db077c641ee7a646ce46c845c4313a2a468a`。E/board-before.log、F/board-check.log，独立 catalog 当前 `draft-THfIe5` success、running=version=1、未隔离、confirmed successful=1；`FWCHECK1 match`、8 服务 active、0 failed、健康通过。
- 正式 AM625 正常候选重打，Buildroot `BR2_TARGET_UBOOT_BUILD_SYSTEM_KCONFIG=y`，清单 `uboot_build.mode=kconfig`，实际 U-Boot `.config` SHA256 `e186e35d68ff08b5db900bf189a562f82b6421788aca7729dc9074783c85695d`，R5 `.config` SHA `7dba14ebdd3b0297e99d30d801a0942071f5a9af5990cd0c6cd9543c25024b39`，与独立计算一致（F/manifest-uboot-verify.log）。保留实际包 build-info f5875140，打包时 checkout 557d33a2 另有记录，没有覆盖旧包 metadata。
- 四份 FIT（包括 bootloader）与 A3 成功候选逐字相同；kernel FIT 12940585 bytes SHA `c4fcabb0eca03e633b660d08df52110cdc5b649fc8efe69ccc1ef9ca36e46931`、独立提取 rootfs payload 30429184 bytes SHA `0021c4445bd24e8148773e505f50005c2341a6f4118a6429b5c0e40ac9c8b45b`，完整 identity 相等（F/content-reuse.log、rootfs-extract.log）。只改变 sidecar，不重复发布同一内容；未安装/刷写新 bootloader，不将 kernel/rootfs OTA 宣称为 bootloader 安装验证。
- 重新比较从最终 FIT 提取 FDT 与活动树 `bsp,bootlog-v2`、memory-region 指向 reservation phandle 0x3f、reg 0x9c900000/0x100000 一致，F/board-verify.log、active-*.bin。9/9 实装 payload 与该候选 rootfs SHA 相等（F/board-package-compare.log）。
- 同一 boot 的 logctl persistent/sync=ok、verify-boot、RAM acknowledged；正常 V2 实际归档 `a3cc8dd6-ff6d-4c90-8c2e-76565aa063e9`，r5-spl 418 bytes CRC 968e5d16、a53-spl 455 CRC ea107dd6、uboot 3027 CRC 323630a1、kernel 24699 CRC ab0dd177。四段 dropped=0，前三段本地/服务端字节相等，kernel 早期 0 bytes 为正确 prefix、sealed CRC 相等。F/archive-verified.log。
- legacy ARMv7/缺 `.config`/分源场景仅由独立主机 Make/制品夹具验收，未给 AM625 更换 bootloader 或修改实际设备状态。其他真实服务器未进行状态变更。独立候选与常规 images 同步，上一目录保留；验收后各仓提交/远端核对见 E/git-verification.log。

全部回归结束后，2026-11-26 21:52:39+08:00 再经可信 SSH 核对同一 boot、running ID 与 confirmed successful=1、健康及无 failed unit，F/board-final-health.log。
