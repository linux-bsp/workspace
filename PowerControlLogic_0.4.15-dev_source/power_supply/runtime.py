import csv
import json
import queue
import time
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path
from PySide6.QtCore import QThread, Signal
from .core import Modbus, PowerService, ResponseTimeout, StateUnknown, ProtocolError
from .serial_bus import SerialTransport
from .tcp_bus import TcpEndpoint, TcpTransport
from .devices import Device, valid_address
from .recovery import Program, RecoveryWindow, protection_ok, protection_tripped


def timestamp():
    return datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='milliseconds')


class Recorder:
    fields = ['time', 'source', 'device_name', 'address', 'channel', 'set_voltage', 'set_current',
              'ovp','ocp','ovp_enabled','ocp_enabled','protection_error','protection_trip',
              'voltage', 'current', 'power', 'output', 'output_raw', 'output_command_confirmed', 'mode', 'status', 'error',
              'comm_timeouts','comm_failures','comm_consecutive','comm_last_success',
              'protection_age_seconds','protection_fresh','channel_consecutive','channel_last_success']

    def __init__(self, root, source):
        self.path = Path(root) / (datetime.now().strftime('%Y%m%d_%H%M%S_%f') + '_' + source)
        self.path.mkdir(parents=True, exist_ok=False)
        self.csv = (self.path/'samples.csv').open('x', encoding='utf-8-sig', newline='')
        try:
            self.writer = csv.DictWriter(self.csv, fieldnames=self.fields, extrasaction='ignore')
            self.writer.writeheader()
            self.csv.flush()
            self.events = (self.path/'events.jsonl').open('x', encoding='utf-8')
        except Exception:
            self.csv.close()
            raise
        self.source = source
        from . import VERSION
        self.event(dict(kind='诊断说明',power_version=VERSION,
            protocol='Modbus RTU',output_registers={'CH1':'0x0109','CH2':'0x0113'},
            output_encoding={'0':'已使能','1':'未使能'},remote_register='0x0000',
            remote_encoding={'0':'本地','1':'远控'},
            note='客户端收发证据，不证明面板或线路实态；首次、设值/状态变化和异常保存原始帧'))

    def sample(self, row):
        self.writer.writerow(dict(row, source=self.source))
        self.csv.flush()

    def event(self, message):
        self.events.write(json.dumps(dict(time=timestamp(), message=message), ensure_ascii=False)+'\n')
        self.events.flush()

    def diagnostic(self, record):
        path = self.path/'communication.jsonl'
        if path.exists() and path.stat().st_size >= 10*1024*1024:
            for index in range(3,0,-1):
                old = self.path/('communication.jsonl' if index==1 else f'communication.{index-1}.jsonl')
                if old.exists():old.replace(self.path/f'communication.{index}.jsonl')
        with path.open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(dict(time=timestamp(),**record),ensure_ascii=False)+'\n')

    def close(self):
        self.csv.close()
        self.events.close()


class RecordingController:
    """Only the worker touches files; UI only changes the requested Event."""
    def __init__(self, root, source, enabled, on_state=lambda *args:None, on_error=lambda *args:None):
        self.root,self.source = root,source
        self.requested = threading.Event()
        self.generation = 0
        self.set_enabled(enabled)
        self.recorder = None
        self.recorder_generation = None
        self.on_state,self.on_error = on_state,on_error

    def set_enabled(self, enabled):
        if enabled:
            if not self.requested.is_set():self.generation += 1
            self.requested.set()
        else:
            self.requested.clear()

    def sync(self):
        try:
            if self.recorder is not None and self.recorder_generation != self.generation:self.close()
            if self.requested.is_set() and self.recorder is None:
                self.recorder = Recorder(self.root,self.source)
                self.recorder_generation = self.generation
                self.on_state(True,str(self.recorder.path))
            elif not self.requested.is_set() and self.recorder is not None:
                self.close()
        except OSError as error:
            self.fail(error)

    def fail(self, error):
        self.requested.clear()
        recorder,self.recorder = self.recorder,None
        if recorder:
            try:
                recorder.close()
            except OSError:
                pass
        self.on_state(False,'')
        self.on_error(str(error))

    def write(self, kind, value):
        self.sync()
        if self.recorder:
            try:
                getattr(self.recorder,kind)(value)
                return True
            except OSError as error:
                self.fail(error)

    def sample(self, row):
        self.write('sample',row)

    def event(self, text):
        self.write('event',text)

    def diagnostic(self, record):
        return self.write('diagnostic',record)

    def close(self):
        recorder,self.recorder = self.recorder,None
        if recorder:
            try:
                recorder.close()
            finally:
                self.on_state(False,str(recorder.path))


