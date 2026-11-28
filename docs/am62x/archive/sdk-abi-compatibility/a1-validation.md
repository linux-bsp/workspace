# 新轮次 A1：公共 SDK 日志策略数据布局 AM625 验收

2026-11-28。[工程记录](../../../../edk/docs/archive/sdk-abi-compatibility/a1-validation.md) · [本轮板验索引](README.md)。E=`output/edk-sdk-abi-compatibility-a1-20261128-095705-o6ZDzN/`，C=E/candidate2/，F=C/final/。

指定 MAC `1c:63:49:22:c4:f7`，HWID `1010001000110000`，aarch64，可信上一轮 SSH key。开工 boot `fa7a815f-b166-4c3a-87bb-2cf9e53468cd`，A 槽确认，现役完整 ID `452a56bde73f16133dd32557b5785dd8d5ec5714cd7b46ef92229547b3004fc9`，fwctl version、ota-status、health-check 通过（C/board-start.log）。

旧 AArch64 默认配套基准与实际旧正式 rootfs/staging 库分别使用同一冻结旧程序（SHA `c30fdfdd62865c74d79c08040b0e8da913c2ba36955377eec5a9a01b0713f11c`），真实字段布局 enum=4 struct=84、偏移 0/68/72/76/80。三组入参/落盘/读回均为 `review 42 2 3 25`。E/legacy-board/board.log，前两次夹具仅因板端缺 stat/cut 未完整执行，保留原日志；使用 shell 目录权限模式核对后原样完成。

C/arm-layout 最终实际 12 个配套 SDK 前缀（两顺序、仅配置头、受管、合法 flags、strip、旧未知前缀的独立恢复、旧头刷新、实际旧正式库的补头/升级）。F/board-probes.tar、board-probes.tar.sha256、manifest.sha256、links.manifest；562 个文件与 52 个软链接逐项匹配。每前缀实际 CMake/pc 消费者、冻结旧程序，共 36 次调用；`libbsl` 实际加载对应临时路径。各自 policy-dir 权限 0700，set/list 退出 0、count=1，domain=review/event=42，实际写入 `OSALOG1` 和 `review 42 2 3 25`，读回 level/capture/burst `2/3/25`。无正式策略写入，所有夹具只在独立临时目录，清理通过；正式服务只读、路由保持、健康通过（F/board-candidate.log）。

## 正式发布

候选 ID `1bab5b05507f357b4dbf15f3892cc6f22746384f45976d528f53b999ebc7e5ea`，v0.0.1 packed 1，kernel SHA `f1bd10f1080a84cb9f655d349ad559180f7518526d13ec7a4245f4e5b65c7c49`、rootfs SHA `bcbf8ec70b25f2cb77f0668c255d82378415a108b7837df457165a739a431de5`、OTA SHA `898abf46400afca12e587e778c2246fbb86eab7b2b6ddddac7607ffc8b796cad`。与现役内容不同，第一版未发布；2026-11-28T10:27:47+08:00 发布 `draft-MTEcMD`（F/publication.json、upload.json），设备报告 `2026-11-28T10:29:34.067423+08:00 id=1bab5b05507f357b4dbf15f3892cc6f22746384f45976d528f53b999ebc7e5ea phase=success running=1 target=1 quarantined=False`。串口确认重启后 SSH key，新 boot `9df4b3ce-4fa4-4a10-a2c8-9aec3a8c3e16`，B 槽确认；FWCHECK1 match、健康、8 个 active、0 failed、9/9 实装关键制品 SHA 与正式 rootfs.tar 一致。F/serial-key.log、board-check.log、board-package-compare.log、ota-timeline.log、device-transaction.json、post-ota-verify.log。

发布后 F/board-installed.log 重跑同一 36 次 ARM64 字段往返，摘要、加载路径、退出码、输入/落盘/读回、目录权限、健康、路由和回收全部通过。仅指定 AM625 发版；其他真实服务器未写入/控制。A1 板验通过。
