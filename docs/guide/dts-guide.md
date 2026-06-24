# DTS 配置与硬件验证指导手册

本文是仓库级 DTS 配置与硬件验证通用指南，以 ALIENTEK ATK-DL6Y2C i.MX6ULL 开发板作为贯穿示例，说明从拿到硬件原理图和芯片手册，到编写 Linux DTS 节点，再到上板验证硬件功能的完整流程。

本文示例参考文件：

- 原理图：`docs/imx6ull/schematics/Schematic.pdf`
- i.MX6ULL 参考手册：`docs/imx6ull/reference-manuals/IMX6ULL参考手册.pdf`
- i.MX6ULL 数据手册：`docs/imx6ull/datasheets/IMX6ULL数据手册(工业级).pdf`、`docs/imx6ull/datasheets/IMX6ULL数据手册(商用级).pdf`
- i.MX6ULL 勘误手册：`docs/imx6ull/errata/IMX6ULL勘误手册.pdf`
- 当前板级 DTS：`linux/linux-7.0/arch/arm/boot/dts/nxp/imx/imx6ull-atk-dl6y2c.dts`
- i.MX6ULL SoC 公共 DTSI：`linux/linux-7.0/arch/arm/boot/dts/nxp/imx/imx6ull.dtsi`
- i.MX6UL SoC 公共 DTSI：`linux/linux-7.0/arch/arm/boot/dts/nxp/imx/imx6ul.dtsi`
- i.MX6UL 引脚复用宏：`linux/linux-7.0/arch/arm/boot/dts/nxp/imx/imx6ul-pinfunc.h`
- i.MX6ULL SNVS 引脚复用宏：`linux/linux-7.0/arch/arm/boot/dts/nxp/imx/imx6ull-pinfunc-snvs.h`
- Linux Devicetree bindings：`linux/linux-7.0/Documentation/devicetree/bindings/`

## 1. DTS 要解决什么问题

DTS 的职责是告诉内核“这块板子的硬件长什么样”。对 i.MX6ULL 这类 SoC 来说，DTS 通常描述以下信息：

- CPU、DDR、SoC 内部控制器的基地址、中断、时钟。这类信息大多已经在 `imx6ul.dtsi` 和 `imx6ull.dtsi` 中描述。
- 板级外设连接关系。例如 UART1 接调试串口，USDHC1 接 MicroSD，FEC1/FEC2 接 PHY，I2C1 接某个 7-bit 地址的外设。
- 引脚复用和电气属性。例如某个 PAD 复用为 I2C1_SCL，是否开漏、是否上拉、驱动强度是多少。
- GPIO 极性。例如复位脚是低有效还是高有效，卡检测脚是否低有效。
- 电源关系。例如 SD 卡供电来自哪个 regulator，PHY 供电是否一直打开。
- 总线子设备。例如 I2C 设备地址、SPI 片选编号、MDIO PHY 地址。

不要把 DTS 理解成“外设驱动代码”。DTS 不实现驱动逻辑，只提供驱动 probe 时需要的硬件描述。

## 2. 三类资料各自提供什么信息

### 2.1 原理图提供板级连接

原理图要重点看这些内容：

- SoC PAD 名称和网络名。例如 `UART4_TXD / I2C1_SCL`、`SNVS_TAMPER7 / ENET1_RST`。
- 外设芯片型号。例如 Ethernet PHY、触摸 IC、音频 Codec、摄像头、CAN 收发器。
- 总线连接。例如 I2C 几号总线、SPI 几号控制器、片选接哪个 GPIO。
- I2C 地址、MDIO PHY 地址、Boot strap 电阻、模式选择电阻。
- 复位脚、中断脚、使能脚、卡检测脚、写保护脚。
- 电源网络。例如 `VCC_3V3`、`SD_3V3`、`VDD_1V8`。
- 外部时钟来源。例如 RMII 50 MHz、Codec MCLK、摄像头 XCLK。
- 是否存在电平转换、上拉电阻、串联电阻、ESD、开漏总线。

原理图中常见后缀含义：

- `_B`、`#`、`N` 通常表示低有效，例如 `RESET_B`、`CD_B`。
- `TXD/RXD` 要结合信号方向看，不要只按名字猜。
- `INT` 通常是外设输出给 SoC 的中断输入。
- `EN`、`PWR_EN` 通常是 SoC 输出给电源或外设的使能脚。
- `VSELECT` 通常用于 SD I/O 电压选择。

### 2.2 芯片参考手册提供 SoC 约束

i.MX6ULL 参考手册重点查：

- IOMUXC 章节：每个 PAD 支持哪些 ALT 复用功能。
- IOMUXC SW_MUX_CTL 寄存器：选择当前 PAD 的 mux mode。
- IOMUXC SW_PAD_CTL 寄存器：设置上拉、下拉、开漏、驱动强度、速度、迟滞、SION。
- 外设章节：UART、I2C、ECSPI、FEC、USDHC、LCDIF、CSI、SAI、ADC、USB、GPMI NAND 等控制器能力。
- CCM 时钟章节：外设时钟来源、可选父时钟、频率限制。
- SNVS 章节：SNVS_TAMPER 这类低功耗域引脚。

### 2.3 Linux bindings 提供 DTS 写法

同一个硬件信息在 DTS 中用什么属性名，不由原理图决定，而由内核 binding 决定。例如：

- 固定电源：`Documentation/devicetree/bindings/regulator/fixed-regulator.yaml`
- MMC/SD/eMMC：`Documentation/devicetree/bindings/mmc/mmc-controller-common.yaml`
- FEC 以太网：`Documentation/devicetree/bindings/net/fsl,fec.yaml`
- Ethernet PHY：`Documentation/devicetree/bindings/net/ethernet-phy.yaml`
- I2C：`Documentation/devicetree/bindings/i2c/i2c-imx.yaml`
- SPI：`Documentation/devicetree/bindings/spi/fsl-imx-cspi.yaml` 和 `spi-controller.yaml`
- FlexCAN：`Documentation/devicetree/bindings/net/can/fsl,flexcan.yaml`
- PWM：`Documentation/devicetree/bindings/pwm/imx-pwm.yaml`
- i.MX pinctrl：`Documentation/devicetree/bindings/pinctrl/fsl,imx-pinctrl.txt`
- Watchdog：`Documentation/devicetree/bindings/watchdog/fsl-imx-wdt.yaml`

写 DTS 前要先看 binding，尤其是新增一个不熟悉的外设时。

## 3. i.MX6ULL DTS 文件分层

当前板级 DTS 文件开头如下：

```dts
/dts-v1/;

#include "imx6ull.dtsi"

/ {
	model = "ALIENTEK ATK-DL6Y2C i.MX6ULL Board";
	compatible = "alientek,imx6ull-atk-dl6y2c", "fsl,imx6ull";
};
```

分层关系：

- `imx6ul.dtsi`：描述 i.MX6UL/ULL 大部分公共 SoC 控制器，例如 `uart1`、`ecspi3`、`fec1`、`usdhc1`、`i2c1`、`lcdif`、`csi`、`usbotg1`。
- `imx6ull.dtsi`：在 `imx6ul.dtsi` 基础上修正 i.MX6ULL 差异，例如 CPU 频率、DCP、RNGB、SNVS IOMUX。
- `imx6ull-atk-dl6y2c.dts`：描述 ATK-DL6Y2C 板级连接，启用板上实际使用的控制器。

公共 dtsi 中大多数外设默认是：

```dts
status = "disabled";
```

板级 DTS 需要按原理图启用：

