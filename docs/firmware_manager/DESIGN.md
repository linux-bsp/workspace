# Firmware Manager 设计方案与功能概述

## 1. 文档范围

本文档描述当前 Firmware Manager 的实际实现，包括：

- U-Boot <code>fw</code> 固件管理命令。
- SPL 阶段的 A/B deployment 选择。
- MMC 和 SPI NOR 存储访问框架。
- bootloader、kernel、rootfs 三类组件升级。
- FIT 组件包和 release manifest。
- 冗余 metadata、启动尝试、确认和回滚。
- Linux <code>fwctl</code> 及自动健康确认。
- Buildroot 打包和 AM62x SD RAW A/B 集成。
- 断电安全边界、生产安全要求和已知限制。

当前落地平台是 TI AM62x SD/MMC。框架包含部分跨平台能力，但 bootloader 子镜像名称、region 集合和 Linux 默认设备仍有 AM62x 特定约束，详见“跨平台扩展”和“已知限制”。

## 2. 设计目标

| 目标 | 说明 |
|---|---|
| A/B 升级 | 新固件写入非活动槽，当前 confirmed 版本保持可启动 |
| 多组件 deployment | bootloader、kernel、rootfs 可独立选择槽位，但作为一个 deployment 启动和确认 |
| 原子 release | 完整 release 只有在全部组件成功后才提交 pending |
| 可重复升级 | pending 状态下可以替换单组件或重新开始完整 release |
| 自动回滚 | 未确认 deployment 尝试次数耗尽后回到 last-good |
| 冗余 metadata | 两份带 sequence 和 CRC32 的 metadata，单副本损坏可恢复 |
| 包校验 | 校验 FIT、产品、布局、版本、rollback index、image hash 和 release 文件 SHA-256 |
| 跨启动阶段一致 | R5 SPL、A53 SPL、U-Boot 和 Linux 使用同一个 selected deployment |
| Linux 确认 | Linux 健康检查通过后由 fwctl 直接确认 deployment |
| 布局可信 | 固定 RAW region 从 U-Boot control device tree 获取，不信任升级包提供的偏移 |

## 3. 非目标

| 非目标 | 说明 |
|---|---|
| 旧 fu 兼容 | 不保留 <code>fu</code> 命令、<code>fu,*</code> FIT 属性、FUMD metadata 或 fuctl |
| 在线分区调整 | fw 不创建或调整分区，只操作可信 DT 中定义的固定 region |
| 通用文件系统升级 | 当前更新目标是 RAW region，不负责包管理器或文件级升级 |
| 远程传输安全 | TFTP 只负责传输；真实性必须由 FIT 签名保证 |
| 硬件级防回滚 | 当前 rollback index 保存在可写 metadata，不等价于 OTP/eFuse 安全计数器 |
| AM62x bootloader 生产原子性 | ROM 固定读取 tiboot3_a，bootloader 更新主要用于调试和恢复 |

## 4. 术语

| 术语 | 定义 |
|---|---|
| Slot | 组件的物理 A/B 存储位置 |
| Deployment | bootloader、kernel、rootfs 三个组件槽位及其版本的组合 |
| Active | 当前逻辑活动 deployment |
| Pending | 已写入完成、等待测试和确认的 deployment |
| Selected | 本次启动链已经选定的 deployment |
| Last-good | 最近一次确认成功的 deployment |
| Confirmed | 已通过 Linux 健康检查的 deployment |
| Boot-testing | 正在试启动、尚未确认的 deployment |
| Release | 描述多个组件文件、SHA-256 和版本策略的 FIT manifest |
| Component package | 单独的 bootloader.itb、kernel.itb 或 rootfs.itb |
| Metadata | 记录 deployment 状态的 128 字节冗余磁盘结构 |

Deployment 编号和物理槽位不是同一个概念。deployment 0 可以组合 bootloader B、kernel A 和 rootfs B；实际选择完全由每个 component slot 字段决定。

## 5. 总体架构

