# AM625 EDK 子系统重构 M0–M7 板级验收归档

本卷保存 2026-11-25 各阶段的实机验收、发布事务和关闭核查。配套文档见 [EDK 归档索引](../../../edk/docs/archive/2026-11-25-subsystem-refactoring/README.md)，此前的板级记录见 [历次 EDK 验收](../edk-module-refactoring-validation.md)。

## EDK 子系统重构 M0：基线确认（2026-11-25）

- EDK `85ea958fa058b68c65593194568ba690e34a1a00`、BSP `05a047237b8f5f4b87d864cf32ca38c238113305`、
  workspace `fde9168ffdb9e2551b485d35e27b42b02d173146` 为起始源码。仅文档、接口所有者索引和
  基线验收记录变更；公开 API、生产代码、包配置及 `VERSION=0.0.1` 不变，未发布新固件。
- V1 文档检查通过；V2 42/42、V3 124/124、V4 79/79；两角色正式 Buildroot 包及 PDM
  诊断开/关 AArch64 Kbuild 成功，两个独立安装 SDK 消费者通过。详见 EDK
  [M0 基线](../../../edk/docs/archive/2026-11-25-subsystem-refactoring/edk-subsystem-m0-baseline.md)。原始证据根 `output/edk-subsystem-m0-20261125/`。
- 指定 AM625 `192.168.10.211`、MAC `1c:63:49:22:c4:f7`、HWID `1010001000110000`。
  Dropbear 主机密钥因 `/run/dropbear` 启动生成而变化，用户在板端串口查询 ED25519 指纹
  确认与网络一致；本次使用临时固定 known-hosts，不改主机原信任库。
- V6 前发现板时钟为 2026-03-04、节点 3 Redfish 证书在 2026-11-19 至 2027-02-17 有效；
  板端 CA 与 BSP SHA256 一致，主机按当前时间、CA、IP 验证证书通过。
  OTA 与时钟源 `192.168.10.246:8090` 的上一轮临时通道已关闭。复制 11-24 成功发布的
  本地 catalog 至独立 `board-management-feed/`，不改原 catalog、不发布新内容；PMCD
  loopback 18090，通过 socat 只允许 `192.168.10.211` 访问 `192.168.10.246:8090`。
  `timectl sync` 2026-11-25 17:33:45+08:00 成功，offset 1ms，RTC written。观测至 V6
  无新增 TLS peer certificate/OTA manifest download 错误；catalog 已记录当前 boot ID
  连续至少 6 次同内容 requested，未触发重启。节点 2/3 Redfish 及节点 3 PMC 样本 fresh、
  last_status=0。节点 1 `192.168.50.201` 独立连接超时（-110），不在 M0 设备基线关闭范围，
  不改变其他真实服务器状态或配置。所有测试控制用例均在隔离网络 namespace 本地夹具执行。
- **当次 V6，2026-11-25 17:35:44+08:00**：`fwctl hwid value`、`fwctl version`、
  `fwctl ota-status` 证实 B 槽已确认、版本 1、完整内容 ID 为
  `4412d622c6b0b709fe1a0a61051a5857a6fa0bc5ad2cd394ad0cb8687175044e`；启动 ID
  `fc6b77f0-9ed6-4717-b9dd-efb26b0fffc7`。`fwctl ota-check` 对历史已确认镜像的实际长度、
  kernel/rootfs SHA256 返回 `FWCHECK1 match`；rootfs 是 `/dev/fw-root` 只读 SquashFS。
  从 `output/validation/edk-app-src-include.QLDKwqoC/artifacts/release/rootfs.itb` 提取
  并校验 payload SHA256，8/8 运行制品（4 库、pdm.ko、两个遥测进程、fwctl）匹配，
  `/proc/<pid>/maps` 证实实际加载相应库；`fwctl health-check` 返回 0，pdm、CAN、遥测、星务、
  固件健康、OTA、日志、时间八个服务 active，零失败单元。实际目标 SDK 安装头和库编译
  只读探针，经本机临时目录运行并自动清理，SHA256
  `56a18426a7ce969da101dd4fe213ffd0c6772165cd53ce837434dec47d72ec3e`，加载板上库：
  BSL HWID 选 `phytium-s5000c`、Satellite v1.0（2000ms）、PDI 读取 PDM 代数 15，
  main_mcu/CAN 和 dc_power/UART 两个已绑定设备（健康 unknown，未发送设备动作）。通过。