```dts
&uart1 {
	pinctrl-names = "default";
	pinctrl-0 = <&pinctrl_uart1>;
	status = "okay";
};
```

## 4. 从原理图到 DTS 的标准流程

### 4.1 建立外设清单

拿到原理图后，先做一张表。建议每个外设至少记录：

| 外设 | SoC 控制器 | 网络名 | PAD | 复用功能 | GPIO/中断/复位 | 电源 | 地址/片选 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 调试串口 | UART1 | UART1_TXD/RXD | UART1_TX_DATA/RX_DATA | UART1_DCE_TX/RX | 无 | 3.3V | 无 | 控制台 |
| MCU I2C | I2C1 | I2C1_SCL/SDA | UART4_TX_DATA/RX_DATA | I2C1_SCL/SDA | 无 | 3.3V | 0x10 | 100 kHz |
| MCU SPI | ECSPI3 | ECSPI3_SCLK/MOSI/MISO/SS0 | UART2_* | ECSPI3_* / GPIO CS | GPIO1_IO20 CS | 3.3V | CS0 | 1 MHz |
| MicroSD | USDHC1 | USDHC1_* | SD1_* | USDHC1_* | CD: GPIO1_IO19 | SD_3V3 | 无 | 可插拔 |
| eMMC | USDHC2 | USDHC2_* | NAND_* | USDHC2_* | 无 | 3.3V | 无 | 8-bit |
| ENET1 | FEC1 | ENET1_* | ENET1_* | ENET1_* | RST: GPIO5_IO07 | 3.3V | PHY addr 2 | RMII |
| ENET2 | FEC2 | ENET2_* | ENET2_* / GPIO1_IO06/07 | ENET2_* | RST: GPIO5_IO08 | 3.3V | PHY addr 1 | RMII |
| CAN1 | FlexCAN1 | CAN1_TX/RX | UART3_CTS_B/RTS_B | FLEXCAN1_TX/RX | 收发器 EN 视硬件而定 | 3.3V | 无 | 与 UART3 复用 |

### 4.2 在 SoC DTSI 中找控制器 label

用 `rg` 查公共 DTSI：

```bash
rg -n "uart1:|i2c1:|ecspi3:|fec1:|fec2:|usdhc1:|usdhc2:|can1:|lcdif:|csi:" \
  linux/linux-7.0/arch/arm/boot/dts/nxp/imx/imx6ul.dtsi
```

找到 label 后，板级 DTS 用 `&label` 覆盖或补充属性。

例如 `imx6ul.dtsi` 中已有：

```dts
uart1: serial@2020000 {
	compatible = "fsl,imx6ul-uart", "fsl,imx6q-uart";
	reg = <0x02020000 0x4000>;
	interrupts = <GIC_SPI 26 IRQ_TYPE_LEVEL_HIGH>;
	clocks = <&clks IMX6UL_CLK_UART1_IPG>,
		 <&clks IMX6UL_CLK_UART1_SERIAL>;
	clock-names = "ipg", "per";
	status = "disabled";
};
```

板级 DTS 不需要重复 `reg`、`interrupts`、`clocks`，只需补充板级内容：

```dts
&uart1 {
	pinctrl-names = "default";
	pinctrl-0 = <&pinctrl_uart1>;
	status = "okay";
};
```

### 4.3 根据原理图和参考手册确定 pinmux

步骤：

1. 在原理图找到网络名和 SoC PAD 名。例如 `UART4_TXD` 这颗 PAD 在板上连到 `I2C1_SCL`。
2. 在参考手册 IOMUXC Muxing Options 表中确认该 PAD 是否支持目标功能。
3. 在 `imx6ul-pinfunc.h` 中找对应宏。
4. 在 `&iomuxc` 下新增或复用 pinctrl 组。
5. 在外设节点里引用 `pinctrl-0 = <&pinctrl_xxx>;`。

示例：

```dts
&iomuxc {
	pinctrl_i2c1: i2c1grp {
		fsl,pins = <
			MX6UL_PAD_UART4_TX_DATA__I2C1_SCL	0x4001b8b0
			MX6UL_PAD_UART4_RX_DATA__I2C1_SDA	0x4001b8b0
		>;
	};
};

&i2c1 {
	pinctrl-names = "default";
	pinctrl-0 = <&pinctrl_i2c1>;
	status = "okay";
};
```

### 4.4 设置 pad control

i.MX 的 `fsl,pins` 格式是：

```dts
MX6UL_PAD_xxx__yyy  CONFIG
```

前半部分 `MX6UL_PAD_xxx__yyy` 展开为 5 个整数，包含 mux 寄存器、pad control 寄存器、input select 寄存器、mux mode、input daisy 值。

后半部分 `CONFIG` 是 pad control 配置值，需要查参考手册 IOMUXC `SW_PAD_CTL_PAD_xxx` 寄存器。常见含义包括：

- HYS：输入迟滞。
- PUS：上拉/下拉电阻选择。
- PUE：使用 pull 还是 keeper。
- PKE：使能 pull/keeper。
- ODE：开漏输出，I2C 常用。
- SPEED：速度等级。
- DSE：驱动强度。
- SRE：转换速率。
- SION：Software Input On，常见值中 `0x40000000` 表示强制打开输入路径。

常见经验值：

| 场景 | 常见值 | 说明 |
| --- | --- | --- |
| UART | `0x1b0b1` | 输入输出普通数字信号，带上拉和迟滞 |
| I2C | `0x4001b8b0` | 常用于 SCL/SDA，含 SION/开漏/上拉配置 |
| ENET RMII | `0x1b0b0`、`0x4001b031` | 普通信号和 RMII REF_CLK 分开配置 |
| USDHC 默认 | `0x17059`、CLK 用 `0x10059` | SD/eMMC 低速或默认状态 |
| USDHC 100 MHz | `0x170b9`、CLK 用 `0x100b9` | 高速状态增强驱动 |
| USDHC 200 MHz | `0x170f9`、CLK 用 `0x100f9` | 更高速度状态 |
| GPIO 输出 | `0x1b0b0` | 普通 GPIO |
| PWM 输出 | `0x110b0` | PWM 输出 |
| Watchdog 输出 | `0x30b0` | 外部复位输出 |

这些值不能机械套用。高速接口、长线、外部上拉、负载能力不同，可能需要结合数据手册和示波器波形调整。

### 4.5 描述电源 regulator

板上固定 3.3V 电源可以写成：

```dts
reg_3v3: regulator-3v3 {
	compatible = "regulator-fixed";
	regulator-name = "3v3";
	regulator-min-microvolt = <3300000>;
	regulator-max-microvolt = <3300000>;
	regulator-always-on;
	regulator-boot-on;
};
```

如果电源由 GPIO 控制，例如 SD 卡电源：

```dts
reg_sd1_vmmc: regulator-sd1-vmmc {
	compatible = "regulator-fixed";
	regulator-name = "VSD_3V3";
	regulator-min-microvolt = <3300000>;
	regulator-max-microvolt = <3300000>;
	gpio = <&gpio1 9 GPIO_ACTIVE_HIGH>;
	enable-active-high;
	regulator-boot-on;
};
```

然后由消费者引用：

```dts
&usdhc1 {
	vmmc-supply = <&reg_sd1_vmmc>;
};
```

电源节点应根据原理图确认：

- 电压是多少。
- 是否可关断。
- 使能脚接哪个 GPIO。
- 使能极性是高有效还是低有效。
- 是否需要 `startup-delay-us`。
- 是否必须 `regulator-always-on`。

## 5. 当前 ATK-DL6Y2C 板级 DTS 解析