~~~text
Buildroot post-image
    |
    +-- bootloader.itb
    +-- kernel.itb
    +-- rootfs.itb
    +-- release.itb
            |
            +-- TFTP ----------> U-Boot fw command --+
            |                                          |
            +-- local / HTTP(S) -> PAF fwctl update ---+
                                                       |
                                                       +-- FIT/manifest verification
                                                       +-- trusted layout validation
                                                       +-- inactive region write + readback
                                                       +-- redundant metadata transaction
                         |
                         v
ROM -> R5 SPL -> A53 SPL -> U-Boot -> Linux
        |          |          |          |
        +----------+----------+----------+
              selected deployment
                                      |
                                      v
                              fwctl mark-good
~~~

实现分层如下：

| 层 | 职责 | 主要文件 |
|---|---|---|
| Metadata 核心库 | 状态机、双副本、选择、确认、回滚 | <code>include/firmware_manager.h</code>、<code>lib/firmware_manager.c</code> |
| U-Boot 命令层 | 解析布局、校验 FIT、写入存储、导出环境 | <code>cmd/fw.c</code> |
| SPL 平台层 | 在早期启动阶段选择下一 bootloader 槽 | <code>board/ti/am62x/evm.c</code> |
| 可信布局 | 定义存储、产品、layout-id、region 和策略 | <code>arch/arm/dts/k3-am625-sk-u-boot.dtsi</code> |
| 默认启动环境 | fw_boot、网络、分区、快捷升级命令 | <code>board/ti/am62x/am62x_raw_ab.env</code> |
| Linux 工具 | 下载、校验、写入 release 并管理 FWMD metadata | <code>paf/apps/fwctl</code> |
| Buildroot 集成 | 生成 FIT、安装 fwctl 和启动服务 | <code>br2-external/board/ti/am62x</code> |

## 6. AM62x SD RAW 布局

| Region | Offset | Size | 用途 |
|---|---:|---:|---|
| tiboot3_a | 0x00000000 | 1 MiB | ROM 固定加载的第一阶段 |
| tispl_a | 0x00100000 | 2 MiB | A 槽 A53 SPL |
| uboot_a | 0x00300000 | 2 MiB | A 槽 U-Boot |
| meta0 | 0x00500000 | 64 KiB | metadata 副本 0 |
| meta1 | 0x00510000 | 64 KiB | metadata 副本 1 |
| env | 0x00600000 | 64 KiB | U-Boot environment |
| env backup | 0x00620000 | 64 KiB | 冗余 environment |
| tiboot3_b | 0x00700000 | 1 MiB | B 槽第一阶段镜像备份 |
| tispl_b | 0x00800000 | 2 MiB | B 槽 A53 SPL |
| uboot_b | 0x00a00000 | 2 MiB | B 槽 U-Boot |
| kernel_a | 0x01000000 | 24 MiB | A 槽 kernel FIT |
| kernel_b | 0x02800000 | 24 MiB | B 槽 kernel FIT |
| rootfs_a | 0x04000000 | 128 MiB | A 槽 SquashFS |
| rootfs_b | 0x0c000000 | 128 MiB | B 槽 SquashFS |

可信 DT 节点使用 <code>compatible = "u-boot,firmware-manager"</code>，并定义：

| 属性 | 当前值 | 含义 |
|---|---|---|
| storage | mmc | 存储类型 |
| device | 1 | MMC device |
| product | ti-am62x | FIT 产品匹配值 |
| layout-id | am62x-sd-ab-v1 | FIT 布局匹配值 |
| boot-attempts | 3 | 未确认版本最大尝试次数 |
| default-slot | 0 | 空白 metadata 自动初始化槽 |
| auto-init | true | 仅允许全 00/FF metadata 自动初始化 |
| spl-selects | true | deployment 由 SPL 提前选择 |
| allow-bootloader-update | true | 允许 bootloader 更新的本地策略门 |

布局打开时会检查：

1. 所有 region 均存在且 size 非零。
2. region 不超过设备容量。
3. region 之间不能重叠。
4. MMC offset 必须按 block size 对齐。
5. SPI NOR region 必须按 erase size 对齐。
6. metadata region 至少能容纳 128 字节结构。

## 7. 存储抽象

框架当前实现两类存储：

| 存储 | 定位参数 | 写入方式 | 擦除要求 |
|---|---|---|---|
| MMC | device | block read/write，尾块使用 bounce buffer | 不需要显式擦除 |
| SPI NOR | bus、chip-select | spi_flash read/write | 每个目标 region 写前擦除 |