- 证据：`board-v6-readonly.sh`、`board-v6-readonly.log`、`board-artifact-compare.log`、
  `board-probe-live.log`、`board-time-before.log`、`board-time-sync.log`、
  `board-after-sync-runtime.log`、`ota-recovery-requests.log`、`start-board-management.sh`。
  运行制品的既往成功发布记录 `output/validation/edk-app-src-include.QLDKwqoC/ota-success.json`；
  本次不把旧 success 冒称新 OTA，也不验证未安装的 bootloader。
  EDK 阶段验收提交：`c866c97693992437d7ad0f9decb48b0ae061bee5`（master）；工作区
  使用其准确 gitlink，最终工作区和远端核验 SHA 见阶段完成报告。

## EDK 子系统重构 M1：统一模块接口约束（2026-11-25）

- 起始 EDK `c866c97693992437d7ad0f9decb48b0ae061bee5`，workspace `8a528185be4de4bdce4c91c0406ccec690c8bff4`。
  文档、规则和原生 CMake/CTest 变更，无板端生产源码、配置、协议、公开 ABI 或版本变更。
  V2 45/45，最终新检查 3/3；真实管理 289、联合 392 个编译依赖及诊断关闭 PDM Kbuild，
  预期依赖命中与拒绝/缺失反例全部通过。详见 EDK [M1 验收](../../../edk/docs/archive/2026-11-25-subsystem-refactoring/edk-subsystem-m1-validation.md)。
- **当次 AM625 V6，2026-11-25 17:51:10+08:00**：指定板卡 `192.168.10.211`、MAC
  `1c:63:49:22:c4:f7`、HWID `1010001000110000`、boot ID `fc6b77f0-9ed6-4717-b9dd-efb26b0fffc7`。
  `fwctl ota-status` 完整 ID `4412d622c6b0b709fe1a0a61051a5857a6fa0bc5ad2cd394ad0cb8687175044e`，
  B 槽确认版本 1；`ota-check` 返回 `FWCHECK1 match`，`health-check` 成功，八单元 active，
  零失败单元。读取实际加载的 4 SDK 库、pdm.ko 和三个应用 SHA256，8/8 与已经核验的
  正式 rootfs 相同；只读 SDK 探针哈希匹配 M0、实际库加载路径 `/usr/lib`，项目
  `phytium-s5000c`、Satellite v1.0、PDM 代数 15、设备 2 个已绑定。真实板端未启用 hwmon，
  不将无 PDM 主机夹具冒称实体 hwmon 验收。无新 OTA 发布或其他真实服务器写操作。
- 此时 M0 恢复的管理端仍提供同一已确认内容，时钟同步、TLS/OTA 报错无复发。节点 2/3
  Redfish 和节点 3 PMC 只读新鲜采样；节点 1 的独立外部连接超时保留观察。
  实机证据 `output/edk-subsystem-m1-20261125/board-v6-final.log`、`board-probe-final.log`、
  `board-artifact-compare.log`、`board-recovery-observation.log`，当次 V6 通过。
  EDK 验收提交：`a7a78c7c26fbd6094387e5f856465afc8c500155`（master）；工作区记录准确 gitlink。

## EDK 子系统重构 M2：PDI/BSL 试点（2026-11-25）

- 起始 EDK `a7a78c7c26fbd6094387e5f856465afc8c500155`、workspace `6b8894af59d5fdf4edcb7e7a734a2dcab257c8b4`。
  PDI hwmon API/错误文档、可选模块内 fd 清理、两套安装 SDK、BSL 基础功能说明与模块依赖
  回归；V2 45/45、V3 127/127、V4 82/82、BSL 局部 2/2。正式 AM625 hwmon 关闭，
  Buildroot edk-reconfigure 及新安装 SDK 四库和头与 M0 字节相同，原有跨版本消费者通过。
  用户授权无上下文独立 AI 维护者实际修正局部实现和非普通属性回归；发现并修订指南
  的证据位置后，由同一维护者复测成功。详见 EDK [M2 验收](../../../edk/docs/archive/2026-11-25-subsystem-refactoring/edk-subsystem-m2-validation.md)。