### 5.1 根节点、兼容字符串、控制台

```dts
/ {
	model = "ALIENTEK ATK-DL6Y2C i.MX6ULL Board";
	compatible = "alientek,imx6ull-atk-dl6y2c", "fsl,imx6ull";

	chosen {
		stdout-path = &uart1;
	};
};
```

说明：

- `model` 是人类可读的板卡名称。
- `compatible` 用于内核匹配板级兼容性，通常从具体板卡到通用 SoC 排列。
- `stdout-path = &uart1` 表示内核早期控制台默认走 UART1。

验证：

```bash
cat /proc/device-tree/model
cat /proc/device-tree/compatible | tr '\0' '\n'
cat /proc/device-tree/chosen/stdout-path
```

### 5.2 DDR 内存

```dts
memory@80000000 {
	device_type = "memory";
	reg = <0x80000000 0x20000000>;
};
```

含义：

- DDR 起始物理地址：`0x80000000`
- DDR 大小：`0x20000000`，即 512 MiB

来源：

- DDR 颗粒容量和位宽来自原理图/BOM。
- i.MX6ULL DDR 地址空间来自芯片手册。
- 实际初始化由 Bootloader 完成，Linux DTS 只描述可用内存范围。

验证：

```bash
cat /proc/meminfo
dmesg | grep -i memory
```

### 5.3 UART1 调试串口

当前 DTS：

```dts
&uart1 {
	pinctrl-names = "default";
	pinctrl-0 = <&pinctrl_uart1>;
	status = "okay";
};

&iomuxc {
	pinctrl_uart1: uart1grp {
		fsl,pins = <
			MX6UL_PAD_UART1_TX_DATA__UART1_DCE_TX	0x1b0b1
			MX6UL_PAD_UART1_RX_DATA__UART1_DCE_RX	0x1b0b1
		>;
	};
};
```

配置流程：

1. 原理图确认 UART1_TXD/RXD 接到调试串口或 USB 转串口芯片。
2. 参考手册确认 `UART1_TX_DATA` 和 `UART1_RX_DATA` PAD 支持 UART1 DCE 功能。
3. `imx6ul-pinfunc.h` 找到对应宏。
4. `&uart1` 设置 `status = "okay"`。
5. 根节点 `chosen` 指向 `&uart1`。

验证：

```bash
dmesg | grep -i ttymxc
ls -l /dev/ttymxc*
cat /proc/tty/driver/IMX-uart
```

常见问题：

- TX/RX 反接：串口无输出或只能收不能发。
- DCE/DTE 模式选错：引脚方向异常。
- 波特率不一致：乱码。
- U-Boot 使用一个 DTB，Linux 使用另一个 DTB：改了 DTS 但启动后不生效。

### 5.4 UART3 MCU 通信

当前 DTS：

```dts
&uart3 {
	pinctrl-names = "default";
	pinctrl-0 = <&pinctrl_uart3>;
	status = "okay";

	pdm_mcu_uart: mcu {
		compatible = "pdm,mcu-uart";
		pdm,id = <0>;
		current-speed = <115200>;
		rx-timeout-ms = <100>;
	};
};
```

要点：

- `uart3` 是 SoC 控制器。
- `mcu` 是挂在串口上的自定义逻辑设备，`compatible = "pdm,mcu-uart"` 需要有对应驱动支持。
- `current-speed = <115200>` 是设备初始通信速率。

如果只是普通串口，不需要子节点：

```dts
&uart3 {
	pinctrl-names = "default";
	pinctrl-0 = <&pinctrl_uart3>;
	status = "okay";
};
```

验证：

```bash
ls -l /dev/ttymxc*
stty -F /dev/ttymxc2 115200
echo test > /dev/ttymxc2
```

注意实际设备号由 probe 顺序和 alias 决定，不要假定 UART3 一定是 `/dev/ttymxc2`。

### 5.5 I2C1

当前 DTS：

```dts
&i2c1 {
	clock-frequency = <100000>;
	pinctrl-names = "default";
	pinctrl-0 = <&pinctrl_i2c1>;
	status = "okay";

	pdm_mcu_i2c: mcu@10 {
		compatible = "pdm,mcu-i2c";
		reg = <0x10>;
		pdm,id = <2>;
		rx-timeout-ms = <100>;
		command-bytes = <1>;
		address-bytes = <1>;
	};
};
```

配置来源：

- 原理图确认 `I2C1_SCL`、`I2C1_SDA` 接到外设，且有上拉电阻。
- 参考手册确认 PAD `UART4_TX_DATA`、`UART4_RX_DATA` 可复用为 I2C1。
- 外设手册或固件约定提供 I2C 地址 `0x10`。

通用 I2C 设备模板：

```dts
&i2c1 {
	clock-frequency = <100000>;
	pinctrl-names = "default";
	pinctrl-0 = <&pinctrl_i2c1>;
	status = "okay";

	device@50 {
		compatible = "vendor,device";
		reg = <0x50>;
	};
};
```

验证：

```bash
i2cdetect -l
i2cdetect -y 0
i2cget -y 0 0x10 0x00
dmesg | grep -i i2c
```

如果 `i2cdetect` 看不到设备：

- 检查总线编号是否正确。
- 检查 7-bit 地址是否写成了 8-bit 地址。DTS 的 `reg` 通常写 7-bit 地址。
- 检查 SCL/SDA 是否有 3.3V 上拉。
- 检查 pinctrl 是否生效。
- 用示波器看 SCL/SDA 是否有波形。
- 检查外设电源和复位。

### 5.6 ECSPI3

当前 DTS：

```dts
&ecspi3 {
	/delete-property/ dmas;
	/delete-property/ dma-names;
	cs-gpios = <&gpio1 20 GPIO_ACTIVE_LOW>;
	pinctrl-names = "default";
	pinctrl-0 = <&pinctrl_ecspi3>;
	status = "okay";

	pdm_mcu_spi: mcu@0 {
		compatible = "pdm,mcu-spi";
		reg = <0>;
		pdm,id = <1>;
		spi-max-frequency = <1000000>;
		rx-timeout-ms = <100>;
		command-bytes = <1>;
		address-bytes = <1>;
	};
};
```

pinmux：

```dts
pinctrl_ecspi3: ecspi3grp {
	fsl,pins = <
		MX6UL_PAD_UART2_RX_DATA__ECSPI3_SCLK	0x10b0
		MX6UL_PAD_UART2_CTS_B__ECSPI3_MOSI	0x10b0
		MX6UL_PAD_UART2_RTS_B__ECSPI3_MISO	0x10b0
		MX6UL_PAD_UART2_TX_DATA__GPIO1_IO20	0x10b0
	>;
};
```

要点：

- `cs-gpios` 表示使用 GPIO1_IO20 作为片选，低有效。
- 子设备 `mcu@0` 的 `reg = <0>` 表示使用 SPI chip select 0。
- `spi-max-frequency` 要由外设手册、板级走线、实测波形共同决定。
- 当前删除 DMA 属性，通常用于规避小包通信或自定义设备上的 DMA 限制，是否保留要根据驱动和测试结果决定。

通用 SPI 设备模板：

```dts
&ecspi3 {
	cs-gpios = <&gpio1 20 GPIO_ACTIVE_LOW>;
	pinctrl-names = "default";
	pinctrl-0 = <&pinctrl_ecspi3>;
	status = "okay";

	spidev@0 {
		compatible = "rohm,dh2228fv";
		reg = <0>;
		spi-max-frequency = <1000000>;
	};
};
```

验证：

