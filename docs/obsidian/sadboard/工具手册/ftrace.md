[[首页]] · [[工具索引]] · [[案例索引]]

## 解决的问题

理解内核 tracer、事件、tracefs 和缓冲区的控制关系。

## 工作原理与准备

ftrace 是内核跟踪框架，tracefs 是控制/读取接口。[[工具手册/trace-cmd]] 是配置、录制与解码的用户态工具。SadBoard 只准备接口，不在启动时开启全量跟踪。

## 参数与结果解释

| 参数/字段 | 含义与判断方法 |
| --- | --- |
| `available_tracers` | 当前构建可选择的 tracer。 |
| `current_tracer` | 当前 instance 选用的 tracer。 |
| `tracing_on` | 控制是否继续向缓冲区记录。 |
| `trace` / `trace_pipe` | 前者读取缓冲内容；后者消费流式记录。 |
| `set_ftrace_filter` | 限制函数跟踪的范围。 |
| `events/SUBSYSTEM/EVENT` | 事件配置入口，先核对当前内核是否提供。 |

## 操作步骤

设备端：列出实际可用 tracer。

```sh
cat /sys/kernel/tracing/available_tracers
```

设备端：查看当前选择及记录状态，先确认是否已有其他采集。

```sh
cat /sys/kernel/tracing/current_tracer
```

设备端：查看记录开关的现值。

```sh
cat /sys/kernel/tracing/tracing_on
```

## 判断边界

函数和事件跟踪均会占用缓冲并扰动系统。同一 instance 的配置会影响其他使用者，应限定范围、使用自己的 instance 并恢复配置。

扩展练习可以读 `current_tracer`、`tracing_on`、`trace`、`trace_pipe`、
`set_ftrace_filter`：前者选择 tracer，tracing_on 控制写缓冲，trace 是快照式读取，
trace_pipe 消费流式记录，filter 限定函数。函数跟踪需先筛选，避免全局高频跟踪冲掉
证据或改变系统行为。写这些文件会影响同一 tracing instance 的其他使用者；
优先使用独立 instance 并恢复自己的配置。接口见
[当前内核 ftrace 文档](https://github.com/linux-bsp/linux-7.0/blob/master/Documentation/trace/ftrace.rst)。

## 使用场景

下面链接直达具体案例的定位章节。基础流程沿用实机验收，扩展工具观测不自动记作已执行。

| 案例 | 本工具的观测目标 |
| --- | --- |
| [[05-锁与线程调度/B-SYNC01-持锁执行慢操作导致线程串行等待/B-SYNC01：持锁等待与线程调度#定位方法\|B-SYNC01：持锁等待与线程调度]] | 核对内核事件/跟踪器与观测范围 |
| [[05-锁与线程调度/B-SYNC02-ABBA锁顺序造成互相等待/B-SYNC02：ABBA 锁顺序造成互相等待#定位方法\|B-SYNC02：ABBA 锁顺序造成互相等待]] | 核对内核事件/跟踪器与观测范围 |
| [[05-锁与线程调度/B-SYNC03-条件变量丢失唤醒/B-SYNC03：条件变量丢失唤醒#定位方法\|B-SYNC03：条件变量丢失唤醒]] | 核对内核事件/跟踪器与观测范围 |
| [[05-锁与线程调度/B-SYNC04-分开的检查与更新导致逻辑丢失/B-SYNC04：分开的检查与更新导致逻辑丢失#定位方法\|B-SYNC04：分开的检查与更新导致逻辑丢失]] | 核对内核事件/跟踪器与观测范围 |
| [[05-锁与线程调度/B-SYNC05-退出路径等待一个永不完成的工作线程/B-SYNC05：退出路径等待一个永不完成的工作线程#定位方法\|B-SYNC05：退出路径等待一个永不完成的工作线程]] | 核对内核事件/跟踪器与观测范围 |
