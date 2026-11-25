# EDK 管理模块分阶段重构验收

当前设计见 [EDK 架构](../../edk/docs/architecture.md)。本文记录已经完成的分阶段验收。
固件版本固定 v0.0.1；每阶段完成构建、发布和 AM625 健康确认后提交推送。

## 公司级框架重构基线

本轮基线的原生回归 84 项通过，AM625 Buildroot 目标包和 PDM 模块构建通过。
[当前交付架构](../../edk/docs/architecture.md)

- AM625 在私有运行目录中加载候选程序。真实 HWID `1010001000110000` 匹配
  `h200_ccm` 和星务协议 v1.0，启动校验发现 4 个测点和 3 条命令。
- Phytium 的 Redfish 与 IPMI 只读连接验证通过。CCM 从 BMC 取得电源状态，
  从 PMC 取得 CPU、内存及综合样本。单节点和全部节点查询均标记来源为节点 3。
- AM625 上的四项 ARM64 星务夹具通过，涵盖双路切换、背压、超时和结果查询。
  物理星务对端及第二块 CCM 分别列入后续实机验收。
- 本轮候选程序在隔离环境验证。板上常驻镜像早于该候选，历史镜像 hash 与
  候选程序校验值分别保存。现场认证仅用于隔离验证和本地配置。

本地构建日志和源码快照位于 `output/edk-framework-stage0.slXQ1QWK/`。

### 公司级重构阶段 1 · 产品装配

- 产品目录为 `projects/phytium-s5000c/`。AM625 的真实 HWID 匹配该项目，星务侧继续使用 v1.0。
- 两个进程通过本机固定 IPC 地址完成能力校验，报告 4 个测点、3 条命令。未知 HWID 和错误 IPC 地址均被拒绝。
- 原生回归 84 项通过，AM625 的 EDK 与 PDM 交叉构建通过。
- Phytium Redfish、IPMI 分别通过只读连接检查。节点 3 和全部节点查询均返回节点 3 的电源、CPU、内存和综合利用率。8 次缓存查询的最大观测值为 2 ms。
- 候选程序通过隔离运行验证。真实星务对端仍按计划另行验收。

本地证据位于 `output/edk-framework-stage1.HCBtnV9Y/`。

### 公司级重构阶段 2 · 采集与遥控注册

- 公共业务类型和星历编解码归入 `user/lib/telemetry`，沿用现有 SDK 头文件和线上值。
- 执行器按完整描述符一次注册采集和遥控。原生回归 84 项通过，覆盖注册失败回滚、同资源串行、跨来源样本一致、优先级与控制期限。
- AM625 的 EDK 与 PDM 交叉构建通过。隔离验证真实 HWID 选表、v1.0 入口和 4 个测点、3 条命令。
- Phytium 的 Redfish、IPMI 只读检查和 PMC 采样通过。单节点、全部节点结果均保留节点 3 来源。FPGA 和 MCU 的节点来源替换由测试夹具验证。

本地证据位于 `output/edk-framework-stage2.RksS0tPA/`。

### 公司级重构阶段 3 · 服务器端点

- 执行器在同一节点快照中按需绑定 BMC 和 PMC。原生回归 85 项通过，含坏端点隔离、PMC 超时和取消、BMC 原采样时间复用。
- AM625 EDK 与 PDM 交叉构建通过。板上隔离候选程序重新匹配 `phytium-s5000c` 与 v1.0。
- Phytium Redfish、IPMI 只读连接和 PMC 采样均通过。单节点和全部节点返回同一正确来源，8 次缓存查询最大观测值为 1 ms。

本地证据位于 `output/edk-framework-stage3.PExEveMX/`。

### 公司级重构阶段 4 · 星务收发与查询

- 原生回归 85 项通过。沿用 IPC v3，类型化查询覆盖本地、指定节点和全部节点。
- AM625 EDK 与 PDM 交叉构建通过。四项新构建的 ARM64 协议夹具在板上隔离运行通过，包含 v1.0 单接收链、八节点最大应答、v2.0 双路切换和队列满时仍可收帧。
- 完整报文的接收时间纳入控制启动期限。夹具覆盖排队到期后未提交、提交确认丢失后查询原结果。
- Phytium Redfish 和 IPMI 只读连接通过。通过 CCM 读取 PMC 与 BMC 的 4 项样本，单节点及全部节点均保留来源。

本地证据位于 `output/edk-framework-stage4.k5Sj1jL5/`。

### 公司级重构阶段 5 · BSP 与 PDM

- AM625 的星务主链路由 BSP 指定为 `can0`。错误的主备角色在执行器能力查询前被拒绝。BSP 的 Classic CAN、CAN FD 和必需/可选接口用例通过。
- 原生回归 86 项通过。AM625 Buildroot 与独立 Kbuild 均成功构建 ARM64 `pdm.ko`。
- 板上隔离程序通过新的 CAN 角色读取路径启动。Phytium Redfish、IPMI 和 PMC 只读测试通过。PDI 清单验证已运行内核中的 MCU CAN 和电源 RS485 设备。
- I²C 原生 probe 的直绑修改通过交叉构建；当前 AM625 没有 I²C MCU，物理绑定和解绑待验。
- RK3588 预设完成 ARM64 用户态构建，ELF 依赖检查确认无 PDI/PDM 与服务器库。此次使用 AM625 ARM64 工具链，RK3588 目标 sysroot、内核和实机验收保持待办。