```bash
dmesg | grep -i spi
ls -l /dev/spidev*
spidev_test -D /dev/spidevX.Y -s 1000000 -p "abcd"
```

调试重点：

- SCLK 是否输出。
- CS 极性是否正确。
- CPOL/CPHA 是否匹配外设。
- MISO/MOSI 是否接反。
- 多个 SPI 设备时 `reg` 和 `cs-gpios` 顺序是否一致。

### 5.7 FlexCAN1

当前 DTS：

```dts
&can1 {
	pinctrl-names = "default";
	pinctrl-0 = <&pinctrl_flexcan1>;
	status = "okay";
};

pinctrl_flexcan1: flexcan1grp {
	fsl,pins = <
		MX6UL_PAD_UART3_CTS_B__FLEXCAN1_TX	0x1b020
		MX6UL_PAD_UART3_RTS_B__FLEXCAN1_RX	0x1b020
	>;
};
```

配置流程：

1. 原理图确认 CAN TX/RX 接到 CAN 收发器，而不是直接接总线。
2. 查收发器电源和 STB/EN/SILENT 引脚。
3. 如果收发器电源可控，增加 `xceiver-supply`。
4. 如果 STB/EN 接 GPIO，按驱动 binding 或 gpio-hog 配置。

带收发器电源的示例：

```dts
reg_can_3v3: regulator-can-3v3 {
	compatible = "regulator-fixed";
	regulator-name = "can-3v3";
	regulator-min-microvolt = <3300000>;
	regulator-max-microvolt = <3300000>;
	regulator-always-on;
};

&can1 {
	pinctrl-names = "default";
	pinctrl-0 = <&pinctrl_flexcan1>;
	xceiver-supply = <&reg_can_3v3>;
	status = "okay";
};
```

验证：

```bash
ip link set can0 down
ip link set can0 type can bitrate 500000
ip link set can0 up
ip -details link show can0
candump can0
cansend can0 123#11223344
```

常见问题：

- CAN TX/RX 和 UART3 复用冲突。
- 收发器待机脚未拉到正常工作状态。
- 终端电阻缺失或重复。
- 位率与对端不一致。
- CANH/CANL 反接。

### 5.8 FEC 以太网和 PHY

当前 DTS：

```dts
&fec1 {
	pinctrl-names = "default";
	pinctrl-0 = <&pinctrl_enet1>;
	phy-mode = "rmii";
	phy-handle = <&ethphy0>;
	phy-supply = <&reg_3v3>;
	status = "okay";
};

&fec2 {
	pinctrl-names = "default";
	pinctrl-0 = <&pinctrl_enet2>;
	phy-mode = "rmii";
	phy-handle = <&ethphy1>;
	phy-supply = <&reg_3v3>;
	status = "okay";

	mdio {
		#address-cells = <1>;
		#size-cells = <0>;

		ethphy0: ethernet-phy@2 {
			compatible = "ethernet-phy-id0022.1560";
			reg = <2>;
			pinctrl-names = "default";
			pinctrl-0 = <&pinctrl_enet1_rst>;
			reset-gpios = <&gpio5 7 GPIO_ACTIVE_LOW>;
			reset-assert-us = <10000>;
			reset-deassert-us = <30000>;
			micrel,led-mode = <1>;
			clocks = <&clks IMX6UL_CLK_ENET_REF>;
			clock-names = "rmii-ref";
		};

		ethphy1: ethernet-phy@1 {
			compatible = "ethernet-phy-id0022.1560";
			reg = <1>;
			pinctrl-names = "default";
			pinctrl-0 = <&pinctrl_enet2_rst>;
			reset-gpios = <&gpio5 8 GPIO_ACTIVE_LOW>;
			reset-assert-us = <10000>;
			reset-deassert-us = <30000>;
			micrel,led-mode = <1>;
			clocks = <&clks IMX6UL_CLK_ENET2_REF>;
			clock-names = "rmii-ref";
		};
	};
};
```

关键点：

- `phy-mode = "rmii"` 来自原理图和 PHY 连接方式。
- `reg = <2>`、`reg = <1>` 是 PHY 的 MDIO 地址，来自 PHY strap 电阻。
- 当前两个 PHY 都挂在 `fec2` 的 MDIO 节点下，`fec1` 通过 `phy-handle = <&ethphy0>` 引用。
- `reset-gpios` 极性要由原理图复位网络确认。
- RMII 需要 50 MHz 参考时钟，时钟来源可能是 SoC 输出，也可能是外部晶振/PHY 输出，必须按硬件设计配置。

验证：

```bash
dmesg | grep -Ei "fec|phy|mdio|eth"
ip link
ethtool eth0
ethtool eth1
udhcpc -i eth0
ping -I eth0 192.168.1.1
```

PHY 地址调试：

```bash
for a in $(seq 0 31); do
  phytool read eth0/$a/2 2>/dev/null && echo "phy addr $a exists"
done
```

常见问题：

- MDIO/MDC 没有复用正确，导致找不到 PHY。
- PHY 地址写错，驱动 probe 不到 PHY。
- 复位释放时间太短，PHY strap 采样失败。
- RMII REF_CLK 没有 50 MHz 或方向不对。
- `phy-mode` 写成 `mii`、`rgmii` 等错误模式。
- PHY 电源未开启。

### 5.9 USDHC1 MicroSD

当前 DTS：

```dts
&usdhc1 {
	pinctrl-names = "default", "state_100mhz", "state_200mhz";
	pinctrl-0 = <&pinctrl_usdhc1>;
	pinctrl-1 = <&pinctrl_usdhc1_100mhz>;
	pinctrl-2 = <&pinctrl_usdhc1_200mhz>;
	cd-gpios = <&gpio1 19 GPIO_ACTIVE_LOW>;
	keep-power-in-suspend;
	wakeup-source;
	vmmc-supply = <&reg_sd1_vmmc>;
	status = "okay";
};
```

pinmux 中包含：

```dts
MX6UL_PAD_SD1_CMD__USDHC1_CMD
MX6UL_PAD_SD1_CLK__USDHC1_CLK
MX6UL_PAD_SD1_DATA0__USDHC1_DATA0
MX6UL_PAD_SD1_DATA1__USDHC1_DATA1
MX6UL_PAD_SD1_DATA2__USDHC1_DATA2
MX6UL_PAD_SD1_DATA3__USDHC1_DATA3
MX6UL_PAD_UART1_RTS_B__GPIO1_IO19
MX6UL_PAD_GPIO1_IO05__USDHC1_VSELECT
MX6UL_PAD_GPIO1_IO09__GPIO1_IO09
```

配置来源：

- 原理图 `TF_CARD` 连接 `USDHC1_DATA0..3`、`CMD`、`CLK`。
- `USDHC1_CD_B` 接 GPIO1_IO19，所以写 `cd-gpios = <&gpio1 19 GPIO_ACTIVE_LOW>`。
- SD 卡电源 `SD_3V3` 由 `reg_sd1_vmmc` 描述。
- 4-bit 数据线由 `imx6ul.dtsi` 默认 `bus-width = <4>`，板级可不重复写。

验证：

```bash
dmesg | grep -Ei "mmc|sdhci|usdhc"
lsblk
cat /sys/kernel/debug/mmc*/ios
mount /dev/mmcblkXp1 /mnt
dd if=/dev/mmcblkX of=/dev/null bs=1M count=64
```

常见问题：

- `cd-gpios` 极性反了，插卡显示拔出，拔卡显示插入。
- SD 电源使能 GPIO 极性错。
- CLK/CMD/DATA 上拉缺失。
- 高速模式不稳定，需要降低频率或调整 pad control。
- `no-1-8-v`、`vqmmc-supply` 与硬件电压切换能力不一致。

