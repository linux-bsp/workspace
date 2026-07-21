# 通用固件升级方案设计

## 1. 文档目的

本文定义一套运行于 U-Boot 和 Linux 的通用固件升级方案。目标设备不依赖
GPT/MBR，eMMC、SD 和 SPI NOR 均使用固定 RAW 区域。

方案分为两层：

- U-Boot 提供调试、工厂烧录、救援升级、A/B 选择和回滚。
- Linux 提供远程下载、升级策略、健康检查和完整 OTA。
- 两层共享同一份布局定义和 deployment metadata。

升级产物拆分为 bootloader.itb、kernel.itb、rootfs.itb，并使用可选的 release.itb
组织完整发布。单组件升级只下载对应 FIT。

## 2. 设计目标

- 支持 eMMC、SD 和 SPI NOR。
- 支持完整 bootloader、Kernel 和 rootfs 独立升级。
- 支持多个组件组合成可回滚 deployment。
- 支持启动尝试次数、成功确认和自动回滚。
- 支持指定 deployment 或 recovery 启动。
- 支持单组件恢复和工厂整盘 RAW 烧录。
- 支持签名、SHA-256、设备兼容性检查和防降级。
- 普通升级断电不得破坏当前 last-good deployment。
- rootfs 约 120 MiB，第一阶段允许单个 FIT 加载到 RAM，并预留流式接口。

## 3. 非目标

- 普通 OTA 不动态修改设备布局。
- 普通 update all 不覆盖整个设备。
- 普通升级不更新 data、序列号、MAC 和校准数据。
- 第一阶段不要求差分升级和断点续传。
- metadata 不采用 Android BCB，避免绑定 Android 和块分区模型。
- 不假设所有介质都能安全在线更新第一阶段 bootloader。

## 4. 总体架构

~~~text
                    构建和打包配置
                          |
              +-----------+-----------+
              |                       |
       生成介质 RAW 布局          生成升级产物
              |                       |
       +------+------+         +------+------+
       |             |         |             |
    U-Boot 表      Linux 表   组件 FIT     Linux OTA 包
       |             |         |             |
       +------+------+---------+------+------+
                          |
               统一组件名称和 deployment metadata
~~~

功能分层：

~~~text
传输层        TFTP / USB DFU / USB存储 / SD / 内存
包解析层      boot/kernel/rootfs FIT / release manifest
策略层        签名、兼容性、版本、权限、依赖和升级顺序
存储层        MMC block backend / SPI NOR MTD backend
状态层        冗余 deployment metadata
启动层        deployment选择、尝试、确认、回滚和recovery
~~~

## 5. RAW 区域布局

### 5.1 逻辑区域

上层只通过逻辑名称访问存储，不接受升级包提供的任意物理 offset。

~~~text
meta0         metadata主副本之一
meta1         metadata主副本之二

tiboot3_a     bootloader bank A
tispl_a
uboot_a

tiboot3_b     bootloader bank B
tispl_b
uboot_b

kernel_a      完整kernel.itb
kernel_b

rootfs_a      RAW ext4或SquashFS
rootfs_b

recovery      可选最小救援系统
data          持久数据
factory       可选工厂恢复数据
~~~

bootloader 区域不能套用一组通用 offset，必须按照 AM62x ROM 对 eMMC、SD 和
SPI NOR 的启动规则分别定义。布局还必须标明每个阶段是否具备可靠回退能力。

### 5.2 多介质布局

不同介质允许不同物理布局，但必须暴露相同逻辑组件。

~~~text
emmc-8g-v1
sd-8g-v1
spinor-256m-v1
spinor-512m-v1
~~~

每个布局具有唯一 layout-id。FIT 只声明允许的 layout-id，实际 offset 和 size
始终来自本机可信布局。

### 5.3 唯一布局源

构建系统建议维护 YAML 作为唯一来源：

~~~yaml
layout: spinor-512m-v1
medium: spinor
alignment: 0x10000

regions:
  - { name: meta0,     offset: 0x00000000, size: 0x00010000 }
  - { name: meta1,     offset: 0x00010000, size: 0x00010000 }
  - { name: tiboot3_a, offset: medium-defined, size: layout-defined }
  - { name: tispl_a,   offset: medium-defined, size: layout-defined }
  - { name: uboot_a,   offset: medium-defined, size: layout-defined }
  - { name: tiboot3_b, offset: medium-defined, size: layout-defined }
  - { name: tispl_b,   offset: medium-defined, size: layout-defined }
  - { name: uboot_b,   offset: medium-defined, size: layout-defined }
  - { name: kernel_a,  offset: layout-defined, size: layout-defined }
  - { name: kernel_b,  offset: layout-defined, size: layout-defined }
  - { name: rootfs_a,  offset: layout-defined, size: 0x08000000 }
  - { name: rootfs_b,  offset: layout-defined, size: 0x08000000 }
