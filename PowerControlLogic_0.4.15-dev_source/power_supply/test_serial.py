"""Transport timing fixtures; no hardware port is opened."""
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from . import serial_bus
from .core import ResponseTimeout, frame


class SerialTests(unittest.TestCase):
    def exercise(self, timeout, delay, response):
        clock=[0.0]
        real=serial_bus.QSerialPort
        class Port:
            DataBits=real.DataBits;Parity=real.Parity;StopBits=real.StopBits
            FlowControl=real.FlowControl;Direction=real.Direction
            def __init__(self,name):self.buffer=b'';self.delivered=False
            def setBaudRate(self,*a):pass
            def setDataBits(self,*a):pass
            def setParity(self,*a):pass
            def setStopBits(self,*a):pass
            def setFlowControl(self,*a):pass
            def open(self,*a):return True
            def clear(self,*a):self.buffer=b'';return True
            def clearError(self):pass
            def error(self):return real.SerialPortError.NoError
            def errorString(self):return ''
            def bytesToWrite(self):return 0
            def write(self,data):self.start=clock[0];return len(data)
            def waitForBytesWritten(self,*a):return True
            def bytesAvailable(self):return len(self.buffer)
            def waitForReadyRead(self,ms):
                remain=max(0,self.start+delay-clock[0])
                clock[0]+=min(ms/1000,remain) if not self.delivered else ms/1000
                if not self.delivered and clock[0]>=self.start+delay:
                    self.buffer=response;self.delivered=True;return True
                return False
            def readAll(self):data=self.buffer;self.buffer=b'';return data
        fake_time=SimpleNamespace(perf_counter=lambda:clock[0],sleep=lambda seconds:clock.__setitem__(0,clock[0]+seconds))
        with patch.object(serial_bus,'QSerialPort',Port),patch.object(serial_bus,'time',fake_time):
            transport=serial_bus.SerialTransport('FAKE',response_timeout_ms=timeout)
            try:return transport.exchange(frame(bytes.fromhex('010301000001')))
            except ResponseTimeout:
                self.assertEqual(transport.last_exchange['rx_bytes'],len(response) if delay<timeout/1000 else 0)
                self.assertGreater(transport.quarantine,clock[0])
                raise

    def test_delayed_reply_respects_selected_timeout(self):
        response=frame(bytes.fromhex('0103020000'))
        with self.assertRaises(ResponseTimeout):self.exercise(300,.4,response)
        self.assertEqual(self.exercise(500,.4,response),response)
        self.assertEqual(self.exercise(800,.7,response),response)

    def test_truncated_reply_is_not_success(self):
        with self.assertRaises(ResponseTimeout):self.exercise(300,.01,b'\x01\x03\x02')

    def test_lost_reply_is_bounded(self):
        with self.assertRaises(ResponseTimeout):self.exercise(800,2,b'')

class SendCompletionTests(unittest.TestCase):
    def test_precise_gap_rechecked_after_early_wakeup(self):
        clock=[1.001]
        sleeps=[]
        def sleep(seconds):
            sleeps.append(seconds)
            clock[0]+=seconds/2 if len(sleeps)==1 else seconds
        fake=SimpleNamespace(monotonic=lambda:1.020,perf_counter=lambda:clock[0],sleep=sleep)
        port=self.port()
        reply=frame(bytes.fromhex('010600000001'))
        port.waitForReadyRead.return_value=True
        port.readAll.return_value=reply
        def write(data):
            self.assertGreaterEqual(clock[0],1.012)
            return len(data)
        port.write.side_effect=write
        with patch.object(serial_bus,'QSerialPort',return_value=port),patch.object(serial_bus,'time',fake):
            t=serial_bus.SerialTransport('FAKE')
            t.last=1.0
            self.assertEqual(t.exchange(reply),reply)
        self.assertGreaterEqual(len(sleeps),2)

    def port(self):
        from unittest.mock import MagicMock
        port=MagicMock()
        port.write.return_value=8
        port.bytesToWrite.return_value=0
        port.bytesAvailable.return_value=0
        port.error.return_value=serial_bus.SerialError.NoError
        port.errorString.return_value='injected'
        return port

    def test_send_stall_is_not_response_timeout(self):
        from .core import ProtocolError
        port=self.port()
        port.bytesToWrite.return_value=7
        port.waitForBytesWritten.return_value=False
        with patch.object(serial_bus,'QSerialPort',return_value=port):
            t=serial_bus.SerialTransport('FAKE')
            with self.assertRaises(ProtocolError) as caught:
                t.exchange(frame(bytes.fromhex('010600000001')))
        self.assertNotIsInstance(caught.exception,ResponseTimeout)
        port.waitForReadyRead.assert_not_called()
        self.assertEqual(t.last_exchange['tx_pending_on_error'],7)
        self.assertTrue(t.last_exchange['output_abort_ok'])

    def test_receive_error_preserves_driver_reason(self):
        from .core import ProtocolError
        port=self.port()
        def ready(ms):
            port.error.return_value=serial_bus.SerialError.ResourceError
            return False
        port.waitForReadyRead.side_effect=ready
        with patch.object(serial_bus,'QSerialPort',return_value=port):
            t=serial_bus.SerialTransport('FAKE')
            with self.assertRaises(ProtocolError) as caught:
                t.exchange(frame(bytes.fromhex('010600000001')))
        self.assertNotIsInstance(caught.exception,ResponseTimeout)
        self.assertEqual(t.last_exchange['serial_error'],'ResourceError')

    def test_discarded_input_and_split_reply_are_recorded(self):
        port=self.port()
        reply=frame(bytes.fromhex('010600000001'))
        port.bytesAvailable.side_effect=[3,0,0]
        port.readAll.side_effect=[b'old',reply[:3],reply[3:]]
        port.waitForReadyRead.return_value=True
        with patch.object(serial_bus,'QSerialPort',return_value=port):
            t=serial_bus.SerialTransport('FAKE')
            self.assertEqual(t.exchange(reply),reply)
        self.assertEqual(t.last_exchange['discarded_rx'],'6f6c64')
        self.assertEqual(len(t.last_exchange['rx_chunks']),2)
        self.assertTrue(t.last_exchange['tx_drained'])
        for key in ('tx_started_at','tx_drained_at','rx_first_at','rx_last_at','finished_at'):
            self.assertIn('+08:00',t.last_exchange[key])

    def test_all_pending_bytes_drained_before_read(self):
        from unittest.mock import MagicMock
        port=MagicMock()
        port.write.return_value=8
        pending=[8]
        port.bytesToWrite.side_effect=lambda:pending[0]
        def written(ms):
            pending[0]-=4
            return True
        port.waitForBytesWritten.side_effect=written
        port.error.return_value=serial_bus.QSerialPort.SerialPortError.NoError
        port.bytesAvailable.side_effect=lambda:0 if pending[0] else 8
        port.readAll.side_effect=lambda:frame(bytes.fromhex('010600000001')) if not pending[0] else b''
        def ready(ms):
            self.assertEqual(pending[0],0,'read started before complete write')
            return True
        port.waitForReadyRead.side_effect=ready
        with patch.object(serial_bus,'QSerialPort',return_value=port):
            t=serial_bus.SerialTransport('FAKE')
            t.exchange(frame(bytes.fromhex('010600000001')))
        self.assertEqual(pending[0],0)
