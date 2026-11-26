# A3：SDK 安装拒绝保护 AM625 验收

2026-11-25。[EDK 实施与验证](../../../../edk/docs/archive/2026-11-26-module-audit/edk-module-audit-a3-validation.md)。
原始证据 `output/edk-module-audit-a3-20261125-2342/`，正式制品 `formal-final/`。

| 验收项目 | 实测 |
| --- | --- |
| 指定设备 | am625 / 192.168.10.211 / MAC 1c:63:49:22:c4:f7 / HWID 1010001000110000 |
| 交叉 SDK 临时加载 | 23:51:20，真实隔离 staging 成功 on 安装、被拒后保留 SDK 分别使用旧/新消费者，四次通过；核对候选 libpdi/libbsl/探针/文件摘要和实际 loader，清理后健康和原八制品一致 |
| 正式发布 | draft-LqdCiD，23:57:35+08:00，v0.0.1 / packed 1 |
| full firmware_id | `153f0f8d544a312e3147943b07d0e6ee555aeae6a6f1bd662d77e8e6ece4fb76` |
| OTA 归档 SHA256 | `87c5b24b6e33674e2cb4fd9210c26e3b114342ac76289f659c355016d279b732` |
| kernel (12913344 B) | `098b7475aaa284525401ee089a5f1e40e9146535de93e974a30501e0a22d44cd` |
| rootfs (30457856 B) | `079885b8b3b672d56b9d0a362e8708fb7434bd335ebfeb9e9440ac3871688414` |
| 设备最终确认 | **success** 23:59:13，轮询 23:59:15，无 quarantine，槽 B |
| boot | 新 `64e72465-1a3e-4a48-b1e8-8eb6289e83ad`，源 `542e6381-e300-41b7-ae2b-41dddbbd0583` |
| 运行制品/V6 | 23:59:34–23:59:40，八 SHA256 与包中 rootfs 全匹配，fwctl version/ota-status/ota-check/health-check，八 unit 正常，实际 PDM 旧 SDK 枚举，六源状态0/失败0 |
| 测试 | 最终 259/259；两组件拒绝整树不变、真实 Buildroot staging 拒绝/恢复/清理/第三方保留，镜像/OTA 回归通过 |

正式配置仍不安装开发头且 hwmon 关闭；本阶段隔离的 on SDK 不作为
正式镜像。正式重建引起 PDM 构建身份及分区内容变化故重新发布。
严格 SSH 用串口验证新指纹，OTA 入口仅指定板 IP /32，其他服务器仅只读。
实机日志、发布事务与源快照见正式证据；先推两子仓再更新工作区 gitlink。

子仓远端已验证：EDK `0fa3a4f822acc3274394522093fb0637828ad4b3`、BSP `338f21d3545144f9579f36d63ecb0dc1d19f598f`。
