# AM625 节点 1 Redfish 冷启动超时整改验收

2026-11-25，独立于 A1–A6 后续审计阶段。
[EDK 开发与主机回归](../../edk/docs/edk-redfish-recovery-validation.md)。
证据目录 `output/edk-redfish-recovery-20261125-2306/`，
故障基线 `output/bmc-node1-timeout-20261125-2256/`。

| 验收项 | 结果 |
| --- | --- |
| 实板 | am625 / 192.168.10.211 / MAC 1c:63:49:22:c4:f7 / HWID 1010001000110000 |
| 基线 | EDK 48967330、BSP e9cd0ad2、工作区 3696dc6e；M7 活跃发布 2870bc37… |
| 发布 | 2026-11-25 23:17:50+08:00，draft-vmgZuL；v0.0.1 / packed 1 |
| firmware_id | `683e05eaa30726d7d54eced37f55f0c446f3ddcb7b366d75a9fcca935fa9bfed` |
| OTA 归档 SHA256 | `6da1849bb81e2007a68b69f75ba611efa35d08387569e918158a227deebacc07` |
| kernel 12913344 bytes | `2dc3ccdf4d64de0fa3a1839577bb2366289de5440be516d058c0584321a35470` |
| rootfs 30457856 bytes | `7b553c1073f8bbd589c93e5212ffa426d6a97599d99f7e923d9d208b5f378688` |
| 设备最终上报 | **success**，23:19:31+08:00（23:19:35 轮询确认） |
| 槽位和 boot | A；`542e6381-e300-41b7-ae2b-41dddbbd0583`，源 boot `3a2bf0c8-60a6-4fa0-bc8f-b566f9813761` |
| 正式 libserver.so.2 | `d5e4363f1a84e2d784f20c42a03bf87911f5339c8020873261370ffc7cbe8c5f` |
| V6 | 23:19:51–23:20:23，`board-v6.sh`：八制品 digest 匹配、fwctl 版本/OTA/健康、time/log、八服务健康，连续六轮六源均有效且失败=0 |
| 旧 SDK 只读探针 | 23:20:38–23:20:40，Redfish 866 ms、AUTO 1374 ms，均成功并实际走 Redfish，off |
| 本地回归 | 256/256，历史格式诊断 832 不增加，正式镜像和真实 OTA 包验证通过 |

节点 1 原故障为 Redfish 冷查询超过 2 秒且失败销毁上下文，优化后不改
`redfish,ipmi` 协议优先级、采样周期或全局预算；正式新启动已经从首次采样开始
连续成功。没有执行任何其他真实服务器的控制、部署或配置写操作。
剩余 TLS 证书信任问题独立处理（本次未放宽现有配置）；
通用 AUTO 超时预算公平性仍不是本次实现的承诺。
串口确认新 SSH 指纹后使用严格固定密钥。
提交和远端核验顺序：EDK master → 工作区准确 gitlink / master，
验证记录的自提交 SHA 以同次远端核验回报关联。

EDK 子仓远端已验证：`65b1bff3ed1d3c821c20689067a116708c19c8ce`。
