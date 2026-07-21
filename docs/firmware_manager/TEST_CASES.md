# Firmware Manager 实机测试用例

## 1. 文档目标

本文档用于验证 AM62x SD RAW A/B 固件管理功能。测试覆盖 U-Boot <code>fw</code> 命令、SPL 启动选择、FIT 发布包、MMC A/B 槽、Linux <code>fwctl</code>、健康确认、自动回滚、重复升级和故障恢复。

适用配置：

| 项目 | 值 |
|---|---|
| Product | <code>ti-am62x</code> |
| Layout | <code>am62x-sd-ab-v1</code> |
| Storage | MMC device 1 |
| Metadata | <code>meta0=0x00500000</code>，<code>meta1=0x00510000</code> |
| Network | Device <code>192.168.18.246</code>，TFTP server <code>192.168.18.245</code> |
| Boot chain | ROM -> tiboot3 -> tispl -> U-Boot -> kernel -> rootfs |

## 2. 测试准备

| 编号 | 准备项 | 要求 |
|---|---|---|
| PRE-01 | 串口 | 115200 8N1，完整保存 R5 SPL、A53 SPL、U-Boot 和 Linux 日志 |
| PRE-02 | TFTP 根目录 | 包含 <code>release.itb</code>、<code>bootloader.itb</code>、<code>kernel.itb</code>、<code>rootfs.itb</code> |
| PRE-03 | 正常包 | 每个 FIT 的 product、layout、version、rollback-index 和 SHA-256 正确 |
| PRE-04 | 异常包 | 准备错误 product、错误 layout、错误 type、损坏 hash、低版本、低 rollback-index 等变体 |
| PRE-05 | 恢复介质 | 准备可重新烧录的 SD 卡镜像和读卡器 |
| PRE-06 | Linux 工具 | rootfs 包含 <code>/usr/sbin/fwctl</code> 和 <code>S99fw-mark-good</code> |
| PRE-07 | 基线记录 | 每组测试前记录 <code>fw status</code>、槽位内容 SHA-256 和环境变量 |
| PRE-08 | 版本规划 | 基线版本、候选版本和降级版本必须可从 FIT 属性明确区分 |

每个用例至少记录以下结果：

| 记录项 | 内容 |
|---|---|
| U-Boot 状态 | sequence、active、pending、last-good、selected |
| Deployment 状态 | state、successful、tries、release version |
| Component 状态 | bootloader/kernel/rootfs 的 slot、version、rollback、valid |
| 启动日志 | R5 SPL、A53 SPL、U-Boot 和 Linux 选择的 deployment/slot |
| 实际结果 | Pass、Fail 或 Blocked，并附串口日志 |

## 3. 默认环境和布局

| 编号 | 测试功能 | 前置条件 | 测试步骤 | 预期结果 |
|---|---|---|---|---|
| ENV-01 | 默认网络配置 | 加载新版默认环境 | 执行 <code>printenv serverip gatewayip ipaddr</code> | 分别为 <code>192.168.18.245</code>、<code>192.168.18.1</code>、<code>192.168.18.246</code> |
| ENV-02 | 内核 FIT 暂存地址 | 加载新版默认环境 | 执行 <code>printenv kernel_addr_r loadaddr</code> | kernel_addr_r 为 <code>0x90000000</code>，loadaddr 为 <code>0x82000000</code> |
| ENV-03 | 默认启动命令 | 加载新版默认环境 | 执行 <code>printenv bootcmd fw_boot</code> | bootcmd 为 <code>run fw_boot</code>，启动链包含 select、bootargs、MMC read 和 bootm |
| ENV-04 | 快捷升级变量 | 加载新版默认环境 | 执行 <code>printenv upk upr upb upa</code> | 分别指向 kernel、rootfs、bootloader 和 release 升级，路径不含 <code>release/</code> |
| ENV-05 | 环境持久化 | ENV-01 至 ENV-04 正常 | 执行 <code>saveenv</code> 后复位 | 所有环境变量保持不变 |
| ENV-06 | TFTP 网络 | 网线和服务端正常 | 执行 <code>ping 192.168.18.245</code> | 网络连通，使用正确网口 |
| ENV-07 | 布局查询 | 新版 U-Boot | 执行 <code>fw list</code> | 显示 product、layout、storage 和全部 RAW region |
| ENV-08 | 新命令帮助 | 新版 U-Boot | 执行 <code>help fw</code> | 显示全部 fw 子命令 |
| ENV-09 | 旧命令移除 | 新版 U-Boot | 执行 <code>help fu</code> | 返回 Unknown command |
| ENV-10 | fw_boot 空确认路径 | fw_confirm 未设置 | 执行 <code>run fw_boot</code> | 不在 fw_apply_confirm 静默退出，继续执行 fw select |

