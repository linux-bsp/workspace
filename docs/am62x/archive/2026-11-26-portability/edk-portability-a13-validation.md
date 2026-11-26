# A13：AM625 旧 PDI 升级后候选与正式运行布局验证

2026-11-26 15:30:45+08:00 V6 结束，E=`output/edk-portability-a13-20261126-152019-XjZwsW/`。
[EDK A13 工程验收](../../../../edk/docs/archive/2026-11-26-portability/edk-portability-a13-validation.md)。

固定使用 A7 串口确认的 SSH ED25519 主机密钥，先断言 am625/aarch64、
MAC `1c:63:49:22:c4:f7`、HWID `1010001000110000`。
boot ID `8fb95921-66b5-431b-b5b5-1074e58148c3`，v0.0.1 packed 1、kernel/rootfs A 槽 confirmed successful=1，
完整 ID `16f44b78e3915e830ae7bdcf2293ebc06738b1a187edead8d74aab3359b81730`。
A7 `draft-3v0bSf` 的本机 catalog 同一设备/ID/success/running=1；包 SHA256
`b05b1f984f7e9e2dad669f81b08bab8926e91c5b9bdecaa6b322553e64fe8b7c`，
当次 `fwctl ota-check` 对原实际 kernel/rootfs 长度、SHA 返回 FWCHECK1 match。
正式运行内容未改变，未发布新 OTA。

| 临时装入指定板 /tmp 的实际升级 SDK | SHA256 |
| --- | --- |
| libpdi.so.2 | `e41497d87051611196b07fdd523170b901c50de223e4a9ccb455d2cbc9178b00` |
| libbsl.so.2 | `e1e7b416f7049b5db923708e7695712eba8c58edab05cc0bc3d8d02cbdc632cd` |
| 从升级 SDK 重新交叉编译的公共 API 探针 | `d152f3d9ea0337de5e473c903b31f6cbbc19df87ffd5c237a03ab1917bad625a` |

实际 LD_DEBUG 加载 `/tmp/edk-a13-sdk.Zxc0P5/lib/libpdi.so.2` 和对应 libbsl.so.2。
复用 A12 原属性输入，-12000、INT32_MIN/MAX、溢出和错误先后、缺失/非普通/非法输入、失败输出哨兵、
无写端 FIFO 限时均通过；不是物理新增传感器验收。E/board-bundle/SHA256SUMS、board-v6.sh/.log。
临时目录显式清理并断言不存在。

实板正式当前链接 `libpdi.so -> libpdi.so.2 -> libpdi.so.0.0.1`，
`libbsl.so -> libbsl.so.2 -> libbsl.so.0.0.1`，旧 ABI3 两项均不存在；九项真实运行制品与 A7 已发布 rootfs 同摘要。
`fwctl health-check` 成功，八服务 active、无 failed unit。E/board-formal-match.log。
隔离旧 ABI 注入仅本机 staging/target，ABI3 stub 退役后 loader 不再加载是预期；正式支持仍为 ABI2。
其他真实服务器未执行控制、配置写入或部署。
host 47/47、BSP 12/12、定向 4/4，实际提交与远端核验 E/git-verification.log，干净交接复验 E/clean-checkout.log。