通用存储行为：

- 检查 offset、length 和设备容量。
- 分块写入和读取，验证块大小为 64 KiB。
- 每次组件写入后逐块读回并逐字节比较。
- 只有写入和回读全部成功后才允许提交 metadata。

## 8. Metadata 磁盘格式

Metadata 固定为 128 字节、小端格式：

| 字段 | 说明 |
|---|---|
| magic | <code>FWMD</code>，数值 0x46574d44 |
| format_version | 当前为 1 |
| header_size | 固定 128 |
| sequence | 冗余副本新旧判定 |
| active_deployment | 当前活动 deployment |
| pending_deployment | 待测试 deployment，none 为 0xff |
| last_good_deployment | 最近确认成功 deployment |
| boot_once_deployment | 单次启动目标 |
| selected_deployment | 启动链本次已选目标 |
| update_state | 当前整体更新状态 |
| deployment[2] | 两个 deployment 描述 |
| crc32 | 前 124 字节 CRC32 |

每个 deployment 包含：

| 字段 | 说明 |
|---|---|
| component[3] | bootloader、kernel、rootfs 的 slot、valid、version、rollback-index |
| state | empty/writing/ready/boot-testing/confirmed/failed |
| tries_remaining | 剩余启动尝试次数 |
| successful | 是否已确认成功 |
| release_version | 完整 release 版本 |

冗余保存算法：

1. 读取 meta0 和 meta1。
2. 分别校验 magic、version、size 和 CRC32。
3. 两份都有效时选择 sequence 更新的一份。
4. 保存时写入当前 source_copy 的另一份。
5. sequence 加 1，写入后立即读回并重新解码。
6. 读回失败时不接受本次保存。

## 9. Deployment 状态机

| 当前状态 | 触发 | 新状态 | 说明 |
|---|---|---|---|
| empty | 初始化目标 | writing 或 ready | release 使用 writing，单组件直接准备 ready |
| writing | 所有 release 组件成功 | ready | 设置 pending 和 tries |
| ready | SPL 首次选择 | boot-testing | tries 减 1 |
| boot-testing | Linux 健康检查成功 | confirmed | active 和 last-good 更新 |
| boot-testing | tries 耗尽 | failed | pending 清除，回到 last-good |
| ready/boot-testing | mark-bad | failed | 禁止继续自动选择 |
| ready/boot-testing | rollback | failed | 取消 pending，选择 last-good |
| confirmed | 新更新 | 保持 confirmed | 作为新 deployment 的克隆基线 |

核心不变量：

- last-good 必须指向 successful 且完整有效的 deployment。
- pending 只能指向完整有效且未确认的 deployment。
- deployment 有效必须包含三个 valid component。
- 新更新基线优先使用 active；active 无效时使用 last-good。
- 组件 rollback-index 不能低于 confirmed 基线。
- release version 不能低于 confirmed 基线 release version。

## 10. 单组件升级流程

以 <code>fw update tftp kernel.itb</code> 为例：

1. 从 TFTP 加载 FIT 到 <code>loadaddr</code>。
2. 校验 FIT 格式和默认 configuration。
3. 校验 <code>fw,type</code>、product、layout-id、version、rollback-index。
4. 校验 configuration 引用的 kernel 和 FDT image hash。
5. 从 active 或 last-good deployment 获取当前 kernel slot。
6. 选择相反物理槽作为目标。
7. 检查目标不会覆盖受保护的 last-good 组件。
8. 将完整 kernel FIT 写入目标 kernel region。
9. 分块读回比较。
10. 创建或复用 pending deployment。
11. 保存冗余 metadata，并设置 tries=3。

组件合并规则：

- pending 不存在时，从 confirmed deployment 克隆完整三组件描述。
- pending 已存在时，更新对应 component 字段，其他 staged component 保留。
- 因此先 upk 再 upr 会得到一个同时包含新 kernel 和新 rootfs 的 pending。
- 重复 upk 会覆盖 pending 的 kernel 目标槽并更新版本字段。

