# A3 Server 目录与协议端点 AM625 验收

2026-11-28。[EDK 工程结论](../../../../edk/docs/archive/framework-modules/a3-validation.md)。
E=output/edk-framework-modules-a3-20261128-141950-pncNN3/、F=E/final。

指定 HWID 1010001000110000、MAC 1c:63:49:22:c4:f7；完整 ID 7890421d2826d540f98beec64c0488f6b7c5db917f3c4bbb2d6d531ce139a599、kernel SHA 4b80edc235d41b987968a036bbc37a9bf86de6af5dd54bcdce41616a4944c1b4、rootfs SHA 7708bb4bc6eec035af8d54a6cf6577fecf54e840108bfb881ec4d2b5e6e5c04a、OTA SHA 6222d4dbb324f41f4315c7b4b8b6059cbf77d5256ce3fcc768416c30497302b9，版本 v0.0.1/packed 1。publication draft-Rgj8T6，2026-11-28T14:34:47+08:00；设备报告 2026-11-28T14:36:37.010661+08:00 id=7890421d2826d540f98beec64c0488f6b7c5db917f3c4bbb2d6d531ce139a599 phase=success running=1 target=1 quarantined=False。可信串口确认 boot fa065a2b-d944-4206-8f47-bf81a410bc70 和 SSH key，确认槽、FWCHECK1 match、8 active、0 failed、健康及 8 项实装摘要与正式包匹配。

实际 ARM64 公开 SDK probe 读取本机 catalog，节点 1/2/3 与索引 1/2/3 一致，BMC status 0，PMC 缺席 -ENODEV 或已声明 0，解析返回一致；新 libserver 实际加载并与镜像 SHA 相符。ptelemetryd/psatellited --check-config、runtime-status 缓存只读查询的点/索引/provider 集合发布前后相同。没有向其他真实服务器发控制；采样超时等真实状态不冒称成功。CI 62/212/106、真实包补测、BSP 14/14、镜像 19/19、恢复和 loader 均通过。F/board-installed.log、board-package-compare.log、device-transaction.json、E/board-start.log。未安装 bootloader 不计实装验收。阶段通过。
