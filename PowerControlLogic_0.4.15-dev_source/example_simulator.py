"""Offline protocol example. Never connects to hardware."""
from power_supply.core import Modbus, PowerService, Simulator

service = PowerService(Modbus(Simulator((11,))))
for channel in (1, 2):
    print(channel, service.sample(11, channel))
service.output(11, 1, False)  # Simulator only.
service.local(11)  # Final bus request: do not query after releasing remote mode.
print('SIMULATOR_OK')
