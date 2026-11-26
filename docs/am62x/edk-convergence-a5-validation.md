# A5：AM625 正式包配置来源与 OTA 实机验收

E=`output/edk-convergence-a5-20261126-221458-eOMKEr/`，F=E/final/。[工程验证](../../edk/docs/edk-convergence-a5-validation.md)。

| 项目 | 实际证据 |
| --- | --- |
| 指定板 | MAC `1c:63:49:22:c4:f7`，HWID `1010001000110000`，IP `192.168.10.211`，Linux 7.0.0/aarch64；原可信 SSH 核对，升级前 slot A boot `fba8a8cf-97fa-42f5-8376-bf992e784687`，完整 ID `8472924c9470022a7ae05db552e5db077c641ee7a646ce46c845c4313a2a468a`。E/board-before.log。 |
| 正式候选 | `v0.0.1` packed 1，ID `c35df4d7c7ee09cb7cfc489bec3d48c16b0bb4f3c4e1343fad3f6a08b3d85f8a`；OTA 包 SHA `537c749e782808de06ec8befe1ce225884eee1db2ccc5b81140809afdcdbf21f`；kernel FIT 12940585 bytes `52a6fcaa11da87a7cbc04e4f77c61c1317cb2034648a7c40e86d9996f4d3dc1c`，rootfs payload 30429184 bytes `c9481fc4b9530f529876558a1a94664b81e40b080ba01297228d7348d743c639`。 |
| 所选源码 | 实际正式 target/host 在外层 EDK_SOURCE_DIR=B 下仍缓存正式 workspace EDK，真实包信息、清单 role/source/config 摘要、PDM embedded revision 独立匹配；revision `d15d6939dc41b20142b08d3d33ab1877d9205051-dirty`，源树摘要 `ec48509f36ad76ca2fa49ee5513be535c7bb30a76f490afa322fd1330b99676a`，准备中的文档记录与精确 source snapshot 一并保存，未替换正式 checkout。F/manifest-package-verify.log。 |
| 发布 | `draft-51ltOv`，2026-11-26 22:23:00+08:00；唯一指定 HWID/channel、relay 限指定板、exact ID 检查，F/publication.log、publication.json、server-draft-state.json。 |
| 设备事务 | 22:24:47 catalog `success`，running=version=1，未隔离。F/ota-timeline.log、ota-success.json、device-transaction.json。 |
| 重启验收 | 实际串口核对新 SSH key；boot `4d0b0921-4e4a-43b6-a28b-bdd6c8496fcd`，slot B kernel/rootfs confirmed successful=1，FWCHECK1 match，健康，8 服务 active、0 failed。9/9 实装 artifact 与正式候选 rootfs SHA 相等。F/board-check.log、board-package-compare.log、serial-key.log。 |
| 运行 PDM | 同一 boot 的 dmesg `[PDM:INFO] pdm_main.c:28 - git=d15d6939dc41b20142b08d3d33ab1877d9205051-dirty` 与候选一致；host 通过主机实际包记录验证，F/board-pdm-source.log。 |

最终 FIT FDT 与活动树 `bsp,bootlog-v2`、memory-region/phandle 0x3f、reg 0x9c900000/0x100000 一致，F/board-verify.log。健康与 logctl persistent/sync ok、verify-boot、RAM acknowledged；新 boot 的归档 capture `7f894f3a-ce15-45c7-8cc9-ed08cb9a15f8`：r5-spl 418 bytes CRC b2a72b1c、a53-spl 455 CRC a0eec492、uboot 3027 CRC 985ebd03、kernel 24705 CRC f2101c1b；dropped=0，前三段字节相等、kernel early 0-byte prefix 和 sealed CRC 匹配（F/archive-verified.log）。

原版本、工具链和 bootloader 输入不变，未刷写 bootloader；外部源码冲突测试仅在主机副本，未操作其他真实服务器。正式独立候选与常规 images 逐字同步，原目录保存在 F/previous-default-images。推送核验 E/git-verification.log。