- **当次 AM625 V6，2026-11-25 18:02:40+08:00**：板 `192.168.10.211`、MAC
  `1c:63:49:22:c4:f7`、HWID `1010001000110000`；现行 B 槽 `v0.0.1`、内容 ID
  `4412d622c6b0b709fe1a0a61051a5857a6fa0bc5ad2cd394ad0cb8687175044e`、boot ID
  `fc6b77f0-9ed6-4717-b9dd-efb26b0fffc7`，`ota-check` match、健康正常、8 服务 active、零失败。
  使用同工具链独立 PDI_HWMON=y / PDM=n ARM64 SDK，在板 tmpfs 临时目录核对 probe
  SHA256 `f1c7b0b71cf61125cc93d251abee8a00768e7d06a3402b5b6a1d49446adfb758`、
  libpdi `683c40c54f5a0b0c7262a3d88825fff03cdc25801c76ca6a081be83a0643fd05`、
  libbsl `3b257199b65fe0989ace91ada808085de5d8c6b3522d4cd1970f2f7f6dbef584`；`LD_DEBUG=libs`
  确认加载候选两库。普通文件 -12000 mC、相对/畸形/非普通 -EINVAL、溢出 -ERANGE、
  缺失 -ENOENT、失败不改输出全部通过。清理 tmpfs，18:02:45 复验健康与版本未变。
  仅隔离属性文件，非真实 hwmon 传感器；正式配置未启用该能力、正式库不变，未发布新 OTA，
  未对其他真实服务器写入或控制。证据根 `output/edk-subsystem-m2-20261125/`，文件
  `board-v6.log`、`board-hwmon-candidate.log`、`board-after-candidate.log`、`hwmon-v6-remote-command.sh`。
  EDK 验收提交：`b5310a8b016aeac7955ad6dfc793d268e1a4b900`（master）；工作区记录准确 gitlink。

## EDK 子系统重构 M3：PDM 驱动与公共诊断（2026-11-25）

- 起始 EDK `b5310a8b016aeac7955ad6dfc793d268e1a4b900`、workspace `400aa0a39193592e1cdfcf887598357c220c7b04`。
  LED、MCU 诊断关闭桩移归各驱动，公共桩只依赖 log，移除两全局 driver include 路径。
  V2 45/45、V3 127/127，两组实际 Kbuild 开/关 37/35 个对象，旧私有头反例拒绝；
  Buildroot 增量和干净构建的实际 `.cmd`/模块/SDK 一致。独立 full image、镜像专项检查和
  真实候选包往返通过。详见 [M3 验收](../../../edk/docs/archive/2026-11-25-subsystem-refactoring/edk-subsystem-m3-validation.md)。
- 本机管理端采用 systemd user transient unit `edk-am625-local-manager.service` 监督恢复，
  原独立 catalog、loopback 18090、只允许指定 AM625 的 8090 转发保持。发布前健康、身份、
  版本 B 槽、单一 active channel 核对通过。包 SHA256
  `7f966a3feaa8ff5265c89abe15e64f916568f4dacf94e855cf90e5084169559a`，
  draft `draft-xXRxnz`，发布 2026-11-25 20:23:54+08:00，`v0.0.1`、packed version 1、完整 ID
  `386c56dff2d6505b7d6b3d0ab7af084a0394b115171c6e227569c88b50bdb7f2`。板 `192.168.10.211`
  MAC `1c:63:49:22:c4:f7`、HWID `1010001000110000` 经 installing、boot-testing，
  20:25:31 服务端观测最终 success、running=1，未隔离；新 boot ID
  `6d78605c-27f3-47dc-936d-ef6e35a3c775`。证据 `ota-success.json`，不把中间状态当成功。
- **当次 V6，20:27:25+08:00**：用户在物理板串口确认新 ED25519 指纹后 SSH 固定临时密钥。
  `fwctl version` / `ota-status` 显示 A 槽确认 `386c56df`，`ota-check` 对同候选长度和哈希
  返回 `FWCHECK1 match`，`health-check` 0，八单元 active、零失败，Linux 7.0.0、PDM 已加载。
  包中 `pdm.ko` 与实机 SHA256 `e4570586f40ebb9a99dc02e42900063a0eb35b7a84f7c4b1c68f1ef0ab283409`，
  内核日志内容 ID、EDK revision 及配置匹配；八个运行制品与实际新 FIT rootfs 逐项一致。
  只读枚举 sysfs、proc `led/mcu/log_level` 与 debugfs `led_control/mcu_control`，日志级别 info；
  PDI SDK 探针代数 15、main_mcu、dc_power 已绑定，项目 `phytium-s5000c`、v1.0。
  其他真实服务器仅只读遥测，节点 2/3 Redfish、节点 3 PMC fresh/0，校时与 RTC 正常。
  没有真实设备动作或外部服务器写入；未安装引导程序，不能验证 SPL/U-Boot。
  原始证据 `output/edk-subsystem-m3-20261125/final/` 中 `board-v6.log`、`board-probe-live.log`、
  `board-artifact-compare.log`、`ota-timeline.log`、`ota-success.json`、`publication.json`、
  `source.patch`、`untracked-source.tar.gz` 与 `images/release/build-manifest.json`。
  EDK 验收提交：`9aad7b8e6896b0ded47d397110c4c040d7a6fff2`（master）；工作区记录准确 gitlink。

