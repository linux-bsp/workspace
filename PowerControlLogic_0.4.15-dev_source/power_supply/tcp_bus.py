"""One RTU request at a time over a transparent TCP serial server."""
import ipaddress
import socket
import select
import time
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from .core import ProtocolError, ResponseTimeout, frame


@dataclass(frozen=True)
class TcpEndpoint:
    host: str
    port: int

    def __post_init__(self):
        ipaddress.IPv4Address(self.host)
        if type(self.port) is not int or not 1 <= self.port <= 65535:
            raise ValueError('TCP端口需为1–65535')

    def __str__(self):
        return f'{self.host}:{self.port}'


class TcpTransport:
    def __init__(self, endpoint, *, response_timeout_ms=300, deadline=None):
        self.endpoint = endpoint
        self.response_timeout = response_timeout_ms / 1000
        self.closed = False
        self.last = 0.0
        self.last_exchange = {}
        self.deadline = deadline
        budget = 3 if deadline is None else min(3, max(.001, deadline-time.monotonic()))
        self.sock = socket.create_connection((endpoint.host, endpoint.port), timeout=budget)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    def exchange(self, request):
        if self.closed:
            raise ProtocolError('网络连接已关闭，请人工重新连接；输出状态需核对')
        time.sleep(max(0, self.last + .012 - time.monotonic()))
        if self.deadline is not None and time.monotonic() >= self.deadline:
            raise ResponseTimeout('恢复核验超过5秒')
        response = bytearray()
        self.last_exchange = dict(transport='TCP RTU', endpoint=str(self.endpoint),
                                  tx=request.hex(), tx_bytes=len(request), rx='', rx_bytes=0,
                                  started_at=datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='milliseconds'),
                                  stage='send', tx_drained=False, rx_chunks=[])
        try:
            if select.select([self.sock],[],[],0)[0]:
                unexpected = self.sock.recv(4096)
                self.last_exchange.update(discarded_rx=unexpected.hex(),discarded_rx_bytes=len(unexpected))
                raise ProtocolError('网络存在请求外数据或连接已断开，已停止以避免串帧')
            self.sock.settimeout(.3 if self.deadline is None else max(.001,min(.3,self.deadline-time.monotonic())))
            self.sock.sendall(request)
            self.last_exchange.update(stage='receive', tx_drained=True)
            deadline = time.monotonic() + self.response_timeout
            if self.deadline is not None:
                deadline = min(deadline, self.deadline)
            expected = 3
            while len(response) < expected:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise socket.timeout()
                self.sock.settimeout(remaining)
                chunk = self.sock.recv(expected - len(response))
                if not chunk:
                    raise ProtocolError('网络连接断开，电源实际状态未知')
                response.extend(chunk)
                self.last_exchange['rx_chunks'].append(dict(data=chunk.hex()))
                if len(response) >= 3:
                    if response[1] & 0x80:
                        expected = 5
                    elif response[1] == 3 and 0 < response[2] <= 128:
                        expected = 5 + response[2]
                    elif response[1] in (6, 16):
                        expected = 8
                    else:
                        raise ProtocolError('网络收到无效RTU帧头')
            if (response[0] != request[0] or response[1] not in (request[1],request[1] | 0x80)
                    or frame(bytes(response[:-2])) != bytes(response)):
                raise ProtocolError('网络RTU回复地址、功能码或CRC错误')
            return bytes(response)
        except socket.timeout as error:
            self.close()
            raise ResponseTimeout('网络响应超时，已断开以隔离迟到回复；写入不重发') from error
        except Exception:
            self.close()
            raise
        finally:
            self.last_exchange.update(rx=response.hex(), rx_bytes=len(response))
            self.last_exchange['finished_at']=datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='milliseconds')
            self.last = time.monotonic()

    def close(self):
        self.closed = True
        self.sock.close()
