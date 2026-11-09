# 场景入口、现场记录与复位

本阶段把案例入口与执行负载分开：`/usr/bin/sadboard` 检查前提、创建现场、监督并记录；
`/usr/libexec/sadboard/execute` 调用具体案例。C 程序仍可直接用于 GDB/perf 等独立诊断。
直接调用程序不经过统一记录与监督，需要操作者自行保存证据及限制资源。

## 使用方法

```sh
sadboard list
sadboard run crash
sadboard run cpu 4096 500000 42
sadboard run lock 20 50000
sadboard run oom
sadboard verify crash
sadboard verify oom
sadboard verify cpu 4096 500000 42
sadboard verify lock 20 50000
```

CPU 的三个参数为记录数、查询数、种子；锁案例两个参数为每线程迭代数、每次等待微秒。
crash 可选非负记录编号，默认 42；OOM 使用固定预算，不接受扩大内存限制的参数。
未填写参数时使用文档默认值，记录中保存实际使用值。程序对工作量和数值范围继续做
检查；传入非数字、缺参数等应返回 64，不能解释为成功触发故障。

| 案例 | 可选参数与上限 |
| --- | --- |
| crash | KEY 为 0..2147483647，1 是存在的记录，其他编号触发故障版缺失路径 |
| cpu | ITEMS=1..16384、QUERIES=1..2000000、SEED=0..4294967295，且 ITEMS×QUERIES≤4000000000 |
| lock | ITERATIONS=1..200、DELAY_US=1..100000，且两线程累计等待预算≤10000000 微秒 |
| oom | 统一入口固定 64 次、每次 1 MiB、间隔 50 ms，32 MiB 组限制 |

入口要求本次启动已通过健康确认、没有待启动固件、data 健康且至少有 64 MiB 可用空间。
这是为了保留 core/日志空间，而不是替用户删除旧现场。未满足前提返回 75，不触发案例。

## 现场格式

每次创建私有目录 `/data/sadboard/<案例>-<本地时间戳>-<随机后缀>/`，UTC+8 时间戳便于
查找，随机后缀避免同秒重复。实际开始时间附时区，boot ID 负责区分时钟回拨前后启动。

| 文件 | 作用 |
| --- | --- |
| run.info | SADBOARD1 键值格式：案例、操作、完整固件 ID、tag、boot ID、内核、命令、实际参数及独立 unit 名 |
| firmware-status.txt | 公共 `fwctl ota-status` 的原始 FWOTA2 记录，用于追溯固件与部署状态 |
| stdout.log / stderr.log | 案例标准输出与错误输出 |
| supervisor.log | systemd-run 启动及监督信息 |
| result | 原子写入场景退出码、监督器原始退出码、是否取消、完成时间；缺失表示没有完成记录 |
| core.* / memory-*.events 等 | 各案例特有证据；详细解释见对应手册 |

键值记录只作为数据读取，不要用 `source run.info` 执行。短 ID 用于普通日志，完整 ID
用于证据匹配。必须保留镜像对应的 images/debug 才能分析具体源行。

## status、check 与 reset

复制入口打印的实际目录替换下面的 RUN：

```sh
sadboard status /data/sadboard/RUN
sadboard check /data/sadboard/RUN
sadboard reset /data/sadboard/RUN
```

`status` 显示元数据与结束记录；缺结束记录明确显示 incomplete，不报告通过。
`check` 对照预期信号和证据：crash 的 SIGSEGV 要有 core，OOM 要有正 oom_kill，
正常完成还要有业务输出；参考修复必须成功完成自身的对照检查。
**故障复现检查通过与问题已修复是两个概念**，性能提升仍需读采样及同输入时序数据。

`reset` 只停止该目录所属、本次 boot 的实验 unit，并保留证据；不会重置系统服务、
清除其他日志或删除现场。其他目录、符号链接、伪造的 unit 名会被拒绝。跨启动的现场
可读、可分析，但不会使用旧记录去停止本次启动的进程。

## 执行与异常边界

每次使用独立 transient service，30 秒运行上限、5 秒停止期限、16 个任务、128 MiB
监督组内存预算、32 MiB core 上限；结束后自动回收 unit。OOM 负载另受专用 32 MiB
叶子 cgroup 限制，其监督脚本保留在组外，退出时保存计数并清理。

停止请求有记录；Ctrl-C/TERM/HUP 会尝试停止本实验。控制端被强杀或设备重启时可能
没有 result，此时按不完整现场处理。systemd 的运行上限和程序本身有限工作预算仍然
生效，不能因控制端退出就把这次实验记为成功。

取消统一返回 130，同时保留 `supervisor_exit_code`。这是必要的区分：实测正常停止
unit 时 systemd-run 可以返回 0，但这并不代表业务完整执行；`cancelled=1` 的现场
始终无法通过 check。

这些边界只用于明确的手动教学负载，不改变 OTA、SOL 或 PDM 的生产服务策略；
随机组合及面向任意修复方案的自动评分仍未实现。
