"""Qt serial transport, constructed and used only on the worker thread."""
import time
from datetime import datetime, timezone, timedelta
from PySide6.QtCore import QIODevice
from PySide6.QtSerialPort import QSerialPort
from .core import ProtocolError, ResponseTimeout

SerialError = QSerialPort.SerialPortError


def observed_time():
    return datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='milliseconds')


class SerialTransport:
    def __init__(self, port, *, response_timeout_ms=300):
        if response_timeout_ms not in (300,500,800):
            raise ValueError('响应等待仅支持300/500/800毫秒')
        self.response_timeout = response_timeout_ms / 1000
        self.port = QSerialPort(port)
        self.port.setBaudRate(9600)
        self.port.setDataBits(QSerialPort.DataBits.Data8)
        self.port.setParity(QSerialPort.Parity.NoParity)
        self.port.setStopBits(QSerialPort.StopBits.OneStop)
        self.port.setFlowControl(QSerialPort.FlowControl.NoFlowControl)
        if not self.port.open(QIODevice.OpenModeFlag.ReadWrite):
            raise ProtocolError(self.port.errorString())
        self.last = 0.0
        self.quarantine = 0.0
        self.deadline = None

    def wait_until_ready(self):
        deadline = max(self.last + 0.012,self.quarantine)
        while True:
            remaining = deadline-time.perf_counter()
            if remaining <= 0:
                return
            time.sleep(remaining)

    def exchange(self, request):
        # Ten idle bytes at 9600 8N1 require 10.417 ms, rounded upwards.
        self.wait_until_ready()
        if self.deadline is not None and time.monotonic() >= self.deadline:
            raise ResponseTimeout('恢复核验超过5秒')
        response = bytearray()
        self.last_exchange = dict(tx=request.hex(),tx_bytes=len(request),rx='',rx_bytes=0,
                                  stage='clear_input',started_at=observed_time(),
                                  tx_accepted_bytes=0,tx_drained=False,rx_chunks=[])
        send_started = False
        try:
            # Capture bytes visible to Qt before clearing. Bytes arriving during
            # clear cannot be reconstructed; this is not a wire-level capture.
            discarded = bytes(self.port.readAll()) if self.port.bytesAvailable() else b''
            cleared = self.port.clear(QSerialPort.Direction.Input)
            self.last_exchange.update(clear_at=observed_time(),clear_ok=bool(cleared),
                                      discarded_rx=discarded.hex(),discarded_rx_bytes=len(discarded))
            if not cleared:
                raise ProtocolError('串口接收缓存清理失败：'+self.port.errorString())
            self.port.clearError()
            self.wait_until_ready()
            self.last_exchange['idle_before_send_ms'] = (
                round((time.perf_counter()-self.last)*1000,4) if self.last else None)
            self.last_exchange['timing_clock'] = 'perf_counter'
            self.last_exchange.update(stage='send',tx_started_at=observed_time())
            send_started = True
            send_end = time.perf_counter()+0.3
            accepted = self.port.write(request)
            self.last_exchange['tx_accepted_bytes'] = accepted
            if accepted != len(request):
                raise ProtocolError('串口发送未完整入队：'+self.port.errorString())
            while self.port.bytesToWrite() > 0:
                remaining = send_end-time.perf_counter()
                if remaining <= 0:
                    raise ProtocolError('串口发送超时，待发缓冲区未清空')
                written = self.port.waitForBytesWritten(max(1,int(remaining*1000)))
                if self.port.error() not in (SerialError.NoError,SerialError.TimeoutError):
                    raise ProtocolError('串口发送错误：'+self.port.errorString())
                if not written and self.port.bytesToWrite() > 0:
                    raise ProtocolError('串口发送未完成：'+self.port.errorString())
            if self.port.error() not in (SerialError.NoError,SerialError.TimeoutError):
                raise ProtocolError('串口发送错误：'+self.port.errorString())
            self.last_exchange.update(tx_drained=True,tx_drained_at=observed_time(),stage='receive')
            self.port.clearError()
            end = time.perf_counter() + self.response_timeout
            if self.deadline is not None:
                end = min(end,time.perf_counter()+max(0,self.deadline-time.monotonic()))
            while time.perf_counter() < end:
                if self.port.bytesAvailable() or self.port.waitForReadyRead(max(1, int((end-time.perf_counter())*1000))):
                    chunk = bytes(self.port.readAll())
                    if chunk:
                        at = observed_time()
                        self.last_exchange.setdefault('rx_first_at',at)
                        self.last_exchange['rx_last_at'] = at
                        self.last_exchange['rx_chunks'].append(dict(time=at,data=chunk.hex()))
                        response.extend(chunk)
                if self.port.error() not in (SerialError.NoError,SerialError.TimeoutError):
                    raise ProtocolError('串口接收错误：'+self.port.errorString())
                if len(response) >= 3:
                    expected = 5 if response[1] & 0x80 else (5+response[2] if response[1] == 3 else 8)
                    if len(response) >= expected:
                        return bytes(response)
            raise ResponseTimeout('串口响应超时，设备状态未知')
        except Exception:
            self.last_exchange.update(serial_error=self.port.error().name,
                                      serial_error_text=self.port.errorString())
            if send_started and not self.last_exchange['tx_drained']:
                self.last_exchange['tx_pending_on_error'] = self.port.bytesToWrite()
                self.last_exchange['output_abort_ok'] = bool(self.port.clear(QSerialPort.Direction.Output))
            # Drain late replies before the next request; never retry a write.
            self.quarantine = time.perf_counter() + max(0.35,self.response_timeout)
            raise
        finally:
            self.last_exchange.setdefault('serial_error',self.port.error().name)
            self.last_exchange.setdefault('serial_error_text',self.port.errorString())
            self.last_exchange.update(rx=response.hex(),rx_bytes=len(response),finished_at=observed_time())
            self.last = time.perf_counter()

    def close(self):
        self.port.close()
