# AM625 HWID 环境存储与验证

## 方案与当前身份

HWID 直接保存为 U-Boot 的 `hwid` 环境变量，复用现有环境的 CRC、冗余副本和存储驱动。编码规则见 [HWID 编码规范](hwid-specification.md)，工具说明见 [Device Manager HWID 文档](../../edk/device-manager/docs/hwid.md)。

当前板卡：`1-01-0001-0001-10-000`，规范文本 `1010001000110000`，PCB V1.0。

| 介质 | 存储方式 | 本次验证范围 |
| --- | --- | --- |
| SD | U-Boot MMC 环境，Linux 块设备 | AM625 实机读写、重启、启动传递及固件匹配 |
| eMMC | MMC user area 或明确配置的 boot0/boot1 | 真实 libubootenv 的文件模拟测试；未接实物 |
| SPI NOR | U-Boot SPI Flash 环境，Linux MTD 字符设备 | U-Boot/SPL 交叉编译、真实 libubootenv 配合 NOR 擦写与中断模拟；未接实物 |
| NAND | 暂不支持 | Linux HWID 接口明确拒绝 NAND MTD |

跨介质保持 HWID 格式和命令一致。环境设备、偏移、大小及冗余参数由各板 BSP 配置，并非自动扫描任意介质。

## 当前 SD 环境位置

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

## 启动和更新行为

- SPL 在存储控制器可用后，通过原生环境后端加载身份。
- 完整 U-Boot 打印身份，并写入传给 Linux 的 `/chosen/dm,hwid`。
- initramfs 与 fwctl 使用 libubootenv 读取相同环境；两份 CRC 都无效时不自动重建环境。
- AM625 的 release、bootloader、kernel 和 rootfs FIT 声明完整 `fw,hwids` 列表。U-Boot 与 Linux 更新、恢复校验要求精确匹配，该阶段保留了原有兼容性字段；后续已在 HWID 独立发布阶段移除，当前接口以 [Device Manager HWID 文档](../../edk/device-manager/docs/hwid.md) 为准。

固件内容 ID、软件 tag、设备 HWID 和实物序列号分别管理；HWID 不随软件升级改变。

## 2026-11-04 验证结果

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

## 镜像与审计材料

生成文件保存在工作区 `output/ota-validation/0.0.1-hwid/`，不进入 Git：

- `package.tar.gz`：已发布且通过升级的 kernel/rootfs OTA 包。
- `factory-images/sdcard.img`：包含新版 R5/A53 SPL、U-Boot、双环境及双槽系统的完整工厂镜像；环境带本板 HWID。
- `final-bootloader/`：用于 B 槽实机验证的维护包；内核/rootfs 内容 ID 与已发布包相同。
- `final-complete-boot.log`、`uboot-hwid-match-tests.log`：最终启动和 U-Boot 正反匹配日志。
- `final-device-state.log`、`final-server-state.json`、`factory-image-validation.json`：本地健康、服务端成功及工厂镜像区域核对证据。

本次保留 ROM 使用的原始 R5 SPL A 槽作为回退入口。新版 R5 已编译并包含在工厂镜像和维护包中，但 ROM 未执行该新版 R5；实机执行验证覆盖 A53 SPL 与完整 U-Boot B 槽。完整工厂镜像已逐区核对，未整卡烧录。eMMC、SPI NOR 的物理写入、掉电行为仍需对应实物验证。