## 4. Metadata 初始化和冗余

| 编号 | 测试功能 | 前置条件 | 测试步骤 | 预期结果 |
|---|---|---|---|---|
| META-01 | 初始化 A 槽 | 测试卡 metadata 可重建 | 执行 <code>fw init a</code> 和 <code>fw status</code> | deployment 0 confirmed，active/last-good/selected 为 0，pending 为 none |
| META-02 | 初始化 B 槽 | 测试卡 A/B 固件均有效 | 执行 <code>fw init b</code> 和 <code>fw status</code> | deployment 0 或基线 deployment 的三个组件均指向 B 槽 |
| META-03 | init 仅修改 metadata | 记录所有组件区域 SHA-256 | 执行 <code>fw init a</code> | bootloader、kernel、rootfs 区域内容不变 |
| META-04 | 空白 metadata 自动初始化 | meta0/meta1 均为全 00 或全 FF | 执行 <code>fw select</code> | 使用 default-slot 自动初始化并正常导出环境 |
| META-05 | 非空损坏拒绝自动初始化 | meta0/meta1 写入非空无效数据 | 执行 <code>fw select</code> | 提示 metadata unavailable，不自动覆盖 |
| META-06 | 单副本恢复 | meta0 损坏、meta1 有效 | 执行 <code>fw status</code> | 从 meta1 成功加载 |
| META-07 | 反向单副本恢复 | meta1 损坏、meta0 有效 | 执行 <code>fw status</code> | 从 meta0 成功加载 |
| META-08 | 双副本损坏 | meta0/meta1 都无效 | 执行 <code>fw status</code> | 明确提示 metadata unavailable |
| META-09 | sequence 选择 | 两份 metadata 有效但 sequence 不同 | 执行 <code>fw status</code> | 选择 sequence 较新的副本 |
| META-10 | 交替写入 | metadata 正常 | 连续执行会保存 metadata 的命令并读取两个副本 | 副本交替更新，sequence 单调增加 |
| META-11 | 参数检查 | metadata 正常 | 执行 <code>fw init c</code> | 返回用法错误，不修改 metadata |
| META-12 | 重启持久化 | 完成一次 metadata 更新 | 复位后执行 <code>fw status</code> | 状态与复位前一致 |

## 5. FIT 包校验

| 编号 | 测试功能 | 前置条件 | 测试步骤 | 预期结果 |
|---|---|---|---|---|
| FIT-01 | kernel 包校验 | 正常 kernel.itb | 执行 <code>fw verify tftp kernel.itb</code> | 输出有效 kernel 包、版本和 rollback index |
| FIT-02 | rootfs 包校验 | 正常 rootfs.itb | 执行 <code>fw verify tftp rootfs.itb</code> | 输出有效 rootfs 包 |
| FIT-03 | bootloader 包校验 | 正常 bootloader.itb | 执行 <code>fw verify tftp bootloader.itb</code> | tiboot3、tispl、uboot 三个 image hash 均通过 |
| FIT-04 | release 包校验 | 正常 release.itb | 执行 <code>fw verify tftp release.itb</code> | 输出有效 release 包和版本 |
| FIT-05 | 内存地址校验 | 正常 kernel.itb | TFTP 到 loadaddr，再执行 <code>fw verify addr 0x82000000 &lt;filesize&gt;</code> | 与 TFTP 直接校验结果一致 |
| FIT-06 | product 不匹配 | 制作错误 product FIT | 执行 verify/update | 被拒绝，存储和 metadata 不变 |
| FIT-07 | layout 不匹配 | 制作错误 layout-id FIT | 执行 verify/update | 被拒绝，存储和 metadata 不变 |
| FIT-08 | component type 不匹配 | 文件名与 FIT type 不一致 | 执行对应 update/restore | 被拒绝 |
| FIT-09 | FIT image hash 损坏 | 修改 FIT image 数据 | 执行 verify/update | SHA-256 校验失败 |
| FIT-10 | rollback-index 降级 | rollback 小于 confirmed | 执行 update | 返回降级错误，不写入目标槽 |
| FIT-11 | release version 降级 | release version 小于 confirmed | 执行 <code>run upa</code> | 被拒绝，原 pending 保持或 confirmed 保持 |
| FIT-12 | manifest SHA 错误 | 修改组件文件但不更新 release SHA | 执行 <code>run upa</code> | 组件完整文件 SHA 校验失败 |
| FIT-13 | manifest 文件名错误 | release 指向不存在文件 | 执行 <code>run upa</code> | TFTP 下载失败，不提交新 pending |
| FIT-14 | release 重复组件 | manifest 重复列出同一组件 | 执行 verify/update | release 校验失败 |
| FIT-15 | 未授权 bootloader | release 包含 bootloader 但无 allow 属性 | 执行 <code>run upa</code> | bootloader 更新被拒绝 |
| FIT-16 | bootloader image 缺失 | bootloader FIT 缺 tiboot3/tispl/uboot 任一 image | 执行 verify/update | 校验失败，不写入 |
| FIT-17 | 超大组件 | FIT 或解包数据超过 region | 执行 update | 返回文件过大，不越界写入 |
| FIT-18 | 错误地址参数 | addr、size 无效 | 执行 <code>fw verify addr</code> | 返回参数或 FIT 格式错误，不崩溃 |