~~~

生成内容包括：

- U-Boot 布局表。
- Linux blkdevparts 或 MTD fixed-partitions。
- genimage_ti.cfg 和各组件独立 ITS。
- Linux OTA 描述。
- 工厂整盘 RAW 镜像。
- layout-id、布局版本和布局 hash。

普通升级包不得修改布局。布局迁移只能通过受限的 provision 流程执行。

## 6. A/B Deployment Metadata

### 6.1 Deployment 模型

组件可以独立切换 A/B，因此不能只保存一个全局 active_slot。metadata 保存两组
可启动 deployment：

~~~c
enum fw_component {
	FW_COMPONENT_BOOTLOADER,
	FW_COMPONENT_KERNEL,
	FW_COMPONENT_ROOTFS,
	FW_COMPONENT_COUNT,
};

struct fw_component_slot {
	u8 slot;
	u8 valid;
	u16 reserved;
	u32 version;
	u32 rollback_index;
};

struct fw_deployment {
	struct fw_component_slot component[FW_COMPONENT_COUNT];
	u8 state;
	u8 tries_remaining;
	u8 successful;
	u8 reserved;
	u32 release_version;
};

struct fw_metadata {
	u32 magic;
	u16 format_version;
	u16 header_size;
	u32 sequence;
	u8 active_deployment;
	u8 pending_deployment;
	u8 last_good_deployment;
	u8 boot_once_deployment;
	u8 update_state;
	u8 reserved[3];
	struct fw_deployment deployment[2];
	u32 crc32;
};
~~~

磁盘格式必须明确大小端、字段大小和对齐，不能直接依赖编译器结构体布局。

典型组合：

~~~text
只升级kernel：     bootloader_a + kernel_b + rootfs_a
只升级rootfs：     bootloader_a + kernel_a + rootfs_b
普通完整升级：     bootloader_a + kernel_b + rootfs_b
包含bootloader：   bootloader_b + kernel_b + rootfs_b
~~~

### 6.2 Metadata 冗余

- metadata 分别保存在 meta0 和 meta1。
- SPI NOR 两份副本必须位于不同 erase block。
- 更新旧副本，读回验证后以更大的 sequence 生效。
- 启动时选择 CRC 正确且 sequence 最大的副本。
- 任意时刻至少保留一个完整有效副本。

### 6.3 状态

~~~text
EMPTY         未安装
WRITING       正在写入，不可启动
READY         写入和校验完成
BOOT_TESTING  正在试启动
CONFIRMED     Linux健康检查通过
FAILED        启动失败或镜像损坏
~~~

写入中断时不提交 pending deployment，重新执行升级即可。

## 7. 启动选择和回滚

选择顺序：

~~~text
强制recovery
  -> boot_once deployment
  -> pending且tries_remaining大于0
  -> active且successful
  -> last-good deployment
  -> recovery
~~~

对于未确认 deployment，U-Boot 在跳转 Kernel 前减少一次 tries_remaining 并持久化。
Linux 健康检查通过后调用 mark-good。尝试次数耗尽后恢复 last-good deployment。

bootloader 回退发生在 U-Boot 执行之前，必须由 ROM、不可变 selector 或更早启动
阶段完成，不能只依靠本 metadata。

## 8. U-Boot fw 命令

建议接口：

~~~text
fw status
fw list
fw verify <source> <fit-file>
fw update <source> <fit-file>
fw update <source> <release-file> all
fw boot <deployment>|recovery [once]
fw mark-good [deployment]
fw mark-bad <deployment>
fw rollback
fw restore <component> <source> <fit-file>
fw provision <source> <factory-image>
~~~

示例：

~~~text
fw update tftp bootloader.itb
fw update tftp kernel.itb
fw update tftp rootfs.itb
fw update tftp release.itb all
fw rollback
fw restore rootfs tftp rootfs.itb
~~~

fw 必须从已验证的 FIT configuration 中读取 fw,type，不能根据文件名判断类型。