<code>fw restore</code> 使用相同校验、写入和 metadata 路径，但额外要求包类型必须与命令指定组件一致。它不是绕过校验的原始写命令。

## 11. 完整 Release 事务

<code>release.itb</code> 只保存清单，不内嵌组件大数据。清单格式最多可描述三个组件。AM62x 默认远程 OTA 清单只包含 kernel 和 rootfs；bootloader FIT 仍会生成，但不进入默认 release：

| 属性 | 内容 |
|---|---|
| fw,type | release |
| fw,product | ti-am62x |
| fw,layout-id | am62x-sd-ab-v1 |
| fw,version | release 版本 |
| fw,rollback-index | 所有组件最低 rollback 要求 |
| fw,components | 默认 kernel、rootfs；调试清单可显式加入 bootloader |
| fw,*-file | TFTP 根目录中的组件文件名 |
| fw,*-sha256 | 完整组件 ITB 文件 SHA-256 |
| fw,allow-bootloader | release 对 bootloader 更新的授权 |

<code>fw update tftp release.itb all</code> 和 Linux <code>fwctl update release.itb</code> 使用相同的事务模型：

1. 校验 release FIT configuration。
2. 校验 product、layout-id、version 和 manifest image。
3. 检查 component 不重复、数量不超过 3、文件名合法。
4. 将目标 deployment 重建为 confirmed 基线的副本。
5. 保存 <code>pending=none</code>、目标 state=writing 的 metadata。
6. 按 manifest 从 TFTP、本地目录或相对 HTTP(S) URL 获取每个组件。
7. 校验完整 ITB SHA-256。
8. 校验组件自身 FIT 属性和所有 image hash。
9. 检查组件 rollback-index 不低于 release rollback-index。
10. 写入目标槽并读回比较。
11. 所有组件成功后 state 变为 ready。
12. 设置 pending 和 tries，并再次保存 metadata。

### 11.1 Pending Release 替换

当已有 pending 时再次执行完整 release：

- 不返回 EBUSY。
- 原 pending 被明确取消。
- boot-once 被清除。
- selected 暂时回到 confirmed 基线。
- 目标 deployment 从 confirmed 基线重新克隆。
- 写入前先持久化 non-bootable writing 状态。
- 成功后提交新的 pending。
- 失败后 confirmed 仍可启动，并可直接再次执行 upa。

该设计保证完整 release 替换不会继续启动已经被部分覆盖的旧 pending。

## 12. 组件包格式

### 12.1 通用属性

每个组件 FIT 默认 configuration 必须包含：

~~~dts
fw,product = "ti-am62x";
fw,layout-id = "am62x-sd-ab-v1";
fw,version = <VERSION>;
fw,rollback-index = <ROLLBACK_INDEX>;
~~~

### 12.2 Kernel 包

| 项目 | 要求 |
|---|---|
| fw,type | kernel |
| kernel property | 引用 gzip Image |
| fdt property | 引用目标板 DTB |
| 写入内容 | 完整 kernel.itb |
| 启动方式 | bootm |

FIT 暂存地址为 <code>0x90000000</code>，FIT 内 kernel load/entry 为 <code>0x82000000</code>，避免 gzip 输入与输出重叠。

### 12.3 Rootfs 包

| 项目 | 要求 |
|---|---|
| fw,type | rootfs |
| firmware property | 引用 SquashFS image |
| 写入内容 | FIT 中 firmware image 的原始数据 |
| Linux 挂载 | rootfstype=squashfs，ro，rootwait |

rootfs 不把 FIT wrapper 写入 rootfs RAW region，只写入被引用的 SquashFS 数据。

### 12.4 Bootloader 包

| 项目 | 要求 |
|---|---|
| fw,type | bootloader |
| 必需 image | tiboot3、tispl、uboot |
| 写入顺序 | uboot -> tispl -> tiboot3 |
| 授权 | DT allow-bootloader-update，release 模式还要求 fw,allow-bootloader |

tiboot3 最后写，减少先覆盖第一启动阶段而后续镜像尚未完成的窗口。

## 13. AM62x 启动流程

~~~text
ROM
 |
 | 固定读取 tiboot3_a
 v
