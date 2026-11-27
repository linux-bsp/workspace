# A3：AM625 正式包来源、清单与 OTA 实机验收

E=`output/edk-convergence-a3-20261126-212838-XI4MfJ/`，F=E/final/。[工程回归及六种独立角色验证](../../../../edk/docs/archive/2026-11-27-boundary-convergence/edk-convergence-a3-validation.md)。

| 事项 | 实际证据 |
| --- | --- |
| 指定板 | MAC `1c:63:49:22:c4:f7`、HWID `1010001000110000`、IP `192.168.10.211`、aarch64 Linux 7.0.0。原可信 SSH 核对，升级前 slot B boot `f2288b6f-1aca-444a-8d13-efe9e917cc2a`，ID `43efbac30fe4a8f4a4b7f9ba7be92b7d33568056fa5959c2e9ffeb7869c7c695`。E/board-before.log。 |
| 正式候选 | `v0.0.1` packed 1、firmware ID `8472924c9470022a7ae05db552e5db077c641ee7a646ce46c845c4313a2a468a`；OTA 包 SHA `993f8c7572c2e0f54def18b833bb152fea935fcac5ba312b8cfce197e138c640`；kernel FIT 12940585 bytes `c4fcabb0eca03e633b660d08df52110cdc5b649fc8efe69ccc1ef9ca36e46931`，rootfs payload 30429184 bytes `0021c4445bd24e8148773e505f50005c2341a6f4118a6429b5c0e40ac9c8b45b`。 |
| 源码与清单 | 默认 EDK `f58751404a7d5d919226b7c50f130742cfbd7960`。正式 `source_roles.edk`、`source_roles.host-edk` 均为 `edk`，两份实际 `build-info` 原文、各配置 SHA、同一选定 source SHA 核对；实际 PDM kernel metadata 和候选模块内字符串均与之相等。F/manifest-package-verify.log。外部/分源测试只在主机隔离副本。 |
| 发布 | `draft-THfIe5`，2026-11-26 21:38:39+08:00；唯一指定设备/HWID channel/仅指定板可达 relay、exact ID 核对，F/publication.log、server-draft-state.json、publication.json。 |
| 设备事务 | 21:40:21 catalog `success`，running=1、version=1，未隔离。F/ota-timeline.log、ota-success.json、device-transaction.json。 |
| 实装 | 串口确认新 SSH key 与 boot `fba8a8cf-97fa-42f5-8376-bf992e784687` 后严格连接；slot A kernel/rootfs confirmed successful=1、FWCHECK1 match、健康，8 服务 active、0 failed。9/9 候选 rootfs 实装制品逐文件 SHA 相等。F/board-check.log、board-package-compare.log、board-verify.log、serial-key.log。 |
| 运行中实际 PDM | 同一 boot 的 `dmesg` 实际输出 `[PDM:INFO] pdm_main.c:28 - git=f58751404a7d5d919226b7c50f130742cfbd7960`，F/board-pdm-source.log；host source 由主机实际配置和 build-info 证明，不冒充板上安装。 |

最终 FIT 所选 FDT 与活动树 `bsp,bootlog-v2`、memory-region/phandle=0x3f、reg=0x9c900000/0x100000 相等，F/active-*.bin。logctl persistent/sync ok，verify-boot PASS，RAM acknowledged；新 boot 的实际归档 `a3cc8dd6-ff6d-4c90-8c2e-76565aa063e9`：r5-spl 418 bytes CRC 968e5d16、a53-spl 455 CRC ea107dd6、uboot 3027 CRC 323630a1、kernel 24699 CRC ab0dd177，dropped=0；前三段本地/服务端字节一致，kernel 早期 0 bytes 前缀匹配 sealed CRC。F/archive-verified.log。

VERSION/工具链/原 boot 输入不变；未安装 bootloader、未切换正式源码至外部测试 checkout、未操作其他真实服务器。独立候选与常规 images 逐字同步，原目录 F/previous-default-images 保留。源码与各仓远端验收 E/git-verification.log。
