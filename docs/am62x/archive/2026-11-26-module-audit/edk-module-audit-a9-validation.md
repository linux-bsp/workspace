# A9：AM625 安装冲突拒绝与候选 SDK 实机验证

2026-11-26，证据 E=`output/edk-module-audit-a9-20261126-134647-J5AxT5/`。
[EDK A9 开发记录](../../../../edk/docs/archive/2026-11-26-module-audit/edk-module-audit-a9-validation.md)。

正式部署沿用 A7；仅测试 SDK 在指定板 /tmp 运行，不覆盖板端安装库。
通过 A7 经串口确认的固定 SSH ED25519 主机密钥，先断言 am625、aarch64、MAC
`1c:63:49:22:c4:f7`、HWID `1010001000110000`。最终当次 boot
`8fb95921-66b5-431b-b5b5-1074e58148c3`、A 槽 confirmed successful=1、v0.0.1 packed 1，
完整 ID `16f44b78e3915e830ae7bdcf2293ebc06738b1a187edead8d74aab3359b81730`。
`fwctl ota-check` 对 A7 分区长度和 SHA 返回 FWCHECK1 match，catalog GET 同一
`draft-3v0bSf` 设备 success/running=1；A7 成功事务与包摘要见 [A7](edk-standalone-test-boundary-validation.md)。
包 SHA256 `b05b1f984f7e9e2dad669f81b08bab8926e91c5b9bdecaa6b322553e64fe8b7c`，实际默认 FIT 同 A7 一致。

| 实际 /tmp SDK | SHA256 与断言 |
| --- | --- |
| 拒绝后保留 hwmon-on libpdi.so.2 | `77066b733a803bd248fad205fe295b0b85935d6df7463a6e5d0160d2ac294cbd` |
| 成功安装 hwmon-off libpdi.so.2 | `97642e5fb0ce26bf10bf6fbfbc30f5ba6639ea892d393fb397463e8d1e61b10b` |
| 两套 libbsl.so.2 | `e1e7b416f7049b5db923708e7695712eba8c58edab05cc0bc3d8d02cbdc632cd` |
| 旧/新 hwmon probes | `d152f3d9ea0337de5e473c903b31f6cbbc19df87ffd5c237a03ab1917bad625a`（独立编译同内容）；实际 -12000、INT32_MIN/MAX、错误优先级、输出哨兵、无写端 FIFO 5s 限时全部通过 |
| off probe | `6bf695ed06fe1927cffbae6b1e4e9f3f4f3b0cce9e56f124f55c882909d5a5d2`；实际 `pdi_manager_close(-1)=-9`，通过 |

最终 13:59:05+08:00 完成。E/board-v6.sh、board-v6.log、board-bundle/SHA256SUMS；
LD_DEBUG 实际加载 `/tmp/edk-a9-sdk.P8l39w/board-on/` 或 `board-off/` 中 libpdi.so.2/libbsl.so.2。
首次 sha256sum -c 不支持、二次板端无 mkfifo，trap 清理后修复夹具，最终以完整摘要比对及交叉编译 FIFO 工具通过。
E/board-v6-first.log、board-v6-second.log 保留失败；最终临时目录显式清理且确认不存在。
实板 Satellite `libsatellite.so -> libsatellite.so.3 -> libsatellite.so.3.0.0.1`，三项旧库均无，九项当前运行制品
与 A7 实包逐一匹配，`fwctl health-check` 成功，八个 service active，零 failed unit。E/board-formal-match.log。
本轮不是新安装固件，不声称新 bootloader 验收。其他真实服务器未执行部署、控制或配置写入，
主机集成网络隔离；板探针只使用本机文件和无效 fd。

EDK 完整 250/250、BSP 12/12，包括实际安装 hook 的新正反例。远端提交与 gitlink 的对应见 E/git-verification.log。
