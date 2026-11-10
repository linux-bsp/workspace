---
title: "可选 KGDB 与内存诊断配置"
type: "topic"
tags: ["sadboard/topic"]
chapter: "附录B-构建与官方实验"
---

# 可选 KGDB 与内存诊断配置

[[首页]] · [[附录B-构建与官方实验/00-章节导航|章节导航]] · [[案例索引]] · [[工具索引]]


## B.4 可选 KGDB 与内存诊断配置

为诊断变体使用新的输出目录，不覆盖已验证的常规镜像：

```sh
make -C buildroot O="$PWD/output/am625-kgdb" \
  BR2_EXTERNAL="$PWD/bsp-base-external $PWD/sadboard-external" sadboard_am625_debug_defconfig
buildroot/utils/config --file output/am625-kgdb/.config \
  --set-str BR2_LINUX_KERNEL_CONFIG_FRAGMENT_FILES \
  '$(BR2_EXTERNAL_SADBOARD_PATH)/kernel/debug.config $(BR2_EXTERNAL_SADBOARD_PATH)/kernel/kgdb.config'
make -C output/am625-kgdb olddefconfig all
```

内存诊断使用另一个输出目录，以同样的原生步骤将额外片段换为
`$(BR2_EXTERNAL_SADBOARD_PATH)/kernel/memory.config`；也可以在 Buildroot 的
Kernel 菜单中直接设置额外配置片段。不要覆盖常规镜像的输出目录。

KGDB 需要确认串口所有权和 watchdog：内核被调试器暂停后，依赖 Linux 任务的喂狗也会
停止。memory 片段提供 lockdep、原子上下文检查和 kmemleak 等诊断选项。
片段中 kmemleak 默认关闭，可按该独立诊断配置通过启动参数 `kmemleak=on` 开启；
实际选项以最终配置为准。诊断配置不等于已经完整构建或实机验收，状态见验收档案。

当前教材没有把 Bootlin 的故意破坏 watchdog 补丁、BTF/eBPF、KASAN 或 kdump 捕获
内核视为已集成案例。kdump 需要独立捕获内核、内存预留、保存 vmcore 和匹配符号的验证，
不能仅凭一个配置项宣称完成。