### 5.10 USDHC2 eMMC

当前 DTS：

```dts
&usdhc2 {
	pinctrl-names = "default", "state_100mhz", "state_200mhz";
	pinctrl-0 = <&pinctrl_usdhc2>;
	pinctrl-1 = <&pinctrl_usdhc2_100mhz>;
	pinctrl-2 = <&pinctrl_usdhc2_200mhz>;
	bus-width = <8>;
	non-removable;
	no-1-8-v;
	keep-power-in-suspend;
	vmmc-supply = <&reg_3v3>;
	status = "okay";
};
```

要点：

- `bus-width = <8>` 来自 eMMC 8 根数据线连接。
- `non-removable` 表示板载不可拔出设备。
- `no-1-8-v` 表示当前硬件不支持 1.8V 信号电压切换，具体要按原理图确认。
- 当前使用 `NAND_RE_B`、`NAND_WE_B`、`NAND_DATA00..07` 复用为 USDHC2，因此和 NAND 功能互斥。

验证：

```bash
dmesg | grep -Ei "mmc1|mmcblk|usdhc"
lsblk
cat /sys/kernel/debug/mmc*/ios
mmc extcsd read /dev/mmcblkX
```

常见问题：

- 8-bit/4-bit 配置与硬件不一致。
- eMMC 复位脚未配置或电源时序不满足。
- 与 GPMI NAND/QSPI 复用冲突。
- 高速模式不稳定，需先限制频率定位。

### 5.11 GPIO LED 和 PWM LED

当前 DTS 中的自定义 PDM LED：

```dts
pdm_led_gpio: led@0 {
	compatible = "pdm,led-gpio";
	reg = <0>;
	led-gpios = <&gpio1 3 GPIO_ACTIVE_LOW>;
	max-brightness = <1>;
	default-state = "off";
};

pdm_led_pwm: led@1 {
	compatible = "pdm,led-pwm";
	reg = <1>;
	pwms = <&pwm1 0 5000000 0>;
	max-brightness = <255>;
	default-state = "off";
};
```

如果使用 Linux 通用 LED 子系统，可以写成：

```dts
leds {
	compatible = "gpio-leds";

	user-led {
		label = "user";
		gpios = <&gpio1 3 GPIO_ACTIVE_LOW>;
		default-state = "off";
	};
};
```

PWM 背光示例：

```dts
backlight_display: backlight-display {
	compatible = "pwm-backlight";
	pwms = <&pwm1 0 5000000 0>;
	brightness-levels = <0 4 8 16 32 64 128 255>;
	default-brightness-level = <6>;
	status = "okay";
};

&pwm1 {
	pinctrl-names = "default";
	pinctrl-0 = <&pinctrl_pwm1>;
	status = "okay";
};
```

验证：

```bash
ls /sys/class/leds
echo 1 > /sys/class/leds/user/brightness
echo 0 > /sys/class/leds/user/brightness

ls /sys/class/pwm
```

### 5.12 Watchdog 外部复位

当前 DTS：

```dts
&wdog1 {
	pinctrl-names = "default";
	pinctrl-0 = <&pinctrl_wdog>;
	fsl,ext-reset-output;
};

pinctrl_wdog: wdoggrp {
	fsl,pins = <
		MX6UL_PAD_LCD_RESET__WDOG1_WDOG_ANY	0x30b0
	>;
};
```

要点：

- `fsl,ext-reset-output` 表示 watchdog 触发时输出外部复位信号。
- 必须确认原理图中 `LCD_RESET` 这个 PAD 连接到了系统复位链路或预期复位对象。

验证：

```bash
dmesg | grep -i watchdog
ls /dev/watchdog*
```

触发 watchdog 会导致系统复位，测试前要确认文件系统和业务状态。

## 6. 常见扩展外设配置示例

以下示例基于 i.MX6ULL 常见开发板设计和 NXP EVK 写法。用于新板或扩展功能时，必须按自己的原理图替换 PAD、GPIO、电源、地址和时钟。

### 6.1 USB OTG 和 USB Host

SoC 公共 DTSI 已有 `usbotg1`、`usbotg2`、`usbphy1`、`usbphy2`。

OTG 示例：

```dts
&usbotg1 {
	dr_mode = "otg";
	pinctrl-names = "default";
	pinctrl-0 = <&pinctrl_usb_otg1>;
	status = "okay";
};

&iomuxc {
	pinctrl_usb_otg1: usbotg1grp {
		fsl,pins = <
			MX6UL_PAD_GPIO1_IO00__ANATOP_OTG1_ID	0x17059
		>;
	};
};
```

Host 示例：

```dts
&usbotg2 {
	dr_mode = "host";
	disable-over-current;
	status = "okay";
};
```

如果 VBUS 由 GPIO 控制，应增加 regulator：

```dts
reg_usb_otg_vbus: regulator-usb-otg-vbus {
	compatible = "regulator-fixed";
	regulator-name = "usb_otg_vbus";
	regulator-min-microvolt = <5000000>;
	regulator-max-microvolt = <5000000>;
	gpio = <&gpio1 4 GPIO_ACTIVE_HIGH>;
	enable-active-high;
};

&usbotg1 {
	vbus-supply = <&reg_usb_otg_vbus>;
	status = "okay";
};
```

验证：

```bash
dmesg | grep -Ei "usb|ci_hdrc|ehci|otg"
lsusb
cat /sys/kernel/debug/usb/devices
```

### 6.2 LCDIF RGB 屏

RGB 并口屏一般需要：

- LCDIF 数据线 `LCD_DATA00..23`
- `LCD_CLK`、`LCD_ENABLE`、`LCD_HSYNC`、`LCD_VSYNC`
- 背光 PWM
- 屏供电
- 可选 reset GPIO
- panel timing 或 compatible panel 驱动

示例：

```dts
backlight_display: backlight-display {
	compatible = "pwm-backlight";
	pwms = <&pwm1 0 5000000 0>;
	brightness-levels = <0 4 8 16 32 64 128 255>;
	default-brightness-level = <6>;
	status = "okay";
};

panel {
	compatible = "innolux,at043tn24";
	backlight = <&backlight_display>;
	power-supply = <&reg_3v3>;

	port {
		panel_in: endpoint {
			remote-endpoint = <&display_out>;
		};
	};
};

&lcdif {
	assigned-clocks = <&clks IMX6UL_CLK_LCDIF_PRE_SEL>;
	assigned-clock-parents = <&clks IMX6UL_CLK_PLL5_VIDEO_DIV>;
	pinctrl-names = "default";
	pinctrl-0 = <&pinctrl_lcdif_dat &pinctrl_lcdif_ctrl>;
	status = "okay";

	port {
		display_out: endpoint {
			remote-endpoint = <&panel_in>;
		};
	};
};
```

pinmux 示例：

