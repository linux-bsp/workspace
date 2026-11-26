# A10：AM625 实板 runtime-only 拒绝与完整 SDK 更新

2026-11-26，E=`output/edk-module-audit-a10-20261126-141044-5WQUzn/`。
[EDK A10 验收](../../../../edk/docs/archive/2026-11-26-module-audit/edk-module-audit-a10-validation.md)。

14:21:04+08:00 当次 V6 结束且通过。严格固定 A7 经串口核实的 SSH key，
先断言设备 am625/aarch64、MAC `1c:63:49:22:c4:f7` 和 HWID `1010001000110000`。
boot `8fb95921-66b5-431b-b5b5-1074e58148c3`，v0.0.1 packed 1、kernel/rootfs A 槽
confirmed successful=1；完整 `16f44b78e3915e830ae7bdcf2293ebc06738b1a187edead8d74aab3359b81730`。
A7 `draft-3v0bSf` 最终 success，当前 catalog 仍同一设备、ID、running=1/success。
包 SHA256 `b05b1f984f7e9e2dad669f81b08bab8926e91c5b9bdecaa6b322553e64fe8b7c`，
实际分区摘要 FWCHECK1 match、九运行制品与实包相符；正式镜像内容未改，不创建新 OTA。

| 临时交叉 SDK | libpdi.so.2 SHA256 | 运行结果 |
| --- | --- | --- |
| runtime-only 拒绝保留 on | `675454bd905d04a691071263531409d3d7e0df7b7b62c1425cf3b41c2e80a36f` | 拒绝前编译的旧探针、拒绝后新探针均通过 |
| 完整 off 更新 | `0453156d2cdd9c5fa2c07e2efe116363cee6109059fbbe8680014f790774359a` | pdi_manager_close(-1)=-9；主机编译 hwmon 预期失败、无导出符号 |
| 完整 on 更新 | `675454bd905d04a691071263531409d3d7e0df7b7b62c1425cf3b41c2e80a36f` | 完整更新后重编的 hwmon 探针通过 |

三套 libbsl.so.2 都为 `e1e7b416f7049b5db923708e7695712eba8c58edab05cc0bc3d8d02cbdc632cd`，
三份独立编译的 hwmon probe 摘要均 `d152f3d9ea0337de5e473c903b31f6cbbc19df87ffd5c237a03ab1917bad625a`，
off probe `6bf695ed06fe1927cffbae6b1e4e9f3f4f3b0cce9e56f124f55c882909d5a5d2`。
E/board-bundle/SHA256SUMS、board-v6.sh / .log。LD_DEBUG 证明实际加载
`/tmp/edk-a10-sdk.avhJqT/board-on/`、`board-off/`、`board-updated-on/` 各自 libpdi/BSL。
hwmon 正常温度 -12000、INT32 边界、错误优先级和输出哨兵、无写端 FIFO 限时通过；属性夹具为本机 tmpfs，
不是新增物理传感器验收。复用 A9 经验证的本地 FIFO 小工具和摘要比对，临时目录显式清理确认不存在。
复查 Satellite ABI3 当前链接，三项旧实体均无，八服务 active、无 failed unit、`fwctl health-check` 成功。
E/board-formal-match.log。无新运行固件或 bootloader 安装，无其他真实服务器控制/配置写入。
完整 EDK 250/250、BSP 12/12，实际提交/远端/gitlink 核验 E/git-verification.log。
