[[README|首页]] · [[00-实验准备与通用方法/案例索引|案例索引]] · [[00-实验准备与通用方法/工具索引|工具索引]] · [[07-内核启动与恢复/00-章节导航|章节导航]]

先按现象提出假设并完成练习，再核对定位、内核机制和参考修复。`verify` 验证镜像提供的参考实现。

[[07-内核启动与恢复/B-BOOT01-内核panic触发后的启动日志取证与恢复/B-BOOT01：内核panic启动日志与恢复#现象与原理|现象与原理]] · [[07-内核启动与恢复/B-BOOT01-内核panic触发后的启动日志取证与恢复/B-BOOT01：内核panic启动日志与恢复#练习任务|练习任务]] · [[07-内核启动与恢复/B-BOOT01-内核panic触发后的启动日志取证与恢复/B-BOOT01：内核panic启动日志与恢复#使用工具|使用工具]] · [[07-内核启动与恢复/B-BOOT01-内核panic触发后的启动日志取证与恢复/B-BOOT01：内核panic启动日志与恢复#定位方法|定位方法]] · [[07-内核启动与恢复/B-BOOT01-内核panic触发后的启动日志取证与恢复/B-BOOT01：内核panic启动日志与恢复#内核流程与汇编|内核流程与汇编]] · [[07-内核启动与恢复/B-BOOT01-内核panic触发后的启动日志取证与恢复/B-BOOT01：内核panic启动日志与恢复#修复与验收|修复与验收]] · [[07-内核启动与恢复/B-BOOT01-内核panic触发后的启动日志取证与恢复/B-BOOT01：内核panic启动日志与恢复#实机证据与反例|实机证据与反例]]

## 现象与原理

### 7.1 学习目标与边界

难度：进阶。这是手动、确定性的 panic，用来学习内核终止路径、调用栈、持久化证据、
跨启动关联和自动恢复。它不伪装成未知的内存破坏，也不声称一次实验能覆盖所有卡死。
源码：[run-panic](https://github.com/linux-bsp/sadboard-external/blob/93c81e82acfdf5d54155d1b9bb750e78645d384f/package/sadboard-labs/run-panic)、
[check-panic](https://github.com/linux-bsp/sadboard-external/blob/93c81e82acfdf5d54155d1b9bb750e78645d384f/package/sadboard-labs/check-panic)。

必须先让本固件完成 OTA 和健康确认。实验再进行一次普通重启，在新启动约 13～49 秒
之间、SSH 已就绪而本次日志尚未封存时执行 `sadboard run panic`。入口仍检查持久 data、
完整固件 ID、元数据 good/confirmed 且无 pending，拒绝在新固件试启动期间执行。
已封存的正常启动也会被拒绝，避免拿晚期运行崩溃冒充启动失败日志验证。

### 7.3 启动故障：一次固件与多次启动

固件内容 ID、Linux boot ID 和启动日志 startup ID 含义不同：相同固件可重启多次，
而 SPL 阶段还没有 Linux boot ID。要把故障启动的 SPL、U-Boot、kernel、rootfs 证据
关联到恢复启动，需要依赖阶段缓冲、持久记录、复位原因和上传确认。

先保存原始串口，再做栈符号化。内核栈里的 vpanic 是共同终止路径，需要追调用者；
`Tainted: O` 只说明加载过树外模块，不能因此判定它是根因。复位标签如 RST 本身
也不能区分 OTA 主动重启与异常重启，必须结合软件意图和上一次健康状态。

暖重启后内存保留的验证不能证明断电仍保留；pstore 导出后目录为空也不等于没有日志，
可能已经被归档消费。检查本地文件、服务端内容与 ACK，而不是只检查目录非空。

### 7.4 从最简单的分类开始：进程故障为何有时变成整机故障

普通用户进程被 SIGSEGV 终止时，内核通常还能调度其他任务；它与内核失去可靠执行
环境不是一回事。但 PID 1 承担特殊角色，退出会触发另一条关键失败路径。因此早期
`/init` 缺动态库可能产生如下因果链：

故障因果链：区分动态加载器先退出、PID 1 终止、内核 panic 和后续复位。

```text
动态加载器找不到必需库
  → /init 的程序入口尚未运行，加载器先退出
  → PID 1 退出
  → 内核触发 Attempted to kill init! panic
  → 按重启策略或 watchdog 进入下一次启动
```

这条说明用于分析曾遇到的 libcrypto 缺失问题，不是本例实际的 SysRq 注入调用栈。
真正根因在 initramfs 依赖闭包/打包，不能因为最终出现 panic 就修改 panic.c。
先找到最早的有效错误，比仅分析最后的共同终止栈更重要。

### 7.5 重启不等于回滚，更不等于修复成功

| 结论 | 需要什么证据 | 还缺什么时不能下结论 |
| --- | --- | --- |
| 发生 panic | 原始 panic 文本/栈、时间与 boot 关联 | 只有 reset 标签或 ping 中断 |
| 设备恢复运行 | 新 boot、关键服务/健康确认 | 只有串口重新出现 SPL |
| 回退到旧固件 | 启动部署/槽及完整内容 ID 改变到已知正常版 | 仅看到新一次重启 |
| 新 OTA 成功 | 目标内容实际启动、健康通过且结果上报 | 仅下载、写入或开始 reboot |
| 失败日志已保存 | 对应失败 startup 的内容、持久化和服务端确认 | 只有一个空目录或记录标题 |

本例在原已确认固件/网络参考构建上注入一次 panic，下一次仍启动同一构建；不能把它写成“三次
升级失败后完成回滚”。测试目标是启动失败与恢复的日志接力，固件回滚属于另一类测试。

### 7.7 发生了什么：panic 与 Oops 的差别

panic 表示内核决定不能继续正常运行。Oops 是一次内核异常诊断，有些情况下只终止
当前任务；是否进一步 panic 取决于异常上下文、配置和策略。用户程序 SIGSEGV 通常
只终止进程；PID 1 退出则可能触发 `Attempted to kill init!` panic，不能混为一种故障。

本内核 7.0 的 SysRq c 直接调用 `panic("sysrq triggered crash")`，并非故意解引用 NULL。
因此不能从本实验伪造 Data Abort 的 FAR/ESR 证据。如下为**源码整理路径**：

源码流程示意：沿 SysRq 写入、panic 日志保存与复位路径理解本例。

```text
用户态写 /proc/sysrq-trigger
  write_sysrq_trigger → __handle_sysrq → sysrq_handle_crash → panic
  panic 框架：协调 CPU、输出诊断、调用持久日志 dumper
  kmsg_dump_desc(KMSG_DUMP_PANIC) → pstore_dump → ramoops_pstore_write
  panic_timeout → emergency_restart → 启动链重新执行
```

阅读 [sysrq.c](https://github.com/linux-bsp/linux-7.0/blob/master/drivers/tty/sysrq.c)、
[panic.c](https://github.com/linux-bsp/linux-7.0/blob/master/kernel/panic.c)、
[printk.c](https://github.com/linux-bsp/linux-7.0/blob/master/kernel/printk/printk.c)、
[pstore/platform.c](https://github.com/linux-bsp/linux-7.0/blob/master/fs/pstore/platform.c)、
[pstore/ram.c](https://github.com/linux-bsp/linux-7.0/blob/master/fs/pstore/ram.c)。实际版本中 panic 公共实现会经过
内部辅助函数；以实机栈为准，不要求编译优化后每个源码函数都保留一个栈帧。
SysRq 权限及掩码规则见 [内核官方说明](https://www.kernel.org/doc/html/latest/admin-guide/sysrq.html)。

## 练习任务

### 7.2 独立练习任务与分级提示

**入口和窗口**：严格按 [[07-内核启动与恢复/00-章节导航|panic 案例]] 操作，先确认固件正常，
额外重启后在未封存窗口手动触发；不放进自动批量练习。

**任务**：证明发生了 panic、故障属于哪一次 Linux boot、SPL/U-Boot 日志属于哪个
startup，以及恢复后是否仍是原固件。不要用“设备又能 ping”代替恢复验收。

**必须提交**：原始串口、配套 vmlinux 解码、operator 意图、pstore、失败/恢复四段
SOL、boot ID/startup ID 的关联、完整固件 ID 和恢复健康证明。

<details><summary>L1 提示：分清三种标识</summary>

固件 ID 标识内容，Linux boot ID 标识一次内核启动，startup ID 标识启动日志缓冲。
同一固件可以有多次 boot；失败与恢复缓冲也不是同一个 UUID。

</details>
<details><summary>L2 提示：不要把检测入口当成根因</summary>

vpanic 是共同终止路径，要向下看调用者。本例 sysrq_handle_crash 及 marker 证明是
主动注入。Tainted O 仅说明加载了树外模块，不能据此归罪 PDM。

</details>

**L3 对照**：为什么停止 fw-confirm 会引入额外 OnFailure，而 SIGSTOP 不改变 unit
生命周期？为什么 pstore 目录已空仍可能有成功归档？为什么暖重启证明不了断电保留？
查代码和已有原始记录即可，不需要为回答问题反复触发 panic。

## 使用工具

通用原理、参数和使用边界见工具手册；具体命令与证据判断见本例定位方法。

[[工具手册/sadboard|sadboard]] · [[工具手册/GDB|GDB]] · [[工具手册/objdump|objdump]] · [[工具手册/addr2line|addr2line]] · [[工具手册/logctl|logctl]]

## 定位方法

### 7.8 第一层证据：原始串口

按时间把以下片段串起来：旧 boot ID/现场 marker、panic 原因、CPU/PID/Comm、
Call trace、重启倒计时、新的 SPL/U-Boot 启动、initramfs 校验、rootfs 和健康确认。
先区分第一个异常与后续连锁输出，不要只截最后一行 `Kernel panic`。

分析未知故障时优先回答：是显式 panic、Oops 后 panic、PID 1 退出、lockup 策略，
还是硬件复位后根本没有 panic 证据？`Reset reason: RST/ESM` 是另一层硬件观察，
不能单凭这个标签断言软件根因。系统上报 `linux-panic-observed` 表示确实找到 panic
文本，也不等价于已经证明是哪个软件缺陷造成的。

### 7.9 第二层证据：配套符号与调用栈

先验证该固件的 images/debug 清单，再用其中 vmlinux 解码。主机示例：

主机端：用异常发生时匹配的 vmlinux 解码 panic 日志，先替换输入与输出路径。

```sh
CROSS_COMPILE="$PWD/output/am625-debug-systemd/host/bin/aarch64-buildroot-linux-gnu-" \
  bash linux/linux-7.0/scripts/decode_stacktrace.sh \
  /path/to/saved/images/debug/vmlinux "$PWD/linux/linux-7.0" \
  < /path/to/panic.log > /path/to/panic-decoded.log
```

`CROSS_COMPILE` 选择 ARM64 工具前缀，vmlinux 提供符号和 DWARF，第二个路径帮助
定位源码。不能用下一个固件覆盖后的 vmlinux 解释旧栈。`func+offset/size` 可在符号
范围内定位；KASLR 下的绝对 PC 则需要正确处理运行偏移，不能原样交给普通 addr2line。

也可用交叉 GDB 加载匹配 vmlinux，`info line *FUNCTION+OFFSET`、
`disassemble /s FUNCTION` 检查函数范围和源行。只拿到日志时没有完整内核内存快照，
不能假装能够查看所有局部变量；那需要独立规划 kdump/vmcore 或 KGDB 环境。

### 7.10 第三层证据：两套 RAM 机制与持久归档

启动日志接力缓冲保存 SPL、U-Boot 和启动 kernel 的原始输出，用于失败与恢复启动
成对上报；ramoops/pstore 则在预留 RAM 保存 panic/oops 等记录，供下一次 Linux 读取。
它们作用不同，也不同于 ext4 中归档的历史文件。

恢复后 logctld 把 pstore 内容复制、同步到持久 boot 目录，再清理已安全保存的原始记录。
因此 `/sys/fs/pstore` 为空不一定说明没有捕获；还要查 `logctl diagnostic-reason previous`
和导出的归档。预留 RAM 的保留依赖平台重启行为，不能把暖重启验证外推为完全断电
仍保留内存，机制依据见 [ramoops 官方说明](https://www.kernel.org/doc/html/latest/admin-guide/ramoops.html)。

设备端：将本次 NFS/SD 模式的实际结果根目录保存为当前终端变量，供后续命令复用。

```sh
SADBOARD_RESULTS=$(sadboard results)
```

设备端：查看启动记录与阶段状态，定位失败启动和恢复启动的关联。

```sh
logctl boot-state
```

设备端：查询上一次启动的诊断原因，结合原始串口与复位信息判定。

```sh
logctl diagnostic-reason previous
```

设备端：检查日志采集、持久化、上报及归档确认状态。

```sh
logctl status
```

设备端：校验本次启动记录的完整性，再使用其日志作为定位证据。

```sh
logctl verify-boot
```

设备端：把路径占位符替换为本次实际现场目录，复核该次运行的证据完整性与验收约束。

```sh
sadboard check ${SADBOARD_RESULTS}/RUN
```

check 同时要求：boot ID 改变、前一 Linux boot 与现场相同、找到 Linux panic 证据、
新启动健康确认；网络模式比较 SBNET1 参考构建 ID，本地模式比较实际部署 ID 并要求无 pending，最后导出
`recovery.tar.gz` 并写 `recovery.result`。只看到“重启过”不足以判定通过。
最初那次 panic 不会正常返回，所以不能要求其具有普通案例的 result；恢复结果要看
新的独立证明，不能用空结果默认成功。

### 7.6 执行流程

1. 保存当前 `/usr/libexec/sadboard/boot-context`、boot ID，确认本次已正常就绪。
   本地 A/B 先确认 OTA success；网络模式先完整启动一次相同参考构建，并保持 TFTP/NFS 主机在线。
2. 在服务器持续记录 `/dev/ttyACM2`，保留原始字节。
3. 正常 reboot，等待 SSH 可连接，立即执行 `sadboard run panic`。可以使用 SSH
   连接重试脚本，但必须先确认 boot ID 已改变，不能误连到尚未退出的旧启动。
4. 记下输出的现场目录。连接中断是预期现象，不把 SSH 的 255 当成固件安装失败。
5. 等待下一次自动启动、健康确认，再运行 `sadboard check ${SADBOARD_RESULTS}/RUN`。
6. 核对 SOL 中失败启动和恢复启动的记录，并导出现场附件。

helper 用 SIGSTOP 暂停当次 `fw-confirm.service` 内的进程，确认 `startup-state=collecting`；
它不会 stop/disable/mask 服务，不在持久配置里设置下一次故障。随后写入 operator 意图、记录
boot-state、设置本次 `kernel.panic=3`、同步现场，向 `/proc/sysrq-trigger` 写 c。
如果触发前出错或被停止，退出清理会撤销意图并用 SIGCONT 恢复健康确认；真正 panic 后由下一次正常启动
恢复服务。原有固件版本已确认，因此这不是消耗三次试启动次数的 OTA 回滚测试。

初轮实机曾使用 systemctl stop，但该服务带 OnFailure，串口显示额外的健康失败与
重启请求。因此最终方式保持 unit 生命周期完整，只暂停执行。systemctl freeze 对
仍有启动 job 的 oneshot 会返回 busy，也不适用于这里；这些差异需按真实 unit 状态验证。

## 内核流程与汇编

### 7.14 内核源码精读与关键分支

读 [sysrq.c](https://github.com/linux-bsp/linux-7.0/blob/master/drivers/tty/sysrq.c) 与
[panic.c](https://github.com/linux-bsp/linux-7.0/blob/master/kernel/panic.c)：本例通过 SysRq 明确进入 panic，
不是演示未知内存踩踏。转到 [pstore](https://github.com/linux-bsp/linux-7.0/blob/master/fs/pstore/platform.c) 看日志 dump，
再分清内存保留、下次读取、落盘、上传和服务端确认是不同阶段。

只看 vpanic 不能确定根因；只看 reset 标签不能证明发生 panic；只看 SSH 恢复不能
证明启动日志已上传。用失败 boot、恢复 boot、startup 缓冲 ID、原始栈和内容 ID 关联。
最终因果解释必须与实际证据一致，而不是因为有恢复动作就宣称所有故障类型都已覆盖。

### 7.15 详细内核流程：显式 panic、日志 dump 与重新启动

#### 7.15.1 本例的最初入口仍是一个普通写系统调用

源码流程示意：从写系统调用和 procfs 分派追到 SysRq handler 与 panic。

```text
教学脚本写 /proc/sysrq-trigger
  → write 系统调用与 VFS 写入分派
  → proc_reg_write → write_sysrq_trigger
  → __handle_sysrq：查找操作、校验适用策略并调用 handler
  → sysrq_handle_crash：释放此前 RCU 读侧保护后调用 panic
```

因此该例的早期入口是“普通进程发起 write”，真正的终止决策发生在 handler 内。
它不先制造一次用户 NULL 访问，也不先制造一次内核 Data Abort；不能给这个实验补造
ESR/FAR 异常。用户崩溃、PID 1 退出、内核 BUG/Oops 和主动 SysRq 都可能最终出现
panic，但最前面的入口与错误状态不同。

#### 7.15.2 vpanic 的目标是终止与留证，不是恢复业务现场

| 段落 | 当前实现的职责 | 分析注意点 |
| --- | --- | --- |
| 接管与诊断 | 处理本 CPU 状态、panic CPU 协调、打印原因/栈等 | 重入、多 CPU、已有 Oops 会影响输出 |
| 可选捕获 | 按策略尝试已加载的 crash kernel/KGDB 等 | 配置与准备都要实际存在，不能因为有函数就称已部署 |
| 其他 CPU | 协调停止/通知 | 停住仍可能持锁，普通运行假设不再成立 |
| 通知与 dump | panic notifier、sys_info、kmsg_dump_desc | 并非在任意损坏情况下都能完整执行 |
| 结束动作 | 输出刷新、panic_timeout、emergency_restart 等 | 重启硬件、watchdog 及平台策略还会影响结果 |

本内核根据 crash_kexec_post_notifiers 决定捕获内核尝试在 notifier/dump 之前还是之后。
所以“总会先写好 pstore 再进入捕获内核”不是通用保证。本案例没有启用一套已验证的
kdump 流程，实际证据来自串口、ramoops、启动接力缓冲及后续正常启动的归档。
源码见 [panic.c](https://github.com/linux-bsp/linux-7.0/blob/master/kernel/panic.c)。

#### 7.15.3 printk ring、pstore 与文件归档是三层不同的保存

跨启动日志流程示意：比较 printk、pstore/ramoops 保存以及下次启动归档上报的职责。

```text
panic 文本进入 printk 日志
  → kmsg_dump_desc(KMSG_DUMP_PANIC, ...)
  → 已注册的 pstore dumper：pstore_dump
    从日志缓冲按容量、过滤及压缩策略组织记录
  → 后端 ramoops_pstore_write
    → 写入设备树保留的 persistent RAM 区域

下一次正常启动：
  ramoops/pstore 读取旧记录 → 用户态 logctld 复制、同步、归档和上传
  → 服务端内容确认后再按各层协议清理或回收
```

printk 环形缓冲不是普通磁盘文件，ramoops 也不是把整个内核内存转储到 rootfs。
pstore 的容量、max_reason、压缩与平台保留行为会影响可得到多少文本；启动接力缓冲
则另外保存 SPL/U-Boot/启动 kernel，不能用 pstore 代替所有前 Linux 阶段日志。
源码参考 [pstore/platform.c](https://github.com/linux-bsp/linux-7.0/blob/master/fs/pstore/platform.c)、
[pstore/ram.c](https://github.com/linux-bsp/linux-7.0/blob/master/fs/pstore/ram.c)。

#### 7.15.4 从失败原因往前追，而不是只背最后的栈

如果首次有效错误是 `/init: ... libcrypto.so ... not found`，其后发生 PID 1 退出
panic，优先检查 initramfs 的动态依赖与打包；如果栈来自非法访存，先检查第一条
错误指令和对象生存期；本例则由明确的 SysRq 操作导致。共同出现 vpanic 不表示三者
应修改同一个位置。保留第一处错误、阶段身份与重启证据，比只截最后几行更有用。

### 7.16 内核反汇编实战：从函数内偏移找到真正调用点

以下来自 `668ad82f` 配套 vmlinux，是**静态反汇编**；绝对链接地址不被当成新一次
启动的 KASLR 地址。sysrq_handle_crash 从 0xffff8000808af298 开始：

内核反汇编摘录：利用 sysrq_handle_crash 函数内偏移找到实际调用 panic 的位置。

```asm
ffff8000808af2a0: d503233f  paciasp
ffff8000808af2a4: a9bf7bfd  stp x29, x30, [sp, #-16]!
ffff8000808af2a8: 910003fd  mov x29, sp
ffff8000808af2ac: 97e1efa3  bl ffff80008012b138 <__rcu_read_unlock>
ffff8000808af2b0: b0004ce0  adrp x0, ffff80008124c000
ffff8000808af2b4: 9138a000  add  x0, x0, #0xe28
ffff8000808af2b8: 97dd991c  bl ffff800080015728 <panic>
```

ADRP+ADD 形成 panic 格式字符串地址 0xffff80008124ce28。主机 GDB 对这份 vmlinux
实际执行 `x/s 0xffff80008124ce28`，读到 `"sysrq triggered crash\n"`；
`info line *sysrq_handle_crash+0x20` 定位到 drivers/tty/sysrq.c:154。
函数内 0x20 恰好是 BL panic 的位置，连接了符号、指令、参数与源码行为。

这个函数没有普通“恢复栈再 RET”的收尾，因为 panic 不返回；不能因缺少常规尾声就
断言反汇编截断或栈被破坏。PACIASP 与开头预留 NOP 的解释见 0.17，不能由静态编码
断言 A53 已实际启用 PAC。

练习：以配套 vmlinux 反汇编 panic/vpanic，找 dump、可选捕获、超时和重启分支。
先查条件，再画路径；不要为了学习指令重复在设备上触发 panic。现有失败/恢复原始
日志可以继续用于这项离线练习，core、vmlinux 和 vmcore 的可见范围也应分别说明。

## 修复与验收

### 7.12 修复与延伸练习

本案例根因是明确的操作者注入，修复就是不再触发该路径；下一次默认启动没有持续
故障。对真实 panic，定位必须沿第一个出错调用点追根因，不能简单关闭 panic 策略。

练习：对照 SIGSEGV 案例，解释为什么普通应用缺页不会自动进入 panic；再分析
`/init` 缺 libcrypto 导致动态加载器退出、PID 1 退出与内核 panic 的关系。
说明如何用 initramfs 依赖闭包、实际 ARM64 loader 测试和前一正常槽降低这种风险。
最后区分“恢复成功”“回滚成功”“新固件升级成功”，并检查日志证据能否支撑各自结论。

### 7.13 持久化为何需要分阶段验收

捕获到 RAM、复制到文件、同步文件、上传服务器、收到 ACK 和清理缓冲是不同步骤。
如果上传前就清理，网络中断会丢失证据；如果始终不清理，则下一次失败可能覆盖或混入
旧记录。排查时按步骤查内容与状态，不把“上传连接建立了”当成“失败日志已归档”。

保留最后一次异常可减少固定缓冲的空间压力，但必须在记录中明确它对应哪次 startup。
同样 UUID 的文件名或一个设备 IP 不能替代内容核验；启动时间未校准时，还需 boot ID、
uptime 和服务端接收时间协助排序。报告中区分设备时间、接收时间与事件发生时间。

若下次 Linux 也无法启动，依赖 Linux 归档/联网的流程就无法完成。本章实测的是暖重启
后有一次正常 Linux 能读取并上报的边界，不宣称能在所有存储损坏、持续硬锁死或断电
条件下保存完整日志。识别这类边界也是恢复分析的一部分。

## 实机证据与反例

### 7.11 实机解码样例

固件 v0.0.1/7788272e 在启动约 14 秒时触发；下列调用链摘自实机串口并用配套
vmlinux 解码，显示路径省略构建目录前缀：

实机 panic 解码摘录：将串口调用链与本固件的 vmlinux 和源码位置对应。

```text
Kernel panic - not syncing: sysrq triggered crash
vpanic              kernel/panic.c:651
panic               kernel/panic.c:787
sysrq_handle_crash   drivers/tty/sysrq.c:154
__handle_sysrq       drivers/tty/sysrq.c:634
write_sysrq_trigger  drivers/tty/sysrq.c:1269
proc_reg_write      fs/proc/inode.c
vfs_write           fs/read_write.c
ksys_write          fs/read_write.c
```

串口中的 `Tainted: O` 表示加载了树外模块；它本身不能证明 PDM 是根因。这里根因
由 SysRq 写入、实验 marker、源码调用链及 panic 文本共同证明。若将来分析树外模块
中的异常，还需保留其配套未 strip 的 .ko，不能只用 vmlinux 解释模块地址。

本轮 SOL 已保存失败与正常两次启动的四段日志；失败 kernel 段 26406 字节并包含
实验 marker 和 panic，恢复 kernel 段 24967 字节。完整数据与 boot ID 见
[实机记录](https://github.com/linux-bsp/workspace/blob/cb2b20ab8d17e68f4782dd96efe5a1253b64f035/docs/am625-debug-validation.md)，不能把这里的长度作为其他版本的固定验收值。

[[附录A-实验报告/00-章节导航|实验报告与复盘]] · [[00-实验准备与通用方法/01-构建与启动部署#源码与实机证据|匹配源码、固件与实测证据]]

[[07-内核启动与恢复/B-BOOT02-initramfs动态加载器缺库导致PID1退出/B-BOOT02：initramfs 动态加载器缺库导致 PID 1 退出|下一例 B-BOOT02]]
