# A15：AM625 独立包测试与板级测试分离验收

2026-11-26 16:04:47+08:00 V6 PASS，E=`output/edk-portability-a15-20261126-160151-yidZQY/`。
[EDK A15 工程](../../edk/docs/edk-portability-a15-validation.md)。

使用 A7 串口核实的 SSH key，MAC 1c:63:49:22:c4:f7、HWID 1010001000110000，
boot ID 8fb95921-66b5-431b-b5b5-1074e58148c3，kernel/rootfs A 槽 confirmed successful=1、v0.0.1 packed 1。
完整 firmware_id 16f44b78e3915e830ae7bdcf2293ebc06738b1a187edead8d74aab3359b81730，
FWCHECK1 match，catalog 同设备/身份 success/running=1；9/9 运行制品与 A7 发布 SHA 相同。
A14 实际交叉 recipe SDK 编译只读探针 SHA256 53f9ca10bea9a507674d6afd84d9c46def2ac715918cad38e2dcbfe059d28793，
实际从 /usr/lib 加载正式库，读取项目 phytium-s5000c、Satellite v1.0 timeout 2000ms、PDM generation 13 两个设备。
临时目录清理，health-check 通过，7 项服务 active，V6 PASS。
E/board-v6.sh/.log、board-probe-elf.log、board-formal-match.log。
正式聚合 12/12、独立板套件 10/10，通用无启动链套件 2/2。
仅测试和文档变更，未新发 OTA，未执行其他真实服务器的控制或写入。
