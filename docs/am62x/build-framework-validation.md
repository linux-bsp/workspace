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

## 阶段 2：有效构建类型

- 显式 CMAKE_BUILD_TYPE 在 Kconfig 默认值计算前应用；类型切换通过最小配置
  重新推导默认值，保留非默认功能选择。
- effective-config.json 与 build-info.json 保存实际构建类型和归一化配置。
- Debug/Release 来回切换、FORTIFY、PDI 功能保留、SDK 消费与配置映射回归通过。
- 原生安装/固件/时间回归、Host/Target 包、完整板卡镜像和 ARM64 加载器通过。
- 发布审计编号 96；固件 ID `850c9bf97e9941b82e31d9a324a83856acd57ac50733b0130e636db07b1ddc88`。
- 设备 192.168.10.211 上报 success；启动 ID `d147ccc2-3ad4-43ca-8616-3f010444efe8`。
- systemd、双 rootfs、实际负载 SHA256、持久日志、SOL 和 UTC+8 校时通过。
  本阶段未更新引导程序。

证据：`output/ota-validation/0.0.1-build-refactor-s2/`。

## 阶段 3：可复现发布与完整来源

- AM625 启用可复现文件系统时间；FIT 构建时间统一使用 SOURCE_DATE_EPOCH。
- 完整发布包在私有目录生成验证后原子交换；失败保留上次有效 OTA 包。
- build-manifest.json 记录全部仓库、未提交改动、配置、工具与 Host/Target 编译来源；
  编译来源与打包时 EDK 源码摘要一致。Host 来源不再为 unknown。
- 固定输入/时间的真实 FIT 回归、失败保留反例、SDK 与源码摘要回归通过。
- 两次完整镜像生成的四个 ITB 及完整内容 ID 逐字节一致，保留 first/repeat-hashes.json。
  此结果不代表工厂 ext4/SD UUID 或跨机器全量工具链重建已可复现。
- 发布审计编号 97；固件 ID `22e1f15e87e15c53ab0485d2ed444583c0f0dae1262b0724005dbf4a69fd81f2`。
- 设备 192.168.10.211 上报 success，启动 ID `462b6fc6-08e0-4981-b7cd-9deef09f6f67`。
- systemd、双 rootfs、实际负载 SHA256、持久日志、SOL、UTC+8 与 ARM64 加载器通过。
  本阶段未更新引导程序。

证据：`output/ota-validation/0.0.1-build-refactor-s3/`。

## 阶段 4：统一验证、编译边界与增量构建

- 构建框架、配置映射、源码来源、配置矩阵、安装与编译依赖检查接入 CTest。
- 增加 SDK/管理测试预设及可独立选择的 CI 脚本，原生依赖通过环境或用户预设指定。
- 固件与服务器生产 C 源码显式列出；OTA、日志和时间的编译 include 边界受回归约束。
- Make 对不变输入跳过显式配置；构建来源独立刷新，直接 cmake --build 仍保留
  配置时的来源与时间输入。Buildroot 显式传递任务预算。
- 工具链文件内容、实际编译器版本及 sysroot/架构指纹变化要求新输出目录。
- 管理构建 47 项 CTest、SDK CI 16 项、新管理预设 3 项检查通过；新增直接构建来源
  保留、同路径工具链变更拒绝、空构建不配置/不重链接的 SDK 回归通过。
- Host/Target 包、完整板卡镜像、安装 ELF 检查和实际 ARM64 加载器通过；
  打包清单与两个编译来源一致。主机 8090/8091 服务已备份数据库并重载验证。
- 发布审计编号 98；固件 ID `24f1938afb4e72e3b6b23bd68cc766c3178c3858cf6ef97a1068e230def8f65f`。
- 设备 192.168.10.211 上报 success；启动 ID `506bdcfb-0930-4add-a9cf-96588fe587ed`。
- systemd、双 rootfs、实际负载 SHA256、持久日志、SOL 和 UTC+8 均通过。
  本阶段未更新或验证引导程序。

证据：`output/ota-validation/0.0.1-build-refactor-s4/`。

## 完成状态

| 阶段 | 固件 tag | 内容 ID 前缀 | 实机结果 |
| --- | --- | --- | --- |
| 1 完整安装 | v0.0.1 | 3de3a1fa | success |
| 2 有效配置 | v0.0.1 | 850c9bf9 | success |
| 3 可复现发布 | v0.0.1 | 22e1f15e | success |
| 4 构建验证与增量 | v0.0.1 | 24f1938a | success |

各阶段均完成源码快照与硬件确认后提交子仓库，再更新并推送 workspace 引用。
