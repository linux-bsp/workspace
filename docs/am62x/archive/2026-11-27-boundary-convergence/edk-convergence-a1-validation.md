# A1：AM625 旧 SOL 续传内容身份专项与正式 OTA

E=`output/edk-convergence-a1-20261126-210418-pRRwFC/`，F=E/final/。[EDK 回归和修改边界](../../../../edk/docs/archive/2026-11-27-boundary-convergence/edk-convergence-a1-validation.md)。

| 验收项 | 实际证据 |
| --- | --- |
| 指定板 | MAC `1c:63:49:22:c4:f7`，HWID `1010001000110000`，IP `192.168.10.211`，aarch64/Linux 7.0.0。原可信 SSH key 核对，E/board-before.log，重启后通过实际串口核对新 key 与 boot ID，F/serial-key.log。 |
| 发布前 | 唯一指定设备、活动 HWID channel、192.168.10.211/32 限制的 relay 验证；原 slot A、boot `e8e3b199-e334-4d79-891b-804cc57826d5`、ID `cbe56317d9c1c27a002cf220f0e25d88e752c0464d6ea7de57b72c4d6e50e67c` success。 |
| 发布 | `draft-REJVTM`，2026-11-26 21:14:54+08:00；tag `v0.0.1` packed 1，ID `43efbac30fe4a8f4a4b7f9ba7be92b7d33568056fa5959c2e9ffeb7869c7c695`。F/publication.log、publication.json、server-draft-state.json。 |
| OTA 包 | SHA256 `b6abfc3426960ad12f23abfc08336ea8e19fec3d10f580b6f8f88308dc5c1a5f`；kernel FIT 12940585 bytes `d791aa629fb1f8039bb41397e1c0657ab5ff2a6ba4ea1cd337aa12c864460073`，rootfs payload 30429184 bytes `06da5d6611912bd7cb436afe3e8327600e39e11cc29a0766e157f37c9115ddda`。 |
| 设备事务 | 2026-11-26 21:16:36+08:00，catalog exact ID `success`、running=1、version=1、未隔离；非 installing/boot-testing。F/ota-timeline.log、ota-success.json、device-transaction.json。 |
| 重启确认 | boot `f2288b6f-1aca-444a-8d13-efe9e917cc2a`，slot B kernel/rootfs confirmed successful=1，`FWCHECK1 match`，健康检查通过，8 unit active、无 failed。9/9 实装 payload SHA256 等同实际 rootfs，含 `/usr/bin/logctl` `e4a7fd61e43d6a782b44449af9c0bb9b21d8d28498e5724fe08afbe0a913183d`。F/board-check.log、board-verify.log、board-package-compare.log。 |

## 实机隔离接收专项

实际候选来自最终 FIT 解包 rootfs，已核对 5 个复制文件 SHA256。回环 receiver 使用原测试夹具的 `--isolate`；每个 namespace 仅 lo active（sit0 down、无 IPv4 外部路由或非 lo IPv6 路由），独立 temporary log root、仅向本地 listener 发送，不接触正式 collector/真实外部服务器。进程专属 LD_PRELOAD constructor 证明 ENOSYS，未调整实际内核配置。自然及 ENOSYS 各 6 案例：

| 场景 | 期望及实测 |
| --- | --- |
| stable | current 12059/12059 历史 8273/8273；已校验 current 源变更后仍送旧 snapshot、恢复原投影后从 4096 续传。 |
| changed / restart-changed | 同 generation 历史 raw-only 8273 字节，在首游标后替换未恢复；保留准确 4096/8273 字节前缀，其后拒绝（夹具检查 `identity-changed` 及 boot/stage/gen/offset）。 |
| restart-unchanged | 非零 ACK 后重启、原文件不变，准确 8273/8273；未重发确认前缀。 |
| unknown-prefix | 模拟升级前已有正确 4096 字节但本地无证据，不发送后缀，`identity-missing`。 |
| meta-changed | metadata 已生成时变更 raw，发送仍完整旧帧 8273/8273；重启无重复。 |

每案逐块校验 boot/stage/order/gen/offset/length/内容，其他历史健康流 87 bytes 全部继续；普通同阶段、错误投影 invalid、去重和取消仍保护。原始未变历史输入 inode/time/内容不变，变更用例替换后的原始文件保留、未生成历史投影。F/board-candidate-{files,natural,no-memfd}.log。

## 正式启动日志

最终 FIT 内 FDT 与活动设备树 `bsp,bootlog-v2`、memory-region/phandle 0x3f、reg 0x9c900000/0x100000 一致；logctl collector=running、sync=ok、verify-boot、RAM acknowledged，新 boot ID 对应 capture `f3e62d17-0a57-4e8e-b134-8e99e39d64fd` 的实际归档：

| stage | bytes | CRC32 | 本地对照 |
| --- | ---: | --- | --- |
| r5-spl | 418 | 009ae072 | 逐字相等 |
| a53-spl | 455 | 55250dc9 | 逐字相等 |
| uboot | 3027 | c1ce6769 | 逐字相等 |
| kernel | 24705 | 8871cdb1 | 早期本地 0 bytes；sealed CRC 正确 |

四段 dropped=0。F/archive-verified.log、board-local.tar、active-*.bin。没有刷写或改变 bootloader，不拿 kernel/rootfs OTA 验证未安装的 bootloader。VERSION 不变，其他真实服务器未操作。

正式 `success`、重启及健康确认后，使用实装 `/usr/bin/logctl` 和正式系统库重跑相同 12 案（6+6），全部 PASS，F/board-installed-{files,natural,no-memfd}.log。测试临时目录已清理。常规 images 与正式候选逐字一致，上一成功 images 目录保存在 F/previous-default-images。阶段提交/远端精确 gitlink 核验 E/git-verification.log。
