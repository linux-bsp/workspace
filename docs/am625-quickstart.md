# SadBoard AM6254 快速上手

当前基线使用 systemd、现有 RAW A/B 布局和 EDK 的 OTA/SOL。实验需手动启动。
实际通过的固件 ID 与结果见 [验证记录](am625-debug-validation.md)，阶段安排见
[开发计划](sadboard-development.md)。旧 `output/am625-debug/` 产物不用于本轮。

## 构建与产物

新克隆工作区：

```sh
git submodule update --init --recursive
cd buildroot
BR2_EXTERNAL="../bsp-base-external ../sadboard-external" \
  make sadboard_am625_debug_defconfig && make all
```

默认产物在 `buildroot/output/images/`。本机用共享 SDK 加速，采用独立目录：

```sh
python3 sadboard-external/scripts/configure-am625.py \
  --output output/am625-debug-systemd \
  --toolchain ../toolchain/aarch64-buildroot-linux-gnu_sdk-buildroot \
  --dl-dir ../dl
make -C output/am625-debug-systemd all
```

输出已有配置时继续执行 `make all`。修改实验包源码后，需要显式重建本地包：

```sh
make -C output/am625-debug-systemd sadboard-labs-dirclean
make -C output/am625-debug-systemd all
```

不能把内部/外部工具链混入同一个输出目录。

| 产物 | 用途 |
| --- | --- |
| `images/release/{release,kernel,rootfs}.itb` | OTA 升级包，只更新 kernel/rootfs |
| `images/debug/vmlinux`、`System.map`、`kernel.config` | 与设备内核匹配的分析资料 |
| `images/debug/labs/`、`images/debug/source/` | 实验程序及源码 |
| `images/debug/build-info.json` | 固件 ID 与调试资料 SHA256 |
| `staging/` | 远程 GDB 的匹配 sysroot |
| `images/rootfs.tar` | rootfs 归档，供单独的 NFS 实验使用 |

保留现有分区和板上启动链。通过 Device Manager 上传并发布三个 ITB 的 tar.gz，
待设备上报 success 后再触发实验。`sdcard.img` 是工厂镜像，不用于覆盖当前实验板。

构建后先核对符号归属、SHA256、ELF 调试段和关键内核能力：

```sh
python3 sadboard-external/scripts/verify-debug.py output/am625-debug-systemd/images
```

## 检查环境

通过串口或 SOL 在板端执行：

```sh
fwctl version
systemctl --failed --no-pager
sadboard-debug-check
sadboard list
perf stat -e task-clock -- sleep 1
cat /sys/kernel/tracing/available_tracers
```

检查脚本只检查能力；`perf stat` 进一步检验事件实际可用性。基本服务和 OTA 健康
确认完成后，再启动故障案例。内存、perf 与 trace 数据写 `/data/sadboard/`。

## SSH 登录

当前调试配置允许 root 空密码登录，端口为 22：

```sh
ssh root@192.168.10.211
```

SadBoard 从 `/data/ssh/host/` 恢复主机密钥；私钥只在设备生成和保存，不进入 Git 或固件包。
需要 scp 传文件时使用 `scp -O`，本镜像没有配置 SFTP 服务。串口/SOL 入口仍保留。

## 第一个 GDB 在线实验

板端运行：

```sh
gdbserver :2345 /usr/libexec/sadboard/crash-bug 42
```

主机用同次构建的调试器和程序，按本机路径设置 sysroot 和源码映射：

```sh
output/am625-debug-systemd/host/bin/aarch64-buildroot-linux-gnu-gdb \
  output/am625-debug-systemd/images/debug/labs/crash-bug
```

```gdb
set sysroot /home/guohao/workspaces/SadBoard/output/am625-debug-systemd/staging
set substitute-path /usr/src/sadboard /home/guohao/workspaces/SadBoard/output/am625-debug-systemd/images/debug/source
target remote 192.168.10.211:2345
break process_request
continue
next
print key
print record
continue
bt
frame 0
info locals
list
```

现象是查询不存在的记录后 SIGSEGV。正常输入 `1` 能输出 value=64；输入 `42`
使查询返回空指针，故障版在检查前访问 `record->value`。实验源码保存在
`/usr/src/sadboard/src/crash.c`，其中 `SADBOARD_FIXED` 分支是参考修复。

## core 离线分析与参考修复

先检查 core 保存策略和 data 空间：

```sh
cat /proc/sys/kernel/core_pattern
df -h /data
sadboard run crash
```

`run crash` 创建独立现场目录并设置进程 core 上限为 32 MiB，预期进程退出码为
139。若内核 core_pattern 是普通文件名（本基线为 `core.%e.%p`），core 位于该现场目录。
如果策略使用管道收集器，按实际收集器导出，不能假设工作目录里必有 core。

把 core 传回主机后，使用匹配的 crash-bug、sysroot 和上述源码映射：

```gdb
set sysroot /home/guohao/workspaces/SadBoard/output/am625-debug-systemd/target
core-file /实际路径/core
bt
frame 0
info locals
```

离线分析的 sysroot 要包含目标路径下的程序和库；上例使用本次构建的 target，
也可换成同固件 rootfs.tar 的解包目录。staging 主要提供开发库，可能不含主程序。

参考修复验收：

```sh
sadboard verify crash
```

它检查有效输入仍返回 value=64，而不存在的记录返回 2，不能仅以“不再崩溃”作为
修复成功。此命令验证随镜像提供的参考版；用户自行修改的代码仍需重新构建部署并
验证相同输入。复位应用现场不需要重启；完成取证后手动删除自己创建的现场目录。

每次更新保留匹配的符号与完整固件 ID。详细配置见 [环境指南](am625-bootlin-debug-environment.md)。