单组件升级写入未被 active 或 last-good deployment 使用的区域。所有组件完成校验
后才创建 pending deployment。普通 all 默认只包含 kernel 和 rootfs；bootloader
必须由 release manifest 明确授权。

provision 用于首次烧录、整盘 RAW 写入和布局迁移，必须通过工厂构建、硬件授权、
独立密钥或显式确认与普通升级隔离。

## 9. 组件 FIT

### 9.1 Buildroot 产物

Buildroot 默认产物作为输入，post-image 阶段生成：

~~~text
output/images/
  tiboot3.bin
  tispl.bin_unsigned
  u-boot.img_unsigned
  Image.gz
  <board>.dtb
  rootfs.squashfs
  release/bootloader.itb
  release/kernel.itb
  release/rootfs.itb
  release/release.itb
  sdcard.img
~~~

AM62x 的布局和打包配置统一放在 br2-external 的以下目录：

~~~text
board/ti/am62x/layout/
  genimage_ti.cfg
  genimage_sdcard.cfg
  bootloader.its
  kernel.its
  rootfs.its
  release.its.in
~~~

genimage_ti.cfg 定义组件 FIT；genimage_sdcard.cfg 是 SD RAW offset/size 的唯一布局配置。
每个组件使用一个短小且可独立阅读的 ITS，只描述该组件的 image 类型、启动属性、
configuration 和签名策略，不重复 payload 路径和物理 offset。

Buildroot 调用通用入口并直接传入 genimage 配置：

~~~config
BR2_ROOTFS_POST_IMAGE_SCRIPT="$(BR2_EXTERNAL_LINUX_BSP_PATH)/support/scripts/firmware-image.sh"
BR2_ROOTFS_POST_IMAGE_SCRIPT_ARGS="-c $(BR2_EXTERNAL_LINUX_BSP_PATH)/board/ti/am62x/layout/genimage_ti.cfg"
~~~

通用脚本读取 genimage_ti.cfg 中任意数量的 its 项，从配置目录复制同名 ITS 到
Buildroot images 目录，第一阶段生成组件 ITB，随后计算完整文件 SHA-256 并生成
release.itb。第二阶段使用 genimage_sdcard.cfg 将已经生成的 kernel.itb 和 rootfs
写入 A/B RAW 槽。拆分阶段可以避免 genimage 在同一依赖图中把新生成 FIT 当作
零长度 media 输入。成功后删除临时 ITS。

### 9.2 通用 FIT 属性

每个签名 configuration 至少包含：

~~~dts
fw,type = "bootloader";       /* 或 kernel、rootfs、release */
fw,product = "am62x-board";
fw,layout-id = "spinor-512m-v1";
fw,version = <2>;
fw,rollback-index = <10>;
~~~

还应包含硬件版本、介质约束、payload 长度、组件依赖和签名。fw 必须验证
configuration signature、产品、layout-id、版本、rollback index 和区域容量。

### 9.3 bootloader.itb

bootloader.itb 是完整 AM62x bootloader 升级容器，不是 Linux 启动 FIT：

~~~text
bootloader.itb
  tiboot3.bin
  tispl.bin
  u-boot.img
~~~

configuration 建议使用标准 firmware 和 loadables：

~~~dts
conf-1 {
	fw,type = "bootloader";
	firmware = "tiboot3";
	loadables = "tispl", "uboot";

	signature-1 {
		algo = "sha256,rsa2048";
		key-name-hint = "firmware";
		sign-images = "firmware", "loadables";
	};
};
~~~

fw 将三个 payload 分别写入非活动 bootloader bank。推荐顺序：

~~~text
u-boot.img
  -> tispl.bin
  -> tiboot3.bin
  -> 全部读回校验
  -> 提交bootloader pending状态
~~~

是否允许现场更新 tiboot3.bin 取决于介质：

- eMMC：评估 boot0/boot1 和 AM62x ROM 的实际切换能力。
- SD：需要 ROM 备用偏移或保持 tiboot3 不可变。
- SPI NOR：若 ROM 只从 offset 0 启动，应保持第一阶段不可变或提供 ROM 级备份。
- 不具备可靠回退能力时，完整 bootloader.itb 只能用于工厂和可救砖环境。

### 9.4 kernel.itb

kernel.itb 包含 Image、DTB 和可选 initramfs，并作为整体写入 kernel_a/kernel_b。
U-Boot 从 RAW 区域读出完整 FIT 后直接 bootm，确保 Kernel、DTB 和 initramfs 一致。

Kernel 模块必须纳入兼容性设计：

