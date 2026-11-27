# BSP workspace

嵌入式 Linux BSP 开发工作区，通过 Git 子模块固定一组可配套构建的源码版本。当前主线板卡为 ALIENTEK AM625。

## 组成

| 目录 | 职责 |
| --- | --- |
| `buildroot/` | 构建系统 |
| `bsp-base-external/` | 板卡配置、Buildroot 包、启动脚本、镜像布局 |
| `linux/linux-7.0/` | Linux 内核及板级驱动 |
| `uboot/u-boot-2026.04/` | R5/A53 SPL 和 U-Boot |
| `edk/` | PDM/PDI 外设管理及业务服务 |
| `edk/user/apps/` | 遥控遥测、PMC 管理 Web、OTA、设备日志及授时 |
| `libbmc/` | 独立 BMC SDK 源码快照 |
| `docs/` | 硬件资料与设计文档 |
| `output/` | 本地构建、测试与发布产物，Git 忽略 |

EDK 子仓提供设备工具、PMC 主机服务和共享协议。载荷服务器的 BMC 和 PMC 客户端统一由 `libserver` 提供。
当前模块与构建基线见 [EDK 架构](edk/docs/architecture.md)、[软件架构框图](edk/docs/软件架构设计.drawio) 和 [M0–M7 实机验收](docs/am62x/archive/2026-11-25-edk-subsystem-validation.md)。
A1–A6（含 A6.5 收口）已验收，A5 自动重建回归已补齐。logctl 非零旧凭据歧义拒绝，零游标多份旧凭据歧义先保存 v2 再发送，均通过指定 AM625 实机验证。[工作计划](edk/docs/edk-portability-integrity-plan.md) · [历史 A6.4 开发提示词](edk/docs/edk-portability-integrity-prompt.md)
既有验收记录见 [A1–A4 规则所有权与 ABI 核验](edk/docs/edk-convergence-a4-validation.md) · [A5 包来源验收](edk/docs/edk-convergence-a5-validation.md) · [A6 续传验收](edk/docs/edk-convergence-a6-validation.md) · [A6 AM625 实机记录](docs/am62x/edk-convergence-a6-validation.md)。
A19–A21 的开发结果见 [修复计划与回归记录](edk/docs/archive/2026-11-26-portability-repair/README.md) 和 [AM625 实机记录](docs/am62x/archive/2026-11-26-portability-repair/README.md)。
A13–A18 及两轮复查修复的历史资料见 [EDK 计划与过程记录](edk/docs/archive/2026-11-26-portability/README.md) 和 [AM625 实机记录](docs/am62x/archive/2026-11-26-portability/README.md)。更早的模块复核见 [A1–A12 归档](edk/docs/archive/2026-11-26-module-audit/README.md)。

## 拉取与构建

```sh
git clone --recurse-submodules git@github.com:linux-bsp/workspace.git am62x
cd am62x
make -C buildroot O="$PWD/output/am625" \
  BR2_EXTERNAL="$PWD/bsp-base-external" alientek_am62x_defconfig
make -C buildroot O="$PWD/output/am625" all
```

首次构建的 defconfig 使用内部工具链，不依赖预装 SDK。已有输出目录直接执行 `all`；不要重新应用 defconfig 覆盖定制的外部工具链设置。下载缓存可通过 `BR2_DL_DIR="$HOME/workspaces/dl"` 共享。镜像生成在 `output/am625/images/`。

SDK 使用独立输出目录，按 [BSP 外部层说明](bsp-base-external/README.md) 执行 `make sdk` 后手动解压并运行 `relocate-sdk.sh`。共享工具链可放在 `~/workspaces/toolchain/`。

## 设备管理与日志

```sh
make -C buildroot O="$PWD/output/am625" host-edk
export PATH="$PWD/output/am625/host/bin:$PATH"
dmserver --root "$PWD/output/device-feed" \
  --bind 0.0.0.0 --port 8090 --sol-debug-no-auth
```

使用 [Device Manager](edk/user/apps/pmcd/README.md) 管理固件上传、发布、设备升级结果及审计。OTA/SOL 位于侧栏；SOL 支持只读网络日志查看和回放，当前调试环境免凭据自动连接，配置见 [SOL 指南](edk/user/apps/pmcd/README.md#启动日志与异常证据)。端口 8090 避开本机 GitLab 的 8080。

OTA 自动按固件包声明的全部 HWID 发布，页面产品信息从 HWID 解析。身份字段与配置见 [HWID 说明](edk/user/apps/fwctl/README.md#hwid)，操作与验证见 [固件 HWID 自动发布](docs/am62x/firmware-hwid-publication.md)。

跨 U-Boot/Linux 的命令、槽位含义、手动维护及恢复边界见 [固件升级操作指南](docs/am62x/firmware-upgrade-guide.md)；逐阶段实机结果见 [优化验收记录](docs/am62x/firmware-upgrade-optimization-validation.md)。

设备串口执行 `logctl status`、`logctl boots`、`logctl show --boot previous` 查看日志。持久化要求已有可写的 `/data` 文件系统；没有时退回 RAM 并告警。系统不会自动格式化分区，也不依赖 SSH。SPL/U-Boot 日志接力需要安装对应新引导程序，kernel/rootfs OTA 不会自动完成这一步。

AM625 的操作、服务、可靠性边界与验证资料统一见 [板卡文档索引](docs/am62x/README.md)。

## 子模块与版本管理

```sh
git submodule update --init --recursive
git submodule status
git status --short
```

默认使用本仓库记录的准确提交。当前开发统一使用 `master`，EDK、Linux 原 OTA 开发线已经合入主分支。`.gitmodules` 中的 `branch = master` 只影响显式执行 `git submodule update --remote`；普通子模块初始化仍检出固定提交，可能显示 detached HEAD。

EDK 和设备固件共用 [edk/VERSION](edk/VERSION)，当前为 `0.0.1`。Buildroot 的 target/host EDK 包和板级 `firmware.json` 都读取此文件；同版本的不同内容通过 SHA256 hash ID 区分。

修改后先提交子仓库，再更新工作区 gitlink。推送工作区前确保引用的子仓库提交已上传。版本仅在明确要求时调整；设备重启并通过健康检查、上报成功之后才提交对应代码。验证记录见 [AM625 发布记录](bsp-base-external/board/ti/am625/releases/README.md)。
