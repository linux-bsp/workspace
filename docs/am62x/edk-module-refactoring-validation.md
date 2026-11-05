# EDK 管理模块分阶段重构验收

设计与实施顺序见 [EDK 重构计划](../../edk/docs/management-modules-refactoring.md)。
固件版本固定 v0.0.1；每阶段完成构建、发布和 AM625 健康确认后提交推送。

## 阶段 1：Kconfig 完整依赖图

- EDK 使用 Kconfig 生成的 source 依赖图，替代固定目录层级扫描。
- SDK 构建回归通过，覆盖深层配置新增、修改、删除及后续空构建。
- 12 项 CTest、AM625 EDK 交叉编译、完整板卡镜像构建通过。
- 发布 ID：`e50db961929f9441b6d1079933701530fd0e928ea980cc4ba1e44af627f60aef`。
- 发布审计编号 89，设备 192.168.10.211 上报 success。
- 启动 ID：`4763a4c9-520e-4dfe-945e-6d5592092c6c`。
- systemd 无失败单元；六个管理/健康服务 active；健康检查成功。
- 两个 rootfs 槽校验、当前 kernel/rootfs 实际长度与完整 SHA256 校验通过。
- 日志 persistent、sync-state=ok；SOL 恢复连接；时间同步正常，UTC+8。
- 本阶段未安装 SPL/U-Boot，不包含引导程序更新验证。

原始证据、发布包、源码快照和提交检查：
`output/ota-validation/0.0.1-edk-refactor-s1/`。

## 阶段 2：共享传输与 HWID

- 模块迁入 `edk/user/transfer/`、`edk/user/hwid/`，使用 Kconfig/CMake 选择。
- HWID 值解析不依赖 libubootenv；设备环境访问单独启用。
- 本机和 ARM64 静态库构建通过，ELF 架构分别为 x86-64、AArch64。
- CTest 运行 CMake 生成的传输驱动，17 项实际 HTTP/续传/落盘故障测试通过。
- 管理模块 40 组、362 项 unittest 与 SDK 构建回归通过。
- BSP 身份互读、FIT、存储身份和恢复回归通过；补齐三个板级验证脚本的旧路径。
  这些仅验证脚本的补充单独归档，运行代码与构建源码快照一致。
- 发布 ID：`1c04ca1851bdcb448f080b0f94a79a6e79d8c83da1080c870c5990aff2696832`。
- 发布审计编号 90，设备 192.168.10.211 上报 success。
- 启动 ID：`4b37a7fd-f26f-4852-967e-fa0ddc9cda02`。
- systemd、六个管理/健康服务、两个 rootfs 槽及当前镜像内容检查通过。
- 日志持久化、SOL 与 UTC+8 时间同步正常。本阶段未更新 SPL/U-Boot。

证据：`output/ota-validation/0.0.1-edk-refactor-s2/`。

## 阶段 3：固件模块与统一构建

- fwctl 的 CLI、事务、存储、恢复和健康检查整体迁到 `edk/user/fwctl/`；
  fwctld 源码位于该模块的 `agent/`，保留独立服务生命周期。
- Kconfig 自动选择传输/HWID 依赖；Buildroot 生成组件配置后通过 EDK CMake
  构建设备固件工具。本机与 ARM64 构建通过，补全静态环境库的 zlib 依赖。
- 44 个生产 C/头文件逐字节保持一致。SDK 回归、管理模块完整回归、传输
  CTest、实际包 CLI、BSP FIT/身份/恢复回归通过。
- 实际 initramfs ARM64 动态加载器执行、fwctl/BusyBox 依赖与缺库反例通过。
- 发布 ID：`74397335485e81ffd3e2eaf96bac945a1bed9d0bab07ce56def94894362a6328`。
- 发布审计编号 91，设备 192.168.10.211 上报 success。
- 启动 ID：`37da09de-810f-4576-b5ed-30a67c7afcd0`。
- systemd、管理/健康服务、rootfs 双槽及当前镜像 SHA256 校验通过。
- 日志持久化、SOL、UTC+8 同步正常；本阶段未更新 SPL/U-Boot。

证据：`output/ota-validation/0.0.1-edk-refactor-s3/`。
