# AM625 固件模块归并与验证

## 调整范围

将 device-manager 顶层 `firmware/`、`fwctl/`、`recovery/` 归并为一个
`fwctl/` 模块。原来三个目录已经链接进同一个程序，本次统一源码组织和构建入口，
不改变固件命令、A/B 元数据、版本/哈希规则、分区布局或恢复策略。
时间模块保持现有 timectl/timectld 实现，不切换 systemd-timesyncd。

```text
device-manager/fwctl/
├── cli/         # 命令与显示
├── core/        # FIT、身份、元数据、升级和恢复事务
├── storage/     # 块设备与 MTD 后端
├── recovery/    # initramfs PID 1 和根文件系统交接
├── health/      # systemd、外设状态和健康检查
├── include/     # 模块接口
├── tests/       # 固件及恢复测试
├── Makefile
└── README.md
```

模块独立构建：`make -C device-manager/fwctl`；测试：
`make -C device-manager/fwctl test`。仓库原 `make fwctl` 转交模块 Makefile，
继续生成 `device-manager/bin/fwctl`，Buildroot 安装位置仍为 `/usr/sbin/fwctl`。
对象文件记录头文件依赖，未修改时不重新编译，公共头文件变更会重新构建受影响对象。

原生测试随模块移动；BSP 的 FIT、存储身份、initramfs 验证脚本更新源码路径。
存储身份测试补齐独立 HWID 测试桩，只模拟板卡身份，仍使用生产 FIT 解析和存储读取代码。
原未被构建使用的共享库导出映射移除；29 个固件运行源码/头文件按内容核对保持一致。

## 发布前验证

固件保持 `v0.0.1`，本次发布内容 ID：
`40b34fcec79b79832582c3542bcac57fa6527b51be1bdc46ab286e5eff2b3983`。

已通过：

- 8 组固件引擎、命令、事务、恢复与实际读取测试。
- 7 项 systemd 健康检查、17 项公共传输、39 项 OTA 代理测试。
- 6 项 initramfs/恢复、4 项 FIT、7 项存储身份测试。
- Linux → U-Boot sandbox → Linux 元数据互读及错误身份拒绝。
- 实际发布 initramfs 的 ARM64 fwctl/BusyBox 动态加载、PID 1 限制及缺库回归。
- 最终 squashfs 中的 fwctl 与 target 一致；timectl 最终二进制与归并前完全相同。
- Buildroot 清理旧 device-manager 构建树后重新构建，旧源码目录不残留。

## 实机验证

本次发布审计编号为 87。AM625 从 `b3397bb3` 升级到 `40b34fce`，
版本均为 `v0.0.1`。设备重启后进入 confirmed/successful=1，服务器收到 success。
本次 boot ID：`8a293846-1753-4d43-95e3-3bd5cf795d0e`。

串口实测：

- `fwctl health-check` 成功，systemd 无失败单元，相关六个服务均 active。
- `fwctl recovery check-slot 0/1` 均返回 match，两个 rootfs 槽完整。
- `fwctl ota-check` 对当前内核/rootfs 的实际内容返回 match；保持版本不变、
  更换期望哈希后返回 different。
- 普通 rootfs 下 `fwctl init` 返回状态 2，保持 PID 1 执行限制。
- timectld 保持原 HTTP 时间源，已同步且显示 UTC+8；本次未修改其源码或二进制。
- 日志 storage=persistent、sync-state=ok，跨重启存储检查与启动日志归档检查成功，
  两份 RAM 启动缓冲已收到归档确认。

本次不破坏实机分区、不执行工厂初始化；异常输入和中断事务由隔离测试验证。
kernel/rootfs OTA 不代表重新验证或更新了 SPL/U-Boot。

审计目录：`output/ota-validation/0.0.1-fwctl-module/`，保存不可变固件包、源码快照、
测试结果、发布事务和串口日志。模块职责见
[fwctl 模块说明](../../device-manager/fwctl/README.md)。
