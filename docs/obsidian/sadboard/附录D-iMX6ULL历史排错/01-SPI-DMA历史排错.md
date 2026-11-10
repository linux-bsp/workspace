[[首页]] · [[案例索引]] · [[工具索引]] · [[附录D-iMX6ULL历史排错/00-章节导航|章节导航]]

## 现象

内核启动过程中出现如下报错：

历史启动错误摘录：识别 ecspi3 获取 TX DMA 通道失败的具体报错。

```text
spi_imx 2010000.spi: error -ENODEV: can't get the TX DMA channel!
```

其中 `2010000.spi` 对应 SoC 设备树中的 `ecspi3` 控制器。

## 原因

ATK-DL6Y2C 板级设备树中曾删除了 `ecspi3` 继承自 SoC dtsi 的 DMA 属性：

历史 DTS 片段：查看板级覆盖如何删除继承的 DMA 属性，并结合下文分析驱动后果。

```dts
&ecspi3 {
	/delete-property/ dmas;
	/delete-property/ dma-names;
};
```

同时裁剪后的内核配置只保留了 `CONFIG_MXS_DMA=y`，没有启用 i.MX 外设 DMA 控制器驱动 `CONFIG_IMX_SDMA`。`spi-imx` 驱动在初始化 ECSPI3 时会通过设备树申请 `rx` 和 `tx` DMA channel；DMA 属性缺失或 SDMA 驱动未编译进内核，都会导致 TX DMA channel 获取失败。

## 修复

本次修复包含两部分：

1. 恢复 `ecspi3` 的 DMA 属性继承。

   删除 `linux/linux-7.0/arch/arm/boot/dts/nxp/imx/imx6ull-atk-dl6y2c.dts` 中对 `dmas` 和 `dma-names` 的删除语句，让 `ecspi3` 继续继承 `imx6ul.dtsi` 中的配置：

   ```dts
   dmas = <&sdma 7 7 1>, <&sdma 8 7 2>;
   dma-names = "rx", "tx";
   ```

2. 在基础和调试内核配置中启用 i.MX SDMA。

   修改文件：

   - `bsp-base-external/board/freescale/imx6ull-evk/linux_defconfig`
   - `bsp-base-external/board/freescale/imx6ull-evk/linux_debug_study_defconfig`

   增加配置：

   ```text
   CONFIG_IMX_SDMA=y
   ```

## 相关提交

- `linux/linux-7.0`: `8d397569a arm: dts: enable atk dl6y2c ecspi dma`
- `bsp-base-external`: `adb1aa2 board: enable imx sdma for spi`
- 主仓库指针更新: `47d5d4b bsp: enable spi sdma support`

## 后续验证

重新生成并启动内核后，确认启动日志中不再出现：

修复后的日志检查目标：重新启动对应历史板卡，确认以下 DMA 报错不再出现。

```text
spi_imx 2010000.spi: error -ENODEV: can't get the TX DMA channel!
```

如果仍有 SDMA 相关日志，需要继续检查：

- `/lib/firmware/imx/sdma/sdma-imx6q.bin` 是否存在于根文件系统中。
- Buildroot 配置是否启用了 `BR2_PACKAGE_FIRMWARE_IMX=y`。
- DTS 中 `sdma` 节点的 `fsl,sdma-ram-script-name` 是否仍为 `imx/sdma/sdma-imx6q.bin`。
