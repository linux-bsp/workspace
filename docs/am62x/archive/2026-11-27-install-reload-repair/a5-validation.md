# A5：运行时公共接口与 ELF 架构 AM625 验收

[工程记录](../../../../edk/docs/archive/2026-11-27-install-reload-repair/a5-validation.md)。E=`output/edk-install-reload-a5-20261127-140132-yVMc9w/`，F=E/final/，2026-11-27。

可信 A4 key 核验 hostname、MAC 1c:63:49:22:c4:f7、HWID 1010001000110000，原 boot 74c54f6e-838e-495f-99b2-025a0b8e8fe3、B 槽、完整 ID acbe92f308ef393319395d06b73037f05a533548c1d82f65ee1743dc6029958c，健康。ARM64 原构型 CAN SDK 冻结消费者 SHA 7e5baaa416718663a2e1a3e2662ea77d1416a899386780b41c2584694c0aaaae；主机实际保护前后整树一致、五个导出保留；独立临时板目录加载 protected-before/after、same-ability-upgrade、cross-protected，各 NULL 空句柄检查返回 -EINVAL、退出 0，未开总线或发送帧；三组裁剪后 SDK 基础消费者实际运行成功。原 legacy_pconfig 查询匹配与未知 HWID 通过。F/board-candidate-actual.log 保留实际加载路径及 SHA，正式服务仅读。

正式候选 v0.0.1，packed 1，OTA SHA 9d680f4e935b19578af59f187db89f4683876631af20d7b5341c3a604692e46c。2026-11-27T14:11:02+08:00 发布 draft-coEfpS，2026-11-27T14:12:54.286980+08:00 id=f4bd026369af3859fd7fce6312d53609630bdff1d4549f3d8c08e5585de6017c phase=success running=1 target=1 quarantined=False；新 boot 54528f60-f3b5-4a8c-b7b3-e1e2b79b4aaa，A 槽确认及 FWCHECK1 match，fwctl health-check 成功，8 active、0 failed，9/9 实装 SHA 与镜像匹配。F/serial-key.log、board-check.log、board-package-compare.log、board-installed.log、device-transaction.json；重新执行上述本阶段专项成功。其他服务器无控制、未安装 bootloader。A5 实机通过。