R5 SPL
 |
 | load FWMD
 | 处理 boot-once 或 pending
 | pending tries--
 | 保存 selected deployment
 v
A53 SPL (tispl_a/b)
 |
 | 读取已提交 selected deployment
 | 选择 uboot_a/b
 v
U-Boot
 |
 | fw select 导出组件槽和 offset
 | 读取 kernel FIT 到 0x90000000
 | 生成 root=/dev/mmcblk1p13 或 p14
 | bootm
 v
Linux
 |
 | /proc/cmdline: fw.deployment=<id>
 | fwctl health confirmation
 v
Confirmed deployment
~~~

R5 SPL 配置 <code>SPL_FW_BOOT_SELECTOR_COMMIT</code>，负责唯一一次尝试计数递减和 selected 保存。A53 SPL 只读取 selected，不重复消耗 tries。U-Boot 在 <code>spl-selects</code> 布局中只导出相同选择。

## 14. U-Boot fw 命令

| 命令 | 功能 |
|---|---|
| <code>fw list</code> | 显示可信布局和所有 region |
| <code>fw status</code> | 显示 metadata、deployment 和 component 状态 |
| <code>fw init a/b</code> | 工厂初始化 metadata，不写组件 |
| <code>fw verify tftp file</code> | 下载并校验组件或 release FIT |
| <code>fw verify addr address size</code> | 校验内存中的 FIT |
| <code>fw update tftp file</code> | 更新单组件并创建/合并 pending |
| <code>fw update addr address size</code> | 从内存更新单组件 |
| <code>fw update tftp release.itb all</code> | 执行完整 release 事务 |
| <code>fw restore component ...</code> | 按指定组件类型执行恢复写入 |
| <code>fw select</code> | 选择 deployment 并导出启动环境 |
| <code>fw boot id</code> | 将 deployment 设置为 pending 启动目标 |
| <code>fw boot id once</code> | 设置一次性启动目标 |
| <code>fw mark-good [id]</code> | 确认 deployment |
| <code>fw mark-bad id</code> | 标记 deployment 失败 |
| <code>fw rollback</code> | 取消 pending，回到 last-good |

错误返回使用负 errno，U-Boot 命令层输出 <code>fw: operation failed (-N)</code>。

## 15. 默认环境和操作快捷方式

| 变量 | 当前值或功能 |
|---|---|
| serverip | 192.168.18.245 |
| gatewayip | 192.168.18.1 |
| ipaddr | 192.168.18.246 |
| kernel_addr_r | 0x90000000 |
| loadaddr | 0x82000000 |
| upk | fw update tftp kernel.itb |
| upr | fw update tftp rootfs.itb |
| upb | fw update tftp bootloader.itb |
| upa | fw update tftp release.itb all |
| bootcmd | run fw_boot |

<code>fw select</code> 导出：

- fw_deployment
- fw_storage
- fw_bootloader_slot
- fw_kernel_slot、fw_kernel_offset、fw_kernel_size
- fw_rootfs_slot、fw_rootfs_offset、fw_rootfs_size

<code>fw_boot</code> 执行顺序：

1. 如果存在 fw_confirm，先 mark-good 并保存环境。
2. fw select。
3. 根据 rootfs slot 设置 Linux root 分区。
4. 生成 bootargs 和 blkdevparts。
5. 从 RAW kernel region 读取完整 FIT。
6. 执行 bootm。

## 16. Linux fwctl

<code>fwctl</code> 是 <code>paf/apps</code> 中的可选用户态 app，不属于 PDM 内核层或 PDI 外设接口层。Buildroot 通过 PAF package 选择依赖并安装：

| 文件 | 用途 |
|---|---|
| <code>/usr/sbin/fwctl</code> | metadata 管理工具 |
| <code>/etc/fwctl.conf</code> | 可信设备、布局、region、下载和签名策略 |
| <code>/etc/default/fwctl</code> | healthcheck、自动确认开关和配置路径 |
| <code>/etc/init.d/S99fw-mark-good</code> | 启动后健康确认 |

默认配置：

~~~text
device=/dev/mmcblk1
product=ti-am62x
layout-id=am62x-sd-ab-v1
boot-attempts=3
work-dir=/tmp
allow-bootloader-update=false
require-signature=false
signature-key=
~~~

