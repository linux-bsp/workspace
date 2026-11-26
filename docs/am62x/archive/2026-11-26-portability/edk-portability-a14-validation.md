# A14：AM625 受管 SDK 拒绝保留和完整更新探针

2026-11-26 15:57:49+08:00 当次 V6 PASS，E=`output/edk-portability-a14-20261126-154907-HqiZnC/`。
[EDK A14 工程](../../../../edk/docs/archive/2026-11-26-portability/edk-portability-a14-validation.md)。

严格固定 A7 串口核实的 SSH key，先确认 MAC 1c:63:49:22:c4:f7、HWID 1010001000110000，
boot ID 8fb95921-66b5-431b-b5b5-1074e58148c3、kernel/rootfs A 槽 confirmed successful=1、v0.0.1 packed 1。
完整 firmware_id 16f44b78e3915e830ae7bdcf2293ebc06738b1a187edead8d74aab3359b81730，
A7 draft-3v0bSf catalog 同一设备/ID/success/running=1，FWCHECK1 match，9/9 运行制品与 A7 rootfs 相同。
原包 SHA256 b05b1f984f7e9e2dad669f81b08bab8926e91c5b9bdecaa6b322553e64fe8b7c。

| 实际临时版本 | libpdi.so.2 SHA256 |
| --- | --- |
| 拒绝后保留 on | 68e29c5f3c529507a87ba24b3ee09e68c0d555aaf264aeb918282b8e27c77e82 |
| 成功完整 off | d5a21b299d2d0623b05f18b631354f56f84b69de759e03eb78faf99676384ce2 |

两者 libbsl.so.2 SHA256 e1e7b416f7049b5db923708e7695712eba8c58edab05cc0bc3d8d02cbdc632cd。
同一 ABI2 probe SHA256 42ae2dd7a072d4c049b573f82aaa339c4d46dc360fad6f46c4e66cb55e1f9e54，
分别实际加载两套 `/tmp/edk-a14-sdk.0aalL2/board-on/`、`board-off/` 的 PDI/BSL，
pdi_manager_close(-1)=-9 都通过；on 的完整原 hwmon probe、属性输入与 FIFO 全通过。
临时目录显式清理；实际正式 PDI/BSL ABI2 链、旧 PDI ABI3 不存在、8 unit active、health-check、零 failed unit。
E/board-bundle/SHA256SUMS、board-v6.sh/.log、board-formal-match.log。
仅临时 SDK，不改变正式固件，未新发 OTA、未重启其他设备、未对其他真实服务器执行控制或配置写入。
