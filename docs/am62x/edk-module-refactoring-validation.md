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

## OSA 整合阶段 1：公共 IPC 与截止时间（2026-11-06）

- 删除 fwctl 内复制的 peripheral_ipc 实现，改用 OSA 公共头文件与同一组
  IPC 对象文件。libosa 和 fwctl 共用源码；initramfs 不新增 libosa.so 依赖。
- 提取 osa_wait_fd，有限超时采用 CLOCK_MONOTONIC 截止时间，信号打断后
  只等待剩余时间。保留已排队数据优先于对端关闭的语义。
- 新增连续信号干扰回归：旧实现把 100 ms 等待延长到收到 400 ms 后的数据，
  新实现按时返回 ETIMEDOUT。原有 systemd 与 SysV 健康协议行为保持不变。
- SDK 17 项、管理端 49 项 CTest 和真实固件包上传发布回归通过；FIT 4 项、
  恢复 6 项、ARM64 存储身份 7 项及实际 initramfs 加载检查通过。
  同步修正三个 BSP 验证脚本遗留的用户态目录引用。
- 发布 ID：989e81ba34af9f60a788fb6db55dd94bb86035f7ed382e8866dd14295f2692b9，
  tag 为 v0.0.1；发布审计编号 102，设备 192.168.10.211 上报 success。
- 启动 ID：6fa58fde-b9d1-4a14-8d61-5c21f4fdde80。实机无失败服务；双 rootfs
  槽、当前 kernel/rootfs 全量校验、日志持久化与归档、UTC+8 校时通过。
  未更新 SPL/U-Boot；SysV IPC 路径由本机协议回归验证，实机运行 systemd。

证据：`output/ota-validation/0.0.1-osa-ipc/`，包含源码快照、测试、固件包、
OTA 成功记录、串口验收及提交记录。

## OSA 整合阶段 2：公共日志与 OTA 输出适配（2026-11-06）

- OSA 提供公共 va_list 日志入口及可替换输出回调。fwctld 共用日志对象实现，
  删除私有格式化逻辑；libosa 仍向 PDI 等使用者提供同一实现。
- 普通日志统一为 `[模块] [级别] 内容`，DEBUG 才附带源码位置。INFO/DEBUG
  使用单调时钟限流，WARN/ERROR/FATAL 不占该预算；日志保留调用者 errno。
  格式化与输出移出策略锁，输出回调可以安全查询日志统计。
- 保留 fwctld 非阻塞串口镜像及子进程 stdout/stderr 实时转发；已带 fwctl
  前缀的记录原样输出。SOL 原始字节与机器可读命令输出不经过日志格式化。
- 新增日志限流、错误保留、回调重入查询、长消息边界、errno 与串口阻塞回归；
  SDK 18 项、管理端 50 项 CTest 全部通过。扩展 OSA 动态库公共符号/依赖检查。
  最终 FIT 4 项、实际 ARM64 initramfs 加载及真实固件包上传发布检查通过。
- 发布 ID：94ef26aa21f0b924881aeee5db858a5376a5c302ec5bc6ecd811a949d0e39016，
  tag 为 v0.0.1；发布审计编号 103，设备 192.168.10.211 上报 success。
- 启动 ID：3a9fc411-9000-4863-a3b1-199964033bcf。实机无失败服务，双 rootfs
  槽及当前 kernel/rootfs 全量校验通过，日志持久化、SOL 归档、UTC+8 校时正常。
  新 fwctld 启动与缓存回收日志格式正确；未更新 SPL/U-Boot。

证据：`output/ota-validation/0.0.1-osa-logging/`。fwctl/fwctld 未新增 libosa.so
或 libpdi.so 运行时依赖。此次统一公共日志能力和 OTA 适配；日志/时间工具的
其他输出入口与服务端公共依赖仍需按职责分别梳理，不表示所有 POSIX 调用都
应封装进 OSA。

## OSA 整合阶段 3：用户态日志入口统一（2026-11-06）

- fwctl/fwctld、logctl/logctld、timectl/timectld、Device Manager/ota-cli 及
  外设应用的运行诊断统一调用 OSA。日志格式、等级、限流和输出回调由 OSA
  管理；新增显式 FILE 输出入口，保留人类可读 CLI 结果原有的 stdout 通道。
