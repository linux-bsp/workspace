# A6：AM625 旧 SOL 续传切换、升级兼容与 OTA 实机验收

E=`output/edk-convergence-a6-20261126-222810-6Br8uw/`，F=E/final/。[工程验证](../../edk/docs/edk-convergence-a6-validation.md)。

## 正式运行与设备事务

| 项目 | 实际证据 |
| --- | --- |
| 指定板 | MAC `1c:63:49:22:c4:f7`，HWID `1010001000110000`，IP `192.168.10.211`，Linux 7.0.0/aarch64；升级前可信 SSH 核对，slot B boot `4d0b0921-4e4a-43b6-a28b-bdd6c8496fcd`，运行 ID `c35df4d7c7ee09cb7cfc489bec3d48c16b0bb4f3c4e1343fad3f6a08b3d85f8a`，health=ok。E/board-before.log。 |
| 正式候选 | `v0.0.1` packed 1，ID `f09d25468a041e66221c4f80c6a63db9ea3fd93f6f1c1893f6c2be45164835bb`；OTA 包 SHA `d7313ca749f0e4a327c2f5a238243eba0d9b985e8b10b17503314a44211712df`；kernel FIT 12940585 bytes `9247a0c47704950d79b0f31f925c0f5a910484b8b1bf183ba763be3cb80718e7`，rootfs payload 30429184 bytes `c4666e2f515badd3396878ab85caa9031294f5e94759a780928f7cc8763475fa`。 |
| 发布 | publication `draft-O7yyB1`，2026-11-26 22:40:11+08:00，唯一指定 HWID/channel、relay 限指定板、draft exact ID。F/publication.log、publication.json、server-draft-state.json。 |
| 设备事务 | 下载/安装/boot-testing 之后，22:41:52 catalog `success`，running=version=1，未隔离。F/ota-timeline.log、ota-success.json、device-transaction.json。 |
| 重启验收 | 实际串口核对新 SSH key；boot `587b9d98-81c0-4825-9e1a-a718c9bfe741`，slot A kernel/rootfs confirmed successful=1，FWCHECK1 match，health-check 成功，8 服务 active、0 failed。9/9 实装 artifact SHA 与正式候选 rootfs 相等；实装 /usr/bin/logctl SHA `14521cdb2bd08b8704b9e55da3bfa794a0ebaac673d1d30763f9052ed469125d`。F/board-check.log、board-package-compare.log、serial-key.log。 |
| 运行 PDM | 同一 boot 的 dmesg `[PDM:INFO] pdm_main.c:28 - git=0022d087f413181c877433a2c7259fbcf48f40d2-dirty`，与正式候选 metadata 一致；target/host 真实包信息的源树摘要与独立快照一致。F/board-pdm-source.log、manifest-package-verify.log。 |

正式 v2 路径：活动 DT 与 FIT `bsp,bootlog-v2`、memory-region/phandle 0x3f、reg 0x9c900000/0x100000 一致（F/board-verify.log）。logctl 持久化状态正常、sync-state=ok、verify-boot 通过、archive-pending=0、RAM acknowledged。新 boot 的实际归档 capture `deaee2e2-ca6b-454c-a7a5-06affd485f62`：r5-spl 418 bytes CRC bf038e8b、a53-spl 455 CRC dc187eb7、uboot 3027 CRC d8b898aa、kernel 24705 CRC e8293427，全段 dropped=0；前三段原始字节相等，kernel 早期 0-byte 前缀与 sealed CRC 匹配（F/archive-verified.log）。读取实际接收端的既有归档，没有额外写入服务器配置。

## 板上专项（隔离模拟，不是正式 SOL 切换）

候选测试用真正从本次 rootfs 提取的 ARM64 logctl、libbsl、libserver；交叉编译同一接收端测试器，在指定板临时目录独立配置、每项独立网络 namespace、仅 loopback 活跃，无外部路由。自然能力及只对测试进程注入 memfd ENOSYS 两组。A21 原实装 logctl SHA `5f15cf25175f35dd0efa6f6ce28b97e8d109764d7156eceee6e36c4b713ff001`（当时发布制品提取），原依赖 libbsl/libserver/libcrypto/libz 与候选逐字相同（F/a21-library-match.log）。上传后核对所有文件 SHA，旧版实际上传而非虚构游标。F/board-candidate-files.log、board-candidate-{natural,no-memfd}.log。

| 专项 | 候选自然/ENOSYS 实际结果 |
| --- | --- |
| switch、switch-changed | 两端顺序切换，未变 A 从 4096 续完到 8273，B 8273，各 3 块逐字相同；已变 A 留 4096 旧前缀、拒绝拼接，B 完整；普通历史流进展。 |
| old-binding、capacity | 兼容旧 A1 record；768 条边界不牺牲旧目标，允许 A 完成；过期 boot scoped 记录回收后 B 完成。 |
| old-complete | 实际 A21 传完 8273、3 块，切换后连续至少两轮正常，无重复正文、警告或补凭据，普通历史流完成。 |
| full-conflict、malformed、unreadable、overrun | 保留四种独立错误，正文、证据及原文件不变，健康普通流仍完成。 |
| A1 六项保留回归 | current/historical 逐字、源替换、续传、重启去重、取消、meta 变化、原证据保留。 |

发布前候选自然 15/15、ENOSYS 15/15；命令 `bash "$F/board-receiver.sh" "$E" candidate`。发布后使用实装路径 `/usr/bin/logctl`、实装库并重新校验实际 A21 旧二进制，命令 `bash "$F/board-receiver.sh" "$E" installed`；实装结果见本记录末尾。测试结束清理专属临时目录，不更改正式接收配置或历史原文件。

原版本、Buildroot 配置、工具链和 bootloader 输入不变，未刷写 bootloader；其他真实服务器只读，所有断线与接收状态变更仅发生在隔离夹具。

实装复验两组各 15/15，全 30 项成功；F/board-installed-{natural,no-memfd}.log 与 board-installed-files.log。切换稳定/变化、旧格式、768 条容量、实际 A21 升级后的两轮正常状态及异常拒绝均重现候选结果。22:43:41 再核对同一 boot、运行全 ID、slot A confirmed successful=1、health-check、0 failed、logctl sync ok；测试临时目录均已清理。F/board-after-installed-tests.log。复核脚本首次使用的 BusyBox 不支持 `date -Iseconds`，改用显式时间格式重跑只读核对成功。正式独立候选与常规 images 逐字同步，旧目录保存在 F/previous-default-images；F/default-images-check.log、E/git-verification.log。