```dts
pinctrl_lcdif_dat: lcdifdatgrp {
	fsl,pins = <
		MX6UL_PAD_LCD_DATA00__LCDIF_DATA00 0x79
		MX6UL_PAD_LCD_DATA01__LCDIF_DATA01 0x79
		MX6UL_PAD_LCD_DATA02__LCDIF_DATA02 0x79
		MX6UL_PAD_LCD_DATA03__LCDIF_DATA03 0x79
		MX6UL_PAD_LCD_DATA04__LCDIF_DATA04 0x79
		MX6UL_PAD_LCD_DATA05__LCDIF_DATA05 0x79
		MX6UL_PAD_LCD_DATA06__LCDIF_DATA06 0x79
		MX6UL_PAD_LCD_DATA07__LCDIF_DATA07 0x79
		MX6UL_PAD_LCD_DATA08__LCDIF_DATA08 0x79
		MX6UL_PAD_LCD_DATA09__LCDIF_DATA09 0x79
		MX6UL_PAD_LCD_DATA10__LCDIF_DATA10 0x79
		MX6UL_PAD_LCD_DATA11__LCDIF_DATA11 0x79
		MX6UL_PAD_LCD_DATA12__LCDIF_DATA12 0x79
		MX6UL_PAD_LCD_DATA13__LCDIF_DATA13 0x79
		MX6UL_PAD_LCD_DATA14__LCDIF_DATA14 0x79
		MX6UL_PAD_LCD_DATA15__LCDIF_DATA15 0x79
		MX6UL_PAD_LCD_DATA16__LCDIF_DATA16 0x79
		MX6UL_PAD_LCD_DATA17__LCDIF_DATA17 0x79
		MX6UL_PAD_LCD_DATA18__LCDIF_DATA18 0x79
		MX6UL_PAD_LCD_DATA19__LCDIF_DATA19 0x79
		MX6UL_PAD_LCD_DATA20__LCDIF_DATA20 0x79
		MX6UL_PAD_LCD_DATA21__LCDIF_DATA21 0x79
		MX6UL_PAD_LCD_DATA22__LCDIF_DATA22 0x79
		MX6UL_PAD_LCD_DATA23__LCDIF_DATA23 0x79
	>;
};

pinctrl_lcdif_ctrl: lcdifctrlgrp {
	fsl,pins = <
		MX6UL_PAD_LCD_CLK__LCDIF_CLK	    0x79
		MX6UL_PAD_LCD_ENABLE__LCDIF_ENABLE 0x79
		MX6UL_PAD_LCD_HSYNC__LCDIF_HSYNC   0x79
		MX6UL_PAD_LCD_VSYNC__LCDIF_VSYNC   0x79
	>;
};
```

验证：

```bash
dmesg | grep -Ei "lcd|drm|fb|panel|backlight"
ls /dev/fb*
cat /sys/class/graphics/fb0/modes
echo 6 > /sys/class/backlight/*/brightness
fb-test
```

常见问题：

- RGB 数据位顺序和 panel 数据格式不一致。
- pixel clock 配错导致花屏、偏色、滚动。
- DE/HSYNC/VSYNC 极性错误。
- 背光亮但无图像，多数是 LCDIF timing 或数据线问题。

### 6.3 CSI 并口摄像头

以 OV5640 为例：

```dts
&i2c2 {
	clock-frequency = <100000>;
	pinctrl-names = "default";
	pinctrl-0 = <&pinctrl_i2c2>;
	status = "okay";

	camera@3c {
		compatible = "ovti,ov5640";
		reg = <0x3c>;
		pinctrl-names = "default";
		pinctrl-0 = <&pinctrl_camera_clock>;
		clocks = <&clks IMX6UL_CLK_CSI>;
		clock-names = "xclk";
		powerdown-gpios = <&gpio1 5 GPIO_ACTIVE_HIGH>;
		reset-gpios = <&gpio1 6 GPIO_ACTIVE_LOW>;
		AVDD-supply = <&reg_2v8>;
		DVDD-supply = <&reg_1v5>;
		DOVDD-supply = <&reg_1v8>;

		port {
			ov5640_to_parallel: endpoint {
				remote-endpoint = <&parallel_from_ov5640>;
				bus-width = <8>;
				data-shift = <2>;
				hsync-active = <0>;
				vsync-active = <0>;
				pclk-sample = <1>;
			};
		};
	};
};

&csi {
	pinctrl-names = "default";
	pinctrl-0 = <&pinctrl_csi1>;
	status = "okay";

	port {
		parallel_from_ov5640: endpoint {
			remote-endpoint = <&ov5640_to_parallel>;
			bus-type = <MEDIA_BUS_TYPE_PARALLEL>;
		};
	};
};
```

需要在 DTS 顶部包含：

```dts
#include <dt-bindings/media/video-interfaces.h>
```

验证：

```bash
dmesg | grep -Ei "csi|ov5640|video"
media-ctl -p
v4l2-ctl --list-devices
v4l2-ctl -d /dev/video0 --all
v4l2-ctl -d /dev/video0 --stream-mmap --stream-count=100
```

常见问题：

- 摄像头 I2C 地址不对。
- XCLK 没输出或频率不对。
- PWDN/RESET 极性反。
- PCLK/HSYNC/VSYNC 极性不匹配。
- 数据线位宽和 `data-shift` 配错。

### 6.4 电阻触摸 TSC

i.MX6ULL 内部有 TSC/ADC 触摸控制器。示例：

```dts
&tsc {
	pinctrl-names = "default";
	pinctrl-0 = <&pinctrl_tsc>;
	xnur-gpios = <&gpio1 3 GPIO_ACTIVE_LOW>;
	measure-delay-time = <0xffff>;
	pre-charge-time = <0xfff>;
	status = "okay";
};

&iomuxc {
	pinctrl_tsc: tscgrp {
		fsl,pins = <
			MX6UL_PAD_GPIO1_IO01__GPIO1_IO01	0xb0
			MX6UL_PAD_GPIO1_IO02__GPIO1_IO02	0xb0
			MX6UL_PAD_GPIO1_IO03__GPIO1_IO03	0xb0
			MX6UL_PAD_GPIO1_IO04__GPIO1_IO04	0xb0
		>;
	};
};
```

验证：

```bash
dmesg | grep -Ei "touch|tsc|input"
cat /proc/bus/input/devices
evtest
```

### 6.5 SAI2 + WM8960 音频

典型组成：

- SAI2 作为 I2S 控制器。
- WM8960 通过 I2C 配置寄存器。
- SAI2_MCLK 给 Codec 提供主时钟。
- Codec 多路电源 AVDD/DBVDD/DCVDD/SPKVDD。
- 耳机检测、喇叭、MIC 路由。

示例：

```dts
sound-wm8960 {
	compatible = "fsl,imx-audio-wm8960";
	model = "wm8960-audio";
	audio-cpu = <&sai2>;
	audio-codec = <&codec>;
	audio-asrc = <&asrc>;
	hp-det-gpios = <&gpio5 4 GPIO_ACTIVE_HIGH>;
	audio-routing =
		"Headphone Jack", "HP_L",
		"Headphone Jack", "HP_R",
		"Ext Spk", "SPK_LP",
		"Ext Spk", "SPK_LN",
		"Mic Jack", "MICB";
};

&i2c2 {
	status = "okay";

	codec: wm8960@1a {
		#sound-dai-cells = <0>;
		compatible = "wlf,wm8960";
		reg = <0x1a>;
		clocks = <&clks IMX6UL_CLK_SAI2>;
		clock-names = "mclk";
		AVDD-supply = <&reg_audio_3v3>;
		DBVDD-supply = <&reg_audio_1v8>;
		DCVDD-supply = <&reg_audio_1v8>;
		SPKVDD1-supply = <&reg_audio_5v>;
		SPKVDD2-supply = <&reg_audio_5v>;
	};
};

&sai2 {
	pinctrl-names = "default";
	pinctrl-0 = <&pinctrl_sai2>;
	assigned-clocks = <&clks IMX6UL_CLK_SAI2_SEL>,
			  <&clks IMX6UL_CLK_SAI2>;
	assigned-clock-parents = <&clks IMX6UL_CLK_PLL4_AUDIO_DIV>;
	assigned-clock-rates = <0>, <12288000>;
	fsl,sai-mclk-direction-output;
	status = "okay";
};
```

