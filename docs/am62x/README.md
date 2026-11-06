# AM625 文档索引

## 当前使用

- [工作区拉取和构建](../../README.md)
- [固件升级、槽位与恢复操作](firmware-upgrade-guide.md)
- [固件包 HWID 与自动发布](firmware-hwid-publication.md)
- [HWID 编码规范](hwid-specification.md)
- [systemd 服务与健康检查](system-services.md)
- [可靠性与验证边界](reliability-boundaries.md)
- [TFTP 配置](tftp-server.md)、[电源串口连接](power-control.md)

固件生成和板级布局见 BSP 的
[板级说明](../../bsp-base-external/board/ti/am625/README.md)、
[initramfs 与 A/B 恢复](../../bsp-base-external/board/ti/am625/verified-boot.md)。
设备管理命令、SOL 和时间功能见 [EDK 文档索引](../../edk/docs/README.md)。

## 验证与溯源

- [构建框架优化验收](build-framework-validation.md)

- [当前 EDK 模块重构验收基线](edk-module-refactoring-validation.md)
- [固件下载、事务与恢复优化验证](firmware-upgrade-optimization-validation.md)
- [OTA 启动失败日志实机验证](ota-boot-failure-log-validation.md)
- [历史功能验收](validation-history.md)
- [板级历史发布](../../bsp-base-external/board/ti/am625/releases/README.md)
- [管理功能历史发布](../../edk/docs/device-manager/releases/README.md)

历史文档保留原始固件身份、启动记录和验证限制，命令可能反映旧目录。
当前使用以上述操作指南与源码配置为准。原始测试、串口及固件产物位于
各记录注明的 output/ota-validation 目录，生成文件不提交到 Git。