本地证据位于 `output/edk-framework-stage5.mgX6iFW9/`。

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
[双缓冲设计](../../edk/user/apps/pmcd/README.md#启动日志与异常证据)。

## 星务协议与设备适配分层（2026-11-19）

- 星务入口按配置选择 v1.0 或 v2.0 协议。两个协议共用启动、执行器连接和健康状态接口，
  分别管理报文和 CAN 会话。单独选择 v2.0 可以构建并启动，不链接 v1.0 适配代码。
- 遥测执行器通过统一接口装配 MCU、OS 和 BMC 采集器。BMC 设备配置、凭据与会话由
  `libbmc` 管理。现有 Unix IPC、v1.0 遥测字节格式和 `libbmc.so.2` ABI 通过兼容性检查。
- AM625 配置关闭了旧 PDI Satellite 转接。该转接保留给依赖旧 PDI ABI 的二进制，
  只有显式启用时才把 `libsatellite` 加入 `libpdi` 的依赖。
- 主机回归 41 项、BMC 回归 42 项、管理及构建回归 118 项通过。ARM64 交叉构建
  验证了 v1.0、v2.0、OS 与 PMCP 在禁用 PDI 的配置下可独立组合。
- AM625 隔离 vcan 测试核对了 v1.0 快慢遥测字节与 IPC 快照、无处理者时的拒绝响应、
  v2.0 双 CAN 去重、备路重发和会话号持久化。本轮未连接实体星务平台或验证 RK3588 BSP，
  也未验证新增 BMC 厂商或型号的实机交互。
- 首次发布后，旧 Buildroot 输出残留的 BusyBox `init` 使新槽无法完成健康确认，
  U-Boot 自动回滚，服务端保留了回滚记录。使用相同源码重建干净的 systemd 目标文件系统，
  并用新固件包通过整包集成测试。
- AM625 从本地 A 槽启动 v0.0.1，运行内容 ID
  `898b7b2a7fa60a5b4e8e53c1b2a8645a46d706a622d2cdfa80e10240ffa9c5ee`，
  启动 ID `c6aa4a49-9a87-4c83-bd91-bdf36cd7df5f`。设备完成本地健康确认，
  OTA 服务收到 `success`，20 个实机文件的 SHA256 与打包文件一致，五个被检查的
  EDK 服务均运行且无失败单元。测试时日志采集正常，但数据分区空间不足，归档使用
  易失目录。验证后恢复原有 TFTP/NFS 启动，网络启动 ID 为
  `2ab9c3dc-2882-42ca-b413-38676a6a8c93`，原 NFS 根路径和参考固件 ID 已核对。

证据目录为 `output/edk-adapter-refactor.4lYyiI/`。适配器与执行器边界见
[星务与执行器协议](../../edk/docs/satellite-protocol.md)。

## 适配边界与部署收尾（2026-11-19）

- 遥测 IPC 按端点加锁并核对绑定文件的归属。回归覆盖第二实例启动失败时，
  原实例的管理端点和执行端点都能继续应答。
- v1.0 和 v2.0 复用 libsatellite 通道接口。v2.0 的星历更新、读取及自检走
  执行器，星务端管理线格式和最近控制状态。AM625 的隔离 vcan 验证了
  v1.0 快慢遥测、v2.0 双路去重、星历查询、备路重发和会话持久化。
- AM625 的 CAN 初始化支持按接口配置 Classic CAN 或 CAN FD，systemd
  依赖使本机执行器先于星务入口就绪。通用镜像默认采集 OS 遥测。
  测试板未收到有效的 MCU 采样，启用实体 MCU 由项目配置决定。验证了
  无 PDM 时 hwmon 仍能通过 IPC 发布标准有符号温度样本。RK3588 预设
  通过 ARM64 交叉构建和服务安装检查。
- BMC 协议和厂商配置从适配器注册，执行器支持多个缓存点与显式启用的
  BMC 管理命令。PDI 仅保留本地外设 ABI，旧 Satellite、OTA 和文件传输
  转接以及 AM625 的 SysV debugctl 已移除。
- 主机 41 项、BMC 42 项和管理 118 项通过，其中整包测试使用最终固件重跑。
  新的 CAN 配置脚本通过 Classic、FD 和非法接口名测试。当前验证覆盖
  AM625、隔离 CAN 与模拟 BMC，RK3588 BSP、实体星务、实体 MCU 和 BMC
  控制尚未联调。
- 第一份实机确认包 `3356c080…` 上，额外运行查询发现旧输出中的
  libgpg-error ARM64 锁对象尺寸为 0，导致管理查询退出时中止。
  清理旧编译目录后应用仓库已有的可移植 awk 补丁，锁对象重新生成为
  48 字节，随后重编加密依赖并重新打包。
- 最终 AM625 固件 v0.0.1 的内容 ID 为
  `419a1f8ee6ec1c06a394459d6f5cd24eb222bd1dece4bc1def3724dcb230260a`，
  本地 A 槽启动 ID 为 `2b99fb26-3270-4dfe-af7e-21952541b786`。
  系统完成健康确认，OTA 服务收到 `success`，18 个实机文件哈希一致，
  七个相关服务运行且无失败单元，管理查询正常退出并返回有效的 OS 样本。
- 恢复原 TFTP/NFS 启动及 NFS 根路径后，确认网络启动 ID 为
  `4980c92a-bf0e-4bb6-8a9a-9c63102c45d1`，参考构建和服务状态与验证前一致。

证据目录为 `output/edk-layer-completion.KJqFMy/`，包括两份实机包、原始回执、
源码快照和运行日志。[星务与执行器协议](../../edk/docs/satellite-protocol.md)

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
| 星务协议与设备适配分层 | v0.0.1 | 898b7b2a | success |
| 适配边界与部署收尾 | v0.0.1 | 419a1f8e | success |

每阶段均先构建、发布并完成实机健康确认，再提交与推送子仓库，最后更新
workspace gitlink。最新使用方法见 [EDK README](../../edk/README.md)。

## 框架计划第 6–7 阶段与 SD 启动（2026-11-22）

- AM625 `192.168.10.211` 上的 SD A 槽内核和根文件系统哈希均匹配已确认固件。
  保留原启动环境后先试启一次，再将 `tftp_kernel` 和 `nfs_root` 持久设为
  `0` 并重启。两次均从 SD 启动。第二次启动 ID 为
  `cf1ef7c6-237c-49b6-a174-12e7cfb124f7`，根挂载为 `/dev/fw-root`
  上的只读 SquashFS。dm-verity、`fwctl health-check` 和 A 槽确认通过。
  基线为 `v0.0.1`，内容 ID 为
  `419a1f8ee6ec1c06a394459d6f5cd24eb222bd1dece4bc1def3724dcb230260a`。
- AM625 新版 `timectld` 以 Phytium S5000C 上的候选 PMC 为 HTTP 时间源。
  指定 `/dev/rtc0` 返回 `rtc-state=written`，指定 `none` 仍完成校时并
  返回 `rtc-state=disabled`。飞腾服务器常驻 `pmcd` 更新后通过健康检查和
  HTTP 时间响应检查，鉴权后返回有效 CPU、内存和样本新鲜度。部署保留上一版
  运行目录及数据库快照。
- 阶段 6 原生回归 125 项通过，包含真实 OTA 包、板级启动归档、旧归档读取和
  构建边界。AM625 Buildroot 全镜像和 ARM64 initramfs 加载验证通过。
  阶段 7 的联合原生回归 86 项通过，另验证独立 CAN SDK、Redfish-only、
  PMC-only 构建及 RK3588 用户态 ARM64 交叉构建。实体星务与 RK3588 BSP
  测试待设备和链路接入。
- 首个候选固件 `v0.0.1` 内容 ID 为
  `05de7ba6b10fe2880fd15cbeaaf50a792a04747893452bfec0aabf3ab4ccd7d2`。
  OTA 服务记录一次设备下载及 `installing` 上报，随后 AM625 的 SSH 和
  ARP 均无响应。发布包和服务端 FIT 文件的哈希一致，提取的 rootfs 通过全量
  dm-verity 校验。USB/IP 串口确认 B 槽进入 initramfs 救援，读取 A/B 状态的
  `fwctl` 子进程触发栈保护。Buildroot 增量目录残留旧的私有头文件，导致不同
  编译单元采用不同大小的布局结构。PID 1 仍续喂看门狗，B 槽剩余尝试未耗尽。
  通过串口执行 U-Boot `fwctl rollback` 回到 A 槽，保留 SD 启动设置，恢复网络
  和健康检查。原候选随后补报 `rolled-back`。
- 修复通过显式引用各私有头文件归属目录、清理 EDK 包构建目录、运行打包后的
  ARM64 `fwctl` A/B 状态读操作来覆盖混编故障。initramfs 在 A/B 状态子进程
  异常终止时重启，交由 U-Boot 执行后续试启动选择。真实栈保护故障和子进程信号
  分支分别在 QEMU 与原生回归中覆盖。板上验证了手动回退，未引入第二次实机故障。
- 修复固件 `v0.0.1` 内容 ID 为
  `ab46d4e1bf65f5758294f5bf0db2290806a17c1b6a0dd2263d6b47bf0e7febd7`。
  AM625 从 SD B 槽启动，启动 ID `21ccba63-fc63-4703-99ef-52bfbdbb0aa9`，
  dm-verity、健康确认和 OTA `success` 均通过。A 槽仍保留已确认的 `419a1f8e`。
  实际 B 槽 `fwctl` 与打包产物哈希一致。飞腾节点的电源、CPU、内存和负载快照
  在显式 index 3 及 ALL 查询中均有效。当前板载配置的三台服务器均出现在 ALL
  响应中，节点归属分明。

证据见 `output/edk-framework-stage6.q6wkSrGs/`（复测在 `rebuild/`）与
`output/edk-framework-stage7-product.uYPVnL/`。

## 星务业务契约与服务器维护接口（2026-11-23）

- 从星务映射、遥控项目表和调度器中移除了控制器自检和复位。主机强制下电沿用
  已有操作号和权限。控制器维护仍由 `libserver` 提供。星务适配只使用业务测点、
  操作和服务器 index，C 表在 CCM 内绑定 BMC 或 PMC 端点。
- 86 项原生回归全部通过，覆盖两种星务协议、退役配置拒绝、主机控制权限和
  节点寻址。AM625 Buildroot 全镜像和 ARM64 initramfs 实际加载测试通过。
- AM625 从 SD A 槽启动 `v0.0.1`，内容 ID
  `4e3e47cb3cdaaea6ec9f4b089d154bfa6f9585d5bc7e1cbfe173f72322e0c2d7`，
  启动 ID `9a2f7575-5bbc-40c0-beab-6178091ff02f`。dm-verity、健康确认及
  OTA `success` 在板端和服务端均已核对。B 槽保留 `ab46d4e1`。
- 读取实机能力表确认已退役的四个控制器操作缺席。Phytium 节点的 CPU、内存、
  综合利用率和主机电源状态通过显式 index 3 及 ALL 读回。实机业务验证限只读请求。

证据见 `output/edk-satellite-domain.4a1R6sm6/`。

## CCM HWID 定义集中管理（2026-11-23）

EDK 项目表通过 `projects/ccm_hwids.h` 引用板型和 PCB 版本对应的 HWID。宏展开值、
U-Boot 出厂值、FIT 白名单及 AM625 实机身份一致。86 项原生回归通过，三个相关
用户态交付二进制与上一版相同。AM625 从 SD B 槽启动 `v0.0.1`，
内容 ID `a2505fecab4071e23a791f583f26706c0a79b767f666af97e684eaf3fa98e22b`，
启动 ID `7004e707-9ce7-42b1-a3d3-88ecf35b7890`。健康确认和 OTA `success`
通过，两个业务进程仍匹配 `phytium-s5000c` 和星务 v1.0。
证据见 `output/edk-ccm-hwids.SHMwILxt/`。

## EDK 子系统重构 M0：基线确认（2026-11-25）

- EDK `85ea958fa058b68c65593194568ba690e34a1a00`、BSP `05a047237b8f5f4b87d864cf32ca38c238113305`、
  workspace `fde9168ffdb9e2551b485d35e27b42b02d173146` 为起始源码。仅文档、接口所有者索引和
  基线验收记录变更；公开 API、生产代码、包配置及 `VERSION=0.0.1` 不变，未发布新固件。
- V1 文档检查通过；V2 42/42、V3 124/124、V4 79/79；两角色正式 Buildroot 包及 PDM
  诊断开/关 AArch64 Kbuild 成功，两个独立安装 SDK 消费者通过。详见 EDK
  [M0 基线](../../edk/docs/edk-subsystem-m0-baseline.md)。原始证据根 `output/edk-subsystem-m0-20261125/`。
- 指定 AM625 `192.168.10.211`、MAC `1c:63:49:22:c4:f7`、HWID `1010001000110000`。
  Dropbear 主机密钥因 `/run/dropbear` 启动生成而变化，用户在板端串口查询 ED25519 指纹
  确认与网络一致；本次使用临时固定 known-hosts，不改主机原信任库。
- V6 前发现板时钟为 2026-03-04、节点 3 Redfish 证书在 2026-11-19 至 2027-02-17 有效；
  板端 CA 与 BSP SHA256 一致，主机按当前时间、CA、IP 验证证书通过。
  OTA 与时钟源 `192.168.10.246:8090` 的上一轮临时通道已关闭。复制 11-24 成功发布的
  本地 catalog 至独立 `board-management-feed/`，不改原 catalog、不发布新内容；PMCD
  loopback 18090，通过 socat 只允许 `192.168.10.211` 访问 `192.168.10.246:8090`。
  `timectl sync` 2026-11-25 17:33:45+08:00 成功，offset 1ms，RTC written。观测至 V6
  无新增 TLS peer certificate/OTA manifest download 错误；catalog 已记录当前 boot ID
  连续至少 6 次同内容 requested，未触发重启。节点 2/3 Redfish 及节点 3 PMC 样本 fresh、
  last_status=0。节点 1 `192.168.50.201` 独立连接超时（-110），不在 M0 设备基线关闭范围，
  不改变其他真实服务器状态或配置。所有测试控制用例均在隔离网络 namespace 本地夹具执行。
- **当次 V6，2026-11-25 17:35:44+08:00**：`fwctl hwid value`、`fwctl version`、
  `fwctl ota-status` 证实 B 槽已确认、版本 1、完整内容 ID 为
  `4412d622c6b0b709fe1a0a61051a5857a6fa0bc5ad2cd394ad0cb8687175044e`；启动 ID
  `fc6b77f0-9ed6-4717-b9dd-efb26b0fffc7`。`fwctl ota-check` 对历史已确认镜像的实际长度、
  kernel/rootfs SHA256 返回 `FWCHECK1 match`；rootfs 是 `/dev/fw-root` 只读 SquashFS。
  从 `output/validation/edk-app-src-include.QLDKwqoC/artifacts/release/rootfs.itb` 提取
  并校验 payload SHA256，8/8 运行制品（4 库、pdm.ko、两个遥测进程、fwctl）匹配，
  `/proc/<pid>/maps` 证实实际加载相应库；`fwctl health-check` 返回 0，pdm、CAN、遥测、星务、
  固件健康、OTA、日志、时间八个服务 active，零失败单元。实际目标 SDK 安装头和库编译
  只读探针，经本机临时目录运行并自动清理，SHA256
  `56a18426a7ce969da101dd4fe213ffd0c6772165cd53ce837434dec47d72ec3e`，加载板上库：
  BSL HWID 选 `phytium-s5000c`、Satellite v1.0（2000ms）、PDI 读取 PDM 代数 15，
  main_mcu/CAN 和 dc_power/UART 两个已绑定设备（健康 unknown，未发送设备动作）。通过。
- 证据：`board-v6-readonly.sh`、`board-v6-readonly.log`、`board-artifact-compare.log`、
  `board-probe-live.log`、`board-time-before.log`、`board-time-sync.log`、
  `board-after-sync-runtime.log`、`ota-recovery-requests.log`、`start-board-management.sh`。
  运行制品的既往成功发布记录 `output/validation/edk-app-src-include.QLDKwqoC/ota-success.json`；
  本次不把旧 success 冒称新 OTA，也不验证未安装的 bootloader。
  EDK 阶段验收提交：`c866c97693992437d7ad0f9decb48b0ae061bee5`（master）；工作区
  使用其准确 gitlink，最终工作区和远端核验 SHA 见阶段完成报告。

## EDK 子系统重构 M1：统一模块接口约束（2026-11-25）

- 起始 EDK `c866c97693992437d7ad0f9decb48b0ae061bee5`，workspace `8a528185be4de4bdce4c91c0406ccec690c8bff4`。
  文档、规则和原生 CMake/CTest 变更，无板端生产源码、配置、协议、公开 ABI 或版本变更。
  V2 45/45，最终新检查 3/3；真实管理 289、联合 392 个编译依赖及诊断关闭 PDM Kbuild，
  预期依赖命中与拒绝/缺失反例全部通过。详见 EDK [M1 验收](../../edk/docs/edk-subsystem-m1-validation.md)。
- **当次 AM625 V6，2026-11-25 17:51:10+08:00**：指定板卡 `192.168.10.211`、MAC
  `1c:63:49:22:c4:f7`、HWID `1010001000110000`、boot ID `fc6b77f0-9ed6-4717-b9dd-efb26b0fffc7`。
  `fwctl ota-status` 完整 ID `4412d622c6b0b709fe1a0a61051a5857a6fa0bc5ad2cd394ad0cb8687175044e`，
  B 槽确认版本 1；`ota-check` 返回 `FWCHECK1 match`，`health-check` 成功，八单元 active，
  零失败单元。读取实际加载的 4 SDK 库、pdm.ko 和三个应用 SHA256，8/8 与已经核验的
  正式 rootfs 相同；只读 SDK 探针哈希匹配 M0、实际库加载路径 `/usr/lib`，项目
  `phytium-s5000c`、Satellite v1.0、PDM 代数 15、设备 2 个已绑定。真实板端未启用 hwmon，
  不将无 PDM 主机夹具冒称实体 hwmon 验收。无新 OTA 发布或其他真实服务器写操作。
- 此时 M0 恢复的管理端仍提供同一已确认内容，时钟同步、TLS/OTA 报错无复发。节点 2/3
  Redfish 和节点 3 PMC 只读新鲜采样；节点 1 的独立外部连接超时保留观察。
  实机证据 `output/edk-subsystem-m1-20261125/board-v6-final.log`、`board-probe-final.log`、
  `board-artifact-compare.log`、`board-recovery-observation.log`，当次 V6 通过。
  EDK 验收提交：`a7a78c7c26fbd6094387e5f856465afc8c500155`（master）；工作区记录准确 gitlink。

## EDK 子系统重构 M2：PDI/BSL 试点（2026-11-25）

- 起始 EDK `a7a78c7c26fbd6094387e5f856465afc8c500155`、workspace `6b8894af59d5fdf4edcb7e7a734a2dcab257c8b4`。
  PDI hwmon API/错误文档、可选模块内 fd 清理、两套安装 SDK、BSL 基础功能说明与模块依赖
  回归；V2 45/45、V3 127/127、V4 82/82、BSL 局部 2/2。正式 AM625 hwmon 关闭，
  Buildroot edk-reconfigure 及新安装 SDK 四库和头与 M0 字节相同，原有跨版本消费者通过。
  用户授权无上下文独立 AI 维护者实际修正局部实现和非普通属性回归；发现并修订指南
  的证据位置后，由同一维护者复测成功。详见 EDK [M2 验收](../../edk/docs/edk-subsystem-m2-validation.md)。
- **当次 AM625 V6，2026-11-25 18:02:40+08:00**：板 `192.168.10.211`、MAC
  `1c:63:49:22:c4:f7`、HWID `1010001000110000`；现行 B 槽 `v0.0.1`、内容 ID
  `4412d622c6b0b709fe1a0a61051a5857a6fa0bc5ad2cd394ad0cb8687175044e`、boot ID
  `fc6b77f0-9ed6-4717-b9dd-efb26b0fffc7`，`ota-check` match、健康正常、8 服务 active、零失败。
  使用同工具链独立 PDI_HWMON=y / PDM=n ARM64 SDK，在板 tmpfs 临时目录核对 probe
  SHA256 `f1c7b0b71cf61125cc93d251abee8a00768e7d06a3402b5b6a1d49446adfb758`、
  libpdi `683c40c54f5a0b0c7262a3d88825fff03cdc25801c76ca6a081be83a0643fd05`、
  libbsl `3b257199b65fe0989ace91ada808085de5d8c6b3522d4cd1970f2f7f6dbef584`；`LD_DEBUG=libs`
  确认加载候选两库。普通文件 -12000 mC、相对/畸形/非普通 -EINVAL、溢出 -ERANGE、
  缺失 -ENOENT、失败不改输出全部通过。清理 tmpfs，18:02:45 复验健康与版本未变。
  仅隔离属性文件，非真实 hwmon 传感器；正式配置未启用该能力、正式库不变，未发布新 OTA，
  未对其他真实服务器写入或控制。证据根 `output/edk-subsystem-m2-20261125/`，文件
  `board-v6.log`、`board-hwmon-candidate.log`、`board-after-candidate.log`、`hwmon-v6-remote-command.sh`。
  EDK 验收提交：`b5310a8b016aeac7955ad6dfc793d268e1a4b900`（master）；工作区记录准确 gitlink。

## EDK 子系统重构 M3：PDM 驱动与公共诊断（2026-11-25）

- 起始 EDK `b5310a8b016aeac7955ad6dfc793d268e1a4b900`、workspace `400aa0a39193592e1cdfcf887598357c220c7b04`。
  LED、MCU 诊断关闭桩移归各驱动，公共桩只依赖 log，移除两全局 driver include 路径。
  V2 45/45、V3 127/127，两组实际 Kbuild 开/关 37/35 个对象，旧私有头反例拒绝；
  Buildroot 增量和干净构建的实际 `.cmd`/模块/SDK 一致。独立 full image、镜像专项检查和
  真实候选包往返通过。详见 [M3 验收](../../edk/docs/edk-subsystem-m3-validation.md)。
- 本机管理端采用 systemd user transient unit `edk-am625-local-manager.service` 监督恢复，
  原独立 catalog、loopback 18090、只允许指定 AM625 的 8090 转发保持。发布前健康、身份、
  版本 B 槽、单一 active channel 核对通过。包 SHA256
  `7f966a3feaa8ff5265c89abe15e64f916568f4dacf94e855cf90e5084169559a`，
  draft `draft-xXRxnz`，发布 2026-11-25 20:23:54+08:00，`v0.0.1`、packed version 1、完整 ID
  `386c56dff2d6505b7d6b3d0ab7af084a0394b115171c6e227569c88b50bdb7f2`。板 `192.168.10.211`
  MAC `1c:63:49:22:c4:f7`、HWID `1010001000110000` 经 installing、boot-testing，
  20:25:31 服务端观测最终 success、running=1，未隔离；新 boot ID
  `6d78605c-27f3-47dc-936d-ef6e35a3c775`。证据 `ota-success.json`，不把中间状态当成功。
- **当次 V6，20:27:25+08:00**：用户在物理板串口确认新 ED25519 指纹后 SSH 固定临时密钥。
  `fwctl version` / `ota-status` 显示 A 槽确认 `386c56df`，`ota-check` 对同候选长度和哈希
  返回 `FWCHECK1 match`，`health-check` 0，八单元 active、零失败，Linux 7.0.0、PDM 已加载。
  包中 `pdm.ko` 与实机 SHA256 `e4570586f40ebb9a99dc02e42900063a0eb35b7a84f7c4b1c68f1ef0ab283409`，
  内核日志内容 ID、EDK revision 及配置匹配；八个运行制品与实际新 FIT rootfs 逐项一致。
  只读枚举 sysfs、proc `led/mcu/log_level` 与 debugfs `led_control/mcu_control`，日志级别 info；
  PDI SDK 探针代数 15、main_mcu、dc_power 已绑定，项目 `phytium-s5000c`、v1.0。
  其他真实服务器仅只读遥测，节点 2/3 Redfish、节点 3 PMC fresh/0，校时与 RTC 正常。
  没有真实设备动作或外部服务器写入；未安装引导程序，不能验证 SPL/U-Boot。
  原始证据 `output/edk-subsystem-m3-20261125/final/` 中 `board-v6.log`、`board-probe-live.log`、
  `board-artifact-compare.log`、`ota-timeline.log`、`ota-success.json`、`publication.json`、
  `source.patch`、`untracked-source.tar.gz` 与 `images/release/build-manifest.json`。
  EDK 验收提交：`9aad7b8e6896b0ded47d397110c4c040d7a6fff2`（master）；工作区记录准确 gitlink。

## EDK 子系统重构 M4：大型 SDK 内部职责治理（2026-11-25）

- 起始 EDK `9aad7b8e6896b0ded47d397110c4c040d7a6fff2`、workspace `0cb4199c6134d8d3b3b3be4536ba443c3f0ef39b`。
  transfer 共用回调窄头，节点目录访问 BMC 扩展 key 的窄查询，BSL 项目及 Satellite 维护说明。
  V2 45/45、V3 127/127、V4 82/82，collector 两态白盒/符号及同一安装消费者通过。
  正式 target/host 增量和干净包 SDK、实际依赖一致，四库 ABI 保持；完整镜像、专项及候选真实包往返通过。
  [M4 验收](../../edk/docs/edk-subsystem-m4-validation.md)。
- 唯一设备 `192.168.10.211`、MAC `1c:63:49:22:c4:f7`、HWID `1010001000110000`；
  OTA 包 SHA256 `5d7b60df1e75c1b68e16c1467e8cd597fb6155241002c9ed71cbec6ea4f44d55`，
  draft `draft-0vUaam`，21:10:49+08:00 发布，v0.0.1、packed version 1、full ID
  `c683da78ac59336ab613a32f30b715ad591d792e68057c52226f96d81c136acc`，
  21:12:43 服务端最终 success、running=1、未隔离，新 boot ID `242e59ae-9b71-4fc9-bb3d-b3bb9f808ca0`。
- **V6 21:21:02+08:00**：用户 attach USB/IP 双串口、授权 ACL，ACM2 读取物理板 MAC/HWID/boot ID
  和 ED25519 指纹与扫描值一致。固定新密钥，B 槽 confirmed、`FWCHECK1 match`、八服务 active、零失败。
  四库/PDM/两个遥测进程/fwctl 八摘要与实际打包 rootfs 一致，libserver
  `3e8a58a7063e7883cc5fc03f90d6dc2b6d51cee8c6de749ccb8336e929d5a1a7`。
  AArch64 安装 SDK 探针加载板端 libserver，collector start=-95，节点 3 Redfish power=on/status=0、
  PMC cpu=443 bp/memory=370 bp/status=0；其他真实服务器仅查询，节点 2/3 Redfish、节点 3 PMC
  正常，节点 1 为既有外部连接超时。校时/RTC 正常。未写入或控制任何其他服务器；
  未安装引导程序，不验证 SPL/U-Boot。
  证据根 `output/edk-subsystem-m4-20261125/`：`serial-board-identity.log`、`board-v6.log`、
  `board-artifact-compare.log`、`board-server-probe-live.log`、`ota-success.json`、`ota-timeline.log`。
  EDK 验收提交：`a6fb8efaa2c9216fc6aa477ac22eb2d0abced6dd`（master）；工作区记录准确 gitlink。

## EDK 子系统重构 M5：应用模块与共享契约（2026-11-25）

- 起始 EDK `a6fb8efaa2c9216fc6aa477ac22eb2d0abced6dd`，workspace `6ff91c570c4be14194635bcadb30f5b146b90b11`。
  PMC 采样只依赖 directory，请求路由保留 context；HTTP 接收只读取 common，两个旧宽头例外关闭。
  首次接手/补正复走由独立 fresh-context AI 实改及测试；V2 45/45、V3 127/127、V4 82/82，
  四组实际增量依赖、正式 host 增量/干净 SDK 与安装 pmcd 一致，PMC 固定向量和两端进程检查通过。
  正式 AM625 未选 CONFIG_PMCD，四库与 M4 完全一致，本阶段主机代码不发布新 OTA。
  [M5 验收](../../edk/docs/edk-subsystem-m5-validation.md)。
- **当次 V6，21:36:16–21:36:35+08:00**：ACM2 串口核对板 MAC/HWID/boot/key，固定 SSH，
  板 B 槽 M4 full ID `c683da78ac59336ab613a32f30b715ad591d792e68057c52226f96d81c136acc`，
  FWCHECK1 match，八服务 active、零失败，八运行制品与 M4 打包摘要一致。
  logctl sync ok、synced=observed=390、archive pending 0、persistent；timectl synchronized、RTC written。
  用 AM625 交叉工具链直接编译最终接收/BSL file_io 候选，SHA256
  `8ac00b63fe3b118a0d374005f4a5b76ca579cd240df1654118b116338eecd270`，
  板上 /tmp tmpfs、Unix socketpair（无外部网络连接），限额 -EFBIG、取消 -ECANCELED、零写入、
  成功完整接收 6 字节与 progress、清理。非板上正式 pmcd。
  只读节点 3 BMC Redfish power=on、PMC utilization cpu=432 bp memory=371 bp 状态均 0，
  节点 2/3 正常、节点 1 仍既有外部连接超时。不向其他服务器写入/控制。
  证据 `output/edk-subsystem-m5-20261125/`：serial-board-identity.log、board-v6.log、
  board-artifact-compare.log、board-http-probe-live.log、board-pmc-probe-live.log、final/。
  EDK 验收提交：`e77465985e273f6206d2a9b0d86fcfe0f9f59551`（master）；工作区记录准确 gitlink。

## EDK 子系统重构 M6：项目装配、裁剪与交付（2026-11-25）

- 起始 EDK `e77465985e273f6206d2a9b0d86fcfe0f9f59551`、BSP `05a047237b8f5f4b87d864cf32ca38c238113305`、
  workspace `b4079f539dc800b339ffb8653bc327aeaa039a69`。正式项目+执行器缺两 BMC 后端早期配置错误，
  BSP package pre-configure hook 使用同一 Kconfig normalizer；项目 A/B 与双表安装 SDK；
  本机和隔离真实 Buildroot staging 的 hwmon 开→关 ownership 清理与 clean off 对照通过。
  V2 45/45、V3 127/127、V4 82/82，正式 target/host 配置与增量/干净 SDK 一致，
  实际完整镜像、initramfs libbsl/firmware loader、候选包往返通过。
  [M6 验收](../../edk/docs/edk-subsystem-m6-validation.md)。
- OTA 仅指定板 `192.168.10.211`、MAC `1c:63:49:22:c4:f7`、HWID `1010001000110000`。
  包 SHA256 `7afaa244e26209ee081d775405e4dc03fcfd131254d2c192abf57a6674cb4197`，
  draft `draft-aqdPxH`，21:57:13+08:00 发布，v0.0.1、packed version 1、
  full ID `05b8646146cb42143df1cd1d1b4f119f8956a856698b3f0b41c4af2dbdc5e61e`，
  21:59:01 服务端最终 success、running=1、无 quarantine，新 boot
  `ddc2c27a-8fd0-47f7-95b2-340bfac67bac`。
- **当次 V6 21:59:34+08:00**：ACM2 串口独立核对板、事务 boot、新 ED25519，与扫描一致；
  SSH 固定密钥，A 槽 confirmed、FWCHECK1 match、八服务 active、零失败、八个制品与新 FIT rootfs
  全摘要一致。板端新安装 SDK probe 实际加载 libbsl，HWID 命中 phytium-s5000c 4 点，
  未登记合法 HWID -ENODEV/NULL；基线探针 v1.0 2000ms、PDM gen15、main_mcu/dc_power 只读绑定。
  节点 2/3 Redfish、节点 3 PMC 正常、节点 1 既有外部超时；校时同步。未写入/控制其他真实服务器，
  未部署新产品、新外设或引导程序。证据 `output/edk-subsystem-m6-20261125/` 中
  ota-success.json、serial-board-key.log、board-v6.log、board-artifact-compare.log、
  board-project-probe-live.log、board-baseline-probe-live.log。
  BSP 验收提交：`e9cd0ad22ebe737acf349584085e88ca40777785`；EDK 验收提交：`d392a20d845aa01d4b71a0b7d66b9cefd58d828e`（master）；工作区记录准确 gitlink。

## EDK 子系统重构 M7：最终回归及维护交接（2026-11-25）

- 起始 EDK `d392a20d845aa01d4b71a0b7d66b9cefd58d828e`、BSP
  `e9cd0ad22ebe737acf349584085e88ca40777785`、workspace
  `e5a0dbf1e76f9fe2d08cd17c1afe0f5e77fbb926`。回查 M0–M6 各次实机日志、远端提交和准确 gitlink。
  最终 CI host 45/45、management 127/127、telemetry 82/82（254/254），900 用户态实际对象、Kbuild
  diag on/off 37/35；三临时例外均已关闭、现有历史格式基线 832 条无逐文件增加。
  正式 target/host 配置和 M0 ABI 保持，增量/干净 SDK、旧消费者加载新 SDK、
  正式镜像/loader/新 OTA 包往返通过；两次 AI 首次接手实际修改/测试及最终指南复走通过。
  [M7 总体验收及各阶段 SHA](../../edk/docs/edk-subsystem-m7-validation.md)。
- 正式配置未变，重新生成的 PDM 构建标识形成新固件内容，按全量正式镜像验证/OTA 流程。
  只向指定 AM625 192.168.10.211、MAC 1c:63:49:22:c4:f7、HWID 1010001000110000 发布；
  draft `draft-sYt2Hs`，22:21:39+08:00 发布 v0.0.1 / packed 1，
  full ID `2870bc37f4024106b3782b57293bc36fce0d897b56c35173e924d61195496982`，
  包 SHA256 `48f54ef3e1790254e3c07b5af424a7448a0f3ec248ddca0bc1e1e430083af868`。
  重启健康确认后 22:23:24+08:00 最终 success（22:23:26 轮询确认）、running=1、无 quarantine，
  新 boot `3a2bf0c8-60a6-4fa0-bc8f-b566f9813761`。
- **当次 V6 22:25:11–22:26:04+08:00**：USB/IP ACM2 串口核对身份、boot、ED25519
  `SHA256:738GcHE6jEBhHAEbbnOgGCYZ50AjS3jnTKeIO6n7JaY` 与 SSH scan 一致，严格固定密钥；
  B 槽 confirmed、FWCHECK1 match、8 服务 active、0 failed、4 libs+PDM KO+两 daemon+fwctl
  的 8 全摘要与打包镜像相符，候选夹具后再次相同。选表 4 点、合法未登记 HWID -ENODEV/NULL；
  M0 原 board probe v1.0/2000ms、PDM gen15、main_mcu/dc_power 被动枚举；
  node3 Redfish power on、PMC CPU/memory status0，collector off -95；node2/3 Redfish 正常、
  node1 既有外部 -110。校时 synchronized、RTC written，log sync ok。
  AArch64 HTTP receiver socketpair 正/反例及隔离 hwmon SDK /tmp fixture -12000mC、错误保持输出
  都通过且清理，未称正式配置启用 hwmon 或使用真实 hwmon 外设。未写入/控制其他真实服务器，
  未部署第二产品/新外设/bootloader。
  证据 `output/edk-subsystem-m7-20261125/`：ci.log、prior-stage-remote-audit.log、
  prior-v6-audit.log、ota-success.json、serial-board-key-retry.log、board-v6.sh/log、
  board-probes.sh、board-artifact-compare.log、board-*-live.log、git-verification.log。
  EDK 验收提交：`489673305d6c862870f7c8fe4c309755d84def24`；BSP 沿用 `e9cd0ad22ebe737acf349584085e88ca40777785`，均已核对 origin/master；工作区提交准确 gitlink。
