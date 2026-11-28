# 新轮次 A2：普通绝对命令目录与整轮 AM625 验收

2026-11-27。[工程记录](../../../../edk/docs/archive/sdk-install-contract/a2-validation.md) · [本轮板验索引](README.md) · [A1 板验](a1-validation.md)。E=`output/edk-sdk-install-contract-a2-20261127-181711-DiIvF6/`，F=E/final/。

指定 MAC `1c:63:49:22:c4:f7`，HWID `1010001000110000`，aarch64，可信 A1 SSH key。开工 boot `279c4734-de74-4ca5-b0bf-f6e70f0e0a0a`，B 槽确认，完整现役固件 ID `79086d3bf65f2ea2b7f0171f370e7aa1b24c12944833da4af301c641776d8e4d`，fwctl version、ota-status、health-check 通过（E/board-start.log，F/board-candidate.log）。

F/board-probes.tar、board-probes.tar.sha256、manifest.sha256、links.manifest，731 个文件与 157 个软链接逐项核对。24 个 BSL/PDI 前缀和 4 个 Core/EPDU 前缀各经独立 CMake 和 pc 消费者，56 次实际调用 exit=0；在 5 个真实 ARM64 绝对命令 staging 前缀（先工具、先库、默认全装、DESTDIR 根别名、旧行为还原后配套重试）分别运行 `$root/opt/edk-tools/bin/ptelemetryd --help` exit=1 Usage、`--check-config` exit=0 project=phytium-s5000c；`$root/opt/edk-tools/sbin/timectl --help`、相对注册别名 `timectld --help` 各 exit=2 Usage，均未启动守护进程。20 次实际命令调用从对应 `$root/usr/lib` 加载所有 EDK DT_NEEDED 库、路径和摘要正确，未误写 `$root/usr/bin`、`$root/usr/sbin`。所有不配套/恶意链接等拒绝及变异实验只在主机独立前缀，未在板上写真实路径。CAN 与 hwmon 只用 NULL；BMC 仅纯枚举和空对象清理；旧六查询消费者只读，正式 ptelemetryd runtime-status、psatellited --check-config、health-check 只读；整板路由保持，临时目录回收。F/board-candidate.log。

## 正式发布

正式候选 ID `452a56bde73f16133dd32557b5785dd8d5ec5714cd7b46ef92229547b3004fc9`，固定 v0.0.1 packed 1，kernel SHA `8b6edea7e7b82cc14f687a4a4680dbb724fff76a84c678919f62e227dedab1a0`、rootfs SHA `662156229540019bd5243fdc5d0eeff9f9ca25bdf008acf9f8e786b5c30569e8`，OTA SHA `7230ad5478a1fbc38df67c26f46612c1e2d6de18c7e291cf30dbcc947b5a2b51`。内容与 A1 现役变化；四个正式公共库二进制 SHA 完全相同，PDM 构建标识不同。2026-11-27T18:40:23+08:00 发布 `draft-hlEIJX`（F/publication.json、upload.json）；设备报告 `2026-11-27T18:41:59.920330+08:00 id=452a56bde73f16133dd32557b5785dd8d5ec5714cd7b46ef92229547b3004fc9 phase=success running=1 target=1 quarantined=False`。新 boot `fa7a815f-b166-4c3a-87bb-2cf9e53468cd`，A 槽确认，FWCHECK1 match，健康、8 个 active、0 failed；串口确认新 SSH key，9/9 实装关键制品 SHA256 与正式镜像一致。F/serial-key.log、board-check.log、board-package-compare.log、ota-timeline.log、device-transaction.json、post-ota-verify.log。

发布后 F/board-installed.log 完整重跑 76 个实际探针/命令，加载路径、摘要、退出码、冻结旧查询、正式服务只读、整板路由、健康及清理均通过。只对指定 AM625 发布和运行临时资源，其他真实服务器未写入、未控制。A2 板验通过，本轮实机验收完成。
