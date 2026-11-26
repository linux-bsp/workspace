# A12：AM625 最小 hwmon SDK 实板与最终验收

2026-11-26 14:51:11+08:00 V6 结束，E=`output/edk-module-audit-a12-20261126-143843-I9pIn0/`。
[EDK 最终开发和回归记录](../../edk/docs/edk-module-audit-a12-validation.md)。

严格使用 A7 串口核实的固定 SSH 主机 key；实际 hostname am625、aarch64、MAC `1c:63:49:22:c4:f7`、
HWID `1010001000110000` 断言成功。boot ID `8fb95921-66b5-431b-b5b5-1074e58148c3`，
v0.0.1/packed 1、A 槽 confirmed successful=1、full firmware_id
`16f44b78e3915e830ae7bdcf2293ebc06738b1a187edead8d74aab3359b81730`。
本机 catalog 同一 A7 `draft-3v0bSf` success/running=1、实际 `fwctl ota-check` FWCHECK1 match，
包 SHA256 `b05b1f984f7e9e2dad669f81b08bab8926e91c5b9bdecaa6b322553e64fe8b7c`、9 项运行制品与 A7 实际发布内容匹配。
本阶段主机测试/文档变化，不重建正式镜像或新发布。

## 最小交叉 SDK 实际加载

临时 SDK 是本阶段以原 AM625 toolchain 只构建 pdi/BSL 的测试候选；正式生产配置仍关闭 hwmon，临时开启不改变正式板上库。
E/cross-sdk、cross-probe、board-bundle/SHA256SUMS。

| 实际装入 /tmp 的制品 | SHA256 |
| --- | --- |
| hwmon libpdi.so.2 | `28b0f5226f11b78ca543b13207a5427abc5c40b94be2b4009c613e0bf16de040` |
| libbsl.so.2 | `fab5195f418fa1c22d1427e6d480fd8dd37022cbbd3358c1d4f71f580799993c` |
| 同一公共 API 探针 | `d152f3d9ea0337de5e473c903b31f6cbbc19df87ffd5c237a03ab1917bad625a` |

实际板端 tmpfs `/tmp/edk-a12-sdk.4RNeXG/lib/` 的两库由 LD_DEBUG 确认加载；
SHA 比对包括两库、探针、十个原生 fixture 的实际文件。复用原探针，全 13 个属性路径以及相对路径断言，
正常负温 -12000、两 int32 边界、正负溢出、错误优先级、无换行/过长/无文件/非普通文件、
每个失败输出哨兵 123456 保留；无写端 FIFO 5s bounded 返回 -EINVAL，全通过。非实体新传感器验收。
E/board-v6.sh、board-v6.log（实际 probe 及 loader）和交叉 QEMU E/cross-probe-run.log，板端首次即通过。

临时目录显式删除并断言不存在；复查 `fwctl health-check` 成功、八 unit active、零 failed unit，
九项实际正式运行制品与 A7 rootfs 相同，E/board-formal-match.log。无设备新 OTA、未重启、未安装 bootloader；
其他真实服务器未执行有状态控制。最终 EDK 253/253、BSP 12/12，定向 5/5；逐仓 gitlink/远端核验见 E/git-verification.log。
A8–A12 无未完成工程验收；A6 真人首次接手仍待验证，不以独立 AI 或本次自动化替代。
