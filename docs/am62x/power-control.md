# SPPS3010R-2KD RS485 connection

The reference is `ATK-DLAM62xB_V1.1.pdf`, sheet 10 of 12,
`ATK_AM62x_CAN_RS485.SchDoc`. Connector J11 is the board-edge 8-pin
CAN/RS485 terminal block. Identify pins by the board marking; the schematic
does not establish a left/right orientation when viewed from outside the box.

| J11 pin | Signal | UART / transceiver | Use |
| --- | --- | --- | --- |
| 1 | RS485_1_A | UART1 / U10 SP3485 | UART1 remains reserved for TIFS |
| 2 | RS485_1_B | UART1 / U10 SP3485 | UART1 remains reserved for TIFS |
| 3 | RS485_2_A | UART2 / U12 SP3485 | Connect to the supply communication A |
| 4 | RS485_2_B | UART2 / U12 SP3485 | Connect to the supply communication B |
| 5 / 6 | CAN1_H / CAN1_L | MAIN MCAN0 | Existing MCU connection |
| 7 / 8 | CAN2_H / CAN2_L | MCU MCAN0 | Existing Satellite connection |

Use pins 3 and 4. J11 does not expose a ground pin; when a separate signal
reference is required, use an identified board signal ground. The supply's
communication connector is separate from its adjustable DC output terminals.

UART2 RXD is SoC ALW ball A15, routed through R261 to U12 RO. UART2 TXD is
ball B15, routed through R262 to U12 DI and the Q3 automatic-direction circuit.
The schematic's `RS485_2_TX`/`RS485_2_RX` labels describe the transceiver side;
follow RO/DI connectivity rather than interpreting those labels as SoC TX/RX.
U12 RE/DE are controlled by the circuit, so no DE GPIO/RTS configuration is used.
The schematic shows R247 as a 120-ohm termination resistor across this pair.

The [TI AM625 data sheet, pin attributes table](https://www.ti.com/lit/ds/sprsp58b/sprsp58b.pdf)
maps A15 to UART0_CTSn pad offset 0x01d0, mux mode 3 = UART2_RXD;
B15 is UART0_RTSn offset 0x01d4, mux mode 3 = UART2_TXD. The board DTS now
configures these two pads for `main_uart2`. The console stays on `main_uart0`.

The serdev client owns UART2; applications open the logical PDM device
`dc_power`, not a `/dev/ttyS*` node. The device is configured for Modbus slave address
12 (0x0c), 9600/8N1, voltage limit 30 V, current limit 10 A and the
`dual-independent` register profile with two channels. Change the DT `reg` if
the supply uses a different slave address.

The connected supply's address was discovered on the target using
`pdebug power probe`: it returned the exact remote-mode echo
`0c 06 00 00 00 01 49 17` at 9600/8N1. The previous address 1 came from the
protocol examples and was not the device's actual address. The board DTS now
uses `power@c` with `reg = <12>`; its logical name remains `dc_power`.
This confirms the remote-mode exchange. A subsequent read timeout at 0x001b
and the integrator's working `PowerControlLogic_0.4.15-dev_source` established
that the initial regular register profile was wrong for this integration.
The product DT now selects `pdm,register-profile = "dual-independent"`.
CH1/CH2 are read from 0x0101/0x010b as 10-register blocks, with unsigned mV/mA
values and inverted output/CV bits. Channel operations require panel independent
mode (0x0100 = 0). The updated EDK path still needs target verification:

```sh
pdebug power remote dc_power
pdebug power get dc_power
pdebug power get dc_power --channel 2
```

`info` should show `channels=2`, `telemetry_registers=10` and
`profile=dual-independent`. Sampling leaves `remote=unknown`, because it does
not query the separate remote-state register. Reads may reactivate remote mode;
do not query again after `pdebug power local dc_power` when returning the panel
to local control.

Build and validate through Buildroot as described in
[the EDK Power guide](../../edk/docs/power-control.md).
