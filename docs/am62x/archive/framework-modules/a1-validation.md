# A1 产品与应用装配 AM625 验收

2026-11-28。[EDK 工程结论](../../../../edk/docs/archive/framework-modules/a1-validation.md)。
E=`output/edk-framework-modules-a1-20261128-132706-ohcpDe/`、F=E/final。

指定 AM625 HWID `1010001000110000`、MAC `1c:63:49:22:c4:f7`。实际正式包版本 v0.0.1/packed 1，完整 ID `a59c703c8c85d50599faba5eada002ee35f11b54bd3ec3a9aa16845480367bac`、kernel SHA `42ce0e3a36b210a4a8a761f9ed8905df612b994ef70bccbad9b83eabcdad615a`、rootfs SHA `2cf1cc9849fe159038dee227e577fcdbafb0bd18e65cc3ee94ca8f75ba018e9e`、OTA SHA `e415b563e86369cd907e1352c9e222dbee3e0590cd7e9e6f16415d787bdacc15`。publication `draft-dTt7gf`，2026-11-28T13:46:18+08:00；设备报告 2026-11-28T13:48:06.387457+08:00 id=a59c703c8c85d50599faba5eada002ee35f11b54bd3ec3a9aa16845480367bac phase=success running=1 target=1 quarantined=False。串口确认新的 SSH key 和 boot `e2cb66d2-5087-4daf-81d0-2f6265fa2488`，B 槽 confirmed，FWCHECK1 match、健康检查、8 active、0 failed；四库、PDM、两进程和配套配置 8 项实际 SHA 与 rootfs.tar 一致。F/board-installed.log、board-package-compare.log、device-transaction.json 和 serial-key.log。

实际 ptelemetryd --check-config 输出 phytium-s5000c 及节点点表；psatellited --check-config 输出 v1.0、can0，实测运行进程映射指向正式 SDK。原冻结 ARM64 查询 ABI 程序的 SHA 与 A1 前历史夹具相同，正常产品、未知 HWID 原错误返回均通过；四个库 ABI 及字节不变。复测健康通过。CI 62/210/104（真实包补跑），BSP 14/14、镜像 19/19、恢复/加载器检查合格。其他真实服务器只读；未安装 bootloader 不作为本次实装验收。阶段通过。
