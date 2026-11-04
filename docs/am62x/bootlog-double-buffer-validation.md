# AM625 双缓冲启动日志验收

日期：2026-11-03。按新增需求，在现有接力机制上扩容并保留两次启动；正常启动通过健康检查后，上报保留记录，服务器持久确认后清空，下次从第一组开始。

## 版本与实机状态

- 固件标签 `v0.0.1`，内容 ID `39635b333ea4cce5ecfd6f23272f3a3b918cf6a53f2cd3c2ee4c57224d62c5e7`，发布 #43。
- 设备 `1c-63-49-22-c4-f7`，AM625 SD 卡。kernel/rootfs A、B 槽均已安装这一固件并通过健康确认；最终启动 `daf481e1-d903-4987-a840-9d9fc3163ea2`，deployment 1、kernel/rootfs B，OTA server 为 success。
- 引导程序独立升级：先 B 后 A，各次启动均健康确认；tiboot3、tispl、U-Boot 两槽逐项读回，与实际部署包负载逐字节一致。ROM 执行的首级是 tiboot3_a；不宣称执行验证了 tiboot3_b。
- kernel/rootfs 普通 OTA 没有解除远程 bootloader 策略。引导更新使用临时本机维护配置和仅含 bootloader 的受控清单；正式配置仍禁用远程更新。U-Boot 网口协商超时未在本轮修复，维护下载通过 Linux 完成。

## 实现

保留 DDR 从 64 KiB 扩大至 1 MiB，紧邻但不覆盖 ramoops。两组各 512 KiB，每组为 R5 SPL 32 KiB、A53 SPL 32 KiB、U-Boot 64 KiB、kernel 320 KiB，另留头部和间隙。R5 轮换组，后续阶段追加当前组；kernel printk 注册后回放缓冲并记录至本次健康确认。

每段验证长度与 CRC，并保存上一份已提交前缀以恢复被复位打断的追加。满缓存记录 dropped；损坏、缺失和恢复前缀分别标识。设备健康确认后冻结快照，上传进程按偏移重试；服务器独立 SQLite 归档检查全部有限清单并提交，设备才核对两个 capture ID、先使头部失效再清空两组。实时 SOL 轮转不会删除此归档，ACK 丢失可跨恢复启动重试。

清除的是已确认的 DDR 启动缓存；服务器历史和现有普通本地日志保留。SOL 启动下拉框可以选择正常启动和上次未确认启动归档，正文、阶段筛选和导出继续使用原始串口格式。接口与边界见 [组件说明](../../device-manager/docs/startup-buffers.md)。

## 实机验证

1. 发布 #43 后设备下载安装、重启和健康确认成功，服务器收到正常启动四段数据，其中 kernel 20515 字节。首次迁移保留的旧内核时期记录有损坏段，明确标记并排除损坏内容，没有当作完整日志。
2. 在未保存环境变量的 U-Boot 会话中，为单次启动添加 `rdinit=/bin/sh`；尚未进入正式 rootfs、尚未执行健康检查时，通过 sysrq 触发一次受控 kernel panic。未修改或发布异常固件。
3. 异常启动使用第一组，capture `df6e92a1-61fa-44b6-86e0-bab2799ce871`；自动复位后的正常启动使用第二组，capture `ed0abacf-e728-47d6-a601-3929d05b0295`。服务器分别保留 R5 SPL、A53 SPL、U-Boot、kernel；异常 kernel 20521 字节，包含 panic 原因和调用栈，正常 kernel 20515 字节，不含该 panic。八段均 CRC 正常、dropped=0。
4. 恢复启动 `be1c4a06-a650-4c18-9272-0045c53fef5d` 健康确认后，两组归档成功，设备为 `startup-state=acknowledged`、`next-buffer=1`，`banks` 为空。
5. 再次正常重启，capture `6bdafb1e-b72b-4b8d-a4f9-9096c7db749e` 确认仅 bank0、generation=1、`active-buffer=1`；归档完成后再次清空。旧异常和正常归档仍在服务器。
6. 使用已有 `fwctld --once --auto-install --force` 将同一版本、同一内容 ID 写入备用 kernel/rootfs B 槽，通过重启健康确认及服务器 success。两槽均覆盖新版机制；initramfs 验证备用 rootfs 完整，无需修复。

本轮没有格式化 data，没有用手动 mark-good 绕过健康检查；最终 data 为 persistent、日志 sync-state=ok。

## 主机检查与工件

U-Boot 实际生产代码 ABI/轮换/损坏/满缓存/前缀恢复测试 4 项、归档 HTTP/上传器测试 8 项、健康门槛测试 4 项、SOL 回归 10 项、日志生命周期 9 项、事故附件回归 9 项、正文解码 10 项通过。隔离浏览器验证两组选择、正文及导出一致、手机无横向溢出；真实 FIT 下载字节比较通过。

工件位于 `output/ota-validation/0.0.1-bootlog-v2/`，包含版本身份、源码基线与补丁、新文件快照、OTA 结果、八段原始归档及其 SHA256、串口、测试记录和引导程序读回结果。构建为 `output/am625-bootlog-v2/`，维护备份在 `output/bootlog-v2-maintenance/`；生成物不提交 Git。

## 尚未覆盖的边界

仅证明本次软件重启和受控 panic 复位能保留 DDR。真正断电、其他复位类型、内核 console 注册前的致命故障不在本次保证范围；ROM/TIFS/ATF 输出仍未接入。两组只能覆盖最多两次尚未归档启动，连续更多失败会覆盖最旧记录。SPL/U-Boot 阶段卡死复位、真实掉电中断追加/清空仍需专门实机测试，不能以主机故障夹具替代。

## 真实 OTA 故障包补充

2026-11-04 通过发布 46 的隔离故障包验证了 OTA 后 PID 1 panic、三次启动失败、自动回退、两组日志补传及异常固件隔离；B 槽已用正常发布 47 修复。实际日志与尚未打通的 OTA 附件关联见 [OTA 启动失败日志验收](ota-boot-failure-log-validation.md)。
