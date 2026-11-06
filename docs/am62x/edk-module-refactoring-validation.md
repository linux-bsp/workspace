# EDK 管理模块分阶段重构验收

当前设计见 [EDK 架构](../../edk/docs/architecture.md)。本文记录已经完成的分阶段验收。
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

## 阶段 4：日志与时间模块

- logctl/logctld、timectl/timectld 分别迁到 `user/logctl/`、`user/timectl/`，
  使用 EDK Kconfig/CMake，daemon 命令通过别名运行相同程序。
- 时间源契约迁到 `protocol/management/`，解除时间工具对 OTA 目录的依赖。
- 管理完整回归、SDK 构建回归、实际 initramfs 动态加载验证通过。
- CMake 原生产物的日志、启动记录、时间同步/源配置/服务共 46 项测试通过。
- 独立日志 ARM64 配置无 fwctl/HWID 环境库依赖；别名删除重建不重新链接，
  按组件安装保留别名链接；host 管理服务重新构建并重载。
- 发布 ID：`870e576bbfd5c94789df9d8d0d4085965816817d36a69c3d465266f1341f6a49`。
- 发布审计编号 92，设备 192.168.10.211 上报 success。
- 启动 ID：`c691cb2b-dcee-40d0-8a92-8073f5c9b8bb`。
- 实机服务、健康、双 rootfs 和当前镜像校验、持久日志、SOL、UTC+8 均通过。
- 本阶段未更新 SPL/U-Boot。

证据：`output/ota-validation/0.0.1-edk-refactor-s4/`。

## 阶段 5：主机服务与协议边界

- 主机工具迁到 `host/device-manager/`，HTTP、OTA、SOL、时间、设备与审计
  分别组织为私有对象目标，仍生成一个 device-server。
- Web 资源在构建目录生成，HWID 映射归属 `configs/`，服务模板迁到 `integration/`。
- 报告编解码、值校验进入纯协议目标；文件清单/进程适配进入 fwctl 私有层。
  fwctld 不再引用服务器头文件，server 二进制无 libcurl/libubootenv 依赖。
- 本机与 ARM64 构建、SDK 回归、40 组 362 项管理测试通过；服务端回归直接
  运行 CMake 产物。实际固件包 CLI 和 initramfs ARM64 加载验证通过。
- 发布 ID：`cc53966b96817f753128235a5b40257ebff3c1224f1337497b211726d35b56a1`。
- 发布审计编号 93，设备 192.168.10.211 上报 success。
- 启动 ID：`9004ec40-799b-47ac-82ae-23a707987dad`。
- 实机服务、健康确认、双 rootfs 与当前镜像校验、持久日志、SOL、UTC+8 通过。
- 本阶段未更新 SPL/U-Boot。

证据：`output/ota-validation/0.0.1-edk-refactor-s5/`。

## 阶段 6：统一配置、安装和回归入口

- Buildroot 收敛为 edk、host-edk，删除旧 device-manager 包定义和组件递归 Makefile。
  板级组件选项生成单一 Kconfig 输入，内核依赖仅由 PDM 引入。
- 同一源码树分别输出 host/target；staging 只安装公共库和可选 SDK 头文件。
  根 Make 支持单独工具目标，libs 仅构建库；源码目录不再产生工具和 Web 头。
- 统一原生回归注册 41 个 CTest 项：38 项首次通过，3 项旧源码程序路径修正后
  重跑通过，无剩余失败。测试支持完整 Python 和显式构建产物，失败可单独重跑。
- SDK 配置/增量/安装消费、配置映射稳定性、新克隆 defconfig、库单独构建、
  日志与服务器依赖隔离、BSP FIT/身份/恢复、实际 initramfs ARM64 加载均通过。
- 发布 ID：`2868a46343897abc3606cbfdb174eee3dc40181f369398ff730beadfd416b2f0`。
- 发布审计编号 94，设备 192.168.10.211 上报 success。
- 启动 ID：`a752f496-aa44-45a5-9c45-b7cf98aec2db`。
- 实机 systemd 无失败服务，固件/日志/时间/健康服务 active，PDM active；两个
  rootfs 槽和当前 kernel/rootfs 完整 SHA256 验证通过。
- 日志持久化、SOL、UTC+8 同步和命令别名正常；HWID 为 1010001000110000。
- 本阶段未更新 SPL/U-Boot。libbmc 保持独立，提交 abcd362 未改变。

证据：`output/ota-validation/0.0.1-edk-refactor-s6/`，包含源码快照、验证脚本、
固件包、服务器结果、串口日志和提交检查。服务重载辅助脚本的进程退出竞态已
修复；首次未重启成功时尚未发布固件，相关重载/串口记录保留用于追溯。

## 后续整理：外设协议归位与模拟器移除（2026-11-06）

- MCU、电源报文定义迁入 `kernel/pdm/drivers/mcu/`、`kernel/pdm/drivers/power/`，
  作为对应驱动的私有头文件；Satellite 协议原本就在内核驱动内。
- OTA 报告和时间源等用户态共享协议迁到 `user/protocol/`；移除顶层 `protocol/`。
  UAPI 保持独立，报文字段、CRC 和用户态管理协议内容没有改变。