- logctld 负责采集、持久化、归档和转发，其自身诊断输出到 stderr，避免
  回灌采集入口。timectld 保留时间源、校时和 RTC 职责，使用 OSA 记录日志。
  OSA 不依赖这两个守护进程，也不依赖可用网络或管理服务器。
- initramfs 使用 OSA 回调接入原有控制台和启动日志保存路径。SOL 原始串口
  字节、遥测数据、CLI 机器协议及 HTTP 响应不经过日志格式化；内核 PDM
  继续使用内核日志接口。fwctl/fwctld/logctl/timectl 未新增 libosa.so 或
  libpdi.so 运行时依赖。
- SDK 18 项、管理端 50 项 CTest 全部通过；完整 AM625 镜像、FIT 4 项、
  恢复 6 项、真实固件包上传发布和实际 ARM64 initramfs 加载验证通过。
  首轮发现的独立测试链接遗漏和服务启动消息解析假设均已修复并重新验证，
  初次失败记录保留。Device Manager 服务已使用新产物重载。
- 发布 ID：`4a31f6d8a75c5764a106af46008a07f2121e264b6ba07d149da4b788c93babd2`，
  tag 保持 `v0.0.1`；发布审计编号 104，设备 `192.168.10.211` 上报 `success`。
- 启动 ID：`cc716efb-348c-46e6-bca7-6c09ae53b2f2`。运行 deployment 0，
  kernel/rootfs 使用 A 槽；实机无失败服务，六个管理/健康服务正常，健康检查、
  双 rootfs 槽和当前 kernel/rootfs 完整 SHA256 校验通过。
- 日志持久化、上一启动记录读取、SOL 连接、启动缓冲归档确认及 UTC+8 校时
  均通过；串口确认 OSA 日志格式正常。本阶段未更新 SPL/U-Boot。

证据：`output/ota-validation/0.0.1-osa-all-logs/`，包含源码快照、构建和测试
记录、固件包、OTA 成功记录、串口验收与提交记录。

## 抽象分层与解耦：执行顺序（2026-11-06）

每个阶段独立构建、保留源码与固件快照、发布 v0.0.1、新 hash 的固件，经 AM625
重启和健康确认后提交推送，再进入下一阶段。功能协议与存储格式保持不变。

1. OSA 边界：服务健康协议移出通用 IPC；抽取有截止时间、取消和子进程回收的
   执行接口，替换 OTA 与健康查询中重复的执行逻辑。
2. 持久化基础能力：统一小文件原子替换和同步语义，接入 OTA 事务、日志归档
   与时间配置；业务层保留重试、保留期和断电恢复策略。
3. 固件模块：通过类型化的 fwctl 客户端适配器隔离 CLI 协议解析；启动日志证据
   由日志模块提供接口，OTA 不再直接理解日志目录和内部文件。
4. 服务端：提取公共设备访问策略，时间服务不再依赖 SOL；将跨模块业务动作
   从存储层移至明确的应用编排层。
5. 应用内部：明确日志采集和时间服务的运行上下文，拆分入口、策略和平台操作；
   评估外设应用与 MCU 驱动的职责边界，避免为了形式统一增加新的 IPC。

## 分层优化阶段 1：OSA IPC 与进程执行边界

- OSA 保留通用消息传输，健康协议定义归入用户态 protocol，服务通知归入
  service 库；保持原有线格式。libosa 因删除业务 API 升级 SONAME 至 2，
  外设应用同步重建；fwctl/initramfs 未新增 libosa 或 libpdi 动态库依赖。
- OTA 命令与 systemd 健康查询使用公共有限时执行接口，覆盖取消、输出溢出、
  信号中断、子进程退出与进程组清理。不可中断 I/O 中未回收的子进程保留在
  上下文内，并拒绝再次启动，避免无限堆积；不宣称 SIGKILL 能终止 D 状态。
- SDK 19 项、管理端 50 项、实际包上传发布下载、FIT 4 项、恢复 6 项及
  ARM64 initramfs 动态加载验证通过。初次测试 fixture 依赖遗漏已修正。