## EDK 子系统重构 M4：大型 SDK 内部职责治理（2026-11-25）

- 起始 EDK `9aad7b8e6896b0ded47d397110c4c040d7a6fff2`、workspace `0cb4199c6134d8d3b3b3be4536ba443c3f0ef39b`。
  transfer 共用回调窄头，节点目录访问 BMC 扩展 key 的窄查询，BSL 项目及 Satellite 维护说明。
  V2 45/45、V3 127/127、V4 82/82，collector 两态白盒/符号及同一安装消费者通过。
  正式 target/host 增量和干净包 SDK、实际依赖一致，四库 ABI 保持；完整镜像、专项及候选真实包往返通过。
  [M4 验收](../../../edk/docs/archive/2026-11-25-subsystem-refactoring/edk-subsystem-m4-validation.md)。
- 唯一设备 `192.168.10.211`、MAC `1c:63:49:22:c4:f7`、HWID `1010001000110000`；
  OTA 包 SHA256 `5d7b60df1e75c1b68e16c1467e8cd597fb6155241002c9ed71cbec6ea4f44d55`，
  draft `draft-0vUaam`，21:10:49+08:00 发布，v0.0.1、packed version 1、full ID
  `c683da78ac59336ab613a32f30b715ad591d792e68057c52226f96d81c136acc`，
  21:12:43 服务端最终 success、running=1、未隔离，新 boot ID `242e59ae-9b71-4fc9-bb3d-b3bb9f808ca0`。
- **V6 21:21:02+08:00**：用户 attach USB/IP 双串口、授权 ACL，ACM2 读取物理板 MAC/HWID/boot ID
  和 ED25519 指纹与扫描值一致。固定新密钥，B 槽 confirmed、`FWCHECK1 match`、八服务 active、零失败。
  四库/PDM/两个遥测进程/fwctl 八摘要与实际打包 rootfs 一致，libserver
  `3e8a58a7063e7883cc5fc03f90d6dc2b6d51cee8c6de749ccb8336e929d5a1a7`。
  AArch64 安装 SDK 探针加载板端 libserver，collector start=-95，节点 3 Redfish power=on/status=0、
  PMC cpu=443 bp/memory=370 bp/status=0；其他真实服务器仅查询，节点 2/3 Redfish、节点 3 PMC
  正常，节点 1 为既有外部连接超时。校时/RTC 正常。未写入或控制任何其他服务器；
  未安装引导程序，不验证 SPL/U-Boot。
  证据根 `output/edk-subsystem-m4-20261125/`：`serial-board-identity.log`、`board-v6.log`、
  `board-artifact-compare.log`、`board-server-probe-live.log`、`ota-success.json`、`ota-timeline.log`。
  EDK 验收提交：`a6fb8efaa2c9216fc6aa477ac22eb2d0abced6dd`（master）；工作区记录准确 gitlink。

## EDK 子系统重构 M5：应用模块与共享契约（2026-11-25）

- 起始 EDK `a6fb8efaa2c9216fc6aa477ac22eb2d0abced6dd`，workspace `6ff91c570c4be14194635bcadb30f5b146b90b11`。
  PMC 采样只依赖 directory，请求路由保留 context；HTTP 接收只读取 common，两个旧宽头例外关闭。
  首次接手/补正复走由独立 fresh-context AI 实改及测试；V2 45/45、V3 127/127、V4 82/82，
  四组实际增量依赖、正式 host 增量/干净 SDK 与安装 pmcd 一致，PMC 固定向量和两端进程检查通过。
  正式 AM625 未选 CONFIG_PMCD，四库与 M4 完全一致，本阶段主机代码不发布新 OTA。
  [M5 验收](../../../edk/docs/archive/2026-11-25-subsystem-refactoring/edk-subsystem-m5-validation.md)。
