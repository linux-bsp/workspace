# A11：活动 DTB 引用与四段启动日志实板验收

2026-11-26 14:32:52–14:32:56+08:00，E=`output/edk-module-audit-a11-20261126-142758-63i8KG/`。
[EDK/BSP A11 验收](../../../../edk/docs/archive/2026-11-26-module-audit/edk-module-audit-a11-validation.md)。

使用 A7 串口核实的固定 SSH key；先断言 am625/aarch64、MAC `1c:63:49:22:c4:f7`、HWID `1010001000110000`。
boot `8fb95921-66b5-431b-b5b5-1074e58148c3`，A 槽 confirmed successful=1，v0.0.1 packed 1，
full firmware_id `16f44b78e3915e830ae7bdcf2293ebc06738b1a187edead8d74aab3359b81730`。
原 A7 `draft-3v0bSf` 同设备/ID 当前 catalog success/running=1；包 SHA256
`b05b1f984f7e9e2dad669f81b08bab8926e91c5b9bdecaa6b322553e64fe8b7c`、实际分区 FWCHECK1 match，
九项运行制品与已发布 rootfs 摘要匹配。正式制品未改变，未创建新 OTA。

## 活动设备树与日志

只读抓取 `/sys/firmware/devicetree/base` 属性的实际二进制数据，每次再次核对 MAC/HWID/boot ID，
与当次板端 sha256sum 输出及从实际 kernel FIT 提取的 DTB 交叉比对。

| 属性 | 活动设备树实测 |
| --- | --- |
| /bootlog/compatible | bsp,bootlog-v2 |
| /bootlog/memory-region | 4 bytes `0000003f` |
| /reserved-memory/bootlog@9c900000/phandle | 4 bytes `0000003f` |
| 同节点 reg | `00000000 9c900000 00000000 00100000` |

引用指向正确节点，0x9c900000 / 1 MiB；与实际 FIT 中 phandle/reg 一致。
E/read-board.sh、board-v6.sh/.log、board-*.bin、board-actual-dtb-check.log。
`cat /sys/firmware/bootlog/state` 实测 startup-state=acknowledged、active-buffer=2、next-buffer=1；
`logctl verify-boot` exit 0，startup logs archived; both RAM buffers acknowledged。

当次从本机管理端 GET /api/sol/devices 核实指定设备、当前 recovery boot 的 healthy-current capture
`c959b47e-de7c-4df1-ab99-0ea53832a1df`，buffer=1/generation=2/archive=complete；逐段 GET 归档内容，
实际重算长度与 CRC32（不只复用旧 A7 日志），均符合记录：

| 启动段 | 字节数 | CRC32 | 状态/丢弃 |
| --- | ---: | --- | --- |
| R5 SPL | 418 | c0d3dbaa | valid / 0 |
| A53 SPL | 455 | a83c48d8 | valid / 0 |
| U-Boot | 3027 | 415c0bb2 | valid / 0 |
| kernel | 24705 | ed6d3866 | valid / 0 |

E/server-startup-devices.json、archive-*.json/bin、archive-verified.log；A7 的历史 V1 不完整记录继续保留。
实际健康检查 exit 0，八个 unit active，零 failed unit，复查同一 boot ID；六遥测来源 last_status=0，
部分来源存在历史累计失败。仅只读访问指定板、本地服务，没有重新启动、安装 bootloader 或向任何真实服务器下发有状态操作。
BSP 12/12、三仓提交/远端/gitlink 核验 E/git-verification.log。