- 发布 ID：`daa25df8dbd2f5d0f62b9bb540d4f2f258d4525a5dcd0714abdd1f35f86a6fd4`，
  tag `v0.0.1`，审计编号 105；设备 192.168.10.211 上报 success。
- 启动 ID `a7951484-43cf-4a8d-822c-c4e998131d00`：零失败服务、六个管理服务、
  本地健康、双 rootfs 槽、当前 kernel/rootfs 全量 SHA256、持久日志、启动
  缓冲归档和 UTC+8 校时均通过。未更新 SPL/U-Boot；SysV 路径由本机测试验证。

证据：`output/ota-validation/0.0.1-layering-s1/`。

## 分层优化阶段 2：小文件持久化接口

- OSA 新增小文件原子替换接口，OTA 本地事务、日志归档回执、时间源配置共同
  使用临时文件、文件同步、重命名、目录同步流程。失败后仅清理本次创建的
  临时文件；中断残留不被当作已提交的归档内容。
- 故障回归验证写入中断、短写、同步失败、可见但未确认持久化的新文件、
  符号链接拒绝和并发替换；业务事务格式、保留期和断电恢复顺序保持不变。
- SDK 20 项、管理端 50 项、真实包上传发布下载、FIT 4 项及 ARM64 initramfs
  加载检查通过。硬件保存时间源配置成功，内容保持原值。
- 发布 ID `dd3049bf0bf180401689e9c9d1b987f5f0d24e095b199a84b3e75bf63623288a`，tag v0.0.1，审计编号 106，上报 success。
  启动 ID `c19b931d-13db-4a7d-9660-d4da4c8b20b5`；服务健康、双 rootfs 槽、当前 kernel/rootfs 全量
  校验、持久日志、SOL 归档和 UTC+8 校时均通过。未更新 SPL/U-Boot。

证据：`output/ota-validation/0.0.1-layering-s2/`。

## 分层优化阶段 3：固件客户端与日志证据边界

- fwctl 内部拆成事务/存储 engine、健康 health、早期启动 init 构建目标。
  OTA 通过 client 类型化适配器读取状态、比较镜像；整数溢出、未知状态、
  非法 hash、额外字段均被拒绝，解析失败不留下半份状态。保留子进程隔离、
  截止时间与停止信号取消。
- 日志/崩溃文件扫描归 logctl，通过 diagnostic-reason 输出 DMEVIDENCE1；
  OTA 只接受已知原因，查询缺失、超时或错误不会伪造原因或修改原失败记录。
- SDK 20 项、管理 51 项最终通过；首轮对象链接依赖和日志命令测试桩问题
  已修正，失败记录保留，受影响回归重新通过。FIT 4 项、恢复 6 项、ARM64
  initramfs 加载、真实固件包上传发布下载均通过。
- 发布 ID `83649a99e8f0330cf045e338374e30cb42a53253789a331fff2acb953cd5130f`，tag v0.0.1，审计编号 107，设备上报 success。
  启动 ID `37dbb228-e779-4e62-8411-afcce2f8a5f2`。零失败服务、双 rootfs 槽、当前镜像全量校验、
  持久日志与校时通过；实机新证据接口正常返回，无异常原因。未更新 SPL/U-Boot。

证据：`output/ota-validation/0.0.1-layering-s3/`。


## 分层优化阶段 4：服务端访问策略与 OTA 编排

- 提取公共 access 模块，时间控制不再依赖 SOL；设备访问密钥格式和已授权的
  无凭据调试模式保持不变。鉴权准备不再隐式初始化 SOL 数据库。
- OTA 上报接收在应用层编排历史写入、异常隔离和设备状态保存，全部完成后才
  确认请求；存储层不再触发隔离发布。恢复镜像选择与最后正常版本选择归入 OTA。
- SDK 20 项通过；管理端 51 项通过，其中 SOL bundle fixture 原先假设鉴权
  会创建数据库，已改为等待其所属模块建表并单独重测通过。实际包上传发布下载、
  FIT 4 项、ARM64 initramfs 加载通过；访问边界回归覆盖独立编译依赖。