class Worker(QThread):
    sample_ready = Signal(dict)
    message = Signal(str)
    ready = Signal(str)
    failed = Signal(str)
    operation_done = Signal(dict)
    recording_changed = Signal(bool,str)
    recording_error = Signal(str)
    recovery_changed = Signal(str)
    program_changed = Signal(dict)
    program_request_done = Signal()

    def __init__(self, port, root, *, devices, recording=True, transport_factory=None,response_timeout_ms=300):
        super().__init__()
        self.port, self.root = port, root
        self.transport_factory = transport_factory
        self.response_timeout_ms = response_timeout_ms
        self.devices = tuple(devices)
        if not self.devices or any(not isinstance(d,Device) for d in self.devices):
            raise ValueError('请配置设备')
        if len({d.address for d in self.devices}) != len(self.devices):
            raise ValueError('设备地址重复')
        self.targets = frozenset((d.address,c) for d in self.devices for c in (1,2))
        self.recording = RecordingController(root,'TEST' if transport_factory else 'HARDWARE',
                                            recording,self.recording_changed.emit,self.recording_error.emit)
        self.commands = queue.Queue(maxsize=1)
        self.command_lock = threading.Lock()
        self.program_commands = queue.Queue()
        self.program_stop = threading.Event()
        self.recovery_window = RecoveryWindow()
        self.recovery_fault = False
        self.resume_addresses = set()
        self.program = None
        self.terminal_requested = False
        self.unavailable_addresses = set()
        self.device_additions = queue.Queue()

    def add_device(self, device):
        if not isinstance(device,Device):raise ValueError('设备配置无效')
        self.device_additions.put(device)

    def accept_devices(self):
        while not self.device_additions.empty():
            device = self.device_additions.get_nowait()
            if any(d.address==device.address for d in self.devices):
                self.message.emit(f'地址{device.address}已存在，未重复加入采样')
                continue
            self.devices = (*self.devices,device)
            self.targets = self.targets | {(device.address,1),(device.address,2)}
            self.recording.event(f'新增采样设备 {device.name} 地址{device.address}；未加入正在运行的程序')

    def program_request(self, action, value=None):
        if action in ('stop', 'pause'):
            self.program_stop.set()
        if action == 'stop':
            self.terminal_requested = True
        self.program_commands.put((action, value))

    def open_transport(self, deadline=None):
        transport = self.transport_factory() if self.transport_factory else (
            TcpTransport(self.port,response_timeout_ms=self.response_timeout_ms,deadline=deadline)
            if isinstance(self.port,TcpEndpoint) else SerialTransport(self.port,response_timeout_ms=self.response_timeout_ms))
        transport.deadline = deadline
        return transport

    def make_service(self, transport):
        service = PowerService(Modbus(transport,self.recording.diagnostic))
        service.bus.recording_generation = lambda:self.recording.generation
        service.bus.retry_allowed = lambda: not self.recovery_fault and not self.isInterruptionRequested() and self.commands.empty()
        service.bus.on_error = self.connection_fault
        return service

    def recovery_message(self, message, state=False):
        self.recording.event(message)
        (self.recovery_changed if state else self.message).emit(message)

    def connection_fault(self, error):
        if self.isInterruptionRequested():
            return
        first = not self.recovery_fault
        self.recovery_window.begin()
        self.recovery_fault = True
        if first:
            with self.command_lock:
                while not self.commands.empty():
                    action,targets,*_ = self.commands.get_nowait()
                    self.operation_done.emit(dict(success=0,failure=0,skipped=len(targets),succeeded=[],
                        channels=[dict(address=a,channel=c,state='未执行',detail='连接中断，未发送手动指令') for a,c in targets]))
                    self.message.emit('本批操作结束：连接中断，未发送手动指令，重连不补发')
            self.resume_addresses = {int(a) for a,s in self.program.state['devices'].items() if s == '运行中'}
            self.program.pause('重连核验中', self.resume_addresses)
            self.recovery_message('重连核验中（最多5秒）：'+str(error), state=True)

    def reconnect(self, transport):
        """Single owner, one absolute deadline; failed addresses rotate last."""
        if transport:
            transport.close()
        addresses = [d.address for d in self.devices]
        verified = set()
        service = None
        transport = None
        while self.recovery_window.remaining() > 0 and not self.isInterruptionRequested():
            if time.monotonic() < self.recovery_window.next_attempt:
                self.msleep(10)
                continue
            try:
                if transport is None:
                    transport = self.open_transport(self.recovery_window.deadline)
                    service = self.make_service(transport)
                    service.bus.retry_allowed = lambda: False
                    service.bus.read_allowed = lambda: self.recovery_window.remaining() > 0 and not self.isInterruptionRequested()
                    verified.clear()
                for address in list(addresses):
                    if self.recovery_window.remaining() <= 0 or self.isInterruptionRequested():
                        break
                    if address in verified:
                        continue
                    old = self.program.state['devices'].get(str(address))
                    try:
                        # Manual-paused/failed devices must not be promoted by reconnect.
                        self.program.verify(service,address,self.recovery_window.deadline,resume=False)
                        verified.add(address)
                    except Exception as error:
                        self.recovery_message(f'重连核验：设备{address}未通过：{error}')
                        if old is not None and address not in self.resume_addresses:
                            self.program.state['devices'][str(address)] = old
                        addresses.remove(address)
                        if not getattr(transport,'closed',False) or not addresses:
                            addresses.append(address)
                        if getattr(transport,'closed',False):
                            raise
                if verified:
                    break
                raise ProtocolError('尚无设备通过恢复核验')
            except Exception as error:
                self.recovery_message('重连核验：'+str(error))
                if transport:
                    transport.close()
                transport = None
                self.recovery_window.retry()
        if not verified or transport is None or self.isInterruptionRequested():
            if transport:
                transport.close()
            self.program.pause('待人工恢复', self.resume_addresses)
            self.recovery_message('待人工恢复：5秒内未完成连接及核验', state=True)
            raise ProtocolError('自动恢复已停止；请手动连接并恢复程序')
        transport.deadline = None
        self.unavailable_addresses = {d.address for d in self.devices} - verified
        service.bus.read_allowed = lambda: True
        for a in verified & self.resume_addresses:
            if self.program.state['devices'].get(str(a)) == '重连核验中' and not self.program_stop.is_set():
                self.program.resume_verified(a)
        for a in self.resume_addresses - verified:
            self.program.pause('待人工恢复', {a})
        self.program.save('恢复核验结束')
        self.recovery_fault = False
        self.recovery_message('连接恢复；已核验设备继续，其他设备待人工恢复', state=True)
        return transport, service

    def submit(self, action, targets, value, *, deadline=None, cancel_event=None, audit=None):
        targets = tuple(targets)
        if not targets or not set(targets).issubset(self.targets):
            raise ValueError('控制目标不在本次设备列表中')
        with self.command_lock:
            if self.recovery_fault or self.isInterruptionRequested():
                raise ValueError('连接正在恢复或已停止，未接收手动指令')
            self.commands.put_nowait((action, targets, value, deadline,cancel_event,audit))

    def set_recording(self, enabled):
        self.recording.set_enabled(enabled)

    def run(self):
        transport = None
        service = None
        recorder = self.recording
        try:
            if self.program is None:
                self.program = Program(Path(self.root)/'program-logs'/('connection_'+str(time.time_ns())+'.jsonl'))
            self.program.notify = self.program_changed.emit
            self.program.stop_requested = lambda: self.isInterruptionRequested() or self.program_stop.is_set()
            self.program_changed.emit(json.loads(json.dumps(self.program.state)))
            transport = self.open_transport()
            service = self.make_service(transport)
            channel_health = {}
            recorder.sync()
            self.ready.emit('')
            next_sample = time.monotonic()
            while not self.isInterruptionRequested():
                recorder.sync()
                self.accept_devices()
                if self.recovery_fault:
                    transport, service = self.reconnect(transport)
                while not self.program_commands.empty():
                    program_action, value = self.program_commands.get_nowait()
                    if program_action == 'stop':
                        self.program.stop()
                    elif program_action == 'pause':
                        self.program.pause()
                    elif program_action == 'pause_after':
                        self.program.request_pause()
                    elif program_action == 'start':
                        self.program_stop.clear()
                        self.terminal_requested = False
                        self.program.start(*value, self.port)
                    elif program_action == 'resume':
                        if self.program.state['endpoint'] != str(self.port):
                            self.message.emit('连接目标已改变，拒绝恢复原程序')
                            self.program_request_done.emit()
                            continue
                        self.program_stop.clear()
                        for device in self.devices:
                            if self.program.state['devices'].get(str(device.address)) in ('已暂停','待人工恢复','待人工处理','重连核验中'):
                                try:
                                    self.program.verify(service,device.address,manual=True)
                                except Exception as error:
                                    self.program.pause('待人工处理',{device.address})
                                    self.message.emit(str(error))
                    self.program_request_done.emit()
                self.program.step(service)
                if self.recovery_fault:
                    continue
                self.recovery_window.clear()
                try:
                    action, targets, value, deadline,cancel_event,audit = self.commands.get_nowait()
                except queue.Empty:
                    action = None
                if action:
                    success_count = failure_count = 0
                    succeeded = []
                    outcomes = []
                    for address, channel in targets:
                        def cancelled():
                            return (self.isInterruptionRequested() or (cancel_event is not None and cancel_event.is_set())
                                    or (deadline is not None and time.time()>deadline))
                        if cancelled():
                            break
                        label = '程序接通电源' if action == 'program_on' else ('设置参数' if action == 'apply' else ('开启输出' if value else '关闭输出'))
                        service.bus.context=dict(action=label,channel=channel)
                        if audit and audit[0]:
                            service.bus.context.update(run_id=audit[0].run_id,cycle=audit[1],row_id=audit[2])
                            recorder.sync()
                            if recorder.recorder:audit[0].mirror(recorder.recorder.path)
                            audit[0].emit('channel_command',cycle=audit[1],row_id=audit[2],address=address,channel=channel,action=action)
                            recorder.event(dict(kind='计划命令',**service.bus.context,address=address))
                        recorder.event(f'请求 {label} {address}/CH{channel}: {value}')
                        try:
                            if action == 'program_on':
                                if any(k[0] == address for k in self.program.state['locks']):
                                    raise RuntimeError('此前达到保护阈值；请人工检查并重新应用参数后再接通')
                                result = service.apply(address, channel, value)
                                if cancelled():
                                    raise RuntimeError('计划已过期；参数已下发但未接通')
                                service.output(address, channel, True, cancelled=cancelled)
                            elif action == 'apply':
                                result = service.apply(address, channel, value)
                                # Preserve manual protection acknowledgement when no program is active.
                                if not any(s not in ('已终止','已结束') for s in self.program.state['devices'].values()):
                                    row = service.sample(address,channel)
                                    if protection_ok(row):
                                        self.program.state['locks'] = [k for k in self.program.state['locks'] if k != [address,channel]]
                            else:
                                if value and any(k[0] == address for k in self.program.state['locks']):
                                    raise RuntimeError('此前达到保护阈值；请人工检查并重新应用参数后再开启')
                                result = service.output(address, channel, value,cancelled=cancelled)
                            detail = (f'电压 {result.voltage:g} V，电流 {result.current:g} A，'
                                      f'OVP {result.ovp:g} V / {"开" if result.ovp_enabled else "关"}，'
                                      f'OCP {result.ocp:g} A / {"开" if result.ocp_enabled else "关"}') if result else ''
                            message = f'{address}/CH{channel} {label} 回读确认成功 {detail}'
                            success_count += 1
                            succeeded.append((address, channel))
                            outcomes.append(dict(address=address,channel=channel,state='成功',detail=detail))
                        except Exception as error:
                            state = '未知' if isinstance(error,(ResponseTimeout,StateUnknown)) else '失败'
                            outcomes.append(dict(address=address,channel=channel,state=state,detail=str(error)))
                            message = f'{address}/CH{channel} {label} 失败，可能部分生效，不自动重发：{error}'
                            failure_count += 1
                            self.sample_ready.emit(dict(time=timestamp(), address=address, channel=channel,
                                                        status='ERROR', output='输出状态未知', error=str(error)))
                        if audit and audit[0]:audit[0].emit('channel_result',cycle=audit[1],row_id=audit[2],**outcomes[-1])
                        recorder.event(message)
                        self.message.emit(message)
                        if self.recovery_fault and getattr(transport,'closed',False):
                            break
                    attempted={(r['address'],r['channel']) for r in outcomes}
                    outcomes.extend(dict(address=a,channel=c,state='未执行',detail='取消或计划过期') for a,c in targets if (a,c) not in attempted)
                    recorder.event(dict(kind='通道操作结果',action=action,channels=outcomes))
                    summary = f'本批操作结束：成功 {success_count}，失败或未知 {failure_count}，未执行 {len(targets)-success_count-failure_count}'
                    recorder.event(summary)
                    self.operation_done.emit(dict(success=success_count,failure=failure_count,
                                                  skipped=len(targets)-success_count-failure_count,
                                                  succeeded=succeeded,channels=outcomes))
                    self.message.emit(summary)
                if not self.recovery_fault and time.monotonic() >= next_sample:
                    for device in self.devices:
                        if device.address in self.unavailable_addresses:
                            continue
                        if self.isInterruptionRequested() or self.recovery_fault or not self.commands.empty():
                            break
                        address = device.address
                        for channel in (1, 2):
                            if self.isInterruptionRequested() or self.recovery_fault or not self.commands.empty():
                                break
                            row = dict(time=timestamp(), device_name=device.name,address=address, channel=channel)
                            service.bus.context=dict(action='采样',channel=channel)
                            try:
                                row.update(service.sample(address, channel), status='OK', error='')
                                key = (address, channel)
                                if row.get('protection_error'):
                                    row.update(status='ERROR', error='保护状态未确认：'+row['protection_error'])
                                    if not self.recovery_fault:
                                        self.program.pause('待人工处理',{address})
                                trip = protection_tripped(row)
                                if row['output'] == '开启' and trip and list(key) not in self.program.state['locks']:
                                    self.program.latch(address,channel)
                                    reason = f'{address}/CH{channel} 测量值达到 OVP/OCP 阈值；客户端补发关闭输出'
                                    recorder.event(reason)
                                    self.message.emit(reason)
                                    try:
                                        service.output(address, channel, False)
                                        row.update(output='关闭',output_raw=1,output_command_confirmed=True)
                                        row['protection_trip'] = '已补关并回读'
                                    except Exception as error:
                                        row['protection_trip'] = '补关失败，实际输出未知：'+str(error)
                                        row['output'] = '输出状态未知'
                                    recorder.event(row['protection_trip'])
                                    self.message.emit(row['protection_trip'])
                            except Exception as error:
                                row.update(status='ERROR', output='输出状态未知', error=str(error))
                            row['time'] = timestamp()
                            health=channel_health.setdefault((address,channel),[0,''])
                            if row['status']=='OK':
                                health[:]=[0,row['time']]
                            else:health[0]+=1
                            row.update(channel_consecutive=health[0],channel_last_success=health[1])
                            row.update(comm_timeouts=service.bus.timeouts,comm_failures=service.bus.failures,
                                       comm_consecutive=service.bus.consecutive,comm_last_success=service.bus.last_success)
                            recorder.sample(row)
                            self.sample_ready.emit(row)
                    next_sample += 1
                    if next_sample < time.monotonic():
                        recorder.event('采样延迟：本轮未按计划时间完成采样，已按实际时间记录（此提示不代表通信失败）')
                        next_sample = time.monotonic()+1
                if getattr(transport,'closed',False):
                    self.connection_fault(ProtocolError('电源连接已中止'))
                self.msleep(20)
        except Exception as error:
            recorder.event('通信或程序异常结束：'+str(error))
            self.failed.emit(str(error))
        finally:
            if self.program is not None:
                try:
                    if self.terminal_requested:
                        self.program.stop()
                    else:
                        self.program.pause('待人工恢复')
                except OSError as error:
                    self.failed.emit('恢复记录保存失败：'+str(error))
            if transport and service and self.isInterruptionRequested():
                service.bus.retry_allowed = lambda: False
                for device in self.devices:
                    service.bus.context = dict(action='退出远控')
                    try:
                        if getattr(transport,'closed',False):
                            raise ProtocolError('连接已失效，无法发送退出远控；请在电源面板核对')
                        service.local(device.address)
                        message = f'{device.name}（{device.address}）已收到退出远控应答，停止查询；请在面板核对本地操作'
                    except Exception as error:
                        message = f'{device.name}（{device.address}）退出远控未确认：{error}'
                        self.failed.emit(message)
                    recorder.event(message)
                    if '退出远控未确认' not in message:self.message.emit(message)
            elif transport:
                self.recovery_message('通信异常结束，退出远控未确认；自动恢复已结束，请在电源面板核对')
            if transport:
                transport.close()
            try:
                recorder.close()
            except OSError as error:
                self.recording_error.emit(str(error))