- **当次 V6，21:36:16–21:36:35+08:00**：ACM2 串口核对板 MAC/HWID/boot/key，固定 SSH，
  板 B 槽 M4 full ID `c683da78ac59336ab613a32f30b715ad591d792e68057c52226f96d81c136acc`，
  FWCHECK1 match，八服务 active、零失败，八运行制品与 M4 打包摘要一致。
  logctl sync ok、synced=observed=390、archive pending 0、persistent；timectl synchronized、RTC written。
  用 AM625 交叉工具链直接编译最终接收/BSL file_io 候选，SHA256
  `8ac00b63fe3b118a0d374005f4a5b76ca579cd240df1654118b116338eecd270`，
  板上 /tmp tmpfs、Unix socketpair（无外部网络连接），限额 -EFBIG、取消 -ECANCELED、零写入、
  成功完整接收 6 字节与 progress、清理。非板上正式 pmcd。
  只读节点 3 BMC Redfish power=on、PMC utilization cpu=432 bp memory=371 bp 状态均 0，
  节点 2/3 正常、节点 1 仍既有外部连接超时。不向其他服务器写入/控制。
  证据 `output/edk-subsystem-m5-20261125/`：serial-board-identity.log、board-v6.log、
  board-artifact-compare.log、board-http-probe-live.log、board-pmc-probe-live.log、final/。
  EDK 验收提交：`e77465985e273f6206d2a9b0d86fcfe0f9f59551`（master）；工作区记录准确 gitlink。

## EDK 子系统重构 M6：项目装配、裁剪与交付（2026-11-25）

- 起始 EDK `e77465985e273f6206d2a9b0d86fcfe0f9f59551`、BSP `05a047237b8f5f4b87d864cf32ca38c238113305`、
  workspace `b4079f539dc800b339ffb8653bc327aeaa039a69`。正式项目+执行器缺两 BMC 后端早期配置错误，
  BSP package pre-configure hook 使用同一 Kconfig normalizer；项目 A/B 与双表安装 SDK；
  本机和隔离真实 Buildroot staging 的 hwmon 开→关 ownership 清理与 clean off 对照通过。
  V2 45/45、V3 127/127、V4 82/82，正式 target/host 配置与增量/干净 SDK 一致，
  实际完整镜像、initramfs libbsl/firmware loader、候选包往返通过。
  [M6 验收](../../../edk/docs/archive/2026-11-25-subsystem-refactoring/edk-subsystem-m6-validation.md)。
- OTA 仅指定板 `192.168.10.211`、MAC `1c:63:49:22:c4:f7`、HWID `1010001000110000`。
  包 SHA256 `7afaa244e26209ee081d775405e4dc03fcfd131254d2c192abf57a6674cb4197`，
  draft `draft-aqdPxH`，21:57:13+08:00 发布，v0.0.1、packed version 1、
  full ID `05b8646146cb42143df1cd1d1b4f119f8956a856698b3f0b41c4af2dbdc5e61e`，
  21:59:01 服务端最终 success、running=1、无 quarantine，新 boot
  `ddc2c27a-8fd0-47f7-95b2-340bfac67bac`。
- **当次 V6 21:59:34+08:00**：ACM2 串口独立核对板、事务 boot、新 ED25519，与扫描一致；
  SSH 固定密钥，A 槽 confirmed、FWCHECK1 match、八服务 active、零失败、八个制品与新 FIT rootfs
  全摘要一致。板端新安装 SDK probe 实际加载 libbsl，HWID 命中 phytium-s5000c 4 点，
  未登记合法 HWID -ENODEV/NULL；基线探针 v1.0 2000ms、PDM gen15、main_mcu/dc_power 只读绑定。
  节点 2/3 Redfish、节点 3 PMC 正常、节点 1 既有外部超时；校时同步。未写入/控制其他真实服务器，
  未部署新产品、新外设或引导程序。证据 `output/edk-subsystem-m6-20261125/` 中
  ota-success.json、serial-board-key.log、board-v6.log、board-artifact-compare.log、
  board-project-probe-live.log、board-baseline-probe-live.log。
  BSP 验收提交：`e9cd0ad22ebe737acf349584085e88ca40777785`；EDK 验收提交：`d392a20d845aa01d4b71a0b7d66b9cefd58d828e`（master）；工作区记录准确 gitlink。

## EDK 子系统重构 M7：最终回归及维护交接（2026-11-25）

