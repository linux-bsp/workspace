# A18：AM625 实际构建、最终 FIT 与活动设备树验收

2026-11-26 16:57:12+08:00 V6 PASS，E=`output/edk-portability-a18-20261126-164352-VGEQDO/`，F=E/final/。
[EDK/BSP A18 工程](../../../../edk/docs/archive/2026-11-26-portability/edk-portability-a18-validation.md)。

本次只读复验指定设备，固定 A16 经串口核实的 SSH key。
MAC 1c:63:49:22:c4:f7、HWID 1010001000110000、boot ID 727e44b9-d1b1-47f8-b992-5be7ca25d7f3、
B 槽 confirmed successful=1、v0.0.1 packed 1、
完整 firmware_id 3856203dcd4a0c1bf712bd7969558533de654a0e178f1a1e10dd0ad03769afc3。
FWCHECK1 match、8 unit active、0 failed、health-check 通过，9/9 运行制品匹配，
catalog 同一 A16 发布事务 success/running=1，E/board-v6.log、board-formal-match.log。

| 实际属性 | 最终 FIT 中选定的 FDT | 运行中 DT |
| --- | --- | --- |
| compatible | bsp,bootlog-v2 | bsp,bootlog-v2，NUL 结尾 |
| bootlog memory-region 第一个 cell | 0x3f | 0x3f |
| /reserved-memory/bootlog@9c900000 phandle | 0x3f | 0x3f |
| reg address / size | 0x9c900000 / 0x100000 | 0x9c900000 / 0x100000 |

E/packed-kernel.dtb、fit-extract.log、active-*.bin、board-dtb-compare.log；
三端实际编译布局、四对象依赖/ELF、build inputs 完整证据 F/images/release/board-validation.txt、
F/actual-check.log。A18 新生成四个 ITB、verity rootfs 与原 boot inputs 全部逐字相同于 A16，
F/formal-content-match.log；仅验证 sidecar 改变，原 OTA 包 SHA256
5b772ef365d1acadd68a54167cee7298cf9a303943945224ad28c551fe46cece 再核对，未新发 OTA。

本次同一 boot 的只读日志再验证：status persistent/sync ok、startup acknowledged，verify-boot exit 0。
capture b10dd856-0b01-44a3-8525-732d1f484ba3 的服务端清单及实际字节重新提取，
r5-spl 418/974a3e55，a53-spl 455/ff5dbe7a，uboot 3027/089e2f6e，kernel 24705/1f26e236，
全部 CRC32 匹配，无 dropped；本地前三段逐字相等、早期 kernel state=absent，分别按自身清单验证。
E/archive-verified.log、archive-*.json/bin、board-local.tar。
未重新安装 bootloader；新构建的 bootloader 制品检查不等于实机启动分区安装。
第二项目仅独立夹具；没有其他真实设备的控制或写入。