支持命令：

| 命令 | 功能 |
|---|---|
| <code>fwctl init a/b</code> | Linux 工厂初始化 metadata |
| <code>fwctl status</code> | 显示 metadata 状态 |
| <code>fwctl update &lt;release.itb&gt;</code> | 从本地目录执行 release 事务 |
| <code>fwctl update &lt;HTTP(S) URL&gt;</code> | 下载 release 和相对路径组件并执行事务 |
| <code>fwctl mark-good [id]</code> | 确认指定或 cmdline deployment |
| <code>fwctl mark-bad id</code> | 标记失败 |
| <code>fwctl rollback</code> | 回到 last-good |

未指定 mark-good ID 时，fwctl 从 <code>/proc/cmdline</code> 解析 <code>fw.deployment</code>。U-Boot 和 fwctl 使用完全相同的 128 字节 FWMD 格式、CRC 和双副本选择规则。HTTPS 请求不能重定向降级到 HTTP；下载有超时、低速和大小上限，临时文件在事务结束后清理。

## 17. Buildroot 打包流程

Buildroot post-image 阶段生成：

~~~text
output/images/release/
    bootloader.itb
    kernel.itb
    rootfs.itb
    release.itb
~~~

部署 TFTP 时，将该目录作为 TFTP 根目录，因此运行时文件名直接是：

~~~text
bootloader.itb
kernel.itb
rootfs.itb
release.itb
~~~

打包关系：

| 输入 | 输出 |
|---|---|
| tiboot3.bin + tispl.bin + u-boot.img | bootloader.itb |
| Image.gz + board.dtb | kernel.itb |
| rootfs.squashfs | rootfs.itb |
| 默认 kernel/rootfs ITB 的文件名和 SHA-256 | release.itb |

<code>firmware-image.sh</code> 在组件 ITB 生成后计算完整文件 SHA-256，并替换 release ITS 模板占位符。

## 18. 错误处理和恢复策略

| 失败阶段 | Metadata 结果 | 下一步 |
|---|---|---|
| FIT 格式或产品校验失败 | 不变 | 更换正确包 |
| 单组件下载失败 | 不变 | 直接重试 |
| 首次单组件写入失败 | 无新 pending | 继续启动 confirmed |
| 完整 release 开始后失败 | pending=none，目标 writing | 修复文件后直接再次 upa |
| readback 失败 | 不提交新状态 | 检查存储并重试 |
| metadata 单副本损坏 | 使用另一副本 | 后续保存自动刷新 |
| metadata 双副本损坏 | 命令拒绝 | 工厂恢复后 fw init |
| 未确认启动失败 | tries 递减 | 耗尽后自动 last-good |
| Linux 健康检查失败 | 不 mark-good | 自动重试或回滚 |
| bootloader 更新失败 | 依失败阶段而定 | 可能需要重新烧卡 |

## 19. 断电安全模型

已实现的安全措施：

1. 普通首次更新先写非活动组件，读回成功后才保存 pending。
2. 完整 release 在写入前清除旧 pending 并保存 writing 状态。
3. 完整 release 所有组件成功后才提交 READY pending。
4. Metadata 使用两个副本、sequence、CRC 和读回验证。
5. Bootloader 按后级到前级顺序写入，tiboot3 最后。

仍需注意：

- 已有 pending 时重复单组件更新会覆盖同一目标槽；当前 metadata 仍可能暂时指向该 pending，重复单组件写入中断电的保护弱于完整 upa。
- AM62x ROM 固定读取 tiboot3_a，无法依据 FWMD 选择 tiboot3_b。
- 覆盖 tiboot3_a 时断电可能导致 ROM 无法加载，需要重新烧卡。
- 因此生产整包升级优先使用 upa；bootloader 更新定位为调试和可现场重烧场景。

## 20. 安全设计

