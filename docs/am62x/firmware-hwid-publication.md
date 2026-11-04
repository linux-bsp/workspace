# 固件包声明适用 HWID 与自动发布

## 唯一来源

适用设备在构建时写入 FIT 的 `fw,hwids` 字符串列表，属于固件包的一部分。上传后 Device Manager 校验并解析声明，将其保存在数据库中；页面只读展示，发布接口和 ota-cli 不接受人工指定 HWID。

例如本板固件声明：

```dts
fw,hwids = "1010001000110000";
```

支持多种硬件时，构建者可以声明多个完整 HWID。release、kernel、rootfs 必须共同支持 release 声明的全部值，否则拒绝上传。

AM625 统一修改 [firmware.json](../../bsp-base-external/board/ti/am625/firmware.json)：

```json
{
    "hwids": ["1010001000110000"]
}
```

四份 FIT 模板只保留 `@FW_HWIDS@` 占位符。镜像构建时读取一次公共配置，统一填入 release、bootloader、kernel、rootfs；配置或模板不完整时直接失败。修改列表后运行原输出目录的 `make all` 重新打包。`images/firmware.json` 留存本次构建实际使用的配置。

公共配置阶段已发布 `v0.0.1 / 64373f72` 并通过 AM625 实机健康确认，见 [验证记录](../../bsp-base-external/board/ti/am625/releases/v0.0.1-64373f72.md)。

设备自身的 HWID 仍来自 U-Boot 环境；服务器不能通过发布改变设备身份。设备下载后、写入前及启动时继续进行精确匹配。

## 使用流程

1. 选择并上传固件包，服务端校验后保存草稿。
2. 详情页展示固件版本、内容 ID 和固定的适用 HWID 列表。
3. 点击“发布到设备”，自动发布到包内声明的全部 HWID。
4. 每个 HWID 同时只有一个当前发布版本；包外的其他硬件通道不变。

```sh
ota-cli --server http://127.0.0.1:8090 upload firmware.tar.gz
ota-cli --server http://127.0.0.1:8090 publish draft-XXXXXX
```

`POST /api/publish/draft-XXXXXX` 不接受 HWID 参数。旧的手选目标路径和 CLI 参数会被拒绝；请求头也不能覆盖固件声明。重复发布全部通道已使用的同一内容会返回已有记录。

每个适用 HWID 保留独立发布快照，供设备上报、审计及健康版本回退。多 HWID 的新快照共享此次新建的不可变载荷，避免重复占用固件存储；历史已发布载荷保持原状。准备全部文件及数据库身份后，通过 Linux 原子目录交换一起切换通道；准备或切换失败不产生部分通道已更新的状态。

## 产品名称

页面从 HWID 解析产品线、项目、产品型号和 PCB 版本。将来可以维护这些编码的中文名称字典，供显示与查询使用；字典不决定固件适配范围，也不能替代包内 HWID 校验。

## 2026-11-04 验证

- 17 项 HWID 通道及继承测试通过，覆盖自动多硬件发布、手选目标拒绝、整包幂等、失败不改变当前版本、隔离及各通道回退。
- OTA 全套测试通过，包括真实固件 CLI 上传、发布、下载及恢复路径验证；Chromium 实际上传/发布通过，页面没有 HWID 选择框。
- 实机验证固件保持 `v0.0.1`，内容 ID 为 `592352ec216af15908a342f8617e86ab8b4ce1cbbba96077a79aaf7fcd293a0a`。使用无 HWID 参数的 ota-cli 发布，AM625 完成自动下载、安装、重启和健康确认，服务端收到成功上报。
- 本次未更改设备端 OTA 协议和环境身份。原健康 B 槽保留；新的 kernel/rootfs 写入 A 槽。未重新烧写引导程序。

构建、测试、成功上报、完整串口日志及源码审计产物保存在 `output/ota-validation/0.0.1-package-hwids/`。
