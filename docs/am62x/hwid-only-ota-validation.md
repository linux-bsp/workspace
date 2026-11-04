# AM625 按 HWID 发布 OTA 验证

验证日期：2026-11-04。设备：`192.168.10.211`，MAC `1c:63:49:22:c4:f7`。

## 当前身份与显示规则

设备 HWID 为 `1010001000110000`，分段显示 `1-01-0001-0001-10-000`：编码版本 1、产品线 01、项目 0001、产品型号 0001、PCB V1.0、保留字段 000。

OTA API、设备上报、运行配置和新生成的 FIT 已移除独立的 `product`、`layout` 身份字段。页面产品列、固件详情和设备详情只从 HWID 解析产品信息；不维护第二套产品身份。物理分区偏移和容量仍由 BSP 指定。

规范见 [HWID 使用说明](../../device-manager/docs/hwid.md)。普通 OTA 不修改环境变量中的 HWID。

## 发布与校验

- 每个完整 HWID 同时只有一个当前发布版本，各 HWID 通道相互独立。
- 上传包从 FIT 读取适用 HWID；release、kernel、rootfs 必须共同支持全部声明值。
- 发布必须选择声明中的目标 HWID。查询、下载、结果上报及恢复均绑定该身份；其他 HWID 的请求被拒绝。
- 设备仍使用完整软件版本和 SHA256 内容 ID 判断是否需要升级；日志显示哈希前八位。
- 同一异常内容被隔离后，停止所有受影响通道；各通道仅回退到自身已健康确认的兼容固件。

```sh
ota-cli --server http://127.0.0.1:8090 upload firmware.tar.gz
ota-cli --server http://127.0.0.1:8090 publish draft-XXXXXX --hwid 1010001000110000
```

## 本次实机结果

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

## 自动化与历史数据

OTA 全套测试通过，包括 14 项 HWID 通道及继承测试、15 项 catalog 测试、浏览器实际上传/发布、跨 HWID 拒绝、异常隔离和中断恢复。固件引擎 5 项测试及新生成 FIT 的 3 项完整性/恢复集成测试通过。

旧服务停止后离线迁移了 manifest、上报、审计及请求数据库；94 份 manifest、170 条历史事件和 19 份审计/隔离记录保留。原始 feed 留存于 `output/ota-validation/feed-before-hwid-only-20261104/`，历史 FIT 字节和内容 ID 未修改。未声明 HWID 的旧固件可下载归档，禁止重新发布。产品代码不包含旧协议兼容分支。

本次构建、测试日志、两次成功快照、完整串口日志和源码快照位于 `output/ota-validation/0.0.1-hwid-only/`，均为本地审计产物，不提交到 Git。
