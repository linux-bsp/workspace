# AM625 SadBoard 调试验证记录

## 阶段 1：systemd 基线与 GDB/core

状态：已构建、OTA、实机验证通过。固件版本保持 v0.0.1。

基线提交：

| 组件 | 提交 |
| --- | --- |
| Buildroot | 89f5a1cf52 |
| BSP | cf5300a（c404bd1 基线上的测试夹具修复） |
| EDK | b7bb487f |
| Linux | 1c04c52c7 |
| U-Boot | 6d569284 |
| libbmc | a991991 |
| SadBoard 实验层 | 5bb4010 |

本机输出目录为 `output/am625-debug-systemd/`，使用共享 AArch64 GCC 15 SDK 和
`../dl` 缓存。旧 `output/am625-debug/` 产物保留，不用于本轮部署或符号分析。

验证工件放 `output/validation/stage1-debug/`。实际固件 ID、测试结果、设备启动 ID
和提交门禁将在通过后补充。本轮 OTA 只更新 kernel/rootfs，不更新板上 SPL/U-Boot。

## 实际结果（2026-11-09）

- 初版 f89b2b06（发布 114）正常完成 OTA 和 SSH/GDB 在线验证；离线 core 的 PIE
  加载地址恢复遇到 ELF 头部缺失，补齐调试内核配置后重新发布，未把该项记为通过。
- 最终内容 ID `aa51f9311088f2e146018e42721073fad86a7a2972a752593e018f2aeee6aba5`，发布 115，设备上报 success。
- 启动 ID `3619d3ed-f0a2-4688-8267-6e630c396f89`；零失败服务，双 rootfs 槽和当前 kernel/rootfs 完整 SHA256
  检查通过，日志持久化、启动归档确认与 UTC+8 校时通过。
- 所有调试能力检查通过；GDB 在线复现 SIGSEGV，显示 process_request、key=42、
  record=0x0 和源码。离线 core 为 278528 字节，SSH 传输后 SHA256
  `b0b8ab5a27b62e22acedca6dbaf25ae7c3dfcac62d5605977d6efa46edcddef3` 一致，匹配符号和完整 sysroot 下回溯正常。
- 参考修复保留正常输入 1 的 value=64，不存在的输入 42 返回 2。strace 捕获 write，
  ltrace 捕获 strtol/printf，Valgrind 零错误；perf task-clock、cycles/instructions
  实际可用；trace-cmd 成功保存四个 CPU 的调度事件。
- SSH 的 root 调试登录在升级后正常，使用升级前缓存的主机指纹校验通过。
  私钥只保存在设备 /data/ssh/host，不进入固件或仓库。
- 原生产 BusyBox 不包含 command 内建，能力检查改为按 PATH 检查可执行文件；
  在旧/新实机 shell 中均验证。Core 上限按 ash 的 512 字节单位设置为 32 MiB。
- 主机案例 4 项、配置快照等价性、实际 FIT 解析/恢复 4 项、ARM64 initramfs
  加载和真实包上传下载回归通过。BSP 恢复测试夹具由固定 32 MiB 改为按实际
  rootfs 大小对齐分配，实际 SD 布局保持不变。

工件：`output/validation/stage1-debug-elfcore/`；初版和对照实验保存在
`output/validation/stage1-debug/`。匹配符号自动导出并校验；只更新 kernel/rootfs，
未烧写工厂镜像或更新实机 SPL/U-Boot。案例手动运行，未在启动时注入故障。
