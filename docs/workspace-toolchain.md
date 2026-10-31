# Workspace 目录与 AM62x SDK

## 建议目录

以下为计划采用的目录布局；现有工作区尚未迁移。

```text
~/workspace/                         # 普通容器目录
├── am62x/                           # workspace 仓库的 BSP 开发副本
├── SadBoard/                        # workspace 仓库的 SadBoard 分支副本
├── dl/                              # 共享源码下载缓存
└── toolchain/                       # 手动解压、重定位后的 SDK
    └── aarch64-buildroot-linux-gnu_sdk-buildroot/
```

两个仓库分别保留构建输出及其 `host/`。公共 `toolchain/` 存放由 `make sdk`
导出的工具链；不把两个构建的 `BR2_HOST_DIR` 指向这里。
迁移前保存未提交修改，在新位置重新生成构建配置；旧构建输出含绝对路径，
不能仅移动目录就假定可以继续增量编译。

## 生成独立 SDK

配置位于 `bsp-base-external/configs/am62x_sdk_defconfig`，只依赖 Buildroot
和 BSP external 源码，不需要 SadBoard external、Linux、U-Boot、EDK 或 libbmc
源代码子模块。主机仍需具备 Buildroot 构建依赖，并能够下载所需源码。

SDK 使用 AArch64、GCC 15、glibc、Linux 7.0 系列头文件，支持 C++，
包含支持 Python 的交叉 GDB 和 `environment-setup`。它关闭 BusyBox、
启动系统及 rootfs 镜像，没有启用板级应用、内核或 bootloader；Buildroot
仍会生成工具链所需的 sysroot 和内部目标目录。它不是可启动的板卡系统。

在新布局的 SadBoard 仓库根目录运行（也可以在包含此配置的 am62x 副本运行）：

```sh
cd ~/workspace/SadBoard
git submodule update --init buildroot bsp-base-external
export BR2_DL_DIR="$HOME/workspace/dl"

make -C buildroot O="$PWD/output/am62x-sdk" \
  BR2_EXTERNAL=../bsp-base-external am62x_sdk_defconfig
make -C output/am62x-sdk sdk
```

尚未迁移时，先进入当前实际仓库根目录，再运行相同的配置和构建命令。
`O=` 指定专用 SDK 输出目录，避免覆盖 AM625 调试镜像的配置。
第二条 `make` 会使用输出目录记录的 external 配置，不必再传 `BR2_EXTERNAL`。
`BR2_DL_DIR` 是当前 shell 的环境变量，新终端需要重新导出或设置在本机 shell 配置中。

原生 `make sdk` 会构建依赖、准备可重定位 SDK 并生成压缩包，无须先执行
`make all`。默认压缩包为：

```text
output/am62x-sdk/images/aarch64-buildroot-linux-gnu_sdk-buildroot.tar.gz
```

## 手动解压与重定位

仍在生成 SDK 的仓库根目录，且目标 SDK 目录尚不存在时执行：

```sh
mkdir -p "$HOME/workspace/toolchain"
tar -xzf output/am62x-sdk/images/aarch64-buildroot-linux-gnu_sdk-buildroot.tar.gz \
  -C "$HOME/workspace/toolchain"
"$HOME/workspace/toolchain/aarch64-buildroot-linux-gnu_sdk-buildroot/relocate-sdk.sh"

"$HOME/workspace/toolchain/aarch64-buildroot-linux-gnu_sdk-buildroot/bin/aarch64-buildroot-linux-gnu-gcc" -dumpmachine
"$HOME/workspace/toolchain/aarch64-buildroot-linux-gnu_sdk-buildroot/bin/aarch64-buildroot-linux-gnu-gcc" -dumpversion
```

预期目标为 `aarch64-buildroot-linux-gnu`，GCC 主版本为 `15`。
以后移动或重命名 SDK 目录，需要再次运行其中的 `relocate-sdk.sh`。
不要将新压缩包直接覆盖解压到正在使用的 SDK 目录；可以在构建时指定
`BR2_SDK_PREFIX`，让压缩包与内部顶层目录采用明确的版本名：

```sh
make -C output/am62x-sdk sdk BR2_SDK_PREFIX=am62x-gcc15-linux7-v1
```

这种情况下，将前述解压和重定位命令中的文件名及目录名相应替换。
需要编译外部应用时，可以在专用 shell 中 source SDK 的 `environment-setup`；
运行 Buildroot 本身时使用未加载该脚本的 shell。

## SadBoard 复用 SDK

在含有 `sadboard-external` 的仓库根目录，使用新的输出目录：

```sh
python3 sadboard-external/scripts/configure-am625.py \
  --output output/am625-shared-sdk \
  --toolchain "$HOME/workspace/toolchain/aarch64-buildroot-linux-gnu_sdk-buildroot" \
  --dl-dir "$HOME/workspace/dl"
make -C output/am625-shared-sdk
```

标准 `sadboard_am625_debug_defconfig` 仍默认自行构建工具链；解压 SDK 不会
自动改变它。上述可选脚本会配置外部工具链。不要在已有输出目录中直接切换
内部与外部工具链。这套 SDK 面向当前 Linux 7.0 的 AM62x 配置；若板上运行
更早的内核，需要调整头文件版本及外部工具链配置。i.MX6ULL 需要独立的 ARM32 SDK。

## 验证范围

本次验证配置加载、工具链选项和包依赖，不代表新 SDK 已完成编译、解压或上板测试。
SDK 导出和重定位流程依据本仓库 Buildroot 的
[`using-buildroot-toolchain.adoc`](../buildroot/docs/manual/using-buildroot-toolchain.adoc)
及 [`Makefile`](../buildroot/Makefile)。
