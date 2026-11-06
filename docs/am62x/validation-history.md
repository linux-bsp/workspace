# 历史功能验收记录

以下保留原发布身份、验证结果和证据位置，属于历史记录。原文中的目录、
命令和阶段限制反映当时状态；当前构建与操作以仓库 README 和现行指南为准。


## 记录索引

- [boot-stage-firmware-validation](#boot-stage-firmware-validation)
- [bootlog-double-buffer-validation](#bootlog-double-buffer-validation)
- [hwid-environment-validation](#hwid-environment-validation)
- [hwid-only-ota-validation](#hwid-only-ota-validation)
- [m1-1-data-mount-validation](#m1-1-data-mount-validation)
- [m1-2a-data-health-validation](#m1-2a-data-health-validation)
- [m1-2b-sync-validation](#m1-2b-sync-validation)
- [m1-2c-log-stop-validation](#m1-2c-log-stop-validation)
- [ota-failure-evidence-validation](#ota-failure-evidence-validation)
- [ota-incident-attachments-validation](#ota-incident-attachments-validation)
- [sol-record-deletion-validation](#sol-record-deletion-validation)
- [time-source-web-validation](#time-source-web-validation)
- [time-sync-and-archive-names-validation](#time-sync-and-archive-names-validation)
- [fwctl-module-consolidation](#fwctl-module-consolidation)
- [edk-device-manager-merge](#edk-device-manager-merge)
- [systemd-migration](#systemd-migration)


<a id="boot-stage-firmware-validation"></a>

## AM625 启动阶段固件信息验证

原记录：`docs/am62x/boot-stage-firmware-validation.md`。


### 日志位置与校验责任

- R5 SPL 和 A53 SPL 打印被选择的 U-Boot A/B 槽、版本、固件 ID。此阶段确认启动元数据，不宣称已校验 U-Boot 镜像负载。
- U-Boot 校验 kernel FIT 后打印槽位、版本、固件 ID 和 FIT SHA256；同时从已校验 FIT 配置读取 rootfs 槽位、版本和预期 SHA256。
- Linux 内核打印继承自 U-Boot 的 kernel FIT 校验状态，以及 rootfs 的目标槽位和预期 payload SHA256。
- initramfs 读取完整 rootfs 分区并校验 SHA256，建立 dm-verity 映射后打印实际校验成功的槽位、版本和 payload SHA256。该结果在 switch_root 前输出。

日志格式统一为 `[fwctl] [INFO]`，人读哈希显示前 8 位；实际校验使用完整 SHA256。

### 实机验证

2026-11-03，在 AM62x 板上通过 OTA 发布 32 验证 `v0.0.1 / 425cba2e`。串口确认：SPL 选择 U-Boot 槽 A；U-Boot 校验 kernel FIT 并读取 rootfs 信息，kernel 与 rootfs 均使用 B 槽；initramfs 的 rootfs SHA256 校验通过并启用 dm-verity。rootfs 校验行完整，未被 watchdog 输出拆分。设备健康检查通过，服务端结果为 `success`。`fwctl status` 显示 deployment 1 已确认，`logctl verify-boot` 显示 R5 SPL、A53 SPL 和 U-Boot 三段日志均已验证。

发布 30 曾因 initramfs 调用 `pthread_cancel`，而精简目标系统缺少 `libgcc_s.so.1`，导致 PID 1 退出。设备 A/B 尝试耗尽后自动回滚，服务端记录 `rolled-back`。修正版使用原子停止标志并等待喂狗线程正常退出，发布 32 在实机验证成功。

### 构建产物与记录

固件标签保持 `v0.0.1`，完整固件 ID 为 `425cba2e7af145352eb452364b7d83485fc6e4a3d660545a5472c63c032d5ea4`。构建日志、OTA 包、构建身份和串口采集保存在忽略目录 `output/ota-validation/0.0.1-stage-logs-safe-handoff/`。


<a id="bootlog-double-buffer-validation"></a>

## AM625 双缓冲启动日志验收

原记录：`docs/am62x/bootlog-double-buffer-validation.md`。


日期：2026-11-03。按新增需求，在现有接力机制上扩容并保留两次启动；正常启动通过健康检查后，上报保留记录，服务器持久确认后清空，下次从第一组开始。

### 版本与实机状态

- 固件标签 `v0.0.1`，内容 ID `39635b333ea4cce5ecfd6f23272f3a3b918cf6a53f2cd3c2ee4c57224d62c5e7`，发布 #43。
- 设备 `1c-63-49-22-c4-f7`，AM625 SD 卡。kernel/rootfs A、B 槽均已安装这一固件并通过健康确认；最终启动 `daf481e1-d903-4987-a840-9d9fc3163ea2`，deployment 1、kernel/rootfs B，OTA server 为 success。
- 引导程序独立升级：先 B 后 A，各次启动均健康确认；tiboot3、tispl、U-Boot 两槽逐项读回，与实际部署包负载逐字节一致。ROM 执行的首级是 tiboot3_a；不宣称执行验证了 tiboot3_b。
- kernel/rootfs 普通 OTA 没有解除远程 bootloader 策略。引导更新使用临时本机维护配置和仅含 bootloader 的受控清单；正式配置仍禁用远程更新。U-Boot 网口协商超时未在本轮修复，维护下载通过 Linux 完成。

### 实现

保留 DDR 从 64 KiB 扩大至 1 MiB，紧邻但不覆盖 ramoops。两组各 512 KiB，每组为 R5 SPL 32 KiB、A53 SPL 32 KiB、U-Boot 64 KiB、kernel 320 KiB，另留头部和间隙。R5 轮换组，后续阶段追加当前组；kernel printk 注册后回放缓冲并记录至本次健康确认。

每段验证长度与 CRC，并保存上一份已提交前缀以恢复被复位打断的追加。满缓存记录 dropped；损坏、缺失和恢复前缀分别标识。设备健康确认后冻结快照，上传进程按偏移重试；服务器独立 SQLite 归档检查全部有限清单并提交，设备才核对两个 capture ID、先使头部失效再清空两组。实时 SOL 轮转不会删除此归档，ACK 丢失可跨恢复启动重试。

清除的是已确认的 DDR 启动缓存；服务器历史和现有普通本地日志保留。SOL 启动下拉框可以选择正常启动和上次未确认启动归档，正文、阶段筛选和导出继续使用原始串口格式。接口与边界见 [组件说明](../../edk/docs/device-manager/startup-buffers.md)。

### 实机验证

1. 发布 #43 后设备下载安装、重启和健康确认成功，服务器收到正常启动四段数据，其中 kernel 20515 字节。首次迁移保留的旧内核时期记录有损坏段，明确标记并排除损坏内容，没有当作完整日志。
2. 在未保存环境变量的 U-Boot 会话中，为单次启动添加 `rdinit=/bin/sh`；尚未进入正式 rootfs、尚未执行健康检查时，通过 sysrq 触发一次受控 kernel panic。未修改或发布异常固件。
3. 异常启动使用第一组，capture `df6e92a1-61fa-44b6-86e0-bab2799ce871`；自动复位后的正常启动使用第二组，capture `ed0abacf-e728-47d6-a601-3929d05b0295`。服务器分别保留 R5 SPL、A53 SPL、U-Boot、kernel；异常 kernel 20521 字节，包含 panic 原因和调用栈，正常 kernel 20515 字节，不含该 panic。八段均 CRC 正常、dropped=0。
4. 恢复启动 `be1c4a06-a650-4c18-9272-0045c53fef5d` 健康确认后，两组归档成功，设备为 `startup-state=acknowledged`、`next-buffer=1`，`banks` 为空。
5. 再次正常重启，capture `6bdafb1e-b72b-4b8d-a4f9-9096c7db749e` 确认仅 bank0、generation=1、`active-buffer=1`；归档完成后再次清空。旧异常和正常归档仍在服务器。
6. 使用已有 `fwctld --once --auto-install --force` 将同一版本、同一内容 ID 写入备用 kernel/rootfs B 槽，通过重启健康确认及服务器 success。两槽均覆盖新版机制；initramfs 验证备用 rootfs 完整，无需修复。

本轮没有格式化 data，没有用手动 mark-good 绕过健康检查；最终 data 为 persistent、日志 sync-state=ok。

### 主机检查与工件

U-Boot 实际生产代码 ABI/轮换/损坏/满缓存/前缀恢复测试 4 项、归档 HTTP/上传器测试 8 项、健康门槛测试 4 项、SOL 回归 10 项、日志生命周期 9 项、事故附件回归 9 项、正文解码 10 项通过。隔离浏览器验证两组选择、正文及导出一致、手机无横向溢出；真实 FIT 下载字节比较通过。

工件位于 `output/ota-validation/0.0.1-bootlog-v2/`，包含版本身份、源码基线与补丁、新文件快照、OTA 结果、八段原始归档及其 SHA256、串口、测试记录和引导程序读回结果。构建为 `output/am625-bootlog-v2/`，维护备份在 `output/bootlog-v2-maintenance/`；生成物不提交 Git。

### 尚未覆盖的边界

仅证明本次软件重启和受控 panic 复位能保留 DDR。真正断电、其他复位类型、内核 console 注册前的致命故障不在本次保证范围；ROM/TIFS/ATF 输出仍未接入。两组只能覆盖最多两次尚未归档启动，连续更多失败会覆盖最旧记录。SPL/U-Boot 阶段卡死复位、真实掉电中断追加/清空仍需专门实机测试，不能以主机故障夹具替代。

### 真实 OTA 故障包补充

2026-11-04 通过发布 46 的隔离故障包验证了 OTA 后 PID 1 panic、三次启动失败、自动回退、两组日志补传及异常固件隔离；B 槽已用正常发布 47 修复。实际日志与尚未打通的 OTA 附件关联见 [OTA 启动失败日志验收](ota-boot-failure-log-validation.md)。


<a id="hwid-environment-validation"></a>

## AM625 HWID 环境存储与验证

原记录：`docs/am62x/hwid-environment-validation.md`。


### 方案与当前身份

HWID 直接保存为 U-Boot 的 `hwid` 环境变量，复用现有环境的 CRC、冗余副本和存储驱动。编码规则见 [HWID 编码规范](hwid-specification.md)，工具说明见 [Device Manager HWID 文档](../../edk/docs/device-manager/hwid.md)。

当前板卡：`1-01-0001-0001-10-000`，规范文本 `1010001000110000`，PCB V1.0。

| 介质 | 存储方式 | 本次验证范围 |
| --- | --- | --- |
| SD | U-Boot MMC 环境，Linux 块设备 | AM625 实机读写、重启、启动传递及固件匹配 |
| eMMC | MMC user area 或明确配置的 boot0/boot1 | 真实 libubootenv 的文件模拟测试；未接实物 |
| SPI NOR | U-Boot SPI Flash 环境，Linux MTD 字符设备 | U-Boot/SPL 交叉编译、真实 libubootenv 配合 NOR 擦写与中断模拟；未接实物 |
| NAND | 暂不支持 | Linux HWID 接口明确拒绝 NAND MTD |

跨介质保持 HWID 格式和命令一致。环境设备、偏移、大小及冗余参数由各板 BSP 配置，并非自动扫描任意介质。

### 当前 SD 环境位置

两份环境分别位于 `/dev/mmcblk1` 的 `0x600000`、`0x620000`，每份 `0x10000` 字节。R5 SPL、A53 SPL、完整 U-Boot 和 `/etc/fw_env.config` 使用一致的大小与位置。

U-Boot 查看和修改：

```text
printenv hwid
setenv hwid 1010001000110000
saveenv
```

Linux 查看和修改：

```sh
fwctl hwid show
fwctl hwid value
fwctl hwid set 1010001000110000
```

Linux 修改仅更新该变量，并读回检查；同值设置不重复写盘。修改后重启，使 SPL、U-Boot、设备树和 Linux 使用统一身份。普通组件 OTA 不覆盖环境。恢复默认环境或重新烧写环境后，应核对 HWID 与实物 PCB。

### 启动和更新行为

- SPL 在存储控制器可用后，通过原生环境后端加载身份。
- 完整 U-Boot 打印身份，并写入传给 Linux 的 `/chosen/dm,hwid`。
- initramfs 与 fwctl 使用 libubootenv 读取相同环境；两份 CRC 都无效时不自动重建环境。
- AM625 的 release、bootloader、kernel 和 rootfs FIT 声明完整 `fw,hwids` 列表。U-Boot 与 Linux 更新、恢复校验要求精确匹配，该阶段保留了原有兼容性字段；后续已在 HWID 独立发布阶段移除，当前接口以 [Device Manager HWID 文档](../../edk/docs/device-manager/hwid.md) 为准。

固件内容 ID、软件 tag、设备 HWID 和实物序列号分别管理；HWID 不随软件升级改变。

### 2026-11-04 验证结果

自动化验证通过：12 项环境测试、5 项固件引擎测试、6 种真实 FIT 身份匹配场景，以及实际 OTA 包发布、下载和逐字节比较。环境测试包含副本回退、计数回绕、双 CRC 损坏不重建、其他变量保留、NOR 擦除/中断和 NAND 拒绝。

实机验证通过：

1. 保存 HWID 后读回，与修改前的其他 77 个环境变量逐项比较，均保留；两份环境 CRC 有效。
2. 将项目字段临时改为 `0002`，读回成功，再恢复本板 HWID；标准 `fw_setenv` 与 fwctl 访问同一环境。
3. A53 SPL、U-Boot、initramfs、rootfs 读到 `1010001000110000`；Linux 设备树属性一致。
4. U-Boot 从 SD 读取实际 kernel FIT：正确 HWID 校验通过；仅在 RAM 将 HWID 改为另一项目后返回 `-EPERM`；恢复后再次通过。该负向测试不保存错误身份、不写固件分区。
5. 最终 B 槽启动，`pending: none`，deployment 1 为 `confirmed successful=1`，SOL 正常连接。

OTA 发布记录为 48，tag 保持 `v0.0.1`，内容 ID：

```text
1824c44826038d3a6b4e66862b5d287f49df8da0cdb7206593b9fb74f5a9e939
```

设备 `1c-63-49-22-c4-f7` 已向服务端报告该发布 `success`。最终维护验证启动 ID：`7a2c1839-33b3-4047-a308-d4d5974f6dd0`。

### 镜像与审计材料

生成文件保存在工作区 `output/ota-validation/0.0.1-hwid/`，不进入 Git：

- `package.tar.gz`：已发布且通过升级的 kernel/rootfs OTA 包。
- `factory-images/sdcard.img`：包含新版 R5/A53 SPL、U-Boot、双环境及双槽系统的完整工厂镜像；环境带本板 HWID。
- `final-bootloader/`：用于 B 槽实机验证的维护包；内核/rootfs 内容 ID 与已发布包相同。
- `final-complete-boot.log`、`uboot-hwid-match-tests.log`：最终启动和 U-Boot 正反匹配日志。
- `final-device-state.log`、`final-server-state.json`、`factory-image-validation.json`：本地健康、服务端成功及工厂镜像区域核对证据。

本次保留 ROM 使用的原始 R5 SPL A 槽作为回退入口。新版 R5 已编译并包含在工厂镜像和维护包中，但 ROM 未执行该新版 R5；实机执行验证覆盖 A53 SPL 与完整 U-Boot B 槽。完整工厂镜像已逐区核对，未整卡烧录。eMMC、SPI NOR 的物理写入、掉电行为仍需对应实物验证。


<a id="hwid-only-ota-validation"></a>

## AM625 按 HWID 发布 OTA 验证

原记录：`docs/am62x/hwid-only-ota-validation.md`。


验证日期：2026-11-04。设备：`192.168.10.211`，MAC `1c:63:49:22:c4:f7`。

本记录保留 HWID 独立发布阶段的验收结果。当前发布流程已改为自动使用固件包内声明的全部 HWID，见 [固件 HWID 自动发布](firmware-hwid-publication.md)。

### 当前身份与显示规则

设备 HWID 为 `1010001000110000`，分段显示 `1-01-0001-0001-10-000`：编码版本 1、产品线 01、项目 0001、产品型号 0001、PCB V1.0、保留字段 000。

OTA API、设备上报、运行配置和新生成的 FIT 已移除独立的 `product`、`layout` 身份字段。页面产品列、固件详情和设备详情只从 HWID 解析产品信息；不维护第二套产品身份。物理分区偏移和容量仍由 BSP 指定。

规范见 [HWID 使用说明](../../edk/docs/device-manager/hwid.md)。普通 OTA 不修改环境变量中的 HWID。

### 发布与校验

- 每个完整 HWID 同时只有一个当前发布版本，各 HWID 通道相互独立。
- 上传包从 FIT 读取适用 HWID；release、kernel、rootfs 必须共同支持全部声明值。
- 发布必须选择声明中的目标 HWID。查询、下载、结果上报及恢复均绑定该身份；其他 HWID 的请求被拒绝。
- 设备仍使用完整软件版本和 SHA256 内容 ID 判断是否需要升级；日志显示哈希前八位。
- 同一异常内容被隔离后，停止所有受影响通道；各通道仅回退到自身已健康确认的兼容固件。

```sh
ota-cli --server http://127.0.0.1:8090 upload firmware.tar.gz
ota-cli --server http://127.0.0.1:8090 publish draft-XXXXXX --hwid 1010001000110000
```

### 本次实机结果

发布固件为 `v0.0.1 / f9008efd`，完整内容 ID：

```text
f9008efd422a19afe825a748e961cbfe7966aefe405c92679fcc6caed49b261c
```

服务端审计发布编号为 49，仅用于追踪，不作为设备固件版本。

1. 先更新备用 B 槽 A53 SPL/U-Boot，保留原 R5 主启动副本；新 U-Boot 成功启动原健康系统。
2. 通过临时维护程序切换 OTA 协议后，按 HWID 发布新固件；设备自动下载、校验、安装 A 槽 kernel/rootfs、重启并上报 `success`。
3. 对相同版本和内容 ID 发起一次主动重装，更新 B 槽 kernel/rootfs，再次重启并上报 `success`。
4. 移除设备临时迁移程序及配置，再次正常启动。A/B 两个 deployment 均为 `confirmed`、`successful=1`，无 pending；正常启动脚本运行安装在系统中的 fwctld。
5. U-Boot、kernel、initramfs 和 rootfs 均显示 `f9008efd`；rootfs 全量 SHA256 校验通过，dm-verity 启用；data 可写，持久化日志和 SOL 上报正常。

两套 deployment 当前引用已验证的 Boot B。主 R5 SPL 和保留的物理 Boot A 未用本次工厂镜像覆盖；不能据此声称新版 R5 ROM 启动已实测。当前为 SD 实机，未新增 eMMC/NOR 硬件验证。

### 自动化与历史数据

OTA 全套测试通过，包括 14 项 HWID 通道及继承测试、15 项 catalog 测试、浏览器实际上传/发布、跨 HWID 拒绝、异常隔离和中断恢复。固件引擎 5 项测试及新生成 FIT 的 3 项完整性/恢复集成测试通过。

旧服务停止后离线迁移了 manifest、上报、审计及请求数据库；94 份 manifest、170 条历史事件和 19 份审计/隔离记录保留。原始 feed 留存于 `output/ota-validation/feed-before-hwid-only-20261104/`，历史 FIT 字节和内容 ID 未修改。未声明 HWID 的旧固件可下载归档，禁止重新发布。产品代码不包含旧协议兼容分支。

本次构建、测试日志、两次成功快照、完整串口日志和源码快照位于 `output/ota-validation/0.0.1-hwid-only/`，均为本地审计产物，不提交到 Git。


<a id="m1-1-data-mount-validation"></a>

## M1.1：AM625 独立 data 挂载验证

原记录：`docs/am62x/m1-1-data-mount-validation.md`。


日期：2026-11-03。阶段目标是让 `/data` 由板级启动负责挂载，并解除 `logctld` 作为挂载者的隐式职责。挂载失败时只降级持久化能力；启动过程不格式化、不改写分区。

### 实现

- `bsp-base-external/board/ti/am625/rootfs-overlay/etc/init.d/S00data` 在服务启动前读取板级 `storage.conf` 并挂载 `/dev/mmcblk1p15` 到 `/data`。
- `S01logctld` 只消费已经挂载的 `/data`；不可用时继续使用 `/run/logctl/boots`。
- 目标固件的 FIT 版本保持 `v0.0.1`，本次内容 ID 为 `d1f470d7cd77b9c174a8f596fefdc0c3a8057f99ebadf8d7a2cd1cdc5be982bd`。

### 构建和 OTA

- 独立 Buildroot 输出：`output/am625-m1`。
- OTA 工件和串口采集：`output/ota-validation/0.0.1-m1-data-mount/`。
- 服务器：`192.168.10.246:8090`，publication `#36`。
- 实机：`1c-63-49-22-c4-f7`，启动 ID `c27823cd-6adf-43d6-b292-72e848412e76`。

### 验收结果

串口显示 ext4 data 分区以 `r/w` 挂载，并在服务启动前输出 `[data] [INFO] persistent storage mounted on /data`。随后 `logctl` 读回前一启动 marker，输出 `storage=persistent cross-boot=verified`。OTA 状态已从 boot-testing 变为 success，设备执行了 `fwctl current deployment marked good`。

Buildroot `make all` 成功；BusyBox `ash -n` 检查通过；logging 组件 8 项测试通过；新源码构建的 OTA 真实固件下载完整性冒烟测试通过。OTA 全套测试的自动安装模拟和精确恢复用例仍有 11 项失败，需在相关阶段另行定位。固件引擎的 `fwctl_version_test` 当前也有既存断言失败。第一次 OTA 冒烟失败来自旧 host 工具，使用当前源码重建后通过。

### 范围限制

本子阶段只交付独立挂载和跨启动持久化验证。板卡日志显示 ext4 `Quota mode: none`；只读、低空间、I/O 错误、满盘、突然掉电和配额策略尚未验证。这些保留在 M1.2，不能据此声称 data 存储已具备完整故障保护。


<a id="m1-2a-data-health-validation"></a>

## M1.2a：data 启动健康检查与服务降级

原记录：`docs/am62x/m1-2a-data-health-validation.md`。


日期：2026-11-03。本子阶段交付启动时的只读、空闲空间和写入探测，以及日志与 OTA 服务对存储状态的消费。M1.2 的配额、同步错误传播、运行时故障和断电验收仍待完成。

### 实现

- `S00data` 在挂载后检查 `/proc/mounts` 的读写标记、`df -Pk` 的可用空间及临时文件写入。结果原子写入 `/run/device-manager/storage-state`，区分 `persistent`、`read-only`、`low-space`、`unavailable`。
- 板级 `storage.conf` 增加 `minimum_free_kib=32768`。这是本阶段的固定启动阈值；架构计划中的容量比例和 OTA 实际空间预算尚未实现。
- `S01logctld` 与 `S98fwctld` 仅在状态为 `persistent` 时使用 data，否则分别选择 RAM 日志目录和 OTA 缓存目录。启动时明确打印降级原因。
- `logctl status` 增加 `data-state` 字段。启动检查不格式化介质，不修改 A/B 分区布局。

### 构建与实机结果

| 项目 | 结果 |
| --- | --- |
| Buildroot 输出 | `output/am625-m1_2b`，target package 重建与完整镜像生成成功 |
| 版本 / 内容 ID | `v0.0.1` / `443a7372995915849de9f61b8d8b089e6d1f2a1c9052f5a950836f878460c905` |
| 发布 / 设备 | #38 / `1c-63-49-22-c4-f7` |
| 新启动 ID | `adacb97b-3dac-4f32-aba1-27d619d01359` |
| OTA 验收 | 自动下载、安装、重启；健康确认后服务端记录 `success` |
| 存储验收 | ext4 r/w 挂载；`data filesystem mounted read-write with sufficient free space` |
| 日志验收 | `storage=persistent cross-boot=verified`，前次 marker 可读 |
| 传输检查 | 真实 FIT 包在临时 feed 下载并逐字节比较通过 |

工件、原始串口、服务器状态、设备事务、文件 SHA256、Buildroot 配置、编译包源码和待提交源码差异保存在 `output/ota-validation/0.0.1-m1-2-data-health-fix/`。生成物不提交 Git。

### 修复过程与限制

先前发布 #37 的启动脚本使用了目标系统未提供的 `awk`，虽然设备通过 OTA 健康确认，存储状态却降级为 unavailable，因此不作为本阶段验收版本。#38 改用 shell 内建 `read` 解析挂载标记与 `df` 输出，实机启动未再出现该错误。

本阶段只验证 SD 卡正常启动路径。只读、低空间、满盘、I/O 错误、运行期间状态变化、RAM 缓存容量边界和突然掉电均未完成实机故障验收；ext4 日志仍显示 `Quota mode: none`。下一子阶段应实现有界空间预算、同步失败传播与故障夹具，再执行对应实机验证，不能将本次 success 解释为整个 M1.2 已完成。


<a id="m1-2b-sync-validation"></a>

## M1.2b：同步失败传播与可查询状态

原记录：`docs/am62x/m1-2b-sync-validation.md`。


日期：2026-11-03。范围为日志同步错误可见性，以及 OTA 文件和目录同步失败时阻止本轮安装。容量配额、日志分段恢复和真正掉电验收仍未完成。

### 实现

- 日志周期同步按单调时钟每 5 秒触发，检查当前启动文件、启动目录及其父目录；事件立即同步文件和目录。
- `logctl status` 增加 `sync-state`、`synced-sequence`、`observed-sequence`、`sync-errno`。失败时不推进已同步序号，并限频打印本地持久化未确认；普通周期同步失败可在后续成功时恢复。写入或事件立即同步失败采用保守锁存，须重启采集器后重新评估。
- OTA 下载辅助同步函数返回错误；完整暂存复用和已完成缓存复用也必须确认文件与父目录同步。同步失败不返回本轮安装就绪，不推进缓存 current 记录。
- `make -C device-manager test-storage` 提供原生主机故障注入。仅测试夹具使用 `LD_PRELOAD` 拦截同步调用，生产固件不包含该开关。

### 验收

| 项目 | 结果 |
| --- | --- |
| 版本 / 内容 ID | `v0.0.1` / `7d6f773e8e45dd6846205cfe8a28153c2505681a75fe633cb2d6c989876e2b4f` |
| 发布 / 设备 | #39 / `1c-63-49-22-c4-f7` |
| 启动 ID | `5fa9ed5e-b928-4da7-93e0-094852ff64d8` |
| 构建 | `output/am625-m1_2b-sync`；target package 与完整板卡镜像成功 |
| 本地日志回归 | 8 项通过 |
| 同步故障注入 | 2 组测试通过；EIO、ENOSPC、EROFS 覆盖日志序号冻结与恢复，以及 OTA manifest、缓存文件复用、暂存目录和缓存父目录失败 |
| OTA 传输回归 | 通过；真实 FIT 包下载及逐字节比较通过 |
| 实机 | 自动下载、安装、重启、健康确认，服务器记录 success |
| 专项实机读回 | `data-state=persistent`、`sync-state=ok`、`sync-errno=0`；写入测试事件并等待 6 秒后，已同步序号从 321 前进到 323 |

固件、配置、服务器记录、串口、测试和构建日志、源码快照及编译包源码位于 `output/ota-validation/0.0.1-m1-2b-sync/`。生成物不提交 Git。

### 边界与下一步

注入测试运行在主机，实机仅验证正常存储路径；不能据此声称 SD/eMMC 的真实 I/O 故障或突然掉电已经通过。序号只表示本次采集器完成的同步范围，不是 CRC 完整记录索引、服务器归档确认或介质断电承诺。

升级前的旧系统退出时出现 data 已开始卸载、日志进程仍在写入的现象。现有 `S01logctld stop` 只发信号，不等待退出；下一子阶段需保证最终同步先于 data 卸载完成。之后继续空间配额、故障夹具及受控掉电验收。M1.2 整体仍进行中。


<a id="m1-2c-log-stop-validation"></a>

## M1.2c：日志停止与 data 卸载顺序

原记录：`docs/am62x/m1-2c-log-stop-validation.md`。


日期：2026-11-03。修复上一子阶段发现的采集器尚未完成退出、data 已开始卸载的竞态。

### 实现

`S01logctld stop` 先确认目标 PID/可执行文件，发送停止信号并最多等待 10 秒退出；随后核对运行时快照中的 `collector-state=stopped` 和 `sync-state=ok`。只有退出和最终同步均确认才报告成功。超时保留 PID 文件并返回错误；同步失败、缺失状态或仍为 running 的过期状态也返回错误。不使用强制终止来冒充同步成功。

`logctld` 在最终采集及停止事件写入完成后，进入 stopped 状态并执行最终同步；该状态由 `logctl status` 展示。

### 验收

| 项目 | 结果 |
| --- | --- |
| 版本 / 内容 ID | `v0.0.1` / `94ca0506956bfcae991e3cc93b9ad17e981a6d1e28c8ad8da1b5350c91dceeb9` |
| 发布 / 设备 | #40 / `1c-63-49-22-c4-f7` |
| 构建 | `output/am625-m1_2c-stop`，package 与完整镜像成功 |
| 主机测试 | 日志回归 9 项、停止脚本 5 项、同步故障注入 2 组通过；真实 FIT 下载逐字节比较通过 |
| OTA | 自动下载安装、重启、健康确认；服务器 success |
| 专项正常重启 | OTA success 后执行一次正常 reboot，最终同步确认先于 ext4 卸载，停止区间无 logctld ERROR |
| 重启后 | 仍为同一固件；boot ID `9a0f88f5-fd55-4a0c-a8f3-38b11b67a518`，confirmed deployment；storage/data-state=persistent，collector-state=running，sync-state=ok，sync-errno=0 |

实机串口关键顺序：

```text
stopped /usr/sbin/logctld (pid 144)
[logctld] [INFO] collector stopped after final synchronization
[   61.443679] EXT4-fs (mmcblk1p15): unmounting filesystem ...
[   63.470142] reboot: Restarting system
```

证据和工件保存在 `output/ota-validation/0.0.1-m1-2c-stop/`，包含原始串口、正常停止片段、服务器与事务快照、测试/构建日志、文件校验和及源码快照。生成物不提交 Git。

### 边界

仅在实机验证正常停止和正常重启；超时、最终同步失败和过期快照分支通过主机夹具验证。停止超时会返回错误，但现有整体关机流程仍会继续，不能保证真实 I/O 永久挂起时保住全部数据。突然掉电、空间配额、容量耗尽及 eMMC 验收仍待后续阶段。


<a id="ota-failure-evidence-validation"></a>

## OTA 失败日志与原因上报验收

原记录：`docs/am62x/ota-failure-evidence-validation.md`。


日期：2026-11-03。按本轮需求优先交付：已采集的普通日志关联 OTA 失败记录；Linux 本身异常、data 不可用时只上报原因，不附日志。

### 版本与部署

- 固件：`v0.0.1 / 1b65ec9555ba2f9e73401bf8928b4ac42dc8424a6efec880f18ee7129e4ac8b0`，发布 #42。
- 设备：`1c-63-49-22-c4-f7`，boot ID `f88e8c68-3399-4c01-b238-921e483a8c2a`。
- 构建：`output/am625-failure-evidence-v2`；服务端已部署，设备自动下载安装、重启并健康确认，服务器 success。
- 中间发布 #41 成功，随后针对回滚后仍保留原 data 异常原因的边界修正并发布 #42；验收以 #42 为准。

### 功能与检查

复用 SOL 上传通道，按事务和实际升级尝试 boot ID 归档已收到的日志；不将升级前或恢复后的日志冒充失败启动。失败片段独立于 SOL 实时轮转保留，后到日志可补入；正常升级删除临时候选记录。每事务上限 32 MiB、16384 块，超限明确标记缺失。

固件详情“失败与设备异常原因”支持查看、下载串口风格日志。Linux/data 类型只展示观察到的原因和观察启动，不提供日志入口；data 异常在 boot-testing 时记录，恢复后仍可保留。未知根因和无法确认归属的 panic/Oops 痕迹明确标注，不猜测。

主机验收：事故 HTTP 9 项、诊断/报告转换 6 项、SOL 10 项、历史 6 项、请求身份 4 项均通过；真实 FIT 包下载逐字节比较通过。隔离服务的真实浏览器验证查看、下载、正文格式、仅原因无按钮和手机布局通过。所有失败夹具仅操作临时数据库/临时服务，没有向生产注入虚假失败。

实机 #42 自然触发 data 低空间保护：升级缓存累积后可用空间 32173 KiB，boot-testing 上报 `data-low-space-observed`，候选归档不附日志；健康成功后临时记录清理正常。核验服务器副本后，手动删除仅可重新获取的旧 OTA 缓存 36/37/39/40，保留 41/42；本次 RAM 日志迁回 data，boot ID 不变，恢复 persistent、sync-state=ok，空闲空间 155808 KiB。该次维护不是自动配额功能。

### 证据与边界

工件、串口、数据库查询快照、测试及构建日志、浏览器截图、源码与编译包快照位于 `output/ota-validation/0.0.1-failure-evidence-v2/`，生成物不提交 Git。接口与原因定义见 [组件说明](../../edk/docs/device-manager/incident-evidence.md)。

本轮实机只验证正常 OTA、自然低空间观察及持久采集恢复；Linux panic、回滚与数据异常失败分支由主机和隔离服务验证，没有宣称实机全部故障通过。Linux 无法运行时由恢复后代理补报；已收到片段始终标记 complete=false。离线日志保护、自动缓存配额和完整分段归档尚待实现。M1.2/M2/M4 的其余工作并未全部完成。


<a id="ota-incident-attachments-validation"></a>

## OTA 异常详情日志附件与 SOL 跳转验收

原记录：`docs/am62x/ota-incident-attachments-validation.md`。


日期：2026-11-04。修复先前实机验收中“SOL 有异常日志，但 OTA 详情仅显示原因”的缺口。本轮只修改管理服务器与 Web，设备继续运行正常发布 47 的 `v0.0.1 / 6fada4df`，没有再次制造启动故障。

### 真实记录回填

异常事务为设备 `1c-63-49-22-c4-f7` 的发布 46、固件 `v0.0.1 / eec785bd`，升级源启动 `0b9ece2d-8e0e-4650-a162-5663ddda591e`，回退观察启动 `6ea6121b-cad1-4d9d-83f6-5c7359438f1e`。

- 前次异常 capture `dab591db-9258-4a34-8d2f-ff37d3ee3fcc`，bank 0、generation 3，23921 字节。
- 回退恢复 capture `96c60157-9a6e-4080-830c-388fccb27832`，bank 1、generation 4，24482 字节。
- 两份快照上报的完整恢复 ID 相同且与该异常事务一致；没有其他异常事务占用同一恢复上下文。重新核对四阶段长度与 CRC 后，独立复制为两份事故附件，共 48403 字节。
- 接收时间仍为最初归档的 `2026-11-04 10:58:24 +08:00`，不是本次回填时刻。具体 panic 原文及原始实机过程保留在 [故障包验收](ota-boot-failure-log-validation.md)。

在固件详情的“失败/设备异常原因”展开该事件，可分别查看异常与恢复启动。异常附件包含 `eec785bd`、PID 1 退出 73 引起的 `Attempted to kill init! exitcode=0x00004900`、调用栈及 SPL/U-Boot 信息。三个入口为“查看日志”“下载附件”“在 SOL 中打开”。

### 跳转与附件保留

SOL 链接携带设备、capture、publication 和 source boot，直接选择对应记录，刷新后选择保持。原始 SOL 记录删除时，链接回退到独立事故副本，界面明确标记，× 禁用；用户仍能查看和导出。记录确实不存在时显示缺失，不展示其他启动来冒充。

生产环境验证只读取真实异常归档，未删除这次现场。原始 SOL 删除后的回退场景使用生产 SQLite 的隔离快照验证。截图、下载文件及浏览器结果存于 `output/incident-link-browser/`。

### 校验与范围

- 新增 10 项 HTTP/数据库集成测试通过，涵盖事件/归档先后到达、服务重启、旧数据库回填（包括首先执行删除）、原始 SOL 删除后附件保留、错误恢复 ID/代次/slot、歧义上下文、CRC 损坏和 dropped 状态。
- 既有事故 9 项、启动归档 8 项、删除 8 项、SOL 10 项回归通过。
- 浏览器验证实际异常/恢复两张附件卡片、panic/调用栈、下载与显示一致、直接 SOL 跳转、刷新保持、独立副本回退和缺失记录处理。
- 管理服务重载后，用真实事件 API 与原始工件对比，附件原始字节 SHA256 一致；坏固件仍被隔离、当前正常固件发布不变。
- 根据后续界面要求，“无效固件，禁止发布”使用灰色，“当前发布版本”使用浅绿色；实测计算样式、悬停颜色和禁用状态保持正确。

自动关联只在恢复上下文唯一、相邻缓存对存在且归档可验证时进行；不按短哈希、接近的时间戳或同一版本号推断。四阶段的 complete 状态不等于整个物理 UART 无遗漏。没有充分关系的数据继续保留在 SOL，并明确显示未关联。

服务升级前 SQLite 备份、回填结果、字节核验及源码快照在 `output/incident-link-validation/`。生成物不提交 Git。实现与 API 说明见 [SOL 文档](../../edk/docs/device-manager/sol.md)。


<a id="sol-record-deletion-validation"></a>

## SOL 启动记录逐行删除验收

原记录：`docs/am62x/sol-record-deletion-validation.md`。


日期：2026-11-04。服务端和 Web 页面增加历史记录删除；本轮不修改设备二进制，继续运行发布 47 的 `v0.0.1 / 6fada4df`。

启动记录使用自定义下拉列表，每行右侧显示“×”。当前采集记录的按钮禁用；其他历史记录确认后删除。取消不修改数据；删除另一行保留当前选择，删除所选历史则切换到剩余记录。下拉列表支持键盘焦点、Escape 和外部点击关闭。

删除 API 校验方法、路径、同源与管理请求头；普通模式使用 viewer 凭据，开放查看不授予删除权限，调试免凭据模式可直接操作。SQLite 同一事务内移除 SOL 正文、记录和原有上传游标，同时保留删除标记及有限续传位置。重试上传不会复活记录，也不会让设备旧记录卡住后续上传。删除时间、来源 IP 和原字节数保存供追踪；独立 OTA 事故附件和设备本地日志保留。

验证结果：

- 删除接口 8 项通过：实时历史和归档、ACK 丢失、服务器重启、错误方法/路径/跨域/权限、当前及未完成上传保护、事故副本保留、真实 logctl 上传进程持续取得进展。
- SOL 10 项、启动归档 8 项、事故附件 9 项回归通过。
- 隔离浏览器数据验证每行按钮、取消、选择保留/切换、当前保护、补传不重建、刷新持久化和移动布局。
- 生产环境只读验证真实 OTA panic/恢复归档的查看与导出，仍可取得之前保存的全部原始字节。未用生产历史做删除测试。
- 管理服务已重载；设备 OTA 结果仍为 success，原故障包仍被隔离。

工件：`output/sol-delete-browser/` 的浏览器脚本、结果和桌面/移动截图，以及 `output/sol-delete-*-regression.log`、`output/sol-delete-tests.log`。操作说明见 [SOL 文档](../../edk/docs/device-manager/sol.md)。本次实际故障日志见 [OTA 启动失败验收](ota-boot-failure-log-validation.md)。


<a id="time-source-web-validation"></a>

## AM625 网页时间源与校时验证

原记录：`docs/am62x/time-source-web-validation.md`。


### 发布与范围

- 日期：2026-11-04；版本保持 `v0.0.1`，OTA 发布 45。
- 内容 ID：`6fada4dff914ce270925ffe4d4e8382f6675b38754f8132cd590dea2639b1d1a`。
- 设备：`1c-63-49-22-c4-f7`，IP `192.168.10.211`。
- 页面：`http://192.168.10.246:8090/#clock`，侧栏“时间同步”。
- OTA 更新 kernel/FIT、rootfs；bootloader 本轮未更新。A 槽为新固件，B 槽保留上次确认可用的发布 44。

### 实现

页面显示管理服务器时间与设备最近上报时的时间（北京时间）、同步状态、实际协议、生效源、周期、最近校时、修正量、延迟估计、RTC、设备 IP 与最后上报。设备时间明确为快照；服务器时间基于响应加单调时间推算。上报超过 30 秒自动标记过期，刷新页面保持 `#clock`，后台刷新保留未保存的编辑。

可选当前管理服务器、其他 Device Manager HTTP/HTTPS origin、标准 NTP（`ntp://主机:端口`，默认 UDP 123）。管理地址与时间源分开，切换源不影响 OTA/SOL 地址。后台 `clock.db` 持久保存请求、首次执行结果及设备回报；只收到请求时显示等待，实际生效源来自设备回报。

设备端复用 logctld 的独立联网进程，使用类型明确的协议拉取配置，无 shell 或 SOL 命令输入。配置原子保存到 `/data/log/time-source.conf` 并同步文件/目录。RAM 临时存储或不可写目录不会报告持久化成功。保存后触发校时，支持 60–86400 秒周期。关闭自动校时仍接收后续配置；网页立即校时要求启用自动校时。

标准 NTP 客户端校验版本、模式、同步指示、stratum、origin 回显与时间戳顺序，处理 2036 年 era 回绕，取三个样本中的最短往返延迟。HTTP 保留原有随机 nonce 校验。两种源都支持取消，不修改本地采集/启动健康判断。

### 实机结果

1. 发布 45 自动下载、安装、重启，通过健康检查；后台收到 `success`。首次启动 UUID 为 `81a8520e-60de-42bf-b3af-3ef0b36cbb07`。
2. 默认 HTTP 自动取时成功，网页读到真实设备时间与状态。
3. 从网页配置 `ntp://192.168.10.246:10123`、60 秒周期，设备收到配置并完成标准 NTP 数据包交换，`clock-source=ntp`、`clock-state=synchronized`、errno 0。
4. 网页“立即校时”用相同配置创建新的请求并重新采样，结果成功。
5. 切换 `http://192.168.10.246:8092` 成功，实际取时源改变，管理端口仍为 8090。
6. 配置不可达的 `http://192.168.10.246:1`，设备回报 errno 113；网页明确显示失败，不将提交成功当作校时成功，设备保留已有系统时间。
7. 恢复 NTP 后软件重启。新启动 UUID `0b9ece2d-8e0e-4650-a162-5663ddda591e`，读取持久化的相同配置并在联网后重新完成 NTP 校时；启动健康与日志归档确认正常。
8. 测试结束恢复“当前 Device Manager”、3600 秒周期，验证 HTTP 同步后停止临时 NTP/HTTP 测试服务。保留现有默认源，用户可自行改为实际外部服务器。

独立时间源测试使用当前服务器的另一 HTTP 端口及临时 UDP NTP 应答器，真实 AM625 走网络取时；未声称测试过另一台物理服务器或公网 NTP 集群。片内 RTC 在软件复位后仍回到 1970 年，随后通过配置源恢复日历时间；本轮没有宣称解决 RTC 跨复位保时。

### 回归与审计

- `logging/tests/test_time_sync.py`：7 项，HTTP、RTC、权限、采样延迟、取消；拦截进程时钟，绝不修改测试主机时间。
- `logging/tests/test_time_sources.py`：5 项，NTP 合法/非法响应、2036 年后时间、独立 HTTP 源、远程配置/失败/进程重启持久化，以及停止时取消 UDP 等待。
- `ota/tests/test-clock-control.py`：6 项，待处理/确认、同源强制重采样、输入及跨域限制、支持的源、错误确认拒绝、普通模式访问限制。
- 既有 time endpoint 3 项、logging 9 项、SOL 10 项、启动双缓冲 8 项、控制台与归档命名 15 项通过；真实三 ITB 发布/下载字节对比通过。
- 浏览器验证桌面/移动布局、两种源设置、期望/生效源区分、失败提示、刷新路由、未保存编辑、陈旧上报；在生产页面实操并记录设备确认。

构建目录 `output/am625-time-ui/`。源快照、构建源对比、完整身份和镜像 SHA256、上传/发布回执、设备状态、重启前后记录及测试日志保存在 `output/ota-validation/0.0.1-time-ui/`；截图与浏览器检查在 `output/time-ui-browser/`。生成物不提交 Git。使用细节见 [设备校时文档](../../edk/docs/device-manager/time-sync.md)。


<a id="time-sync-and-archive-names-validation"></a>

## AM625 校时与归档时间戳验收

原记录：`docs/am62x/time-sync-and-archive-names-validation.md`。


日期：2026-11-04。本轮完成归档时间戳命名和设备联网自动校时；版本标签继续为 `v0.0.1`。

### 发布与构建

- 固件 ID：`4d1ea3894a525cbab38a1d273e4b313ee0db3f301d97d41d71d72186b351f010`，发布 #44。
- 构建目录：`output/am625-time-sync/`；工件：`output/ota-validation/0.0.1-time-sync/`。
- kernel 配置开启 RTC_HCTOSYS；SPL/U-Boot 源码和部署不变，不将本轮 OTA 成功计为新的 bootloader 验收。
- 管理服务仍使用 8090，调试免凭据配置保留。时间接口复用 HTTP，没有增加单独程序或标准 UDP NTP 服务。
- 设备 `1c-63-49-22-c4-f7` 的 A/B kernel/rootfs 均已安装该镜像并通过健康确认；最终 deployment 1、kernel/rootfs B，boot ID `6dfd3da3-7c13-4356-9e7b-b0ae040d67c2`，服务器 #44 为 success。备用槽通过现有同版本同 hash 的强制恢复流程写入。

### 归档命名

服务器已有 `startup_boots.seen` 是首次接收时间，本轮通过 `archive_received_at` 暴露这一不可变时间，不把实时 SOL 的最后心跳冒充归档创建时间。

Web 归档列表显示北京时间和记录类型，导出文件示例为 `2026-11-04_08-36-15+0800_startup_df6e92a1.log`，单阶段导出追加 `_kernel` 等后缀。短 ID 区分同秒记录；内部 capture ID、原始日志和 OTA 关联保留。已有归档即时生效，不改写历史异常发生时间；实时视图导出使用导出时刻。设备本地目录继续使用 boot ID。

隔离浏览器固定数据库接收时间，并把浏览器时区设为 America/New_York：列表和文件仍显示明确的 +08:00 北京时间；同秒两条归档有不同名称，刷新保持所选记录，原文导出与阶段顺序一致，手机布局无横向溢出。生产服务上的历史 panic 归档仍可查看和下载，文件名称使用其 11 月 3 日原接收时间，没有改成今天的导出时间。

### 设备自动校时

`GET /api/time/<nonce>` 返回管理服务器的 Unix 秒和纳秒。logctld 上传进程在 eth0 link UP 且有 IP 后独立校时，采样三次选择最低 RTT，检查 nonce、范围和返回格式，估算半程延迟。失败不阻塞采集和健康检查，30 秒后重试；正常每小时重校，发现系统时间相对 CLOCK_BOOTTIME 跳变超过两秒则提前重校。

新设备配置默认 `time-sync=1`。`logctl sync-time` 支持手工校时，`logctl status` 提供时间来源、最近成功时间、偏差、延迟估计和 RTC 写入状态。具体接口和配置见 [组件文档](../../edk/docs/device-manager/time-sync.md)。

首次实机启动，内核读取片内 RTC 为 `1970-01-01T00:00:08 UTC`；网络就绪后自动校准至 `2026-11-04T00:56:20Z`，RTC 写入成功，设备系统时间和读取出的 RTC 时间相差不超过约一秒。OTA 启动健康确认成功，服务器报告 success，data/persistent、日志 sync-state=ok，启动缓存归档确认后正常清空。

### RTC 复位边界

实机软件重启后，片内 RTC 再次返回初始值，内核读取到 1970 年；待网卡就绪，设备再次自动校准至 `2026-11-04T00:59:00Z`。这项观察保存在 `warm-rtc-early.log`，没有将 RTC 写入成功等同于跨重启保留成功。

检查了 Linux RTC 驱动和 SPL 的 RTC 解锁代码，未为此修改底层寄存器或复位流程。TI [SPRAD05E，第 7.11 节](https://www.ti.com/lit/ug/sprad05e/sprad05e.pdf) 说明 AM625 片内 RTC 在软件、冷或热复位期间可能丢失计时值。该硬件限制未被软件消除；本轮交付以每次联网校时为准，离线且 RTC 已复位时不承诺真实日期。归档时间来自服务器，不受这一设备时间限制影响。

### 检查与证据

主机客户端 7 项使用进程内时钟/RTC 拦截验证，测试始终不调整宿主机时间；覆盖坏 nonce、无效年份/纳秒、服务不可用、设时权限失败、RTC 写失败、已有正确时间和停止取消。真实时间 HTTP 3 项、命名 5 项、原文解码 10 项、启动归档 8 项、SOL 10 项、本地采集 9 项通过。真实 FIT 下载并逐字节比较通过。

工件目录保存源码基线、补丁与新文件快照、固件身份和 SHA256、OTA 结果、串口、测试记录、RTC 复位观察及浏览器记录。上述软复位观察不是断电验证，也不代表高精度 NTP/PTP 校时鉴定。


<a id="fwctl-module-consolidation"></a>

## AM625 固件模块归并与验证

原记录：`docs/am62x/fwctl-module-consolidation.md`。


### 调整范围

将 device-manager 顶层 `firmware/`、`fwctl/`、`recovery/` 归并为一个
`fwctl/` 模块。原来三个目录已经链接进同一个程序，本次统一源码组织和构建入口，
不改变固件命令、A/B 元数据、版本/哈希规则、分区布局或恢复策略。
时间模块保持现有 timectl/timectld 实现，不切换 systemd-timesyncd。

```text
device-manager/fwctl/
├── cli/         # 命令与显示
├── core/        # FIT、身份、元数据、升级和恢复事务
├── storage/     # 块设备与 MTD 后端
├── recovery/    # initramfs PID 1 和根文件系统交接
├── health/      # systemd、外设状态和健康检查
├── include/     # 模块接口
├── tests/       # 固件及恢复测试
├── Makefile
└── README.md
```

模块独立构建：`make -C device-manager/fwctl`；测试：
`make -C device-manager/fwctl test`。仓库原 `make fwctl` 转交模块 Makefile，
继续生成 `device-manager/bin/fwctl`，Buildroot 安装位置仍为 `/usr/sbin/fwctl`。
对象文件记录头文件依赖，未修改时不重新编译，公共头文件变更会重新构建受影响对象。

原生测试随模块移动；BSP 的 FIT、存储身份、initramfs 验证脚本更新源码路径。
存储身份测试补齐独立 HWID 测试桩，只模拟板卡身份，仍使用生产 FIT 解析和存储读取代码。
原未被构建使用的共享库导出映射移除；29 个固件运行源码/头文件按内容核对保持一致。

### 发布前验证

固件保持 `v0.0.1`，本次发布内容 ID：
`40b34fcec79b79832582c3542bcac57fa6527b51be1bdc46ab286e5eff2b3983`。

已通过：

- 8 组固件引擎、命令、事务、恢复与实际读取测试。
- 7 项 systemd 健康检查、17 项公共传输、39 项 OTA 代理测试。
- 6 项 initramfs/恢复、4 项 FIT、7 项存储身份测试。
- Linux → U-Boot sandbox → Linux 元数据互读及错误身份拒绝。
- 实际发布 initramfs 的 ARM64 fwctl/BusyBox 动态加载、PID 1 限制及缺库回归。
- 最终 squashfs 中的 fwctl 与 target 一致；timectl 最终二进制与归并前完全相同。
- Buildroot 清理旧 device-manager 构建树后重新构建，旧源码目录不残留。

### 实机验证

本次发布审计编号为 87。AM625 从 `b3397bb3` 升级到 `40b34fce`，
版本均为 `v0.0.1`。设备重启后进入 confirmed/successful=1，服务器收到 success。
本次 boot ID：`8a293846-1753-4d43-95e3-3bd5cf795d0e`。

串口实测：

- `fwctl health-check` 成功，systemd 无失败单元，相关六个服务均 active。
- `fwctl recovery check-slot 0/1` 均返回 match，两个 rootfs 槽完整。
- `fwctl ota-check` 对当前内核/rootfs 的实际内容返回 match；保持版本不变、
  更换期望哈希后返回 different。
- 普通 rootfs 下 `fwctl init` 返回状态 2，保持 PID 1 执行限制。
- timectld 保持原 HTTP 时间源，已同步且显示 UTC+8；本次未修改其源码或二进制。
- 日志 storage=persistent、sync-state=ok，跨重启存储检查与启动日志归档检查成功，
  两份 RAM 启动缓冲已收到归档确认。

本次不破坏实机分区、不执行工厂初始化；异常输入和中断事务由隔离测试验证。
kernel/rootfs OTA 不代表重新验证或更新了 SPL/U-Boot。

审计目录：`output/ota-validation/0.0.1-fwctl-module/`，保存不可变固件包、源码快照、
测试结果、发布事务和串口日志。模块职责见
[fwctl 模块说明](../../edk/user/apps/fwctl/README.md)。


<a id="edk-device-manager-merge"></a>

## EDK 与 Device Manager 仓库合并验收

原记录：`docs/am62x/edk-device-manager-merge.md`。


### 合并结果

以 EDK 为基础，将 Device Manager 完整文件树导入 `edk/device-manager/`，
保留两边的 Git 历史。该目录是普通源码目录，不包含嵌套 Git 仓库。
workspace 移除独立的 device-manager gitlink；libbmc 保持原提交和独立仓库。
旧源码归档及本地构建副本保存在本次 `output/ota-validation/` 审计目录。

本次不调整管理模块内部目录，不改变固件、日志、时间服务的运行职责。
后续再分别将这些功能整理为 EDK 子模块。

EDK 增加 `manager-host`、`manager-device`、`manager-test` 构建入口。
Buildroot 保留可分别选择的外设、设备工具、主机工具包，从同一 EDK 仓库取源码。
修正测试和文档中的旧路径，并排除源目录内已生成的二进制和对象文件。

模块说明见 [EDK 集成文档](../../edk/docs/device-manager/architecture.md)。

### 验证

- EDK 配置、增量构建、SDK 安装与外部消费者回归通过。
- PDI ELF 依赖与 72 个公开函数导出检查通过。
- 管理模块完整回归通过：40 组 Python unittest，共 362 项；默认跳过的真实
  固件包 CLI 用例已使用本次固件另行通过。另包含 C 引擎和前端测试。
- BSP 的恢复、实际 FIT、存储身份与 Linux/U-Boot 元数据互读测试通过。
- 实际发布 initramfs 中的 ARM64 fwctl/BusyBox 动态加载与缺库回归通过。
- 启动缓存 ABI 的 4 项测试通过。
- 迁移前后 131 个管理模块生产 C 源码及头文件逐字节一致。
- host-device-manager 和目标设备工具均由新路径重新构建，完成 AM625 全镜像构建。

### 实机发布

- 固件版本：`v0.0.1`。
- 内容 ID：`b43043308a2dfce9986fc2d454db77ec9794fa9816a69626516f35c935f1f2e2`。
- 设备：`192.168.10.211`，HWID `1010001000110000`。
- 服务器发布审计编号：88；设备上报 `success`。
- 启动 ID：`6fd2dadf-e5e0-40b3-b952-0ecf069c799a`。
- 当前 deployment 0，kernel/rootfs 使用 A 槽，confirmed、successful=1。

串口确认 systemd 无失败单元，固件、日志、时间及健康确认的六个单元 active；
两个 rootfs 槽校验匹配，当前内核/rootfs 的实际大小与完整 SHA256 匹配发布包。
日志存储 persistent、sync-state=ok，SOL 恢复连接并确认启动缓存归档；时间同步
正常、显示 UTC+8，PDM 加载正常。管理服务器已重载为合并后构建的程序。

本次只发布 kernel/rootfs，未升级或破坏 SPL/U-Boot，不将本次结果作为新的
引导程序升级或全槽故障恢复实机验证。

证据目录：`output/ota-validation/0.0.1-edk-device-manager-merge/`，包含固件包、
源码快照、原始仓库归档、测试日志、发布回报及串口验收日志。


<a id="systemd-migration"></a>

## AM625 systemd 迁移

原记录：`docs/am62x/systemd-migration.md`。


AM625 主 rootfs 使用 systemd 管理服务；独立 initramfs 仍由 `/init` 调用 `fwctl init`，完成分区验证、必要恢复与 `switch_root`。固件版本固定为 `v0.0.1`，每次构建以内容 SHA256 区分。分区布局与 A/B 元数据格式不变。

### 服务和职责

| 服务 | 职责 / 故障处理 |
| --- | --- |
| `bsp-data.service` | 挂载已有 data 文件系统，检查可写性与剩余空间；不自动格式化，失败时日志/缓存降级到 RAM |
| `systemd-networkd.service` | 配置 lo、eth0；不等待载波或管理服务器，静态地址由 `.network` 文件管理 |
| `bsp-can.service` / `pdm.service` | CAN 与 PDM 的依赖和反向停止顺序 |
| `psatellited.service` | 前台外设应用，主循环发送 READY/WATCHDOG；15 秒无心跳时由 systemd 终止并重启，限制重启频率 |
| `pdebug-web.service` | 前台运行 lighttpd；`ptelemetryd.service` 默认禁用 |
| `fwctld.service` | 前台 OTA 轮询；网络未就绪时延迟请求，传输失败不使本地健康检查失败 |
| `logctld.service` / `logctl-journal.service` | 保留 SPL/U-Boot/kernel 原有采集，journal 的 MESSAGE 文本接入 services 流，不附加 unit/时间等展示前缀 |
| `timectld.service` | 独立 NTP/HTTP 校时、RTC 和配置回报；与日志服务无生命周期依赖，不以网络校时成功作为启动门槛 |
| `fw-health.service` | 评估本地健康策略；systemctl 子进程查询使用单调时钟、输出上限和 1 秒总期限 |
| `fw-confirm.service` | 连续六次健康检查通过后确认部署、记录启动事件，仍由 fwctld 向服务器报告 OTA 结果 |
| `fw-health-failure.service` | 记录关键健康失败，拒绝尚未确认的候选部署，并请求受控重启 |
| `device-shutdown-intent.service` | 服务停止前记录关机意图，辅助重启原因归因 |

PID 1 独占 `/dev/watchdog0`，运行及重启 watchdog 期限均为 60 秒。AM625 不再启动旧 `system_manager`，避免双重喂狗和双重进程监督。systemd 看门狗与应用心跳不是业务链路端到端健康的替代品；尚未加入的业务服务应定义自己的就绪条件、心跳及健康策略。

### 配置位置

- 板级 unit、网络、journal、watchdog、preset：`bsp-base-external/board/ti/am625/rootfs-overlay/`。
- `10-board-ethernet.link` 保留内核分配的 `eth0` 等网口名称，避免 udev 改名为 `end0` 后与恢复环境、OTA 和健康策略不一致。
- Device Manager 原生服务及前台启动脚本：`device-manager/integration/systemd/`。
- 必须健康的本地 unit/网卡：`/etc/device-manager/health.conf`。当前要求 networkd 和 lo/eth0 已配置 UP，不要求以太网载波或远端响应。
- `/etc/default/fwctld` 与 `/data/fwctld.conf` 保留 OTA 配置来源；禁用内置 timesyncd，由独立 timectld 使用 `/etc/device-manager/time.conf` 和 `/data/timectl/source.conf` 管理校时，显示 UTC+8。
- journal 使用有上限的 RAM 存储；logctld 负责 data 归档与 SOL 上报。禁用 systemd-pstore 自动搬移，避免抢先处理已有启动证据。

切换 init 系统应使用新的 Buildroot 输出目录。不要在旧 SysV target 目录上直接增量覆盖后发布。旧 SDK、dl 缓存可以复用。

```sh
BR2_EXTERNAL="$PWD/bsp-base-external" make -C buildroot O="$PWD/output/am625-systemd" alientek_am62x_defconfig
make -C buildroot O="$PWD/output/am625-systemd" all
```

板端检查：

```sh
cat /proc/1/comm
systemctl --failed
systemctl status fw-health fw-confirm fwctld logctld psatellited
systemctl status timectld
timectl status
journalctl -b -u fwctld -o cat
fwctl health-check
fwctl version
logctl status
```

`fw.rollback_test=1` 仍是明确启用的台架故障注入：未确认部署的健康检查被拒绝；已确认部署不受影响。该测试不能替代真实断电、介质故障和硬件 watchdog 验证。

### 固件管理删除

固件列表末尾增加“删除”，并要求一次浏览器确认。相同 tag 与完整内容 ID 的重复上传一并移除，避免删除后旧副本重新出现在列表。当前发布和正在安装/等待重启/启动健康检查中的固件受保护；发布锁串行化删除和发布。

删除会彻底移除相同版本与完整内容 ID 的上传包、历史发布副本及回退副本，只保留审计元数据和设备升级记录。SQLite `firmware_deletions` / `firmware_removals` 保存完整固件 ID、tag、HWID、来源 IP、时间及请求/完成状态；先记录全部副本的删除意图，再清理负载。已删除的发布只供审计，下载、恢复及自动回退均不能选择；服务重启后继续完成中断的物理删除。保留的 `manifest` 不包含固件字节，也防止历史发布编号重复使用。

### 验证记录

构建及测试输出保存于 `output/systemd-tools/`；实机发布身份、串口日志和设备确认结果另存于唯一的 `output/ota-validation/` 发布目录。只有目标设备重启并报告对应内容 ID 的 success 后才提交、推送本阶段代码。

2026-11-05 实机验证，AM625 `192.168.10.211` / HWID `1010001000110000`：

- `v0.0.1 / a33d0aa63cd81f48c741847762034cd1001d5bb6500fbb4389ea92a2c6a50fce`：OTA 发布 81，重启后设备报告 success；PID 1 为 systemd，部署 1 已确认，kernel/rootfs 使用 B 槽。
- 所需服务 active，`systemctl --failed` 为零，`fwctl health-check` 返回 0；PID 1 持有 `/dev/watchdog0`，运行与重启超时均为 60 秒。未用暂停 PID 1 或物理掉电测试硬件复位期限。
- 对 psatellited 主进程发送 SIGSTOP：15 秒服务 watchdog 到期，systemd 终止并重启进程，NRestarts=1，随后服务恢复 active，整体健康检查通过。
- 临时阻断到管理服务器的路由 18 秒：本地健康检查仍通过，fwctld/logctld 保持运行；恢复路由后 SOL 补传成功。
- data 保持 persistent；设备时间显示 UTC+8；journal 测试消息 `SYSTEMD_JOURNAL_CAPTURE_OK` 已在服务器 SOL 的 services 流中收到。
- 再次执行正常重启：systemd 服务停止并重新启动，仍为同一固件 ID；健康检查、data 持久化、SOL 上报及 UTC+8 校时通过，失败 unit 为零。
- 首轮候选 `d5ea496e` 因网卡自动改名未通过本地健康检查，150 秒观察期限后被拒绝并回退。服务器记录 rolled-back、隔离异常固件并恢复上一正常版本；失败启动日志整包已上传。该候选没有作为成功版本提交。
- 独立 initramfs 的实际 AArch64 程序通过 QEMU 动态加载检查；恢复测试 6 项、EDK 测试 10 项，以及健康策略、OTA/SOL、删除 API 和 Chromium 页面操作测试通过。

成功发布的镜像、完整身份、设备上报与串口证据位于
`output/ota-validation/0.0.1-systemd-02/`；失败候选单独保留在
`output/ota-validation/0.0.1-systemd-01/`。这轮只通过 OTA 安装 kernel/rootfs，
不代表重新安装或验证了包外的 SPL/U-Boot。

管理端同时验证了固件删除、SOL 首次连接时间标题与启动状态，以及各页面优先用设备 IP
显示的行为。历史事务仍保留当时的 IP，稳定内部设备标识继续用于关联，不因地址变化拆分历史。

#### 后续 OTA 暴露的锁竞争修复

基线 `a33d0aa6` 能正常启动，但进行下一次 OTA 时，更新进程占用固件元数据锁，
旧健康监督将 `Resource temporarily unavailable` 误判为本地故障并重启。
因此仅验证一次迁移启动还不够，必须验证迁移后的系统能继续安装下一固件。

`50147beb` 修复健康结果约定：0 为全部通过，75 为本地服务未就绪，76 为固件事务占锁，
其他错误为失败。76 不产生 READY，也不增加启动确认成功次数；运行监督最多容忍连续
180 秒忙状态，使用 `/proc/uptime` 单调时间。其他服务异常不能被占锁状态掩盖。
`fw-confirm` 同样允许暂时忙，仍要求六次连续成功，并保留总观察期限。

正式镜像实机持锁 22 秒期间监督保持 active，释放后健康恢复；部署已确认，失败 unit 为零。
首轮 OTA 的取消记录、临时修复过程及正式镜像验证均归档，未手动确认候选、关闭健康检查
或停止硬件看门狗。详见 [S5f 验收记录](reliability-boundaries.md)。

再次从该正式镜像自动 OTA 至 `v0.0.1 / c06cfb5d`（完整 ID
`c06cfb5dcd09d8e7d54fd5902ac662db40a8535eebc6175b073e5c4727ab0b4a`，发布 85），
设备安装、重启、健康确认及服务端 success 均通过；没有使用临时健康脚本。
最终部署 1、kernel/rootfs B 槽，备用 rootfs 校验通过，失败 unit=0。
串口和设备最终状态见 `output/ota-validation/0.0.1-reliability-s5f-04/`。

#### 串口输出与尚存提示

PID 1、服务默认环境和调试控制台均使用 `TERM=dumb`，禁用颜色和 URL 转义；控制台固定
行列，避免串口和 SOL 捕获 OSC 会话标记、ANSI 颜色及光标位置查询。保持原有服务状态和
错误信息，不以降低全局日志级别隐藏问题。

- `watchdog already running` / `nowayout prevents watchdog being stopped`：U-Boot、
  initramfs 到 PID 1 接力时硬件仍在计时。实机确认 systemd 接管并持续服务，未关闭 nowayout。
- `Modifying watchdog hardware timeout is not supported`：RTI 驱动不支持重新设置已启动的
  watchdog，systemd 复用实际 60 秒期限；不能把配置请求值当成硬件已改变的依据。
- `pdm: loading out-of-tree module taints kernel`：PDM 为外置模块，属于内核调试状态标记。
- RTC 在本次暖重启早期显示 1970 年，随后 Device Manager 完成校时并写 RTC；设备显示
  UTC+8，RTC 保持 UTC。跨复位/断电保持能力仍待硬件及驱动验证，早期日志时间不视为可信。

配置语义参考 systemd 官方的 [服务就绪通知与服务 watchdog](https://www.freedesktop.org/software/systemd/man/255/systemd.service.html) 和 [管理器硬件 watchdog](https://www.freedesktop.org/software/systemd/man/258/user.conf.d.html)。服务 watchdog 监督应用通知；RuntimeWatchdog 由 PID 1 喂硬件，两者失效边界不同。

#### 时间服务拆分验收（2026-11-05）

固件 `v0.0.1 / b3397bb3`，完整 ID
`b3397bb3c3b9b1a4de52f8306519890d4f3b35175c1672c9c0e05d245e086e02`，发布 86，
AM625 自动 OTA 至部署 0/A 槽，重启后健康确认并向服务器上报 success。

`timectld` 与 `timectl` 共用一个二进制，通过独立 systemd unit 和有界 Unix socket 管理。
日志程序移除设时实现与 `sync-time` 命令；校时配置不再依赖 sol.conf 或日志运行目录。
旧 `/data/log/time-source.conf` 成功导入新位置，原副本保留供固件回退。

- 停止 logctld：timectld 保持 active，`timectl sync` 成功，服务器持续收到时间状态。
- 停止 timectld：CLI 明确报服务不可用，logctld 仍采集并通过 SOL 上传测试消息；健康检查通过。
- 网页 API 下发临时 LAN NTP 源：设备完成 9 次 UDP 采样，手工同步及时间服务重启后配置恢复通过。
  这是使用主机真实 UTC 时间的临时协议夹具，不代表长期精度或外部授时系统验收。
- 测试结束恢复原来的 Device Manager HTTP 时间源，所有相关服务 active，失败 unit=0，
  health-check=0、data=persistent、archive-pending=0、sync-state=ok，UTC+8 显示正常。

20 项时间模块测试、26 项日志/启动记录测试、9 项时间 API 测试及实际 ARM64 加载检查通过。
服务启用链接在最终 SquashFS 中检查；Buildroot 在生成文件系统时执行 preset，原始 target
目录不能代替最终镜像的启用状态。证据在 `output/ota-validation/0.0.1-time-service/`。
本阶段保留原 SNTP/HTTP 算法，不引入 chronyd，不宣称解决 RTC 跨复位保时。