- 发布 ID `667ba9330cecc1eb7b4591eed70bf5e4445983e3a11ca316d3b927638c9c2e1b`，
  tag v0.0.1，审计编号 108，AM625 上报 success。
- 启动 ID `d89eea6a-d0aa-4a30-9321-766e37412a77`；零失败服务、管理服务健康、
  双 rootfs 槽、当前固件全量校验、持久日志及 UTC+8 校时通过。未更新 SPL/U-Boot。

证据：`output/ota-validation/0.0.1-layering-s4/`。审计查询仍可只读关联固件目录，
本阶段约束的是跨模块写入和发布副作用，并未宣称所有查询已完全独立。

## 分层优化阶段 5：日志与时间运行上下文

- 将 logctl 命令入口与采集循环分开；私有上下文持有采集游标、同步序列、
  路径、保留限额和错误状态，退出时关闭采集描述符。原始日志字节、归档格式、
  确认后清理和持久化策略保持不变。
- timectld 由入口持有配置和采样上下文，重试、时间锚点、RTC 状态与取消
  不再使用模块可变全局变量。保留独立守护进程、唯一设时锁、UTC+8 显示。
- 同一进程内双实例回归验证独立时间源、取消传播和日志写入目录；SDK 20 项、
  管理端原有 51 项通过，新增上下文测试及最终日志/时间/边界回归全部通过，
  共 52 项管理/构建测试。真实包上传发布下载、FIT 4 项及 ARM64 initramfs
  加载检查通过；构建目录生产源码与归档源码逐项匹配。
- 发布 ID `fa43a1f28b0542e1a86d3fa9247fef31485eef1d6f7d900bf95903580e80d18e`，
  tag v0.0.1，审计编号 109，AM625 上报 success；启动 ID `f2d3cc17-1a5e-40dc-9214-557fd2c9fe6e`。
- 实机零失败服务、六个管理服务健康、双 rootfs 槽、当前固件全量校验、持久
  日志、上一启动归档与 UTC+8 校时通过。额外重启 logctld/timectld 后 PID
  正常变化，日志序号从 359 继续至 707，新写入标记可读，SOL 重连、
  RTC 保存、校时和本地健康均正常，期间设备未重新启动。
- 外设边界复核：保留 PDI/UAPI/PDM/backend 分层；MCU 已拆协议、固件操作、
  诊断和总线后端，本轮不改驱动收发与卸载时序。更深队列拆分需要真实外设
  的并发收发/卸载验证。本轮未更新 SPL/U-Boot，也未重做破坏性分区故障测试。

证据：`output/ota-validation/0.0.1-layering-s5/`。本轮五阶段均已完成，以上
结果说明所列回归与 AM625 场景通过，不代表所有介质、外设及空间环境认证。

## master 收拢与统一版本源（2026-11-06）

- EDK 和 Linux 的 ota/v1.0.16 开发提交快进合入 master；Buildroot 检出
  master，当前 workspace 及六个子仓库统一在 master。旧 main 与相关功能
  分支的提交均已包含在对应主线，未重写提交历史。
- EDK/VERSION 改为 0.0.1，作为 SDK、Buildroot target/host EDK 包及设备
  固件的共同版本源。板级 JSON 通过文件引用读取版本，生成配置保存解析值，
  构建清单记录 VERSION 的 SHA256。保留完整内容 hash ID 区分同版本固件。
- 版本源无效或已构建 EDK 的版本不匹配时拒绝发布包生成，并保留上一套产物。
  CMake SDK 消费、文档和构建测试同步调整。动态库 ABI 号仍为 2，实际库文件
  版本为 0.0.1；手动清理本机构建输出遗留的 2.0.0 文件，未加入设备清理脚本。
- SDK 20 项、管理与构建 52 项、生成器 14 项、FIT 4 项、实际 ARM64
  initramfs 加载和真实包上传发布下载全部通过；检查最终 squashfs 不含旧库。
