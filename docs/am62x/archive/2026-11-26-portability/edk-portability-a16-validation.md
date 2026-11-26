# A16：AM625 统一启动日志消费及正式 OTA 验收

2026-11-26，E=`output/edk-portability-a16-20261126-161345-corPeB/`，F=E/final/。
[EDK A16 工程](../../../../edk/docs/archive/2026-11-26-portability/edk-portability-a16-validation.md)。

- 预检 A7 严格 SSH key、MAC 1c:63:49:22:c4:f7、HWID 1010001000110000、
  A 槽 v0.0.1 confirmed/healthy、完整 ID 16f44b78e3915e830ae7bdcf2293ebc06738b1a187edead8d74aab3359b81730，
  boot ID 8fb95921-66b5-431b-b5b5-1074e58148c3。
  F/board-before.log、server-before.json、serial-key-before.log。
- 127.0.0.1:18090 catalog 仅该设备及 HWID，8090 TCP relay 限定 192.168.10.211/32，
  F/ota-peer-filter.log。只上传三文件 release/kernel/rootfs FIT 的实际 OTA 包；SHA256
  5b772ef365d1acadd68a54167cee7298cf9a303943945224ad28c551fe46cece。
  F/upload.json、server-draft-state.json、publication.json，draft-hJKoz0，v0.0.1 packed 1。
- 16:26 发布，installing→boot-testing→**16:28:04 success**；
  F/ota-timeline.log、ota-success.json、device-transaction.json（started=1795681597，updated=1795681681，四项事件）。
  新完整 ID 3856203dcd4a0c1bf712bd7969558533de654a0e178f1a1e10dd0ad03769afc3，B 槽 confirmed successful=1。
  串口 /dev/ttyACM2 核对新 SSH fingerprint SHA256:mLes0h4bl6fh0qRPlt3D3Nz5JokWuW99VIX0dPXDl0s，
  boot ID 727e44b9-d1b1-47f8-b992-5be7ca25d7f3，固定新 key；F/serial-key.log。
- 16:28:33 V6 PASS，FWCHECK1 match、health-check、8 unit active、零 failed units。
  kernel 12940588 bytes SHA256 3d4b9139d37330a8c39fcd04fdc605d4a6f832ed87643137b741c3b4783a07b7，
  rootfs 30425088 bytes SHA256 9480ebcf1a2351167ddfd1095d02149e9451f802a9f27b8e0b9592ff0be3737c；
  9/9 实际运行制品同包内 SHA，包括新 logctl 54b2542e9dedce6ebce80766b8d0146bf5a292ce8774cbc9a0e3bb405699d61c。
  F/board-v6.log、board-package-compare.log。仅 kernel/rootfs OTA，未安装新 bootloader。

## 同一 capture 的本地及服务端核验

capture b10dd856-0b01-44a3-8525-732d1f484ba3，recovery boot 727e44b9-d1b1-47f8-b992-5be7ca25d7f3。
status 显示 persistent/sync ok、acknowledged，verify-boot 成功。
本地 startup-bank0.manifest 及二进制只读提取，服务器同一 capture 的四段已归档并 ACK；
F/verify-archive.py、archive-verified.log、board-local.tar、archive-*.json/bin。

| 阶段 | 本地 bytes / CRC32 | seal 后服务端 bytes / CRC32 |
| --- | --- | --- |
| r5-spl | 418 / 974a3e55 | 418 / 974a3e55 |
| a53-spl | 455 / ff5dbe7a | 455 / ff5dbe7a |
| uboot | 3027 / 089e2f6e | 3027 / 089e2f6e |
| kernel | 0 / 00000000 (state=absent) | 24705 / 1f26e236 |

前三段字节逐项相等，内核早期 snapshot 尚未产生，seal 后为完整有效数据；两次均严格匹配对应清单。
服务器四段 dropped=0。实际运行中未改变任何其他设备，异常与替代目录在隔离环境完成。