- 起始 EDK `d392a20d845aa01d4b71a0b7d66b9cefd58d828e`、BSP
  `e9cd0ad22ebe737acf349584085e88ca40777785`、workspace
  `e5a0dbf1e76f9fe2d08cd17c1afe0f5e77fbb926`。回查 M0–M6 各次实机日志、远端提交和准确 gitlink。
  最终 CI host 45/45、management 127/127、telemetry 82/82（254/254），900 用户态实际对象、Kbuild
  diag on/off 37/35；三临时例外均已关闭、现有历史格式基线 832 条无逐文件增加。
  正式 target/host 配置和 M0 ABI 保持，增量/干净 SDK、旧消费者加载新 SDK、
  正式镜像/loader/新 OTA 包往返通过；两次 AI 首次接手实际修改/测试及最终指南复走通过。
  [M7 总体验收及各阶段 SHA](../../../edk/docs/archive/2026-11-25-subsystem-refactoring/edk-subsystem-m7-validation.md)。
- 正式配置未变，重新生成的 PDM 构建标识形成新固件内容，按全量正式镜像验证/OTA 流程。
  只向指定 AM625 192.168.10.211、MAC 1c:63:49:22:c4:f7、HWID 1010001000110000 发布；
  draft `draft-sYt2Hs`，22:21:39+08:00 发布 v0.0.1 / packed 1，
  full ID `2870bc37f4024106b3782b57293bc36fce0d897b56c35173e924d61195496982`，
  包 SHA256 `48f54ef3e1790254e3c07b5af424a7448a0f3ec248ddca0bc1e1e430083af868`。
  重启健康确认后 22:23:24+08:00 最终 success（22:23:26 轮询确认）、running=1、无 quarantine，
  新 boot `3a2bf0c8-60a6-4fa0-bc8f-b566f9813761`。
- **当次 V6 22:25:11–22:26:04+08:00**：USB/IP ACM2 串口核对身份、boot、ED25519
  `SHA256:738GcHE6jEBhHAEbbnOgGCYZ50AjS3jnTKeIO6n7JaY` 与 SSH scan 一致，严格固定密钥；
  B 槽 confirmed、FWCHECK1 match、8 服务 active、0 failed、4 libs+PDM KO+两 daemon+fwctl
  的 8 全摘要与打包镜像相符，候选夹具后再次相同。选表 4 点、合法未登记 HWID -ENODEV/NULL；
  M0 原 board probe v1.0/2000ms、PDM gen15、main_mcu/dc_power 被动枚举；
  node3 Redfish power on、PMC CPU/memory status0，collector off -95；node2/3 Redfish 正常、
  node1 既有外部 -110。校时 synchronized、RTC written，log sync ok。
  AArch64 HTTP receiver socketpair 正/反例及隔离 hwmon SDK /tmp fixture -12000mC、错误保持输出
  都通过且清理，未称正式配置启用 hwmon 或使用真实 hwmon 外设。未写入/控制其他真实服务器，
  未部署第二产品/新外设/bootloader。
  证据 `output/edk-subsystem-m7-20261125/`：ci.log、prior-stage-remote-audit.log、
  prior-v6-audit.log、ota-success.json、serial-board-key-retry.log、board-v6.sh/log、
  board-probes.sh、board-artifact-compare.log、board-*-live.log、git-verification.log。
  EDK 验收提交：`489673305d6c862870f7c8fe4c309755d84def24`；BSP 沿用 `e9cd0ad22ebe737acf349584085e88ca40777785`，均已核对 origin/master；工作区提交准确 gitlink。

## EDK 子系统整改结果与最终关闭确认（2026-11-25）

本节是 M0–M7 已关闭后的交接索引与复核记录，不开启新实施阶段，也不变更
已验收固件、子仓版本或产品配置。按 [整改计划](../../../edk/docs/archive/2026-11-25-subsystem-refactoring/edk-subsystem-refactoring-plan.md)
第 6、9 节，八个阶段均在完成适用 V1–V5、当次指定 AM625 V6 和适用的正式 OTA 验收后，
依次提交、推送并确认远端可达；正式固件未变化的阶段使用当时已确认的运行制品及隔离候选。

### 整改目标落实情况

