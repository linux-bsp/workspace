# EDK 与 Device Manager 仓库合并验收

## 合并结果

以 EDK 为基础，将 Device Manager 完整文件树导入 `edk/device-manager/`，
保留两边的 Git 历史。该目录是普通源码目录，不包含嵌套 Git 仓库。
workspace 移除独立的 device-manager gitlink；libbmc 保持原提交和独立仓库。
旧源码归档及本地构建副本保存在本次 `output/ota-validation/` 审计目录。

本次不调整管理模块内部目录，不改变固件、日志、时间服务的运行职责。
后续再分别将这些功能整理为 EDK 子模块。

EDK 增加 `manager-host`、`manager-device`、`manager-test` 构建入口。
Buildroot 保留可分别选择的外设、设备工具、主机工具包，从同一 EDK 仓库取源码。
修正测试和文档中的旧路径，并排除源目录内已生成的二进制和对象文件。

模块说明见 [EDK 集成文档](../../edk/docs/device-manager-integration.md)。

## 验证

- EDK 配置、增量构建、SDK 安装与外部消费者回归通过。
- PDI ELF 依赖与 72 个公开函数导出检查通过。
- 管理模块完整回归通过：40 组 Python unittest，共 362 项；默认跳过的真实
  固件包 CLI 用例已使用本次固件另行通过。另包含 C 引擎和前端测试。
- BSP 的恢复、实际 FIT、存储身份与 Linux/U-Boot 元数据互读测试通过。
- 实际发布 initramfs 中的 ARM64 fwctl/BusyBox 动态加载与缺库回归通过。
- 启动缓存 ABI 的 4 项测试通过。
- 迁移前后 131 个管理模块生产 C 源码及头文件逐字节一致。
- host-device-manager 和目标设备工具均由新路径重新构建，完成 AM625 全镜像构建。

## 实机发布

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
