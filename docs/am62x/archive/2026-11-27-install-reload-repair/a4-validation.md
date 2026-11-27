# A4：工具组件安装 AM625 实机验收

[工程记录](../../../../edk/docs/archive/2026-11-27-install-reload-repair/a4-validation.md)。E=`output/edk-install-reload-a4-20261127-134921-w4q51r/`，F=E/final/，2026-11-27。

原 A3 可信 key、MAC 1c:63:49:22:c4:f7、HWID 1010001000110000、boot b5e07085-a443-4365-8451-2d72bcbff67a、A 槽、ID 36ffeb03271a8db9a3365f20b2c4732642d3aaf34667bf72a43de90e93ce4bb7、健康。主机 ARM64 预先保护前缀，拒绝前后整个树相同；真实板上临时 compat-target、isolated-prefix、compat-prefix 各使用对应动态库，配置查询均返回 phytium-s5000c，实际 loader 路径与文件 SHA 在 F/board-candidate.log。原 A1 冻结程序正常与未知 HWID 查询成功；正式服务仅读。

2026-11-27T13:58:00+08:00 发布 draft-ezPhlx，2026-11-27T13:59:36.707328+08:00 id=acbe92f308ef393319395d06b73037f05a533548c1d82f65ee1743dc6029958c phase=success running=1 target=1 quarantined=False；新 boot 74c54f6e-838e-495f-99b2-025a0b8e8fe3、B 槽确认，健康、9/9 实装文件与镜像匹配；F/board-installed.log 重复三组原工具和旧 ABI、正式只读结果。F/board-check.log、board-package-compare.log、device-transaction.json、serial-key.log。无 bootloader 安装和其他真实服务器控制。A4 实机通过。