| 阶段 | 整改结果 | 当次 AM625 V6（北京时间） | 详细记录 |
| --- | --- | --- | --- |
| M0 | 建立实际运行架构、正式 target/host 安装 SDK、公开接口与 ABI 基线 | 17:35:44，通过 | [M0](../../../edk/docs/archive/2026-11-25-subsystem-refactoring/edk-subsystem-m0-baseline.md) |
| M1 | 建立模块接口所有者与实际编译依赖检查；正反例可验证，临时例外明确归属 | 17:51:10，通过 | [M1](../../../edk/docs/archive/2026-11-25-subsystem-refactoring/edk-subsystem-m1-validation.md) |
| M2 | hwmon 通过模块 API 与独立 SDK 使用；真实首次接手 AI 维护者完成修改、局部测试和补正，正式关闭配置保持兼容 | 18:02:40，通过 | [M2](../../../edk/docs/archive/2026-11-25-subsystem-refactoring/edk-subsystem-m2-validation.md) |
| M3 | PDM 公共诊断与 LED/MCU 私有实现隔离，真实 Kbuild 开关两态通过并删除相应临时例外 | 20:27:25，通过 | [M3](../../../edk/docs/archive/2026-11-25-subsystem-refactoring/edk-subsystem-m3-validation.md) |
| M4 | BSL 共用机制、Server/BMC 业务接口及 collector 关闭兼容界定；保留已有公共库及接口 | 21:21:02，通过 | [M4](../../../edk/docs/archive/2026-11-25-subsystem-refactoring/edk-subsystem-m4-validation.md) |
| M5 | HTTP 接收、下载、断点、采样及路由责任分离；真实首次接手 AI 维护者与局部增量回归通过，关闭两条 HTTP 临时例外 | 21:36:16–35，通过 | [M5](../../../edk/docs/archive/2026-11-25-subsystem-refactoring/edk-subsystem-m5-validation.md)、[维护练习](../../../edk/docs/archive/2026-11-25-subsystem-refactoring/edk-subsystem-m5-maintainer.md) |
| M6 | 独立项目表装配、功能裁剪与配置冲突提前拒绝；A/B 与双 HWID SDK、干净/复用安装及真实 Buildroot staging 验证 | 21:59:34，通过 | [M6](../../../edk/docs/archive/2026-11-25-subsystem-refactoring/edk-subsystem-m6-validation.md) |
| M7 | 最终依赖回归、架构图、接口需求手册、新人指南、复用 CI 与交接完成；三条 M1 临时例外全部关闭 | 22:25:11–22:26:04，通过 | [M7](../../../edk/docs/archive/2026-11-25-subsystem-refactoring/edk-subsystem-m7-validation.md) |

最终 host 45/45、management 127/127、telemetry 82/82，共 **254/254**；
900 个真实用户态对象及 PDM 37/35 个开、关诊断 Kbuild 对象的依赖检查通过。
目标与 host 正式有效配置、公开 SONAME/NEEDED/导出符号与 M0 对应基线兼容，
跨版本旧消费者及最终安装 SDK 运行通过；正式镜像、initramfs loader 和真实 OTA 包往返通过。
两次独立首次接手 AI 分别为 `/root/hwmon_new_maintainer` 与
`/root/http_receive_new_maintainer`，按授权无父轮开发上下文接手，实际修改和测试；
最终指南复走通过。不将 AI 练习表述为人类维护者验收。

后续开发以 [模块契约](../../../edk/docs/module-contracts.md) 的接口所有者和直接依赖为边界，
按 [新人维护指南](../../../edk/docs/maintainer-guide.md) 执行局部测试，
通过 [项目装配指南](../../../edk/docs/project-assembly.md) 扩展项目表或裁剪功能。
[架构图](../../../edk/docs/软件架构设计.drawio)、[架构说明](../../../edk/docs/architecture.md)、
[接口与需求手册](../../../edk/docs/EDK_接口与需求手册.xlsx) 已同步。

### 原板端报错的整改与复验

| 原现象 | 核实原因及处理 | 验收结论 |
| --- | --- | --- |
| Redfish TLS peer certificate verification failed | 板时钟停在 2026-03-04，早于节点 3 证书有效期；板端 CA 与 BSP 一致，按当前时间核验证书成功；恢复时钟源并执行 `timectl sync`，保持证书校验 | 节点 2/3 Redfish 样本状态 0；未绕过 TLS |
| OTA Download failed (network)、Cannot fetch a valid firmware manifest | 原本机临时管理通道关闭；恢复独立本机 PMCD catalog 与仅允许指定板访问的转发，未改历史 catalog | M3/M4/M6/M7 正式 OTA 均收到指定设备最终 success，且与各次运行版本和制品一致 |
| 板上缺少 ssh-keygen，重启后 Dropbear key 变化 | USB/IP 串口 ACM2 使用板端 `dropbearkey -y` 独立核对 hostname、MAC、HWID、新 boot 和 ED25519 指纹，再与主机 keyscan 比对 | 使用严格 SSH 固定密钥，未关闭主机密钥校验 |

