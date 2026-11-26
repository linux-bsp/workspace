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

## A6.3 实机专项与 OTA

E3=`output/edk-convergence-a6-3-20261126-225712-JxSIoN/`，F3=E3/final/。[工程验证](../../edk/docs/edk-convergence-a6-validation.md#a63历史-order-更正后的冲突检测并补齐-a5-重建回归)。上次 A6 设备事务与文件保留，不覆盖。

| 项目 | 实际证据 |
| --- | --- |
| 开始身份 | 指定 AM625 IP 192.168.10.211、MAC `1c:63:49:22:c4:f7`、HWID `1010001000110000`；可信 SSH key，2026-11-26 22:57:27 boot `587b9d98-81c0-4825-9e1a-a718c9bfe741`，slot A confirmed successful=1，运行 ID `f09d25468a041e66221c4f80c6a63db9ea3fd93f6f1c1893f6c2be45164835bb`，health-check 与 logctl sync 正常。E3/board-before.log。 |
| 正式候选 | ID `c66895a6daf3871fbe7323e15eaacc003231043909e2d1cdc8390029131ba9b4`，v0.0.1 packed 1；OTA SHA `40b5a87afb0cc2c4a3a3f312e13fc1abd6fd29656ed74dab94a46ecf279214f6`。kernel FIT 12940585 bytes `c265c153f8138781de6757836fbf3a7f4137753cf1b3c09dc441072b0ac30a5b`；rootfs payload 30429184 bytes `43e5f3b70aee7af87b85ed23edb361e9695eccd61dec9d954feedaa27718a800`。F3/images/release、ota.sha256、release-files.sha256。 |
| 预发布测试 | 正式 rootfs 提取 ARM64 logctl 及 libbsl/libserver；交叉编译同一接收端，单用例独立 namespace、仅 lo 活跃、无外部路由。自然 23/23、ENOSYS 23/23。原 A21 及 A6 实际 ARM64 二进制，依赖 libbsl/libserver/libcrypto/libz 与候选逐字一致，全部上传文件 SHA 核对。E3/old-binaries.sha256、F3/old-library-match.log、board-candidate-files.log、board-candidate-{natural,no-memfd}.log。 |
| 发布 | publication `draft-cxgm2J`，2026-11-26 23:08:44+08:00；唯一 HWID/channel/device，relay 限指定板 .211/32，草稿 exact ID、非隔离、packed 1。F3/publication.log、server-draft-state.json、publication.json。 |
| 设备事务 | 安装、boot-testing 后 23:10:25 catalog `success`，running=version=1，未隔离。F3/ota-timeline.log、ota-success.json、device-transaction.json。 |
| 重启与健康 | 实际串口核对 SSH key；新的 boot `be5b3125-acb3-4dda-960b-781541ba800a`，slot B kernel/rootfs confirmed successful=1，FWCHECK1 match，8 服务 active、0 failed；9/9 实装制品与候选 rootfs SHA 相同，/usr/bin/logctl SHA `0bcce0c89b96169d645b1e641a11c5f43c11b495719d80fea90bf0cd840a355d`。F3/board-check.log、board-package-compare.log。 |
| PDM 来源 | 实际 dmesg revision `c02037c6801e8a2c87b48a541398576600ea3e6a-dirty`，与候选 PDM 记录一致，F3/board-pdm-source.log。 |

正式 v2 日志：活动 DT 与最终 FIT `bsp,bootlog-v2`、memory-region/phandle 0x3f、reg 0x9c900000/0x100000 逐项一致。collector persistent sync ok、verify-boot、archive-pending=0、RAM 两 buffer acknowledged。实际新 boot 归档 capture `77b821b9-0960-48db-8acf-6b8a57038f45`：r5-spl 418 bytes CRC 343d494d、a53-spl 455 CRC 63c77e8b、uboot 3027 CRC 296e7dd7、kernel 24705 CRC ed479b14；全部 dropped=0，前三段本地/正式归档逐字相等，kernel early 0-byte prefix 与 sealed CRC 一致。F3/board-verify.log、archive-verified.log。

| 独立专项 | 发布前候选结果（自然及 ENOSYS） |
| --- | --- |
| order-full、order-only | 已有 v2 凭据的 8273 全长，更正 order 仍 identity-changed，含同长替换与仅 order 改动两种；三块正文和完整凭据不变。 |
| order-partial | 更正 order 后同一流游标仍 4096，拒绝追加新后缀，仅 1 块原前缀保留。 |
| a6-binding | 真实旧 A6 程序先留下 4096 前缀及旧凭据；原身份匹配，候选续发 4177 字节、完整三块逐字核对，旧凭据不改写。 |
| a6-order-full、a6-order-partial | 实际旧 A6 程序分别生成完整/部分接收状态，候选首次接手已更正 order 无法还原旧域摘要归属，报警 identity-state-ambiguous，原 8273 或 4096 保持。 |
| a1-order-full、a1-order-partial | 依据独立 v1 byte fixture 的 A1 原格式，在更正 order 后拒绝；A1 匹配部分游标的 old-binding 正例仍通过。 |
| old-complete | 实际 A21 先上传 8273 字节；候选至少两轮正常无误报，无新增正文、不补写可信状态。 |
| 原专项 | 两目标切换、容量（768 条）、过期 boot 清理、内容变化、未知部分游标、损坏/不可读/越界、取消及其他健康流进展均通过。 |

邻近健康历史流每项均继续推进，原文及证明文件身份不变。板上专项是隔离模拟，不是切换正式 SOL；`bash "$F3/board-receiver.sh" "$E3" candidate` 与 installed 只为测试进程注入故障。未改变正式接收配置、原始文件或其他真实服务器。未刷 bootloader，kernel/DTB 和 bootloader 输入与上次逐字一致。

安装后 `bash "$F3/board-receiver.sh" "$E3" installed` 使用实际 /usr/bin/logctl 与实装库，全部自然 23/23、ENOSYS 23/23；每个新/旧关键断言再现，F3/board-installed-{natural,no-memfd}.log、board-installed-files.log。2026-11-26 23:12:47 最终可信 SSH 只读复核同一新 boot、slot B confirmed successful=1、完整 ID、health-check、0 failed、logctl sync ok，所有本次测试临时目录已清理（F3/board-after-installed-tests.log）。最终正式独立候选与常规 images 逐字同步，保留上一阶段原 images 于 F3/previous-default-images；F3/default-images-check.log、E3/git-verification.log。
