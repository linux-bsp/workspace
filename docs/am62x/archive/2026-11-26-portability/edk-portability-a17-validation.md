# A17：AM625 HWID 固定协议向量与设备身份验收

2026-11-26 16:36:53+08:00 V6 PASS，E=`output/edk-portability-a17-20261126-163128-TbpKJm/`。
[EDK A17 工程](../../../../edk/docs/archive/2026-11-26-portability/edk-portability-a17-validation.md)。

使用 A16 串口核实的 SSH key，MAC 1c:63:49:22:c4:f7，
boot ID 727e44b9-d1b1-47f8-b992-5be7ca25d7f3，kernel/rootfs B 槽 confirmed successful=1、
v0.0.1 packed 1、完整 ID 3856203dcd4a0c1bf712bd7969558533de654a0e178f1a1e10dd0ad03769afc3。
FWCHECK1 match、health-check、8 unit active，零 failed units，9/9 运行制品匹配 A16 实际包。
catalog 同设备/同 HWID/完整 ID success/running=1。
`fwctl hwid show` 读取 1010001000110000 pcb=v1.0 source=uboot-env；没有调用 set。
实际 DT boot property 为 17 bytes，hex 3130313030303130303031313030303000，严格 NUL 结尾。
E/board-hwid-property.bin/.log。

A14 真实 recipe SDK 公共头/库与正式 GCC 交叉编译探针，SHA256
2041d33c81da8af34ce694b6c2b762247b8148bb1ee415265c68bb403c22fcd3。
实际从 /usr/lib 加载 libbsl.so.2，全固定向量通过，bsl_hwid_read 返回 1010001000110000，
bsl_pconfig_find 选中 phytium-s5000c，清理临时目录后复核健康。
首次板端 od 缺失，从可信连接只读提取属性后在主机验证；第二次精简 BusyBox 的 sha256sum 无 -c，
改为比较摘要，保留两次日志，最终重新执行完整实板断言。
E/board-v6.sh/.log、board-probe-elf.log、board-formal-match.log。
阶段仅测试和文档修改，沿用 A16 已成功发布镜像，未变更 HWID、未新发 OTA、未控制其他真实服务器。