| 控制 | 当前实现 |
|---|---|
| 数据完整性 | FIT image hash、release 文件 SHA-256、metadata CRC32 |
| 产品隔离 | fw,product 必须匹配可信 DT |
| 布局隔离 | fw,layout-id 必须匹配可信 DT |
| 写入范围 | 仅允许可信 DT region |
| 软件防回滚 | component rollback-index 和 release version 比较 |
| Bootloader 双重授权 | 可信 DT allow + release allow |
| 发布真实性 | 依赖 FIT signature 和 control FDT 公钥 |
| HTTPS 信任 | CA 根证书校验，禁止 HTTPS 重定向降级为 HTTP |

生产要求：

1. 在 U-Boot control FDT 中安装并要求 FIT 公钥。
2. 对 release configuration 和组件 FIT 进行签名。
3. 保护 control FDT、U-Boot 和环境存储。
4. 将 rollback index 与 OTP/eFuse 或受保护安全存储结合。
5. 不把 TFTP、普通 SHA-256 或 metadata CRC 当作发布者身份认证。
6. 对 fwctl 的原始块设备写权限进行最小化控制。

当前开发包主要使用 hash。Hash 可以检测传输或存储损坏，但攻击者可以同时替换数据和 hash，因此不能替代签名。

## 21. 跨平台扩展

已经数据驱动或可复用的部分：

- Metadata 状态机与磁盘格式。
- MMC/SPI NOR 基础读写。
- product 和 layout-id 校验。
- FIT version、rollback 和 hash 校验。
- 双副本 metadata。
- deployment 选择、确认和回滚。
- release manifest 和 TFTP 文件下载。

新增平台至少需要：

1. 在 control DT 中增加 firmware-manager 节点。
2. 定义存储类型、设备和所有 region。
3. 配置 SPL 在正确阶段调用 metadata selector。
4. 实现该平台从 selected deployment 到下一 boot stage 的槽位映射。
5. 提供默认 fw_boot 环境和 rootfs 参数。
6. 提供 Buildroot ITS 和 release 模板。
7. 在 <code>/etc/fwctl.conf</code> 配置 Linux 可信布局、设备、region 和签名策略。
8. 完成实机断电和回滚测试。

当前仍然平台相关的部分：

| 项目 | 当前约束 | 后续通用化方向 |
|---|---|---|
| Region 枚举 | 固定 tiboot3/tispl/uboot/kernel/rootfs | 改为 DT 描述的 component target 列表 |
| Bootloader image 名 | 固定 tiboot3、tispl、uboot | 由平台 DT 或 FIT target mapping 指定 |
| SPL hook | AM62x board_spl_mmc_get_uboot_raw_sector | 提供平台 adapter 接口 |
| Rootfs 分区号 | 固定 p13/p14 | 由布局属性或 PARTUUID 生成 |
| fwctl 默认设备 | /dev/mmcblk1 和固定 offset | 通过板级配置生成 |
| ROM 行为 | 固定 tiboot3_a | 各平台单独定义第一阶段恢复策略 |

因此当前版本是“通用 metadata/事务核心 + AM62x 平台实现”，还不是无需代码修改即可支持任意 SoC 的完全数据驱动框架。

## 22. 配置项

| 配置 | 用途 |
|---|---|
| CONFIG_CMD_FW | 启用 U-Boot fw 命令 |
| SPL_FW_BOOT_SELECTOR | 启用 SPL deployment 选择 |
| SPL_FW_BOOT_SELECTOR_COMMIT | 允许当前 SPL 消耗 tries 并保存 selected |
| SPL_FW_METADATA0_OFFSET | SPL metadata 副本 0 offset |
| SPL_FW_METADATA1_OFFSET | SPL metadata 副本 1 offset |
| SPL_FW_RAW_SECTOR_B | B 槽下一阶段 sector |
| CONFIG_ENV_IS_IN_MMC | 将持久化环境保存到 MMC |
| CONFIG_FWCTL | 在 PAF 中构建 fwctl app |
| BR2_PACKAGE_PAF_FWCTL | 选择 fwctl 的 libfdt、libcurl、OpenSSL 和 CA 证书依赖 |
| BR2_PACKAGE_PAF_FWCTL_FIT_SIGNATURE | 安装 fit_check_sign 签名验证工具 |

## 23. 当前功能清单

