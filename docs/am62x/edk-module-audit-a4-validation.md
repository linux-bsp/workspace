# A4 AM625 项目装配验收

2026-11-26。[EDK 开发记录](../../edk/docs/edk-module-audit-a4-validation.md)；
证据 `output/edk-module-audit-a4-20261126-0005/`。

| 项目 | 实测 |
| --- | --- |
| 设备 | am625 / 192.168.10.211 / MAC 1c:63:49:22:c4:f7 / HWID 1010001000110000 |
| 正式配置 | 原 CCM 双后端、PMC host pmcd；归一化仅增空验证字段 |
| 正式发布 | 00:12:34+08:00，draft-GdOrkS，v0.0.1 / packed 1 |
| full firmware_id | `0e27a1546a308cb8d6a3844e6d937440318ddf367043b79717ffb323e526187c` |
| OTA SHA256 | `aae594cb88f19bf8370151774b8bc8dc86bd63e1efa7352d753e00b9118aceb2` |
| kernel 12913344 B | `1655713575f3330c64af724041acd74b8e1b9b7640f6316b7f7b91d347f46e0d` |
| rootfs 30457856 B | `2ca79d8131a6a20469129acffd77a400e6d50fd2ebe82a729b28eb51de0014bf` |
| 最终设备状态 | **success** 00:14:08，轮询 00:14:13；A 槽、无 quarantine |
| boot | 新 `35831c39-3102-45c7-87f1-71adf8c2b865`，源 `64e72465-1a3e-4a48-b1e8-8eb6289e83ad` |
| V6 | 00:15:16–00:15:20；严格 SSH、OTA 核对、健康、八制品及八 unit 全通过，旧 SDK PDM 枚举 |
| SDK 项目查询 | 实际加载 /usr/lib/libbsl.so.2，登记 HWID 1010001000110000 → phytium-s5000c points=4；未登记合法 HWID 1010001000310000 → -ENODEV/NULL，探针 exit=0 |
| 遥测 | 三 Redfish、三 PMC 来源均状态0；节点1本 boot 累积2次失败、连续失败0；附加六轮 sequence 28→34、失败总数未增、每轮 Redfish 状态0 |
| 回归 | 259/259、单后端实际 arm64 SDK、实际 package hook/依赖、第二项目夹具及 OTA 镜像通过 |

仅指定 AM625 接收 OTA，其他真实服务器只读。第二项目为测试夹具，未安装到其他设备。
详见 board-v6.log、board-project-v6.log、board-redfish-stability.log、ota-success.json。
先推 EDK/BSP 两子仓再提交工作区精确 gitlink；提交核验见证据目录。

子仓远端已验证：EDK `5928ebfd4b60613a68354eb28a18e44d9858019c`、BSP `8cfb9a7101a4662c72ad22b9a7db2606c8c6daa9`。
