# A21：AM625 无 memfd 兼容专项及正式 OTA 验收

2026-11-26 20:20:10+08:00 正式板验通过，随后实装二进制自然/ENOSYS 两组隔离接收通过。E=`output/edk-portability-a21-20261126-200433-e8tkel/`，F=E/final/。[EDK 回归](../../edk/docs/edk-portability-a21-repair-validation.md)。

| 项目 | 实际证据 |
| --- | --- |
| 发布 | `draft-EP71gS`，2026-11-26 20:18:02+08:00，只针对指定 HWID 的活动 channel |
| 固件 | `v0.0.1` packed 1，完整 ID `cbe56317d9c1c27a002cf220f0e25d88e752c0464d6ea7de57b72c4d6e50e67c` |
| OTA 包 SHA256 | `e3499cb76c0d15f2b406b0263def3ae082a0d89b9dc6f80857270d719f020029` |
| kernel FIT / rootfs payload | 12940585 bytes `cafcbeaed9a84213a8efe5264588007ddb071703781aea9bc4208e89820e28e2`；30425088 bytes `be1f136d6f2e00911c08901bca0a3302697762e46a0a11f18ba83cda5714eb3c` |
| 设备事务 | 20:19:54 catalog `success`，running=1、version=1、未隔离 |
| 指定板 | MAC `1c:63:49:22:c4:f7`，HWID `1010001000110000`，IP `192.168.10.211`，Linux 7.0.0 |
| 运行 | A 槽 kernel/rootfs confirmed successful=1、FWCHECK1 match、boot ID `e8e3b199-e334-4d79-891b-804cc57826d5`（升级前 `83613296-b1de-42c5-822d-11bd14637d11`） |

发布前核对原可信设备、单设备 catalog/channel、仅指定板可达 relay、候选 exact ID、完整源码及测试证据。F/publication.log、publication.json、server-draft-state.json、ota-timeline.log、ota-success.json、device-transaction.json；重启后物理串口核对新 SSH key 再严格连接，F/serial-key.log。8 个 unit active、0 failed，9/9 运行制品与实际 rootfs FIT 提取文件 SHA 相等（包括新 logctl、libserver），FWCHECK1 match、健康通过。F/board-check.log、board-verify.log、board-package-compare.log。

## 真实板独立接收专项

- 实际当前内核 `/proc/config.gz` 的 CONFIG_MEMFD_CREATE=y、CONFIG_NET_NS=y、CONFIG_NAMESPACES=y；E/board-before.log。未调整内核配置，不冒充无 memfd 实体内核，ENOSYS 通过仅被测进程的 LD_PRELOAD 测试库模拟，constructor 证明返回值。
- 预发布从实际 rootfs 提取 logctl、libserver、libbsl，配合真实 ARM64 接收端及故障库；5 个复制文件 SHA 相等，正常和 ENOSYS 均 PASS，F/board-candidate-{files,natural,no-memfd}.log。首次 shell harness 变量名与 zsh PATH 别名冲突，已清理空临时目录，换非保留变量后成功；未改变设备配置。
- 发布 success 后以实装 `/usr/bin/logctl` 和正式系统库再次重复两组，F/installed-receiver-{files,natural,no-memfd}.log。每组实际隔离 namespace 仅 lo 活跃（sit0 down，无 IPv4 外部路由或非 lo IPv6 路由），接收当前 12059、历史 8273 bytes，完整头/boot/stage/order/gen/offset/正文逐块比较；首个游标请求时修改源副本，仍传正确已校验快照；4096 字节处断线，恢复源后从准确 ACK 续传，重启无重复，取消正常，坏投影跳过，健康阶段继续，历史原文件不变。全部使用独立临时日志树、loopback HTTP 接收端，退出后清理，不启动第二 collector 或访问生产目的端。E/board-preflight-receiver.log、F/board-installed-receiver.sh。真实 pmcd 完整数据及原归档回执验证另在原生隔离测试通过。

## 正式 V2 日志与活动设备树

最终 FIT FDT 与板上 compatible `bsp,bootlog-v2`、memory-region/phandle 0x3f、reg 0x9c900000/0x100000 相等。logctl persistent/sync ok、verify-boot 成功、RAM acknowledged。新 boot 的 capture `5d72305f-f961-4354-b373-eb12452df157` 实际归档：

| stage | 服务端 bytes | CRC32 | 本地对照 |
| --- | ---: | --- | --- |
| r5-spl | 418 | 50ac7c8c | 逐字相等 |
| a53-spl | 455 | 59c32bc7 | 逐字相等 |
| uboot | 3027 | 9efe1d03 | 逐字相等 |
| kernel | 24705 | 835fad3d | 早期本地 absent，0 byte 前缀；sealed CRC 正确 |

四段 dropped=0。F/archive-verified.log、board-local.tar、active-*.bin。真实启动链仍为 V2，旧格式是实板隔离夹具，未安装其他 bootloader，未操作其他真实设备。VERSION 及原 Buildroot 配置不变，正式唯一输出保留，常规 images 与之逐字同步，原目录 F/previous-default-images，F/default-images-check.log、commit-source-check.log。

EDK `a467d44de920ec8e1d439e83c2418a906224894e` 在上述发布/实机验收后提交并推送 master，BSP 仍为 A20 `ae0c744b4e208efe5033143cdb05871b809c2c41`。工作区更新精确 gitlink；E/git-verification.log 核对全部三个阶段提交可从远端 master 到达。
