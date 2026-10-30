"""Protocol and device service. All calls are synchronous on one bus worker."""
import math
import struct
import time
from dataclasses import dataclass
from .devices import valid_address


class ProtocolError(Exception):
    pass


class ResponseTimeout(ProtocolError):
    """Response missing/incomplete; a write may already have taken effect."""
    pass


class StateUnknown(ProtocolError):
    pass


class TargetNotReached(ProtocolError):
    pass


def crc16(data):
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ (0xA001 if crc & 1 else 0)
    return crc


def frame(data):
    return data + struct.pack('<H', crc16(data))


class Modbus:
    def __init__(self, transport, diagnostic=lambda record:None):
        self.transport = transport
        self.diagnostic = diagnostic
        self.timeouts = 0
        self.failures = 0
        self.consecutive = 0
        self.last_success = ''
        self.context = {}
        self.retry_allowed = lambda:True
        self.write_allowed = lambda:True
        self.read_allowed = lambda:True
        self.on_error = lambda error:None
        self.sample_evidence = {}
        self.recording_generation = lambda: 0

    def request(self, address, function, payload):
        started = time.monotonic()
        error = None
        self.response_bytes = b''
        self.exchange_started = False
        previous_exchange = getattr(self.transport, 'last_exchange', None)
        register = int.from_bytes(payload[:2], 'big')
        try:
            result = self._request(address,function,payload)
            self.consecutive = 0
            self.last_success = time.strftime('%Y-%m-%d %H:%M:%S')
            return result
        except Exception as exc:
            error = exc
            self.failures += 1
            self.consecutive += 1
            self.timeouts += isinstance(exc,ResponseTimeout)
            self.on_error(exc)
            raise
        finally:
            # Keep control readbacks and discarded input; routine sampling stays
            # compact so its normal reads do not evict long-run fault evidence.
            generation = self.recording_generation()
            state_key=(address,register,self.context.get('channel'))
            sample_state=(not error and function==3 and self.context.get('action')=='采样' and register in (0x100,0x101,0x10b,0x120,0x126))
            # Config/state changes matter; fluctuating measured V/A does not
            # warrant saving every successful sample's raw frame.
            state_value=(result[1:9]+result[17:21] if register in (0x101,0x10b) else result).hex() if sample_state else None
            first_state=sample_state and self.sample_evidence.get(state_key)!=(generation,state_value)
            if (first_state or error or function != 3 or self.context.get('action') != '采样'
                    or getattr(self.transport,'last_exchange',{}).get('discarded_rx_bytes')):
                request_hex = frame(bytes([address,function])+payload).hex() if valid_address(address) else ''
                trace = dict(getattr(self.transport,'last_exchange',{})) if self.exchange_started else {}
                if error and not self.response_bytes and getattr(self.transport,'last_exchange',None) is previous_exchange:
                    trace = {}  # No new exchange: never attribute an older reply to this failure.
                if trace.get('tx',request_hex)!=request_hex:trace={}
                trace.update(self.context, address=address, function=function, register=register,
                    register_hex=f'0x{register:04X}', recording_generation=generation,
                    elapsed_ms=round((time.monotonic()-started)*1000,2),error=str(error or ''),
                    error_type=type(error).__name__ if error else '')
                # Protocol-level bytes also cover simulators; failed partial reads
                # retain the transport's original receive buffer.
                trace['tx'] = request_hex
                if self.response_bytes:trace['rx'] = self.response_bytes.hex()
                if not error and function == 3:
                    values = list(struct.unpack('>'+'H'*((len(result)-1)//2),result[1:]))
                    trace['register_count'] = len(values)
                    trace['registers'] = {f'0x{register+i:04X}':v for i,v in enumerate(values)}
                    if register in (0x101,0x10b) and len(values)==10:
                        trace['output_state'] = dict(register=f'0x{register+8:04X}',raw=values[8],
                            interpreted={0:'已使能',1:'未使能'}.get(values[8],'未知'))
                saved=self.diagnostic(trace)
                if first_state and saved:self.sample_evidence[state_key]=(generation,state_value)

    def _request(self, address, function, payload):
        if not valid_address(address):
            raise ValueError('设备地址必须为1–255，禁止广播')
        self.exchange_started = True
        response = self.transport.exchange(frame(bytes([address, function]) + payload))
        self.response_bytes = response
        if len(response) < 5 or frame(response[:-2]) != response:
            raise ProtocolError('响应长度或 CRC 错误')
        if response[0] != address:
            raise ProtocolError('响应设备地址不符')
        if response[1] == function | 0x80:
            raise ProtocolError(f'Modbus 异常码 {response[2]:02X}')
        if response[1] != function:
            raise ProtocolError('响应功能码不符')
        if function == 3:
            count = int.from_bytes(payload[2:4],'big')
            if len(response) != 5 + count*2 or response[2] != count*2:
                raise ProtocolError('读取字节数不符')
        return response[2:-2]

    def read(self, address, register, count):
        try:
            return self._read(address,register,count)
        except ResponseTimeout:
            if not self.retry_allowed():raise
            result = self._read(address,register,count)
            self.diagnostic(dict(**self.context,address=address,register=register,event='只读重试恢复',actual=result))
            return result

    def _read(self, address, register, count):
        if not self.read_allowed():
            raise ProtocolError('读取窗口已结束')
        if not 1 <= count <= 64:
            raise ValueError('读取数量越界')
        result = self.request(address, 3, struct.pack('>HH', register, count))
        if not self.read_allowed():
            raise ProtocolError('读取返回超过恢复截止')
        if len(result) != 1 + 2 * count or result[0] != 2 * count:
            raise ProtocolError('读取字节数不符')
        return list(struct.unpack('>' + 'H' * count, result[1:]))

    def write(self, address, register, values, *, verify_timeout=True):
        try:
            return self._write(address,register,values)
        except ResponseTimeout as error:
            if not verify_timeout:
                raise StateUnknown('本地模式命令响应超时，未回读或重发；请在电源面板核对') from error
            try:
                actual = self.read(address,register,len(values))
            except ProtocolError as query_error:
                raise StateUnknown(f'写入超时，核对失败，状态未知：{query_error}') from error
            if actual != list(values):
                raise TargetNotReached(f'写入超时，回读未达到目标：实际{actual}，预期{list(values)}') from error
            self.diagnostic(dict(**self.context,address=address,register=register,event='写入超时后回读一致，未重发',actual=actual))

    def _write(self, address, register, values):
        if not self.write_allowed():
            raise ProtocolError('程序已停止或阶段已改变，取消过时写入')
        if len(values) == 1:
            payload = struct.pack('>HH', register, values[0])
            result = self.request(address, 6, payload)
            expected = payload
        else:
            if not 1 <= len(values) <= 64:
                raise ValueError('写入数量越界')
            expected = struct.pack('>HH', register, len(values))
            payload = expected + bytes([len(values)*2]) + struct.pack('>'+'H'*len(values), *values)
            result = self.request(address, 16, payload)
        if result != expected:
            raise ProtocolError('写入响应不匹配；实际结果未知，请重新读取')


def words(value):
    return [value >> 16, value & 0xFFFF]


def integer(values):
    return values[0] * 65536 + values[1]


@dataclass(frozen=True)
class Settings:
    voltage: float
    current: float
    ovp: float
    ocp: float
    ovp_enabled: bool
    ocp_enabled: bool

    def validate(self):
        for name, limit in [('voltage', 30), ('current', 10), ('ovp', 30), ('ocp', 10)]:
            value = getattr(self, name)
            if not math.isfinite(value) or not 0 <= value <= limit:
                raise ValueError(f'{name} 必须在 0–{limit} 范围内')


class PowerService:
    def __init__(self, bus):
        self.bus = bus
        self.protection_cache = {}
        self.output_confirmations = {}

    @staticmethod
    def registers(channel):
        if channel not in (1, 2):
            raise ValueError('通道必须为 1 或 2')
        return (0x101, 0x120) if channel == 1 else (0x10B, 0x126)

    def independent(self, address):
        if self.bus.read(address, 0x100, 1)[0] != 0:
            raise ProtocolError('设备不是独立模式，请在电源面板切换后重试')

    def remote(self, address):
        self.bus.write(address, 0, [1])
        if self.bus.read(address, 0, 1) != [1]:
            raise ProtocolError('远程模式回读失败')

    def local(self, address):
        context = self.bus.context
        try:
            # Onsite evidence: a mode query reactivates remote control. Release
            # is therefore the final request, including when its ACK is lost.
            # A matching ACK confirms acceptance, not the physical panel state.
            self.bus.context = dict(context,phase='local_write',expected_local=0,
                                    verification='write_ack_only_no_followup_read')
            self.bus.write(address, 0, [0], verify_timeout=False)
        finally:
            self.bus.context = context

    def sample(self, address, channel):
        base, protection = self.registers(channel)
        self.independent(address)
        data = self.bus.read(address, base, 10)
        if data[8] not in (0, 1) or data[9] not in (0, 1):
            raise ProtocolError('输出或 CV/CC 状态无效')
        voltage, current = integer(data[4:6])/1000, integer(data[6:8])/1000
        key = (address, channel)
        confirmed = self.output_confirmations.get(key) == data[8]
        if not confirmed:
            self.output_confirmations.pop(key, None)
        result = dict(voltage=voltage, current=current, power=voltage*current,
                    set_voltage=integer(data[:2])/1000, set_current=integer(data[2:4])/1000,
                    output_raw=data[8], output_command_confirmed=confirmed,
                    output='开启' if data[8] == 0 else '关闭', mode='CV' if data[9] == 1 else 'CC')
        try:
            cached = self.protection_cache.get((address,channel))
            now = time.monotonic()
            fresh = not (result['output']=='关闭' and cached and now-cached[0]<5)
            values = self.bus.read(address,protection,6) if fresh else cached[1]
            if values[2] not in (0,1) or values[5] not in (0,1):
                raise ProtocolError('保护开关状态无效')
            result.update(ocp=integer(values[:2])/1000,ovp=integer(values[3:5])/1000,
                          ocp_enabled=bool(values[2]),ovp_enabled=bool(values[5]),protection_error='')
            if fresh:self.protection_cache[address,channel]=(time.monotonic(),values)
            result.update(protection_fresh=fresh,protection_age_seconds=round(time.monotonic()-self.protection_cache[address,channel][0],3))
        except ProtocolError as error:
            self.protection_cache.pop((address,channel),None)
            result.update(ocp=None,ovp=None,ocp_enabled=None,ovp_enabled=None,protection_error=str(error))
        return result

    def settings(self, address, channel):
        base, protection = self.registers(channel)
        values = self.bus.read(address, base, 4)
        protect = self.bus.read(address, protection, 6)
        if protect[2] not in (0, 1) or protect[5] not in (0, 1):
            raise ProtocolError('保护开关状态无效')
        return Settings(integer(values[:2])/1000, integer(values[2:])/1000,
                        integer(protect[3:5])/1000, integer(protect[:2])/1000,
                        bool(protect[5]), bool(protect[2]))

    def apply(self, address, channel, settings):
        settings.validate()
        self.protection_cache.pop((address,channel),None)
        base, protection = self.registers(channel)
        self.remote(address)
        self.independent(address)
        # Each write is acknowledged. Failures stop this channel; never retry writes.
        self.bus.write(address, protection, words(round(settings.ocp * 1000)))
        self.bus.write(address, protection+3, words(round(settings.ovp * 1000)))
        self.bus.write(address, protection+2, [int(settings.ocp_enabled)])
        self.bus.write(address, protection+5, [int(settings.ovp_enabled)])
        self.bus.write(address, base, words(round(settings.voltage*1000)) + words(round(settings.current*1000)))
        actual = self.settings(address, channel)
        if actual != settings:
            raise ProtocolError(f'参数回读不一致：{actual}')
        return actual

    def output(self, address, channel, enabled, *, cancelled=lambda:False):
        base, _ = self.registers(channel)
        self.output_confirmations.pop((address, channel), None)
        self.remote(address)
        self.independent(address)
        if cancelled():
            raise ProtocolError('控制已取消或过期，未发送输出写入')
        value = 0 if enabled else 1  # Dual-channel polarity differs from single-channel.
        self.bus.write(address, base+8, [value])
        if self.bus.read(address, base+8, 1) != [value]:
            raise ProtocolError('输出回读失败，输出状态未知')
        self.output_confirmations[address, channel] = value


class Simulator:
    """Register-level RTU simulator, never opens a serial port."""
    def __init__(self, addresses=(1,2)):
        self.registers = {a: {0: 0, 0x100: 0} for a in addresses}
        self.offline = set()
        self.requests = []
        for a in self.registers:
            for ch in (1, 2):
                base, protect = PowerService.registers(ch)
                self.registers[a].update({r: 0 for r in range(base, base+10)})
                self.registers[a].update({r: 0 for r in range(protect, protect+6)})
                self.registers[a][base+8] = 1
                self.registers[a][base+9] = 1

    def exchange(self, request):
        self.requests.append(request)
        a, f = request[:2]
        if a in self.offline:
            raise ProtocolError('模拟设备离线')
        reg, value = struct.unpack('>HH', request[2:6])
        memory = self.registers[a]
        if f == 3:
            for ch in (1, 2):
                base, _ = PowerService.registers(ch)
                for offset in range(4):
                    memory[base+4+offset] = memory[base+offset] if memory[base+8] == 0 else 0
            if any(r not in memory for r in range(reg, reg+value)):
                return frame(bytes([a, 0x83, 2]))
            return frame(bytes([a, f, value*2]) + struct.pack('>'+'H'*value, *[memory[r] for r in range(reg, reg+value)]))
        if f == 6:
            memory[reg] = value
            return request
        for i, word in enumerate(struct.unpack('>'+'H'*value, request[7:-2])):
            memory[reg+i] = word
        return frame(request[:6])

    def close(self):
        pass