验证：

```bash
dmesg | grep -Ei "sai|wm8960|asoc|sound"
aplay -l
arecord -l
amixer
speaker-test -D hw:0,0 -c 2
arecord -D hw:0,0 -f S16_LE -r 48000 test.wav
```

### 6.6 ADC

SoC 公共 DTSI 中有 `adc1`，如果板上把某个模拟输入引出，可启用：

```dts
&adc1 {
	status = "okay";
};
```

验证：

```bash
dmesg | grep -i adc
ls /sys/bus/iio/devices/
cat /sys/bus/iio/devices/iio:deviceX/in_voltage*_raw
```

注意：

- ADC 输入电压范围必须符合数据手册。
- 模拟输入不能直接接超过 SoC 允许范围的电压。
- 需要确认引脚没有被复用为其他数字功能。

### 6.7 QSPI NOR Flash

示例：

```dts
&qspi {
	pinctrl-names = "default";
	pinctrl-0 = <&pinctrl_qspi>;
	status = "okay";

	flash0: flash@0 {
		#address-cells = <1>;
		#size-cells = <1>;
		compatible = "jedec,spi-nor";
		spi-max-frequency = <29000000>;
		spi-rx-bus-width = <4>;
		spi-tx-bus-width = <1>;
		reg = <0>;
	};
};
```

验证：

```bash
dmesg | grep -Ei "spi-nor|qspi|mtd"
cat /proc/mtd
flash_erase /dev/mtdX 0 1
```

注意 QSPI、NAND、USDHC2 可能共享 NAND 区域 PAD，必须检查复用冲突。

### 6.8 GPMI NAND

如果板子使用 NAND，而不是 eMMC，需要启用 `gpmi`，并关闭占用相同 PAD 的 USDHC2。

示例框架：

```dts
&gpmi {
	pinctrl-names = "default";
	pinctrl-0 = <&pinctrl_gpmi_nand>;
	nand-on-flash-bbt;
	status = "okay";

	nand@0 {
		reg = <0>;
		nand-ecc-mode = "hw";
		nand-ecc-strength = <8>;
		nand-ecc-step-size = <512>;
	};
};

&usdhc2 {
	status = "disabled";
};
```

验证：

```bash
dmesg | grep -Ei "gpmi|nand|bch|mtd"
cat /proc/mtd
nanddump --bb=skipbad /dev/mtdX | head
```

### 6.9 GPIO Keys

按键通常由 GPIO 输入和中断组成：

```dts
gpio-keys {
	compatible = "gpio-keys";
	pinctrl-names = "default";
	pinctrl-0 = <&pinctrl_keys>;

	key-user {
		label = "user-key";
		gpios = <&gpio1 18 GPIO_ACTIVE_LOW>;
		linux,code = <KEY_ENTER>;
		wakeup-source;
		debounce-interval = <10>;
	};
};
```

需要包含：

```dts
#include <dt-bindings/input/input.h>
```

验证：

```bash
cat /proc/bus/input/devices
evtest
```

### 6.10 RS485

如果某个 UART 连接 RS485 收发器，除了 TX/RX，还要确认 DE/RE 方向控制脚。

示例：

```dts
&uart3 {
	pinctrl-names = "default";
	pinctrl-0 = <&pinctrl_uart3 &pinctrl_uart3_rs485>;
	linux,rs485-enabled-at-boot-time;
	rs485-rts-active-high;
	rts-gpios = <&gpio1 10 GPIO_ACTIVE_HIGH>;
	status = "okay";
};
```

实际属性需要按当前内核串口驱动支持情况确认。若驱动不支持 GPIO RTS，需要在应用或驱动中控制 DE。

## 7. 编译 DTS

常见内核编译方式：

```bash
cd linux/linux-7.0
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- imx_v6_v7_defconfig
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- dtbs
```

只编译某个 DTB：

```bash
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- \
  imx6ull-atk-dl6y2c.dtb
```

不同内核版本的目标路径可能不同。若不确定，先查 Makefile：

```bash
rg -n "imx6ull-atk-dl6y2c" arch/arm/boot/dts
```

如果新增 DTS 文件，需要把 DTB 加入对应目录的 Makefile，否则 `make dtbs` 不会自动构建。

## 8. 部署 DTB

常见方式：

1. 拷贝 DTB 到 boot 分区。
2. U-Boot 环境变量指定 `fdtfile` 或加载路径。
3. 确认启动日志中使用的是新 DTB。

U-Boot 中常见命令：

```bash
printenv fdtfile
printenv bootcmd
printenv mmcdev
ext4ls mmc 0:1 /boot
fatls mmc 0:1
```

Linux 启动后确认：

```bash
cat /proc/device-tree/model
hexdump -C /sys/firmware/fdt | head
```

如果改 DTS 后没有任何变化，优先检查：

- 是否编译了正确源码树。
- 是否部署了正确 DTB。
- U-Boot 是否加载了另一个路径的 DTB。
- Boot 分区是否挂载到了预期设备。
- FIT image 是否内嵌了旧 DTB。

## 9. 通用上板验证流程

### 9.1 启动早期验证

```bash
dmesg -n 8
dmesg | grep -Ei "OF:|Machine model|pinctrl|regulator|clk|deferred"
cat /proc/device-tree/model
```

重点看：

- 是否有 `deferred probe`。
- 是否有 regulator 找不到。
- 是否有 pinctrl 申请失败。
- 是否有时钟错误。
- 是否有驱动 probe 失败。

### 9.2 pinctrl 验证

挂载 debugfs：

```bash
mount -t debugfs none /sys/kernel/debug
```

查看 pinctrl：

```bash
ls /sys/kernel/debug/pinctrl
cat /sys/kernel/debug/pinctrl/*/pinmux-pins
cat /sys/kernel/debug/pinctrl/*/pinconf-pins
```

检查目标 PAD 是否被目标外设占用，是否被别的外设抢占。

### 9.3 GPIO 验证

新内核优先使用 libgpiod：

```bash
gpioinfo
gpioget gpiochip0 3
gpioset gpiochip0 3=1
```

老系统可能使用 sysfs GPIO：

```bash
echo 3 > /sys/class/gpio/export
echo out > /sys/class/gpio/gpio3/direction
echo 1 > /sys/class/gpio/gpio3/value
```

i.MX GPIO 编号换算：

- GPIO1_IO03 通常是全局 GPIO 3。
- GPIO2_IO00 通常是全局 GPIO 32。
- GPIO3_IO00 通常是全局 GPIO 64。
- GPIO4_IO00 通常是全局 GPIO 96。
- GPIO5_IO00 通常是全局 GPIO 128。

但实际用户空间应优先通过 gpiochip/line name 操作，不建议硬编码全局 GPIO 编号。

### 9.4 电源验证

```bash
ls /sys/class/regulator
for r in /sys/class/regulator/regulator.*; do
  echo "$r"
  cat "$r/name" 2>/dev/null
  cat "$r/state" 2>/dev/null
  cat "$r/microvolts" 2>/dev/null
done
```

如果外设 probe 失败，先确认对应电源是否开启。

### 9.5 时钟验证

如果内核启用了 common clock debug：

```bash
cat /sys/kernel/debug/clk/clk_summary
```

检查：

- UART/I2C/SPI/FEC/USDHC 时钟是否 enabled。
- LCD pixel clock 是否接近期望值。
- SAI MCLK 是否为 Codec 需要的频率。
- RMII REF_CLK 是否为 50 MHz。