- 发布 ID `c889c4c410b79f432f805bb0c35bae465c6e43c8c1d0913d7477562ca421a554`，tag v0.0.1，
  审计编号 110，设备上报 success。启动 ID `75b62875-8bb6-4806-948f-c119f15b8258`。
  实机 PDM 显示 edk_version=0.0.1，fwctl 显示同一版本及上述内容 ID；零失败
  服务、双 rootfs 槽、当前 kernel/rootfs 全量校验、持久日志和 UTC+8 校时通过。

证据：`output/ota-validation/0.0.1-master-version/`。本次 OTA 更新 kernel/rootfs，
主分支合入的 Linux 提交内容与此前已验证的开发分支相同。

## 统一管理工具命名与子命令（2026-11-06）

- 主机入口统一为 dmserver 与 dmcli，OTA 使用 dmcli ota list/upload/publish。
  入口统一解析 --server/--json/帮助/版本；公共 HTTP/JSON 输出和 OTA 动作拆成
  私有模块。服务器地址环境变量改为 DM_SERVER，保留现有 HTTP 契约与包格式。
- 同步 Kconfig、Buildroot host 选择、Make/CMake 目标、预设、测试和现行文档。
  当前构建输出移除旧命名可执行文件；仓库未增加兼容别名或设备清理脚本。
  历史发布记录保留当时名称用于追溯。
- SDK 20 项、管理/构建 52 项、FIT 4 项、实际 ARM64 initramfs 加载与真实包
  上传/发布/下载回归通过。命令测试覆盖分发、离线帮助、全局选项位置、JSON
  原样输出、横线开头文件名、异常输入和发布幂等。
- 已重载 dmserver，使用 dmcli ota 上传并发布内容 ID
  `378dea5ac2916841729254f67e888ce6038a9056cecffefff450689b3d0166bd`，tag v0.0.1，审计编号 111；
  设备上报 success。启动 ID `bde97f59-201d-4c0b-8971-02a8008a0591`，零失败服务、
  双 rootfs 槽、当前 kernel/rootfs 全量校验、持久日志、SOL 归档与 UTC+8 校时通过。

证据：`output/ota-validation/0.0.1-dm-cli/`。发布前仅修正本地辅助脚本中的串口
记录目录名；未更改生产源码、固件或重复发布。此轮未更新 SPL/U-Boot。

## 远程日志标签页与历史管理（2026-11-06）

- 查看日志保留原有设备/启动记录/阶段选择、筛选、实时跟随及导出；新增日志
  列表标签，平铺服务器保存的实时、历史、阶段归档与完整包记录，支持按设备、
  状态、时间/完整启动 ID/归档 hash 查找，打开、下载和逐行 × 删除。
- 当前记录及事故副本继续受保护。完整归档下载原包，无整包时下载服务器保存的
  全阶段文本片段；不删除设备本地副本或独立 OTA 审计附件。暂停跟随时手动
  打开历史记录仍读取一次，切换期间过时响应不会覆盖新选择。
- 侧栏与页面标题统一为中文；SOL 下提供“查看日志”“日志列表”。来源 IP、
  存储、复位和健康信息放在查看页的“启动信息与设备状态”，默认折叠。
  页签和列表搜索在刷新后保留，已有事故/启动记录深链接继续打开查看页。
- SDK 20 项、管理/构建 52 项及最终 Web 回归通过；Chromium 桌面/手机验证
  查看功能、列表筛选、UTC+8、页签刷新、文本及整包下载、当前记录删除保护、
  历史删除、深链接和折叠/展开，未发现 JavaScript 错误。删除测试只操作临时
  服务的合成记录，生产历史记录保留。截图与下载校验保存在 browser/。
- FIT 4 项、实际 ARM64 initramfs 加载与真实包上传发布下载通过。发布 tag
  v0.0.1，内容 ID `2f2f08833290895ffc56f806cfa7bcb39a242fcffc7985f2cd2f930901440d18`，
  审计编号 112，设备上报 success；启动 ID `5b8472c7-4328-4b12-85cb-1a4dce7d1adf`。
  实机零失败服务、六个管理服务、双 rootfs 槽及当前 kernel/rootfs 全量校验、
  日志持久化、SOL 归档和 UTC+8 校时通过。前端由主机浏览器独立验收。