## 6. 单组件升级和恢复

| 编号 | 测试功能 | 前置条件 | 测试步骤 | 预期结果 |
|---|---|---|---|---|
| UPD-01 | kernel 快捷升级 | 无 pending | 执行 <code>run upk</code> | 写入非活动 kernel 槽，创建 pending，tries=3 |
| UPD-02 | rootfs 快捷升级 | 无 pending | 执行 <code>run upr</code> | 写入非活动 rootfs 槽，创建 pending |
| UPD-03 | bootloader 快捷升级 | 无 pending，允许 bootloader update | 执行 <code>run upb</code> | 按 uboot、tispl、tiboot3 顺序写入目标 bootloader 槽 |
| UPD-04 | 地址模式升级 | FIT 已在内存 | 执行 <code>fw update addr 0x82000000 &lt;filesize&gt;</code> | 与 TFTP 更新行为一致 |
| UPD-05 | kernel/rootfs 合并 | 无 pending | 依次执行 <code>run upk</code>、<code>run upr</code> | 两个组件合并到同一 pending deployment |
| UPD-06 | 三组件合并 | 无 pending | 依次执行 <code>run upb</code>、<code>run upk</code>、<code>run upr</code> | 三个组件属于同一 pending deployment |
| UPD-07 | 重复替换 kernel | 已有 pending kernel | 替换 TFTP kernel.itb 后再次 <code>run upk</code> | 同一 pending 中 kernel 版本被更新 |
| UPD-08 | 重复替换 rootfs | 已有 pending rootfs | 替换 rootfs.itb 后再次 <code>run upr</code> | 同一 pending 中 rootfs 被更新 |
| UPD-09 | 重复替换 bootloader | 已有 pending bootloader | 替换 bootloader.itb 后再次 <code>run upb</code> | 同一目标槽重新写入完整 bootloader |
| UPD-10 | kernel restore | metadata 正常 | 执行 <code>fw restore kernel tftp kernel.itb</code> | 使用校验和回读路径恢复非活动 kernel 槽 |
| UPD-11 | rootfs restore | metadata 正常 | 执行 <code>fw restore rootfs tftp rootfs.itb</code> | 恢复非活动 rootfs 槽 |
| UPD-12 | bootloader restore | metadata 正常 | 执行 <code>fw restore bootloader tftp bootloader.itb</code> | 恢复完整目标 bootloader 槽 |
| UPD-13 | active 槽保护 | 记录 active 区域 SHA-256 | 普通 kernel/rootfs 更新后重新读取 active 区 | active 组件内容不变 |
| UPD-14 | last-good 槽保护 | 构造 active 与 last-good 不同的状态 | 尝试占用 last-good 使用的槽 | 命令拒绝危险写入 |
| UPD-15 | 写后回读失败 | 注入 MMC 读回错误 | 执行任一组件升级 | 不保存新的 pending metadata |
| UPD-16 | 更新状态展示 | 完成单组件更新 | 执行 <code>fw status</code> | pending、state、tries、slot、version、rollback 均正确 |