## 10. 各类外设验证命令速查

| 外设 | 命令 |
| --- | --- |
| UART | `dmesg | grep -i ttymxc`、`stty -F /dev/ttymxcX` |
| I2C | `i2cdetect -l`、`i2cdetect -y X` |
| SPI | `dmesg | grep -i spi`、`spidev_test -D /dev/spidevX.Y` |
| CAN | `ip link set can0 type can bitrate 500000`、`candump can0` |
| Ethernet | `ip link`、`ethtool eth0`、`ping -I eth0` |
| SD/eMMC | `dmesg | grep -i mmc`、`lsblk`、`cat /sys/kernel/debug/mmc*/ios` |
| USB | `dmesg | grep -i usb`、`lsusb` |
| LCD | `dmesg | grep -Ei "lcd|drm|fb"`、`fb-test` |
| Touch | `cat /proc/bus/input/devices`、`evtest` |
| Camera | `media-ctl -p`、`v4l2-ctl --list-devices` |
| Audio | `aplay -l`、`amixer`、`speaker-test` |
| ADC | `ls /sys/bus/iio/devices`、`cat in_voltage*_raw` |
| GPIO | `gpioinfo`、`gpioget`、`gpioset` |
| Regulator | `ls /sys/class/regulator` |
| Clock | `cat /sys/kernel/debug/clk/clk_summary` |
| Pinctrl | `cat /sys/kernel/debug/pinctrl/*/pinmux-pins` |

## 11. 常见错误和定位方法

### 11.1 节点启用了但驱动没有 probe

检查：

```bash
dmesg | grep -i "compatible"
dmesg | grep -i "probe"
find /sys/bus/platform/devices -maxdepth 1 -type l | grep 21a0000
```

可能原因：

- `compatible` 没有对应驱动。
- 驱动未编进内核或模块未加载。
- 依赖 regulator、clock、GPIO、pinctrl 未就绪。
- 节点路径或 `status` 写错。

### 11.2 pinctrl 报错

常见原因：

- `MX6UL_PAD_xxx__yyy` 宏写错。
- 使用了 i.MX6ULL 没有的 PAD。
- 同一个 PAD 被多个外设同时占用。
- `&iomuxc` 和 `&iomuxc_snvs` 混淆。

SNVS_TAMPER 引脚在 i.MX6ULL 上可能属于 SNVS IOMUX 域，具体写法要按现有 dtsi 和 pinfunc 文件确认。

### 11.3 GPIO 极性反

现象：

- LED 默认亮灭相反。
- 复位脚一直保持复位。
- SD 卡检测反向。
- 电源 regulator 打不开。

定位：

```bash
gpioinfo
gpioget gpiochipX Y
gpioset gpiochipX Y=0
gpioset gpiochipX Y=1
```

再结合万用表或示波器测实际引脚电平。

### 11.4 I2C 地址错误

很多芯片手册会同时给 8-bit 写地址和 7-bit 地址。例如写地址 `0xA0` 对应 DTS 中 `reg = <0x50>`。Linux DTS 一般写 7-bit 地址。

### 11.5 复用冲突

i.MX6ULL PAD 复用资源有限，例如：

- `UART3_CTS_B/RTS_B` 可用于 CAN1，也可能用于 UART。
- NAND 区域 PAD 可用于 NAND、USDHC2、QSPI 等。
- LCD DATA PAD 可能复用为 CSI、UART、GPIO 等。
- GPIO1_IO08 可作为 PWM1，也可能作为其他功能。

处理方法：

```bash
rg -n "MX6UL_PAD_UART3_CTS_B|MX6UL_PAD_NAND_RE_B|MX6UL_PAD_GPIO1_IO08" \
  linux/linux-7.0/arch/arm/boot/dts/nxp/imx
```

一个 PAD 只能选择一种实际功能。

### 11.6 DTB 没更新

定位顺序：

```bash
strings arch/arm/boot/dts/nxp/imx/imx6ull-atk-dl6y2c.dtb | grep -i ALIENTEK
cat /proc/device-tree/model
printenv fdtfile
```

如果 `/proc/device-tree` 中看不到新增节点，说明运行中的 DTB 不是你刚编译的那个。

## 12. 新增或修改外设时的检查清单

提交前逐项确认：

- 已从原理图确认 SoC PAD、网络名、外设型号、地址、复位、中断、电源。
- 已从参考手册确认 PAD 支持目标 ALT 复用。
- 已从 `imx6ul-pinfunc.h` 或 `imx6ull-pinfunc-snvs.h` 找到正确宏。
- 已确认 pad control 适合该接口电气特性。
- 已查对应 Linux binding。
- 已配置所有必要 regulator。
- 已配置所有必要 reset GPIO、interrupt GPIO、enable GPIO。
- 已确认 GPIO 极性。
- 已确认 I2C/SPI/MDIO 地址。
- 已确认没有引脚复用冲突。
- 已确认 `status = "okay"` 只打开真实存在的硬件。
- 已编译 DTB，无 dtc 语法错误。
- 已部署正确 DTB。
- 已查看 `dmesg`，无明显 probe 失败。
- 已完成对应外设的基本读写或功能验证。

## 13. 推荐的 DTS 编写顺序

1. 先只启用串口控制台，保证启动日志可靠。
2. 配置基础电源 regulator。
3. 配置存储启动介质，例如 MicroSD 或 eMMC。
4. 配置以太网，方便远程调试和传文件。
5. 配置 I2C/SPI 总线，并逐个挂载子设备。
6. 配置 GPIO、按键、LED、PWM 这类简单外设。
7. 配置 CAN、USB。
8. 配置 LCD、触摸、摄像头、音频这类多节点图结构外设。
9. 每新增一个外设就单独验证，不要一次打开大量节点。

## 14. 当前板卡已配置外设总览

当前 `imx6ull-atk-dl6y2c.dts` 已覆盖：

- DDR：512 MiB，起始地址 `0x80000000`
- UART1：控制台
- UART3：PDM MCU UART 通信
- I2C1：PDM MCU I2C 通信，地址 `0x10`
- ECSPI3：PDM MCU SPI 通信，GPIO1_IO20 片选
- FlexCAN1：CAN0 alias
- FEC1/FEC2：双 RMII 以太网，PHY 地址分别为 2 和 1
- USDHC1：MicroSD，GPIO1_IO19 卡检测，GPIO1_IO09 电源控制
- USDHC2：8-bit eMMC，使用 NAND 区域 PAD 复用
- PWM1：PWM LED 或背光类输出
- GPIO1_IO03：GPIO LED
- WDOG1：外部复位输出
- SNVS poweroff

后续如果要增加 LCD、USB、摄像头、音频、触摸、ADC、GPIO key 等，应按本文扩展示例结合实际原理图补充。

## 15. 最小调试闭环

每次改 DTS 建议形成这个闭环：

```bash
# 1. 编译
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- dtbs

# 2. 部署 DTB
# 按当前板卡启动介质复制到 boot 分区或 FIT image

# 3. 启动后确认 DTB
cat /proc/device-tree/model

# 4. 查 probe
dmesg | grep -Ei "error|fail|deferred|pinctrl|regulator|clk"

# 5. 查 pinctrl
mount -t debugfs none /sys/kernel/debug
cat /sys/kernel/debug/pinctrl/*/pinmux-pins

# 6. 做外设功能测试
# 按第 10 章选择对应命令
```

只要坚持“原理图确认连接、手册确认复用、binding 确认写法、上板确认波形和日志”这条链路，DTS 配置问题通常都能被定位到具体引脚、具体电源或具体属性。