证据：`output/ota-validation/0.0.1-sol-record-list/`。dmserver 已重载；本轮未更新 SPL/U-Boot。

## 最后一次异常启动与复位证据（2026-11-09）

- 需求限定为保留最后一次异常与恢复启动，沿用两组 DDR 缓冲。三次试启动失败后，
  两组保存最后一次失败和随后回滚启动；不扩大保留内存，也不删除服务器历史。
- OTA 事故附件新增 failure_observation、reset_label、reset_evidence 和 reset_capture。
  panic/oops 从异常 kernel 原始字节观察；导致该启动结束的复位标签取自下一次
  恢复启动 U-Boot，避免误用异常启动自身的标签。缺失、重复或无法识别的标签保留
  UNKNOWN；ESM 不推断为 watchdog，RST 不推断为 panic。原始字节和归档协议不变。
- Web 异常详情分别显示日志故障标记与复位标签，保留查看、下载与 SOL 跳转。
  从独立事故副本读取证据，删除普通 SOL 归档、重启服务器后仍能查看。
- 核对 11 月 4 日 AM625 三次 panic 后回滚的真实归档：最后一次异常 capture
  dab591db-9258-4a34-8d2f-ff37d3ee3fcc，23921 字节，与原始实机工件完全一致；
  SHA256 为 14793d4928b6953e995fd102ee54ff8bd970c205b1c0c62684258c75f8ccd026。
  检出 kernel panic，恢复 capture 96c60157-9a6e-4080-830c-388fccb27832 的
  U-Boot 标签为 RST。Chromium 验证显示、原文查看与 SOL 跳转，无 JavaScript 错误。
- 实际 R5 生产代码的主机 ABI 测试覆盖四次连续启动后只保留第三/第四次的四阶段
  记录，5 项通过。SDK 20 项、管理/构建 52 项通过；新增事故用例校正清单顺序后
  单独复测通过。FIT 4 项、实际 ARM64 initramfs 加载及真实 OTA 包上传下载通过。
- 发布 v0.0.1，内容 ID
  dd8e22eefa192a906a71d64efef4aa1ba1745eb1e2286dee5e1bb3029d00add7，
  审计编号 113，设备上报 success；启动 ID 318ff91d-2a7f-4628-b2b4-5a2f59364946。
  零失败服务、六个管理服务、双 rootfs 槽及当前 kernel/rootfs 全量校验、持久日志、
  启动归档确认和 UTC+8 校时通过。源码快照与提交门禁一致。

证据：`output/ota-validation/0.0.1-last-failed-startup/`。本轮正常 OTA 验证并只读
复核已有实机故障归档，未再次注入三次 panic，也未更新 SPL/U-Boot。DDR 不保留的
复位、掉电和采集启动前的故障仍不保证保存，详见
[双缓冲设计](../../edk/docs/device-manager/startup-buffers.md)。

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
| OSA 公共 IPC 与截止时间 | v0.0.1 | 989e81ba | success |
| OSA 公共日志与 OTA 输出适配 | v0.0.1 | 94ef26aa | success |
| OSA 用户态日志入口统一 | v0.0.1 | 4a31f6d8 | success |
| 分层 1：OSA IPC 与进程执行 | v0.0.1 | daa25df8 | success |
| 分层 2：小文件持久化 | v0.0.1 | dd3049bf | success |
| 分层 3：固件与日志证据接口 | v0.0.1 | 83649a99 | success |
| 分层 4：访问策略与 OTA 编排 | v0.0.1 | 667ba933 | success |
| 分层 5：日志与时间运行上下文 | v0.0.1 | fa43a1f2 | success |
| master 与统一版本源 | v0.0.1 | c889c4c4 | success |
| dmcli / dmserver 与 OTA 子命令 | v0.0.1 | 378dea5a | success |
| 日志列表与统一中文导航 | v0.0.1 | 2f2f0883 | success |
| 最后一次异常日志与复位证据 | v0.0.1 | dd8e22ee | success |

每阶段均先构建、发布并完成实机健康确认，再提交与推送子仓库，最后更新
workspace gitlink。最新使用方法见 [EDK README](../../edk/README.md)。