## 7. 完整 Release 事务

| 编号 | 测试功能 | 前置条件 | 测试步骤 | 预期结果 |
|---|---|---|---|---|
| REL-01 | 完整 release 升级 | 无 pending，四个 ITB 正常 | 执行 <code>run upa</code> | 依次下载并校验三个组件，全部成功后提交 pending |
| REL-02 | release 文件路径 | TFTP 根目录直接存放四个 ITB | 执行 <code>run upa</code> | 下载文件名不包含 <code>release/</code> |
| REL-03 | pending 被 release 替换 | 先执行 <code>run upk</code> | 再执行 <code>run upa</code> | 输出 Replacing pending deployment，不返回 EBUSY |
| REL-04 | 错误 release 再替换 | 已有完整 pending | 更换为新的正确 release 后再次 <code>run upa</code> | 从 confirmed 基线重建目标并提交新 pending |
| REL-05 | 更低 pending 版本替换 | 错误 pending 版本高于新包，但新包不低于 confirmed | 执行 <code>run upa</code> | 允许替换错误 pending |
| REL-06 | 低于 confirmed 的替换 | 新 release 低于 confirmed | 执行 <code>run upa</code> | 仍然拒绝降级 |
| REL-07 | 第一个组件下载失败 | 停止对应 TFTP 文件 | 执行 <code>run upa</code> | 当前 confirmed 保持可启动，不产生可启动的半成品 pending |
| REL-08 | 中间组件失败 | bootloader 正常、kernel 下载或校验失败 | 执行 <code>run upa</code> | metadata 保持 non-bootable writing/no pending，可直接重试 |
| REL-09 | 最后组件失败 | bootloader/kernel 正常、rootfs 失败 | 执行 <code>run upa</code> | 不提交 pending，可直接再次执行 upa |
| REL-10 | 失败后重试 | REL-08 或 REL-09 后修复文件 | 再次执行 <code>run upa</code> | 无需 mark-good 或人工 init，重新开始成功 |
| REL-11 | metadata 预提交保护 | 已有 pending | 启动 replacement 后在写入前读取 metadata | 旧 pending 已取消，目标为 WRITING |
| REL-12 | 成功提交原子性 | 完整 release 成功 | 执行 <code>fw status</code> | 仅最后提交时出现 READY pending，三个组件版本一致 |
| REL-13 | release 重复执行 | release 已 pending | 不修改文件再次执行 <code>run upa</code> | 正常重新写入并重新提交 pending |
| REL-14 | manifest 允许 bootloader | 正常 release | 检查 release 属性并执行升级 | bootloader、kernel、rootfs 全部参与事务 |

## 8. 启动选择和槽位一致性

| 编号 | 测试功能 | 前置条件 | 测试步骤 | 预期结果 |
|---|---|---|---|---|
| BOOT-01 | confirmed 启动 | 无 pending | 复位并观察日志 | R5/A53/U-Boot/Linux 使用 active deployment |
| BOOT-02 | pending 首次启动 | READY pending | 复位并观察日志 | R5 SPL 提交选择并将 tries 减 1 |
| BOOT-03 | A53 复用选择 | BOOT-02 | 比较 R5 和 A53 日志 | A53 使用 R5 已提交的同一 deployment |
| BOOT-04 | U-Boot 导出选择 | SPL 已选定 deployment | 执行 <code>fw select</code> | 导出 fw_deployment 和三个 component slot |
| BOOT-05 | kernel offset/size | fw select 成功 | 查看 fw_kernel_offset 和 fw_kernel_size | 与 fw list 中对应槽 region 一致 |
| BOOT-06 | rootfs 分区 | fw select 成功 | 查看 fw_rootfs_slot、fw_rootpart 和 Linux root 参数 | A 对应 mmcblk1p13，B 对应 mmcblk1p14 |
| BOOT-07 | bootargs deployment | 正常进入 Linux | 查看 <code>/proc/cmdline</code> | 包含正确 <code>fw.deployment=&lt;id&gt;</code> |
| BOOT-08 | kernel FIT 解压 | kernel_addr_r=0x90000000 | 执行 <code>run fw_boot</code> | 内核解压到 0x82000000，无 inflate -5 |
| BOOT-09 | boot once | 两个 deployment 有效 | 执行 <code>fw boot &lt;id&gt; once</code> 后复位 | 只在下一次启动选择指定 deployment |
| BOOT-10 | boot once 清除 | 完成 BOOT-09 | 再次复位 | 恢复正常 active/pending 选择 |
| BOOT-11 | 指定 deployment 启动 | deployment 有效 | 执行 <code>fw boot &lt;id&gt;</code> | 按命令语义选择指定 deployment |
| BOOT-12 | 无效 deployment | metadata 正常 | 执行 <code>fw boot 9</code> | 返回错误，不修改选择 |
| BOOT-13 | metadata 不可用回退 | 两份 metadata 无效 | 复位并观察 SPL | SPL 明确报告错误并使用 slot A 回退策略 |
| BOOT-14 | bootloader/kernel/rootfs 一致性 | 完整 pending | 比较三个阶段日志和 Linux cmdline | 三个组件均来自同一 deployment 描述 |

