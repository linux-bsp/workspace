# A2：AM625 正常 DTB 依赖与活动设备树验证

E=`output/edk-convergence-a2-20261126-212041-44oQpe/`，F=E/final/。[BSP 开发与回归](../../edk/docs/edk-convergence-a2-validation.md)。

- 指定板可信 SSH key 核对，MAC `1c:63:49:22:c4:f7`、HWID `1010001000110000`、boot ID `f2288b6f-1aca-444a-8d13-efe9e917cc2a`，槽 B，`v0.0.1` packed 1、完整 ID `43efbac30fe4a8f4a4b7f9ba7be92b7d33568056fa5959c2e9ffeb7869c7c695`。E/board-before.log、F/board-check.log、ota-success.json/device-transaction.json：仍为 A1 `draft-REJVTM` 的 `success`，running=version=1，confirmed successful=1，健康通过，8 服务 active、0 failed、FWCHECK1 match。
- A2 选定正常候选实际重新打包。独立比较 kernel FIT 12940585 bytes `d791aa629fb1f8039bb41397e1c0657ab5ff2a6ba4ea1cd337aa12c864460073`、rootfs payload 30429184 bytes `06da5d6611912bd7cb436afe3e8327600e39e11cc29a0766e157f37c9115ddda`，完整 identity、kernel/rootfs/bootloader/release FIT、提取的 rootfs bytes 均与 A1 之前成功候选逐字相同（F/content-reuse.log）。因此是校验/sidecar 改动，不重复 OTA，不刷写未安装 bootloader。
- F/packed-kernel.dtb 从最终 FIT 提取所选 FDT；对照实板同一 boot 的 `/sys/firmware/devicetree/base` 得 compatible `bsp,bootlog-v2`、memory-region 与 reservation phandle `0x3f`，reg `0x9c900000 / 0x100000`，全部与 FIT 相等。F/board-verify.log、active-*.bin。9/9 实装目标制品与此候选 rootfs 逐文件 SHA 相同（F/board-package-compare.log）。
- 同一 boot 的启动日志 `logctl status` persistent/sync ok、verify-boot PASS、RAM acknowledged；capture `f3e62d17-0a57-4e8e-b134-8e99e39d64fd`，r5-spl 418 bytes CRC 009ae072、a53-spl 455 CRC 55250dc9、uboot 3027 CRC c1ce6769、kernel 24705 CRC 8871cdb1，dropped=0；前三项本地/服务端逐字相等、kernel early 0-byte prefix 与 sealed CRC 匹配。F/archive-verified.log。
- 三种提前终止或过期记录均仅存在主机独立 build/镜像副本。没有在实板安装异常 DTB 或改变实际设备状态，没有操作其他真实服务器。原 Buildroot 配置、VERSION 不变；阶段源码及远端核验 E/git-verification.log。