最终板运行 v0.0.1、B 槽、完整身份
`2870bc37f4024106b3782b57293bc36fce0d897b56c35173e924d61195496982`，
22:23:24 上报 success，`FWCHECK1 match`，八服务 active、零失败、8/8 运行制品与镜像匹配。
22:30:51 使用固定 SSH 密钥查询 `fwctl version`、`fwctl ota-status`、`timectl status`，
检查当次启动 `journalctl -b -u fwctld.service -u ptelemetryd.service --no-pager`，
未匹配上述三条原报错。证据
`output/edk-subsystem-m7-20261125/board-final-error-check.log`。
22:34:08 为本补充文档再次使用同一严格固定密钥执行 M7 `board-v6.sh` 的只读检查，
身份、boot、B 槽、完整性、8 个制品摘要、8 个服务、时钟与日志同步仍通过；
证据 `output/edk-subsystem-m7-20261125/board-documentation-followup.log`，
未重启、更新、安装任何制品或写入其他服务器。

### 各阶段提交与远端核验

| 阶段 | EDK SHA | Workspace SHA |
| --- | --- | --- |
| M0 | `c866c97693992437d7ad0f9decb48b0ae061bee5` | `8a528185be4de4bdce4c91c0406ccec690c8bff4` |
| M1 | `a7a78c7c26fbd6094387e5f856465afc8c500155` | `6b8894af59d5fdf4edcb7e7a734a2dcab257c8b4` |
| M2 | `b5310a8b016aeac7955ad6dfc793d268e1a4b900` | `400aa0a39193592e1cdfcf887598357c220c7b04` |
| M3 | `9aad7b8e6896b0ded47d397110c4c040d7a6fff2` | `0cb4199c6134d8d3b3b3be4536ba443c3f0ef39b` |
| M4 | `a6fb8efaa2c9216fc6aa477ac22eb2d0abced6dd` | `6ff91c570c4be14194635bcadb30f5b146b90b11` |
| M5 | `e77465985e273f6206d2a9b0d86fcfe0f9f59551` | `b4079f539dc800b339ffb8653bc327aeaa039a69` |
| M6 | `d392a20d845aa01d4b71a0b7d66b9cefd58d828e` | `e5a0dbf1e76f9fe2d08cd17c1afe0f5e77fbb926` |
| M7 | `489673305d6c862870f7c8fe4c309755d84def24` | `d214bccc15597003da9e924fe838f8fdc4353c5f` |

BSP M0–M5 为 `05a047237b8f5f4b87d864cf32ca38c238113305`，
M6–M7 为 `e9cd0ad22ebe737acf349584085e88ca40777785`。
M7 关闭时 `git ls-remote --heads origin master` 核对三个仓库的远端提交与本地一致，
`git ls-tree HEAD edk bsp-base-external` 核对准确 gitlinks，
`git merge-base --is-ancestor` 核对全部历史阶段提交可达；工作树干净，
证据 `output/edk-subsystem-m7-20261125/git-verification.log`。
上述 SHA 为各阶段关闭提交，不随本次纯文档追记改变。

### 范围与保留事项

- 节点 1（192.168.50.201）BMC 仍有既有外部连接超时 -110；节点 2/3 Redfish 和节点 3
  PMC 可用。其他真实服务器整个过程中仅做只读查询，状态变更测试只使用隔离夹具。
- 已验证运行时校时有效，RTC 状态 written；M7 重启后仍发生较大系统时间偏差并由
  timectld 自动校正。未独立验证断电后 RTC 持续精确走时，不将当前同步等同于 RTC 硬件修复。
- 严格全树格式检查仍有既有 832 条/90 文件诊断；CI 按文件数量检查无增加，
  不代表全部历史格式债务已清除。
- 架构图通过 XML 和本机几何预览，未使用缺失的 diagrams.net 原生渲染器；
  XLSX 通过 ZIP/XML 与 LibreOffice 实际加载检查。
- 第二产品和新外设未在真实设备部署。正式 PDI_HWMON 为关闭，相关板上结果来自隔离属性夹具；
  本次正式 kernel/rootfs OTA 没有安装或验证新 SPL/U-Boot。后续具体产品/硬件需求独立实施。

**结论：M0–M7 已全部关闭，整改目标、适用的自动化测试、各阶段实板 V6、正式固件发布成功和远端提交均有实际验收证据。**