| 类别 | 功能 | 状态 |
|---|---|---|
| 查询 | list、status、help | 已实现 |
| 初始化 | init a/b、空白 auto-init | 已实现 |
| 包校验 | tftp/addr、FIT hash、product/layout | 已实现 |
| 单组件 | bootloader/kernel/rootfs update | 已实现 |
| 恢复 | 指定组件 restore | 已实现 |
| 完整发布 | U-Boot TFTP 和 Linux 本地/HTTP(S) release | 已实现 |
| Pending 替换 | 单组件覆盖、完整 release 重启 | 已实现 |
| 防回滚 | version/rollback 检查 | 已实现，软件级 |
| Metadata | 双副本、sequence、CRC、读回 | 已实现 |
| 启动选择 | R5 commit、A53 reuse、U-Boot export | 已实现 |
| 尝试和回滚 | tries、mark-good/bad、rollback | 已实现 |
| 单次启动 | boot deployment once | 已实现 |
| Linux 确认 | fwctl 和 init script | 已实现 |
| 存储 | MMC、SPI NOR 基础后端 | 已实现 |
| FIT 签名策略 | 使用 U-Boot FIT 验证框架 | 框架已接入，生产密钥需部署 |
| 旧 fu 兼容 | 命令、metadata、FIT、工具 | 明确不支持 |
| 任意平台零代码适配 | 完全 DT 数据驱动 | 尚未实现 |

## 24. 已知限制

1. 旧版 fu 不能直接升级当前 fw release。
2. 旧 FUMD metadata 不会自动迁移为 FWMD。
3. AM62x bootloader 更新不是 ROM 层真正可切换的完整 A/B。
4. 重复单组件更新的断电窗口弱于完整 release replacement。
5. 当前 release 版本和 rollback index 由 ITS 模板维护，需要发布流程保证递增。
6. 当前开发配置的 hash 不等同于生产签名。
7. fwctl 直接写原始块设备，权限配置必须由系统负责；更新期间不得由其他工具并行改写同一设备。
8. SPI NOR 后端已有实现，但当前完整实机验证集中在 AM62x MMC。
9. Region 和 bootloader image mapping 尚未完全数据驱动。
10. metadata 只有两个 deployment，当前设计不保存更长版本历史。

## 25. 推荐使用流程

### 25.1 工厂首次烧录

~~~text
env default -a
saveenv
fw init a
fw status
reset
~~~

### 25.2 完整升级

~~~text
run upa
fw status
reset
~~~

Linux 启动后：

~~~text
fwctl status
fwctl mark-good
~~~

默认 AUTO_MARK_GOOD=1 时由启动脚本自动确认。

Linux 也可直接安装下一版本，随后重启进入 boot-testing：

~~~text
fwctl update /mnt/upgrade/release.itb
# 或
fwctl update https://updates.example.com/am62x/release.itb
reboot
~~~

### 25.3 单组件调试升级

~~~text
run upk
run upr
fw status
reset
~~~

### 25.4 替换错误 Pending

~~~text
run upa
~~~

无需先 mark-good；完整 release 会放弃旧 pending 并重新开始。

### 25.5 手动回滚

~~~text
fw rollback
fw status
reset
~~~

## 26. 代码和文档索引

| 内容 | 路径 |
|---|---|
| U-Boot 命令 | <code>cmd/fw.c</code> |
| Metadata API | <code>include/firmware_manager.h</code> |
| Metadata 实现 | <code>lib/firmware_manager.c</code> |
| AM62x SPL selector | <code>board/ti/am62x/evm.c</code> |
| AM62x 默认环境 | <code>board/ti/am62x/am62x_raw_ab.env</code> |
| AM62x 可信布局 | <code>arch/arm/dts/k3-am625-sk-u-boot.dtsi</code> |
| U-Boot 使用文档 | <code>doc/usage/cmd/fw.rst</code> |
| DT binding | <code>doc/device-tree-bindings/firmware/u-boot,firmware-manager.txt</code> |
| Linux 工具 | <code>paf/apps/fwctl</code> |
| Linux 板级配置 | <code>br2-external/board/ti/am62x/rootfs-overlay/etc/fwctl.conf</code> |
| FIT 模板 | <code>br2-external/board/ti/am62x/layout</code> |
| 实机测试用例 | <code>docs/firmware_manager/TEST_CASES.md</code> |
