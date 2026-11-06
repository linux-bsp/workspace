# 构建框架优化验收

固件 tag 固定 v0.0.1。每阶段先完成构建、OTA 与实机确认，再提交推送。

## 阶段 1：完整安装与全新配置

- 服务 unit、启动脚本、按需 preset 和安装清单统一由 EDK CMake 管理。
- 补齐 timectld-start；板级门禁检查目标根目录内的命令、解释器、权限、软链接和 ELF 依赖。
- 修复 Make 包装层在外部配置种子读取前要求 .config 存在的问题。
- 移除旧配置脚本和重复 Buildroot 包骨架，使用隔离目录的配置矩阵。
- EDK Host/Target 包从空包目录构建，完整板卡镜像、9 个配置、SDK 回归、
  41 项管理 CTest、空目录安装及缺文件/权限/链接/动态库反例全部通过。
- 实际 ARM64 initramfs 加载器测试通过，不仅检查依赖文件存在。
- 发布审计编号 95；固件 ID `3de3a1fa6186a09b877af99bf58cbf02f6443277127987de3fe3222279f0947e`。
- 设备 192.168.10.211 重启后上报 success，启动 ID `cb810875-e19e-4b46-9ab6-58146d96a0b4`。
- systemd 无失败服务，六个管理/健康服务 active；双 rootfs、实际 kernel/rootfs SHA256、
  持久日志、SOL 和 UTC+8 时间同步通过。未更新或验证引导程序。

证据与精确源码快照：`output/ota-validation/0.0.1-build-refactor-s1/`。