- 关键驱动编入 Kernel。
- kernel.itb 携带独立 modules 镜像。
- modules 使用独立 A/B RAW 区域。
- release manifest 禁止不兼容的 kernel/rootfs 组合。

### 9.5 rootfs.itb

rootfs.itb 是升级容器，包含 rootfs.ext4 或 rootfs.squashfs。fw 通过 FIT API 取得
rootfs image data，只把 payload 写入 rootfs_a/rootfs_b，不能把 FIT header 写入
rootfs 区域。

rootfs 文件系统通常已有固定块布局或自身压缩，FIT compression 建议为 none。

### 9.6 release.itb

release.itb 是小型发布清单，记录：

- 清单所列组件的文件名和整个文件 SHA-256。
- 产品、硬件、介质和 layout-id。
- release version、rollback index 和组件版本。
- 允许的 deployment 组合。
- 下载和写入顺序。
- 是否具有 bootloader 更新权限。

单组件升级只下载对应 FIT。完整升级先下载 release.itb，再按需下载组件 FIT，
不下载包含所有 payload 的单体 FIT。

当前 am62x-sd-ab-v1 模板包含 bootloader、kernel 和 rootfs。fw 在内存中构造新
deployment，逐个下载、校验和写入组件，全部成功后只保存一次 pending metadata。
bootloader 必须同时具有清单 fw,allow-bootloader 和可信设备布局
allow-bootloader-update 才能进入事务。bootloader.itb 包含 tiboot3、tispl 和
U-Boot，并按 U-Boot、tispl、tiboot3 的顺序写入。当前开发模板只有 hash；生产构建
必须增加签名。

### 9.7 RAM 和流式接口

rootfs 约 120 MiB 时，RAM 足够可先加载单个 rootfs.itb。内部接口仍按流式设计：

~~~c
int begin(const struct fw_region *region, u64 image_size);
int write(u64 image_offset, const void *buf, size_t len);
int finish(const u8 *expected_hash);
void abort(void);
~~~

后续可增加 TFTP 或 USB 流式写入，不改变 FIT 策略和存储 backend。

## 10. 存储抽象

统一使用字节 offset：

~~~c
struct fw_storage_ops {
	int (*probe)(void *ctx);
	int (*get_region)(void *ctx, const char *name,
			  struct fw_region *region);
	int (*erase)(void *ctx, u64 offset, u64 size);
	int (*write)(void *ctx, u64 offset, const void *buf, size_t len);
	int (*read)(void *ctx, u64 offset, void *buf, size_t len);
	int (*sync)(void *ctx);
};
~~~

MMC backend 将字节转换成 LBA并检查 block 对齐、写保护和容量。eMMC boot0/boot1
作为特殊硬件区域处理。

SPI NOR backend 按 erase block 擦除、按 page 或 chunk 写入，禁止越界擦除。
metadata 主备副本使用独立 erase block。

## 11. RAW Rootfs 的 Linux 可见性

SPI NOR 使用 fixed-partitions 暴露 MTD 区域。

eMMC/SD 无 GPT/MBR 时可选择：

- 启用 command-line partition parser并生成 blkdevparts。
- 在 initramfs 使用 device-mapper。
- OTA agent 对整个块设备使用固定 offset。

推荐由布局 YAML 生成 blkdevparts 和 rootfs 参数，避免人工维护两份 offset。

## 12. Linux OTA

Linux OTA 可使用 SWUpdate 或自研 agent：

~~~text
验证release manifest
  -> 流式写入未使用组件槽
  -> 校验全部组件
  -> 创建pending deployment
  -> 重启
  -> U-Boot尝试deployment
  -> Linux健康检查
  -> mark-good
~~~

Linux 提供共享 metadata 工具：

~~~text
fwctl status
fwctl set-pending <deployment>
fwctl mark-good
fwctl mark-bad <deployment>
fwctl rollback
~~~

U-Boot 和 Linux 不得维护两套独立 deployment 状态。

## 13. 恢复策略

- rollback：恢复 last-good deployment，不复制数据。
- component restore：从 TFTP、USB、SD 或 recovery 重写未使用组件槽。
- recovery boot：A/B 都不可启动或显式请求时启动最小 Linux。
- factory recovery：通过 ROM USB/UART boot 或专用工厂 U-Boot重建完整介质。

recovery 至少包含网络、USB、存储、签名验证和恢复工具。

## 14. 安全要求