## 9. 确认、失败和回滚

| 编号 | 测试功能 | 前置条件 | 测试步骤 | 预期结果 |
|---|---|---|---|---|
| ROL-01 | U-Boot mark-good | pending 已成功启动 | 执行 <code>fw mark-good</code> | pending 变为 confirmed，active/last-good 更新 |
| ROL-02 | 指定 mark-good | 指定 deployment 有效 | 执行 <code>fw mark-good &lt;id&gt;</code> | 指定 deployment 被确认 |
| ROL-03 | mark-bad | deployment 有效 | 执行 <code>fw mark-bad &lt;id&gt;</code> | deployment state 变为 failed，不再自动选择 |
| ROL-04 | 手动 rollback | 存在 pending | 执行 <code>fw rollback</code> 后复位 | pending 被取消，启动 last-good |
| ROL-05 | 尝试次数递减 | pending 未确认 | 连续复位并查看 fw status | tries 每次由 R5 SPL 减 1 |
| ROL-06 | 尝试耗尽 | 禁止自动确认 | 重启直到 tries=0 | pending 标记 failed，自动回到 last-good |
| ROL-07 | Linux 状态查询 | Linux 正常启动 | 执行 <code>fwctl status</code> | 与 U-Boot fw status 一致 |
| ROL-08 | Linux 手动确认 | AUTO_MARK_GOOD 关闭 | 执行 <code>fwctl mark-good</code> | 当前 cmdline deployment 被确认 |
| ROL-09 | Linux 自动确认 | AUTO_MARK_GOOD=1 | 启动新 deployment | S99fw-mark-good 自动确认 |
| ROL-10 | 健康检查成功 | 设置成功的 FWCTL_HEALTHCHECK | 启动 Linux | healthcheck 成功后 mark-good |
| ROL-11 | 健康检查失败 | 设置返回非零的 healthcheck | 启动 Linux | 不执行 mark-good，保留测试状态 |
| ROL-12 | fwctl mark-bad | Linux 可访问 metadata | 执行 <code>fwctl mark-bad &lt;id&gt;</code> | U-Boot 后续读取到 failed 状态 |
| ROL-13 | fwctl rollback | Linux 可访问 metadata | 执行 <code>fwctl rollback</code> 后复位 | 启动 last-good |
| ROL-14 | 无效 ID | metadata 正常 | 对 fw/fwctl 使用越界 deployment | 返回参数错误，metadata 不变 |

## 10. 故障注入和断电恢复

