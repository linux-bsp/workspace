# A8：工具及库依赖最终组合 AM625 验收

[工程记录](../../../../edk/docs/archive/2026-11-27-install-reload-repair/a8-validation.md)。E=`output/edk-install-reload-a8-20261127-150035-14UR10/`，F=E/final/，2026-11-27。

可信 A7 key 核验 MAC 1c:63:49:22:c4:f7、HWID 1010001000110000，旧 boot 85d93e54-a20a-4034-ba28-b2fc6f15d75d、A 槽、完整 ID 2e37916a65a9c07578facd982fc1169671c6e4f7f36316fe6ccd0fca6a0761dd，健康。主机实际 ARM64 两反例均写前拒绝整树不变，F/board-probes.tar 对应同一批完整前缀。临时目录逐项核验实体 SHA 与链接，原受保护 ptelemetryd --help 显示 Usage、退出 1（既有正常帮助语义）且实际加载局部 BSL，无 PDI；匹配补库和工具后正常帮助退出 1，实际加载局部 BSL/PDI。另一构型遗漏工具目标的正例亦通过；兼容工具先装后补匹配库，无需重装工具，查询退出 0、project=phytium-s5000c，并实际加载临时前缀 BSL/Server；普通/受管 target 完整替换及同构型查询全部通过。F/board-candidate.log 保留实际 loader 和实体 SHA；A1 冻结查询消费者、正式服务仅读，整板路由不变。

正式 OTA SHA 4e4d132bbae29cffc10d7dd1a0d0365d695e9f5da7165ff78ee04941bb1ae709。2026-11-27T15:10:39+08:00 发布 draft-VfGtWX，2026-11-27T15:12:26.316302+08:00 完整 ID 4ab33b73c7fe3b998c5ebfe4fdccd63efdf1879fd85a2658d1583935b0e794ca phase=success running=1 target=1 quarantined=False；新 boot a08c291a-ec9b-480e-abe6-b22096d0b753、B 槽确认、FWCHECK1 match、健康、8 active、0 failed、9/9 实装 SHA 一致；F/board-installed.log 复跑上述全部实际工具与查询成功。F/board-check.log、board-package-compare.log、post-ota-verify.log、device-transaction.json、serial-key.log。无其他服务器控制或 bootloader 安装。A8 实机通过。
