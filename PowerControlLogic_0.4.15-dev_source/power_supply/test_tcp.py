"""Loopback only: no physical device or external network."""
import socket
import threading
import time
import unittest
import tempfile
from .tcp_bus import TcpEndpoint, TcpTransport
from .core import Modbus, ProtocolError, ResponseTimeout, StateUnknown, frame


class TcpTests(unittest.TestCase):
    def test_recovery_deadline_bounds_total_read_budget(self):
        def handler(conn):
            self.request(conn);time.sleep(.08);conn.sendall(frame(bytes([1,3,2,0,0])))
            self.request(conn);time.sleep(.2)
        transport=self.server(handler,800)
        started=time.monotonic();transport.deadline=started+.16
        try:
            transport.exchange(bytes.fromhex('01030100000185f6'))
            with self.assertRaises(ResponseTimeout):transport.exchange(bytes.fromhex('01030100000185f6'))
            self.assertLess(time.monotonic()-started,.35)
            self.assertTrue(transport.closed)
        finally:transport.close()

    def server(self, handler, timeout_ms=300):
        listener = socket.socket()
        listener.bind(('127.0.0.1',0))
        listener.listen(1)
        endpoint = TcpEndpoint('127.0.0.1',listener.getsockname()[1])
        self.errors = []
        def serve():
            try:
                listener.settimeout(3)
                conn,_ = listener.accept()
                with conn:
                    conn.settimeout(3)
                    handler(conn)
            except Exception as error:
                self.errors.append(error)
            finally:
                listener.close()
        thread = threading.Thread(target=serve)
        thread.start()
        self.addCleanup(lambda: thread.join(4))
        return TcpTransport(endpoint,response_timeout_ms=timeout_ms)

    @staticmethod
    def request(conn):
        data = b''
        while len(data)<8:
            chunk = conn.recv(8-len(data))
            if not chunk:break
            data += chunk
        return data

    def test_network_delay_within_800ms_succeeds_without_resend(self):
        requests=[]
        def handler(conn):
            requests.append(self.request(conn));time.sleep(.45)
            conn.sendall(frame(bytes([1,3,2,0,0])))
        transport=self.server(handler,800)
        try:
            self.assertEqual(Modbus(transport).read(1,0x100,1),[0])
            self.assertEqual(len(requests),1);self.assertFalse(transport.closed)
        finally:transport.close()

    def test_network_delay_beyond_800ms_still_closes(self):
        requests=[]
        def handler(conn):
            requests.append(self.request(conn));time.sleep(.95)
        transport=self.server(handler,800)
        with self.assertRaises(ResponseTimeout):transport.exchange(bytes.fromhex('01030100000185f6'))
        self.assertTrue(transport.closed);self.assertEqual(len(requests),1)

    def test_fragmented_reply_and_wire_protocol(self):
        requests=[]
        def handler(conn):
            requests.append(self.request(conn))
            response=frame(bytes([1,3,2,0,0]))
            for chunk in (response[:1],response[1:3],response[3:]):
                conn.sendall(chunk);time.sleep(.01)
        transport=self.server(handler)
        try:
            self.assertEqual(Modbus(transport).read(1,0x100,1),[0])
            self.assertEqual(requests,[bytes.fromhex('01030100000185f6')])
            self.assertEqual(transport.last_exchange['rx'],'0103020000b844')
        finally:transport.close()

    def test_partial_timeout_keeps_hex_and_closes(self):
        def handler(conn):
            self.request(conn);conn.sendall(b'\xfe');time.sleep(.4)
        transport=self.server(handler)
        with self.assertRaises(ResponseTimeout):transport.exchange(bytes.fromhex('01030100000185f6'))
        self.assertEqual(transport.last_exchange['rx'],'fe')
        self.assertTrue(transport.closed)
        with self.assertRaises(ProtocolError):transport.exchange(b'anything')

    def test_write_timeout_never_reconnects_or_repeats(self):
        requests=[]
        def handler(conn):
            requests.append(self.request(conn));time.sleep(.4)
            requests.append(conn.recv(100))
        transport=self.server(handler)
        with self.assertRaises(StateUnknown):Modbus(transport).write(1,0x109,[1])
        self.assertTrue(transport.closed)
        time.sleep(.15)
        self.assertEqual(requests[0][1],6)
        self.assertEqual(requests[1],b'')

    def test_disconnect(self):
        transport=self.server(lambda conn:self.request(conn))
        with self.assertRaises(ProtocolError):Modbus(transport).read(1,0x100,1)
        self.assertTrue(transport.closed)

    def test_bad_crc_and_address_close(self):
        for response in (b'\x01\x03\x02\0\0\0\0',frame(b'\x02\x03\x02\0\0')):
            def handler(conn):
                self.request(conn);conn.sendall(response)
            transport=self.server(handler)
            with self.assertRaises(ProtocolError):Modbus(transport).read(1,0x100,1)
            self.assertTrue(transport.closed)

    def test_modbus_exception_preserved(self):
        def handler(conn):
            self.request(conn);conn.sendall(frame(bytes([1,0x83,2])))
        transport=self.server(handler)
        try:
            with self.assertRaisesRegex(ProtocolError,'异常码 02'):Modbus(transport).read(1,0x100,1)
        finally:transport.close()

    def test_single_and_multiple_register_writes(self):
        requests=[]
        def handler(conn):
            for size in (8,13):
                data=b''
                while len(data)<size:data+=conn.recv(size-len(data))
                requests.append(data)
                conn.sendall(frame(data[:6]))
        transport=self.server(handler)
        try:
            bus=Modbus(transport)
            bus.write(1,0x109,[1]);bus.write(1,0x101,[0,12000])
            self.assertEqual([r[1] for r in requests],[6,16])
            self.assertEqual(requests[1][7:-2],bytes.fromhex('00002ee0'))
        finally:transport.close()

    def test_invalid_endpoint(self):
        for host,port in [('bad',4008),('127.0.0.1',0),('127.0.0.1',65536)]:
            with self.assertRaises(ValueError):TcpEndpoint(host,port)

    def test_worker_network_samples_both_channels_without_writes(self):
        from PySide6.QtCore import QCoreApplication
        from .runtime import Worker
        from .core import Simulator
        from .devices import Device
        app=QCoreApplication.instance() or QCoreApplication([])
        simulator=Simulator((1,2));requests=[]
        def handler(conn):
            while True:
                request=self.request(conn)
                if not request:break
                requests.append(request)
                conn.sendall(simulator.exchange(request))
        listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen(1)
        endpoint=TcpEndpoint('127.0.0.1',listener.getsockname()[1])
        def serve():
            conn,_=listener.accept()
            try:handler(conn)
            finally:conn.close();listener.close()
        thread=threading.Thread(target=serve);thread.start()
        with tempfile.TemporaryDirectory() as root:
            worker=Worker(endpoint,root,devices=[Device('A',1),Device('B',2)],recording=True)
            rows=[];errors=[]
            worker.sample_ready.connect(rows.append);worker.failed.connect(errors.append)
            worker.start()
            try:
                deadline=time.monotonic()+4
                while len(rows)<4 and time.monotonic()<deadline:
                    app.processEvents();time.sleep(.01)
                self.assertEqual({(r['address'],r['channel']) for r in rows}, {(1,1),(1,2),(2,1),(2,2)})
                self.assertTrue(all(r['status']=='OK' for r in rows))
                self.assertFalse(errors)
                self.assertTrue(requests)
                self.assertTrue(all(r[1]==3 for r in requests))
            finally:
                worker.requestInterruption();self.assertTrue(worker.wait(4000));thread.join(4)