- 正式设备必须验证 FIT 和 release manifest 签名。
- TLS 不能替代离线签名。
- 公钥放入 U-Boot control DT、只读区域或安全存储。
- 校验产品、硬件、介质、layout-id、长度和版本依赖。
- 使用 SHA-256 校验下载和写入内容。
- 使用 rollback index 防止降级。
- bootloader 更新使用显式权限，建议使用独立签名策略。
- 普通包禁止修改 metadata、data、设备身份和校准区域。
- 工厂包与普通 OTA 包使用不同权限或密钥。

## 15. 断电一致性

普通升级提交顺序：

~~~text
1. 选择未被active和last-good引用的组件槽
2. 标记目标为WRITING
3. 擦除并写入
4. 校验全部目标组件
5. 标记组件READY
6. 一次性创建pending deployment并设置tries_remaining
~~~

步骤 6 前断电继续启动 last-good deployment。步骤 6 后由正常尝试和回滚逻辑处理。

bootloader 更新还必须保证更早启动阶段能够选择旧 bank。仅有 U-Boot metadata
不能保护 tiboot3 或 tispl 写坏的场景。

## 16. 测试要求

至少覆盖：

- 三种介质的 boot、kernel、rootfs 单组件升级。
- release.itb 事务升级和组件下载失败。
- 每个擦除、写入、校验和 metadata 提交阶段断电。
- FIT 格式、签名、hash、截断和包类型错误。
- 产品、介质、layout-id、版本和组件依赖不匹配。
- 镜像超出区域、未对齐和越界擦除。
- metadata 单副本、双副本和 sequence 异常。
- kernel_b 与 rootfs_a 等混合 deployment 启动。
- 新 deployment 确认及尝试耗尽回滚。
- A/B 都不可启动进入 recovery。
- bootloader bank 失败时的早期回退。
- 普通包无法触发 provision 或未授权 bootloader 更新。

### 当前实现状态

- 已完成 SD/MMC 固定 RAW A/B 布局、双副本 metadata 和首次启动初始化。
- 已完成 kernel、rootfs 和完整 bootloader 引导链单组件升级。
- 已完成 release.itb 下载、整文件 SHA-256、组件 FIT 校验和单次 pending 提交。
- 已完成 U-Boot RAW FIT 启动选择和 Linux fwctl 基础健康确认。
- 尚未完成生产签名密钥注入、recovery/provision、流式下载和服务端 OTA agent。
- SPI NOR 与 eMMC boot0/boot1 仍需各自布局和板级断电/回退验证，不能复用 SD 偏移。
- SD ROM 固定加载 tiboot3_a，更新 A 槽不具备一级引导断电保护；当前能力定位为
  调试升级，失败后通过重新烧录恢复。

## 17. 实施阶段

### 阶段一：格式和启动

- 固化布局 YAML 和生成规则。
- 固化 metadata 磁盘格式。
- 实现冗余读写和 deployment 选择。
- 实现 status、boot、mark-good、mark-bad 和 rollback。

### 阶段二：组件升级

- 实现 MMC 和 SPI NOR backend。
- 实现 kernel.itb 和 rootfs.itb。
- 实现 release.itb 事务升级。
- 实现 recovery 和受限 provision。

### 阶段三：Bootloader

- 确认每种介质的 AM62x ROM 启动和回退能力。
- 实现 bootloader.itb 解析和三个阶段分区域写入。
- 实现可验证的 bootloader bank 切换。
- 对不具备回退能力的阶段保持工厂模式限制。

### 阶段四：Linux OTA

- 实现 fwctl 或共享 metadata 库。
- 接入 SWUpdate 或自研 agent。
- 实现健康检查和自动 mark-good。
- 接入服务器版本、设备分组和发布策略。

## 18. 待确认事项

- 各介质容量、block size 和 erase size。
- 各 bootloader 阶段在不同介质上的 ROM 搜索和备用规则。
- eMMC 是否使用 boot0/boot1 承载 bootloader A/B。
- SD 和 SPI NOR 的 tiboot3 是否保持不可变。
- kernel、rootfs、recovery 和 data 的最终大小。
- rootfs 使用 ext4 还是 SquashFS。
- Kernel modules 采用哪种独立升级策略。
- Linux 使用 blkdevparts 还是自定义映射。
- recovery 保存完整 rootfs 还是只提供网络恢复。
- 第一阶段整包加载还是直接实现流式下载。
- metadata 是否需要 RPMB 或其他受保护存储。