- 删除独立 CAN 模拟器源码、Kconfig/CMake 入口、三个预设中的选项，以及
  pdebug 帮助和现行文档中的模拟器操作步骤。保留协议固定向量和事务回归测试。
- SDK CI 16 项、管理端 CI 47 项全部通过，实际 ARM64 initramfs 加载检查通过。
  从干净 EDK/host-edk 包目录重新构建，并完成 AM625 镜像打包。
- 清除本机构建输出中此前安装的模拟器；最终 squashfs 和实机均确认没有
  `/usr/bin/simulator`，pdebug、PDM 和管理工具正常保留。无运行时兼容或清理脚本。
- 发布 ID：`0ba0e3a81eee82e2c82b3456e8a811c28e5229cce5f07afa6ec831ccdd29196c`。
- 固件 tag：`v0.0.1`；发布审计编号 99，设备 `192.168.10.211` 上报 `success`。
- 启动 ID：`c5d069b0-111e-41f9-a6bb-af66375890ec`。
- 实机无失败服务，固件健康确认成功；双 rootfs 与当前 kernel/rootfs 完整哈希
  校验、日志持久化、SOL、UTC+8 同步通过。PDM 三个外设节点正常绑定，pdebug
  可查询，帮助信息没有已移除的模拟器命令。
- 本次验证不包含真实 MCU/卫星平台对端的 CAN 互操作；未更新 SPL/U-Boot。
- EDK 提交：`ee31b637`，在实机确认和源码快照检查通过后提交并推送。

证据：`output/ota-validation/0.0.1-kernel-protocol-cleanup/`，包含测试结果、
镜像文件清单、完整源码快照、构建来源、发布记录和串口验收日志。

## 后续整理：内核与用户态目录收敛（2026-11-06）

- 用户态公共库统一进入 `user/lib/`，命令、守护进程和 Device Manager 进入
  `user/apps/`，systemd 服务及部署脚本进入 `user/integration/`。
  顶层不再保留 `apps/`、`host/`、`integration/`；UAPI 迁入
  `kernel/include/uapi/`，六个头文件内容逐字节不变。
- fwctld 与服务端共用的 OTA 文件适配代码迁入 `user/lib/ota/`，消除服务端
  对 fwctl 应用目录的依赖。根 CMake/Kconfig 统一经 `user/` 组织子模块，
  同步更新 Buildroot 验证脚本、测试和现行文档。清理未使用的 HTTP 导出文件。
- SDK 17 项、管理端 47 项 CTest 通过；时间持久化测试的数据迁到构建目录，
  避免临时文件污染源码记录，也避免本机 tmpfs 被误当作持久存储。
  公共库依赖检查区分生产库与集成测试驱动。
- 初版 `012476dd` 首次启动遇到 metadata 共享读锁与 `mark-good` 的竞争，
  确认失败触发一次重启，第二次启动成功。该版本未作为最终验收提交。
  已为健康确认补充有上限的重试，并在重试前复查健康；永久错误、持续占锁
  以及健康恶化仍拒绝确认。四个新增服务回归及 CLI 错误分类测试通过。
- 最终实机主动持有存储只读锁：uptime 36 秒加锁，41 秒确认进入重试，
  48 秒释放，49 秒确认成功。此次 OTA 只有一次启动，没有额外重启。
- 完整 AM625 镜像、实际 ARM64 initramfs 加载及源码来源一致性检查通过。
  发布 ID：`655ecded0519e336918b787eadbec80cbdd3c831ccebaba4f3fb89dc2633885c`，
  tag 保持 `v0.0.1`；发布审计编号 101，设备 192.168.10.211 上报 success。
- 启动 ID：`3dbc3731-18ff-4ea0-9d43-e82cac41c550`。运行 deployment 1，
  kernel/rootfs 使用 B 槽，confirmed=1；systemd 无失败单元，六个管理/健康
  服务 active。双 rootfs 槽、当前 kernel/rootfs 完整 SHA256、日志持久化、
  SOL 归档确认及 UTC+8 校时通过。本次未更新 SPL/U-Boot。
- 验收后提交：EDK `1b4057aa`，BSP 引用调整 `5166b3b`；均已推送远程。

初次构建与问题证据：`output/ota-validation/0.0.1-userspace-layout/`；
最终源码快照、发布、实机验收和锁竞争验证：
`output/ota-validation/0.0.1-userspace-layout-confirmation/`。

## 完成状态

| 阶段 | 固件 tag | 内容 ID 前缀 | 实机结果 |
| --- | --- | --- | --- |
| 1 配置依赖图 | v0.0.1 | e50db961 | success |
| 2 传输与 HWID | v0.0.1 | 1c04ca18 | success |
| 3 固件模块 | v0.0.1 | 74397335 | success |
| 4 日志与时间 | v0.0.1 | 870e576b | success |
| 5 服务端与协议 | v0.0.1 | cc53966b | success |
| 6 构建配置统一 | v0.0.1 | 2868a463 | success |
| 协议归位与模拟器移除 | v0.0.1 | 0ba0e3a8 | success |
| 内核/用户态目录收敛与确认锁重试 | v0.0.1 | 655ecded | success |

每阶段均先构建、发布并完成实机健康确认，再提交与推送子仓库，最后更新
workspace gitlink。最新使用方法见 [EDK README](../../edk/README.md)。
