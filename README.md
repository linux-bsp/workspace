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
| `edk/user/`、`edk/host/device-manager/` | 管理 Web、OTA、fwctl/fwctld、logctl/logctld |
| `libbmc/` | 独立 BMC SDK |
| `docs/` | 硬件资料与设计文档 |
| `output/` | 本地构建、测试与发布产物，Git 忽略 |

Device Manager 已拆为 EDK 子模块；设备工具、主机服务与共享协议统一构建，libbmc 继续独立。
合并范围和实机验收见 [仓库合并记录](docs/am62x/edk-device-manager-merge.md)。

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
output/am625/host/bin/device-server --root "$PWD/output/device-feed" --bind 0.0.0.0 --port 8090
```

使用 [Device Manager](edk/docs/device-manager-integration.md) 管理固件上传、发布、设备升级结果及审计。OTA/SOL 位于侧栏；SOL 支持只读网络日志查看和回放，当前调试环境免凭据自动连接，配置见 [SOL 指南](edk/docs/device-manager/sol.md)。端口 8090 避开本机 GitLab 的 8080。

OTA 自动按固件包声明的全部 HWID 发布，页面产品信息从 HWID 解析。身份字段与配置见 [HWID 说明](edk/docs/device-manager/hwid.md)，操作与验证见 [固件 HWID 自动发布](docs/am62x/firmware-hwid-publication.md)。

跨 U-Boot/Linux 的命令、槽位含义、手动维护及恢复边界见 [固件升级操作指南](docs/am62x/firmware-upgrade-guide.md)；逐阶段实机结果见 [优化验收记录](docs/am62x/firmware-upgrade-optimization-validation.md)。

设备串口执行 `logctl status`、`logctl boots`、`logctl show --boot previous` 查看日志。持久化要求已有可写的 `/data` 文件系统；没有时退回 RAM 并告警。系统不会自动格式化分区，也不依赖 SSH。SPL/U-Boot 日志接力需要安装对应新引导程序，kernel/rootfs OTA 不会自动完成这一步。

AM625 的现状核查、重启原因记录、日志持久化上报和分阶段验收计划见 [固件恢复与启动日志软件架构及开发计划](docs/am62x/firmware-logging-architecture-plan.md)。

## 子模块与版本管理

```sh
git submodule update --init --recursive
git submodule status
git status --short
```

默认使用本仓库记录的准确提交。`.gitmodules` 中的 `branch = master` 只影响显式执行 `git submodule update --remote`；它不会改变固定提交，也不代表每个本地开发分支都叫 master。EDK、Linux 的 OTA 开发提交可能来自 `ota/v1.0.16` 分支。

修改后先提交子仓库，再更新工作区 gitlink。推送工作区前确保引用的子仓库提交已上传。固件 tag 固定 `v0.0.1`，内容变化更新 SHA256；设备重启并通过健康检查、上报成功之后才提交对应代码。验证记录见 [AM625 发布记录](bsp-base-external/board/ti/am625/releases/)。
