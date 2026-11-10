---
title: "配置组成与标准 defconfig 维护"
type: "topic"
tags: ["sadboard/topic"]
chapter: "附录B-构建与官方实验"
---

# 配置组成与标准 defconfig 维护

[[首页]] · [[附录B-构建与官方实验/00-章节导航|章节导航]] · [[案例索引]] · [[工具索引]]


## B.1 配置组成与标准 defconfig 维护

| 层次 | 输入 | 用途 |
| --- | --- | --- |
| 板级基线 | `bsp-base-external/configs/alientek_am62x_defconfig` | AM6254、启动与基础服务 |
| 调试工具 | `sadboard-external/configs/debug-tools.config` | GDB、strace、perf 等工具与调试能力 |
| 调试板配置 | `sadboard-external/board/am625/debug.config` | systemd、overlay 和实验能力 |
| 内核片段 | `sadboard-external/kernel/debug.config` | ftrace、perf、memcg、core 等 |
| 可选诊断片段 | `kernel/kgdb.config`、`kernel/memory.config` | 独立诊断构建，不能混作性能基线 |

标准配置已保存到 `sadboard-external/configs/sadboard_am625_debug_defconfig`。
普通用户从本手册 0.1 的标准入口构建；维护者修改基线/片段后，在新的输出目录重新导出：

```sh
regen_dir=$(mktemp -d)
python3 sadboard-external/scripts/configure-am625.py \
  --output "$regen_dir" --export-defconfig
git -C sadboard-external diff -- configs/sadboard_am625_debug_defconfig
```

核对配置等价和差异后再提交。已有 `.config` 时脚本拒绝覆盖，内部/外部工具链不能
混入同一输出树；外部工具链中原本缺失的 libc 符号不能通过给应用增加 `-g` 补回。
`target/` 是构建中间目录；制作 NFS 根文件系统应从处理权限后的 `rootfs.tar` 解包。
