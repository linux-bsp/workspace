# AM625 A6 独立 AI 模拟的模块实板验证

2026-11-26（北京时间）。用户因无真人测试者授权新独立会话模拟。模块修改与局部测试由
`/root/a6_first_maintainer` 独立 AI 执行，实板验证由本轮主维护者执行；不冒充真人。
证据 E=`output/edk-module-audit-a6-20261126-0950/`。
[EDK A6 开发记录](../../edk/docs/edk-module-audit-a6-validation.md) ·
[独立维护者原始报告](../../edk/docs/edk-module-audit-a6-maintainer.md)。

| 项目 | 实测 |
| --- | --- |
| 设备 | am625 / 192.168.10.211 / aarch64 / MAC 1c:63:49:22:c4:f7 / HWID 1010001000110000 |
| SSH | A5 实体串口确认的 ED25519 `SHA256:BrVgnZLS+2mVjHmJShyEHJltrWrunAoZbZXZGHbF5O0`，固定 E/board-known-hosts |
| 正式固件 | v0.0.1 / A5 `403502c59347e139db86422e02308a2581493c73a5f201e1bbe31cae7a906dc3`，B 槽 confirmed successful |
| boot ID | `34a43973-7489-478c-bfe1-7a2e8a47fb96`，前后一致 |
| 检查时间 | 09:53:30 初始；10:03:37–10:03:42 模块 V6 |

正式配置 hwmon 关闭，本次只有测试与文档改动，正式镜像继续采用已成功发布的 A5。
实际使用同一独立会话补丁的 ARM64 安装 SDK 消费者，不加载或替换板上生产库。
E/candidate-cross.log、candidate-dependency.log、candidate-layout.log、candidate-probe-elf.log。

- `ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=E/board-known-hosts root@192.168.10.211 "$(cat E/board-v6.sh)" < E/board-runtime.tar.gz`，
  脚本用 `fwctl version`、`ota-status`、`fwctl ota-check 1 12913344 85b89e0495ddba7a528b9a8a1e8deb5a8969406a586ff3e09583a9222bdee93f 30420992 07635f132a9fbc869f52c0c49aa497352144d1ed6c80743f7b76c0be5cdd9733`、
  `health-check`、MAC/HWID/boot ID 核对实际制品，FWCHECK1 match。
- `/tmp` 确认 tmpfs，归档候选探针和临时两库、普通属性文件及真实 FIFO，经 BusyBox tar 解包（板端没有 mkfifo applet），
  `test -p` 核对管道；SHA 校验 probe `d152f3d9ea0337de5e473c903b31f6cbbc19df87ffd5c237a03ab1917bad625a`、
  libpdi `35f64ed0004243e37eef108ec57525fcaee889528aec70a79c6b439747b33cc4`、
  libbsl `3b257199b65fe0989ace91ada808085de5d8c6b3522d4cd1970f2f7f6dbef584`、各普通夹具；
  临时目录 `/tmp/edk-a6.72VtfJ`，`LD_LIBRARY_PATH` 指定临时 SDK，`LD_DEBUG=libs` 记录实际载入
  `/tmp/edk-a6.72VtfJ/libpdi.so.2` 和 `/tmp/edk-a6.72VtfJ/libbsl.so.2`。E/board-runtime.sha256、board-v6.log、board-compare.log。
- 板端 `timeout -k 1 5 <probe> ...`，以下实际断言（输出哨兵 123456）：

| 输入 | 返回/输出 | 结果 |
| --- | --- | --- |
| -12000、INT32_MIN、INT32_MAX LF | 0 / -12000、-2147483648、2147483647 | PASS |
| -2147483649 LF | -ERANGE / 不变 | PASS |
| 12000 无 LF、2147483648 无 LF | -EINVAL / 不变（framing 优先） | PASS |
| FIFO 无写端 | -EINVAL / 不变，5s 内返回 | PASS |
| 普通垃圾、相对路径、目录、31 字节 | -EINVAL / 不变 | PASS |
| 2147483648 LF、2147483648X LF | -ERANGE / 不变（range 优先） | PASS |
| 缺失 | -ENOENT / 不变 | PASS |

14 路径断言及 summary PASS，脚本退出 0。探针结束后八个 unit active，无 failed unit，
`fwctl health-check` 通过，A5 八项已安装制品哈希均与正式包相同（E/board-compare.log），
boot ID 不变；BMC 三来源实际 Redfish、PMC 三来源 pmcp，sequence=336、累计失败=0，
last_status=0，未推断未来零失败。另只读确认 tmpfs 目录已删除和健康 E/board-after.log。
所有操作限指定 AM625 的临时夹具及只读检查；未触碰物理传感器、未改正式系统、未重新 OTA，
其他真实服务器未执行任何写入、电源操作或部署。A6 模拟候选 V6 PASS，而真人测试仍未实施。


10:14:49 最终只读健康复核（E/board-final-health.log）：仍为同一 B 槽及 boot，健康通过、
临时目录已清除；三 BMC Redfish 各 sequence=469、失败=0、last_status=0，三个 PMC 源
last_status=0，其中一源累计 1 次失败，不将快照扩展为无限期无失败。全预设 262/262，三套定向
build_pdi_modules 1/1。此阶段只测试和文档，既有 A5 firmware_id 不变，无需新的 OTA。

## 提交与推送

EDK `608731125afdf170ad93fa5514e4919edf86f9c0` 已推送 origin/master，远端 SHA 实测相同。工作区只提交精确 EDK gitlink 和本板验记录，BSP 不变；工作区远端 SHA 见 E/git-verification.log（提交之后生成）。
