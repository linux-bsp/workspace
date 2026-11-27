# A9：私有参考安装锁生命周期 AM625 验收

[工程记录](../../../../edk/docs/archive/2026-11-27-install-reload-repair/a9-validation.md)。E=`output/edk-install-reload-a9-20261127-151512-8wCICR/`，F=E/final/，2026-11-27。

可信 A8 key 核验 MAC 1c:63:49:22:c4:f7、HWID 1010001000110000，旧 boot a08c291a-ec9b-480e-abe6-b22096d0b753、B 槽、完整 ID 4ab33b73c7fe3b998c5ebfe4fdccd63efdf1879fd85a2658d1583935b0e794ca，健康。主机真实 ARM64 四组并发胜出前缀与串行参考整树一致，另 15 次重复、失败及重试的 reference-lifetime 前缀与串行参考 usr 树一致；17 个实际私有键无新增全局锁，真实锁 inode 稳定。板端临时目录封装五组实际产物，逐一 SHA、链接及配置查询 project=phytium-s5000c、exit=0、实际局部 libbsl.so.2 载入路径匹配；旧 A1 冻结查询消费者与三组兼容前缀及正式系统通过，未知 HWID 原契约通过。F/board-candidate.log。无板上 CMake 或系统目录并发写入，整板路由及正式只读服务保留。

正式候选 OTA SHA 7901658dd697521af22b506a1caa98a3501e62161b131f45258ca1470bd4367f。2026-11-27T15:22:11+08:00 发布 draft-6jyohz，2026-11-27T15:23:47.974423+08:00 完整 ID 6a268233332f4ff8b1703c27b917f776f2f7887dc496fa997c16d54f763dfeb1 phase=success running=1 target=1 quarantined=False。新 boot a36943e6-b9f1-4f3a-8cd1-cf9b8c1d9d8e、A 槽确认、FWCHECK1 match、健康、8 active、0 failed、9/9 实装摘要一致。F/board-installed.log 再次运行五组工具、旧消费者和只读正式服务，全部通过。F/board-check.log、board-package-compare.log、post-ota-verify.log、device-transaction.json、serial-key.log。无其他真实服务器控制或 bootloader 安装。A9 实机通过。
