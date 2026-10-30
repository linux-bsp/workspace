电源控制逻辑源码 0.4.15-dev
来源：T5000客户端0.6.8-dev，2026-10-30源码快照。
仅提取控制逻辑，无窗口、UI组件、主题、客户端程序、现场配置或历史日志。
保留退出远控写0后不再查询的修复、原始输出位和通信诊断。
不包含“开启待核对”显示逻辑。设备回报开启/关闭仍按协议解析。

一、文件划分
power_supply/core.py：Modbus RTU帧、CRC、寄存器读写、设值与回读、输出开关、采样及模拟器。
power_supply/tcp_bus.py：TCP透传传输，使用RTU帧，不是带MBAP头的Modbus TCP。
power_supply/serial_bus.py：串口传输，9600/8/N/1、超时及原始帧记录。
power_supply/devices.py：设备地址和设备目录。
power_supply/runtime.py：后台工作线程、命令队列、采样、保护和记录。
power_supply/schedule.py：绝对时间及间隔程序模型。
power_supply/recovery.py：程序状态、通信恢复及保护核对。
power_supply/plan_journal.py：程序执行证据日志。
core.py：仅提供来源客户端版本，供PlanJournal写入来源；不含客户端逻辑。
test_*.py及power_supply/test_*.py：离线回归；不包含界面测试。
source-manifest.json：来源路径和SHA256，原模块逐字复制。

二、依赖
建议Python 3.12。协议、TCP、设备目录、调度和恢复模块仅用标准库。
串口及runtime使用PySide6的QtCore/QtSerialPort；无需QtWidgets、QApplication或界面窗口。
使用Worker及Qt串口时，由调用方建立QCoreApplication并管理线程/事件循环。
本包不重新实现调度界面的点击行为；调用方负责把程序模型、Worker命令和用户业务串接。

三、安装与离线验证（Windows本机PowerShell 7）
将ZIP完整解压，进入解压后的PowerControlLogic_0.4.15-dev_source目录。
整块一次发送：
Set-Location .\PowerControlLogic_0.4.15-dev_source
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe example_simulator.py
.\.venv\Scripts\python.exe verify.py
预期模拟示例输出SIMULATOR_OK；验证各模块退出码0。
验证仅模拟设备及127.0.0.1回环，不连接实际电源。日志在.verification目录。
如果已经进入源码目录，省略上面的Set-Location一行。

四、控制接口
PowerService(Modbus(transport))构造控制服务。
sample(address, channel)：读取采样；settings(address, channel)：读取设值。
apply(address, channel, Settings(...))：写入参数并回读，不开启输出。
output(address, channel, enabled)：明确开关输出并回读。
local(address)：退出远控；收到应答后应立即关闭传输，后续不要再查询。
TcpTransport、SerialTransport创建时会打开实际连接；本包示例只使用Simulator。
同一总线由单个工作线程顺序访问。开启前的设值校验、业务授权和目标选择由调用方负责。
读请求也可能使实机进入远控。原始位0表示开启、1表示关闭，不代表独立实测的物理输出。
未知/超时不得当作关闭；退出远控应答仅证明收到命令，面板操作仍需现场核验。
关闭传输不等于关闭输出。停止程序也不自动关闭输出。

五、数据与边界
调用方通过构造参数指定记录根目录；记录生成CSV、JSONL和程序日志，不自动迁移旧数据。
不含已编译EXE、驱动安装包或完整T5000客户端。未改原控制模块，不新增硬件验证结论。
本包无需向T5000设备上传文件；它是Windows调用方集成使用的电源控制源码。
