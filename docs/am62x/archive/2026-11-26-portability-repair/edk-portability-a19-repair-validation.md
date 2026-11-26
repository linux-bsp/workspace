# A19：AM625 最终 FIT 与完整依赖记录专项板验

2026-11-26 19:50:36+08:00 PASS。E=`output/edk-portability-a19-20261126-194700-pHFcqu/`，F=E/final/。
[工程与回归](../../../../edk/docs/archive/2026-11-26-portability-repair/edk-portability-a19-repair-validation.md)。指定板固定上次串口核实的 key，MAC `1c:63:49:22:c4:f7`、HWID `1010001000110000`、Linux `7.0.0`、boot ID `83613296-b1de-42c5-822d-11bd14637d11`。版本 v0.0.1 packed 1，B 槽 confirmed successful=1，完整 firmware_id `0971e5b329bc717a96389b0f529a9e4da481b3faf45d224e67d0162086f79a13`，catalog 上次 `draft-V54AKR` 对应该运行身份 success/running=1；FWCHECK1 match、8 unit active、0 failed、9/9 运行文件与上次相同正式 rootfs 匹配。E/board-before.log、F/board-check.log、board-package-compare.log、catalog.json。

| 核验项 | 结果 |
| --- | --- |
| kernel FIT / rootfs 实际分区 | 12940588 bytes `21f8facbea36c8f56d4b19b178a02c94c5780b50d52652686a0ce647b37a48c3`；30425088 bytes `0d661e39187fae712a39e41ce7633752564face3a6b1ef829f914626e26bfe28` |
| 候选 / 上次正式制品 | 四 ITB、initramfs、verity rootfs 与完整 identity 逐字相等，F/formal-content-match.log；仅核验侧车及源码记录变化，不重新 OTA |
| FIT 选定 FDT / active DT | compatible `bsp,bootlog-v2`、memory-region 0x3f、reservation phandle 0x3f、reg 0x9c900000/0x100000 全部一致。F/packed-kernel.dtb、active-*.bin、board-dtb-compare.log |
| 启动日志 | persistent/sync ok、verify-boot 成功、RAM acknowledged；同 boot capture `784b65b0-a877-4f40-8f85-1db361e877c5`：r5 418/4c81b2d0，a53 455/e5ad50a2，uboot 3027/ff7b0455，kernel 24705/dc01cabb，四段 CRC 及本地前三段字节相等，早期 kernel 为 absent 且前缀匹配，dropped=0。F/archive-verified.log、board-local.tar。 |

真实 Kbuild 产物 final gate PASS；截断与陈旧反例全部位于构建主机隔离副本，真实打包两次拒绝后保留完整前一成功 release。本阶段未更改板上配置、未安装 bootloader、未操作其他真实设备。本地启动时间首次查询使用不支持的 BusyBox `date -Is`，改用明确 `date +%Y-%m-%dT%H:%M:%S%z` 后通过。

EDK 文档提交 `7dbd95533a8cf9ce26284791b951bbf385b5a14b`、BSP 修复提交 `49d5bc784e118e309d91e76315dd3f353d0b7194` 已分别推送并核对 master。工作区包含用户准备的历史归档、索引、计划及提示词，文档路径检查 276 个相对链接无缺失（E/doc-links.log），记录精确 gitlink。