| 编号 | 测试功能 | 前置条件 | 测试步骤 | 预期结果 |
|---|---|---|---|---|
| ERR-01 | TFTP 启动失败 | 关闭 TFTP 服务 | 执行 upk/upr/upb/upa | 命令失败，confirmed 不变 |
| ERR-02 | TFTP 中途断链 | 下载大文件时拔网线 | 执行 upr 或 upa | 不提交本次组件或 release |
| ERR-03 | kernel 写入断电 | 准备可恢复测试卡 | kernel 写入过程中断电 | 下次启动 confirmed，不启动半写 kernel |
| ERR-04 | rootfs 写入断电 | 准备可恢复测试卡 | rootfs 写入过程中断电 | 下次启动 confirmed |
| ERR-05 | replacement 写入断电 | 已有 pending | run upa 替换过程中断电 | 旧 pending 不再作为可启动版本 |
| ERR-06 | metadata 保存断电 | 控制在 metadata 写入阶段断电 | 重启并读取状态 | 至少一份副本有效，选择最新完整副本 |
| ERR-07 | bootloader U-Boot 写入断电 | 准备恢复卡 | upb 写 uboot 时断电 | 记录实际启动结果，必要时使用旧 confirmed 或重烧 |
| ERR-08 | bootloader tispl 写入断电 | 准备恢复卡 | upb 写 tispl 时断电 | 不应提交 pending；确认 ROM 链恢复能力 |
| ERR-09 | bootloader tiboot3 写入断电 | 准备恢复卡 | upb 最后写 tiboot3 时断电 | 可能需要重新烧卡，结果必须明确记录 |
| ERR-10 | active 数据损坏 | 手工破坏非当前测试的 active 组件 | 复位 | 验证平台恢复策略和错误日志 |
| ERR-11 | MMC 读失败 | 注入读错误或使用故障卡 | fw status/update/select | 返回存储错误，不崩溃 |
| ERR-12 | MMC 写失败 | 写保护或注入写错误 | 执行 update | 不提交新 pending |
| ERR-13 | release 校验后文件替换 | manifest 保持不变，替换组件文件 | 执行 upa | 完整文件 SHA 校验失败 |
| ERR-14 | 错误 rootfs | 使用可校验但无法挂载的 rootfs | 升级并启动，不确认 | 尝试耗尽后自动回滚 |
| ERR-15 | 错误 kernel | 使用可校验但无法启动的 kernel | 升级并启动 | 尝试耗尽后自动回滚 |
| ERR-16 | 环境丢失 | 擦除 U-Boot environment | 复位 | 加载编译默认环境，fw_boot 和网络参数存在 |

## 11. 跨版本和兼容性

| 编号 | 测试功能 | 前置条件 | 测试步骤 | 预期结果 |
|---|---|---|---|---|
| COMP-01 | 旧 fu 命令不可用 | 新版 U-Boot | 执行 <code>fu status</code> | Unknown command |
| COMP-02 | 旧 FUMD metadata | 写入旧格式 metadata | 执行 <code>fw status</code> | 不接受旧格式，提示重新初始化 |
| COMP-03 | 旧 fu FIT 属性 | 使用含 fu,* 属性的 FIT | 执行 fw verify/update | 校验失败 |
| COMP-04 | 新 FWMD metadata | 正常新版 metadata | U-Boot fwctl 分别读取 | 两端解析结果一致 |
| COMP-05 | 新 fw FIT 属性 | 使用 Buildroot 新包 | 执行 verify/update | 正常接受 |
| COMP-06 | 保存环境升级 | 从旧默认环境切换 | 执行 <code>env default -a</code>、<code>saveenv</code> | fw 脚本、快捷变量、网络和 kernel 地址全部更新 |

## 12. 验收标准

| 编号 | 验收项 | 通过标准 |
|---|---|---|
| AC-01 | 正常升级 | kernel、rootfs 和 bootloader 均可独立升级 |
| AC-02 | 完整升级 | release 三组件全部成功后才提交 pending |
| AC-03 | 重复升级 | pending 状态可直接替换组件或完整 release |
| AC-04 | 防降级 | 不能低于 confirmed version/rollback-index |
| AC-05 | 启动一致性 | R5、A53、U-Boot、kernel 和 rootfs 使用同一 deployment |
| AC-06 | 健康确认 | fwctl 自动和手动确认均正确 |
| AC-07 | 自动回滚 | 未确认或启动失败后回到 last-good |
| AC-08 | metadata 冗余 | 任意一个 metadata 副本损坏仍可工作 |
| AC-09 | 故障安全 | 下载、校验、普通组件写入失败不破坏 confirmed |
| AC-10 | 地址安全 | kernel FIT 加载与解压不重叠 |
| AC-11 | 环境持久化 | saveenv 后网络、快捷变量和启动脚本保持 |
| AC-12 | 可恢复性 | bootloader 高风险断电场景有明确重烧恢复路径 |

## 13. 测试结果记录表

| 用例编号 | 固件版本 | 初始 active/pending | 执行日期 | 实际结果 | 结论 | 日志路径 | 备注 |
|---|---|---|---|---|---|---|---|
|  |  |  |  |  | Pass/Fail/Blocked |  |  |
