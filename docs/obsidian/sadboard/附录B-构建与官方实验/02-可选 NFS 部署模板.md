---
title: "可选 NFS 部署模板"
type: "topic"
tags: ["sadboard/topic"]
chapter: "附录B-构建与官方实验"
---

# 可选 NFS 部署模板

[[首页]] · [[附录B-构建与官方实验/00-章节导航|章节导航]] · [[案例索引]] · [[工具索引]]


## B.2 可选 NFS 部署模板

NFS 供独立调试环境使用，下面是部署模板，并非已在当前 systemd/OTA 基线上实测的命令。
要先确认服务器 NFS 服务、板卡地址、实际 U-Boot 能力和可恢复管理链路。使用空的专用
目录解包，不覆盖服务器其他根目录：

```sh
sudo mkdir -p /srv/nfs/sadboard-am625
sudo tar --numeric-owner -xpf output/am625-debug-systemd/images/rootfs.tar -C /srv/nfs/sadboard-am625
BOARD_IP=192.168.10.211
sudo exportfs -o rw,sync,no_subtree_check,no_root_squash "$BOARD_IP:/srv/nfs/sadboard-am625"
```

临时导出不代表已配置永久服务。按实际设备替换 BOARD_IP 与服务器地址，保留板上
正确的串口、加载地址和设备树设置。根文件系统启动参数模板为：

```text
root=/dev/nfs rw ip=<板IP>::<网关>:<掩码>:sadboard:eth0:off nfsroot=<主机IP>:<导出目录>,vers=3,tcp
```

不直接执行占位符；先临时验证，再决定持久化配置。Image.gz 能否直接启动取决于 U-Boot，
必要时主机解压为 Image。NFS 本身会增加网络流量，网络性能比较应使用本地根文件系统。
使用本手册的 `sadboard` 统一入口仍要求持久 data 与已有健康确认；NFS 模板并不取消前提。
