import csv
import tempfile
import unittest
from pathlib import Path
from .core import Modbus, PowerService, ProtocolError, Settings, Simulator, frame
from .runtime import Recorder, Worker


class PowerTests(unittest.TestCase):
    def setUp(self):
        self.transport = Simulator()
        self.service = PowerService(Modbus(self.transport))
        self.settings = Settings(12, 2, 30, 10, True, True)

    def test_initial_on_report_stays_unconfirmed_until_explicit_control_readback(self):
        self.transport.registers[1][0x109]=0
        for unused in range(2):
            row=self.service.sample(1,1)
            self.assertEqual(row['output'],'开启')
            self.assertEqual(row['output_raw'],0)
            self.assertFalse(row['output_command_confirmed'])
        self.assertTrue(all(r[1]==3 for r in self.transport.requests))
        self.service.output(1,1,False)
        self.assertTrue(self.service.sample(1,1)['output_command_confirmed'])
        self.service.output(1,1,True)
        self.assertTrue(self.service.sample(1,1)['output_command_confirmed'])
        self.assertFalse(self.service.sample(1,2)['output_command_confirmed'])
        reconnected=PowerService(Modbus(self.transport))
        self.assertFalse(reconnected.sample(1,1)['output_command_confirmed'])

    def test_external_output_change_invalidates_prior_control_evidence(self):
        self.service.output(1,1,True)
        self.transport.registers[1][0x109]=1
        self.assertFalse(self.service.sample(1,1)['output_command_confirmed'])
        self.transport.registers[1][0x109]=0
        self.assertFalse(self.service.sample(1,1)['output_command_confirmed'])


    def test_document_crc_vectors(self):
        self.assertEqual(frame(bytes.fromhex('01 03 00 1D 00 02')).hex(), '0103001d0002540d')
        self.assertEqual(frame(bytes.fromhex('01 06 00 00 00 01')).hex(), '010600000001480a')

    def test_four_independent_channels_and_power(self):
        self.service.apply(2, 2, self.settings)
        self.assertEqual(self.service.settings(2, 2), self.settings)
        self.assertEqual(self.service.sample(2, 2)['output'], '关闭')
        self.service.output(2, 2, True)
        self.assertEqual(self.service.sample(2, 2)['power'], 24)
        self.assertEqual(self.service.sample(1, 1)['voltage'], 0)
        self.assertEqual(self.service.sample(2, 1)['voltage'], 0)
        self.service.output(2, 2, False)
        self.assertEqual(self.service.sample(2, 2)['power'], 0)

    def test_wire_encoding_independent_literal(self):
        self.service.apply(1, 1, self.settings)
        payloads = [request[:-2].hex() for request in self.transport.requests]
        self.assertIn('0110012000020400002710', payloads)  # 10 A OCP => 10000 mA
        self.assertIn('0110012300020400007530', payloads)  # 30 V OVP => 30000 mV
        self.assertIn('0110010100040800002ee0000007d0', payloads)
        self.service.output(1, 1, True)
        self.assertIn('010601090000', [r[:-2].hex() for r in self.transport.requests])

    def test_limits_rejected_before_any_write(self):
        for value in (31, -1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                self.service.apply(1, 1, Settings(value,2,30,10,True,True))
        self.assertEqual(self.transport.requests, [])

    def test_non_independent_mode_rejects_writes(self):
        self.transport.registers[1][0x100] = 2
        with self.assertRaises(ProtocolError):
            self.service.output(1, 1, True)
        self.assertTrue(all(r[1] == 3 or r[2:4] == b'\x00\x00' for r in self.transport.requests))

    def test_corrupt_wrong_address_and_exception(self):
        for response in [b'bad', frame(bytes.fromhex('0203020000')), frame(bytes.fromhex('018302')),
                         frame(bytes.fromhex('0103040000')), frame(bytes.fromhex('0106020000'))]:
            transport = type('Transport', (), {'exchange': lambda _,r:response})()
            with self.assertRaises(ProtocolError):
                Modbus(transport).read(1, 0x100, 1)

    def test_write_timeout_never_retried(self):
        original = self.transport.exchange
        writes = []
        def exchange(request):
            if request[1] in (6,16):
                writes.append(request)
                raise ProtocolError('timeout')
            return original(request)
        self.transport.exchange = exchange
        with self.assertRaises(ProtocolError):
            self.service.apply(1,1,self.settings)
        self.assertEqual(len(writes),1)

    def test_lost_output_ack_readback_without_repeat_write(self):
        from .core import ResponseTimeout
        original = self.transport.exchange
        writes = []
        def exchange(request):
            result = original(request)
            if request[1] == 6 and request[2:4] == b'\x01\x09':
                writes.append(request)
                raise ResponseTimeout('lost ACK')
            return result
        self.transport.exchange = exchange
        self.service.output(1,1,True)
        self.assertEqual(self.service.sample(1,1)['output'],'开启')
        self.assertEqual(len(writes),1)

    def test_timeout_not_applied_and_unknown_are_distinct(self):
        from .core import ResponseTimeout, TargetNotReached, StateUnknown
        for readable,expected in [(True,TargetNotReached),(False,StateUnknown)]:
            sim=Simulator();writes=[]
            def exchange(request):
                if request[1] in (6,16):
                    writes.append(request)
                    raise ResponseTimeout('lost')
                if not readable:raise ResponseTimeout('read lost')
                return sim.exchange(request)
            bus=Modbus(type('Transport',(),{'exchange':staticmethod(exchange)})())
            with self.assertRaises(expected):bus.write(1,0x109,[0])
            self.assertEqual(len(writes),1)

    def test_read_retry_retains_error_count_and_is_bounded(self):
        from .core import ResponseTimeout
        sim=Simulator();calls=[];events=[]
        def exchange(request):
            calls.append(request)
            if len(calls)==1:raise ResponseTimeout('late')
            return sim.exchange(request)
        bus=Modbus(type('Transport',(),{'exchange':staticmethod(exchange)})(),events.append)
        self.assertEqual(bus.read(1,0x100,1),[0])
        self.assertEqual(bus.timeouts,1)
        self.assertEqual(len(calls),2)
        self.assertEqual(events[-1]['event'],'只读重试恢复')
        def offline(request):calls.append(request);raise ResponseTimeout('offline')
        bus.transport.exchange=offline
        with self.assertRaises(ResponseTimeout):bus.read(1,0x100,1)
        self.assertEqual(len(calls),4)
        bus.retry_allowed=lambda:False
        with self.assertRaises(ResponseTimeout):bus.read(1,0x100,1)
        self.assertEqual(len(calls),5)

    def test_off_output_protection_cache_never_used_when_on(self):
        self.service.sample(1,1)
        before=len(self.transport.requests)
        second=self.service.sample(1,1)
        self.assertFalse(second['protection_fresh'])
        self.assertEqual(len(self.transport.requests)-before,2)
        self.service.output(1,1,True)
        sample=self.service.sample(1,1)
        self.assertTrue(sample['protection_fresh'])

    def test_cancel_during_timeout_recovery_never_opens(self):
        from .core import ResponseTimeout
        original=self.transport.exchange;cancelled=[False]
        def exchange(request):
            response=original(request)
            if request[1]==6 and request[2:4]==b'\x00\x00':
                cancelled[0]=True
                raise ResponseTimeout('lost remote ACK')
            return response
        self.transport.exchange=exchange
        with self.assertRaisesRegex(ProtocolError,'取消'):
            self.service.output(1,1,True,cancelled=lambda:cancelled[0])
        self.assertEqual(self.transport.registers[1][0x109],1)

    def test_csv_failure_has_blank_measurement(self):
        with tempfile.TemporaryDirectory() as folder:
            recorder = Recorder(folder,'SIMULATION')
            recorder.sample(dict(time='2026-10-14T12:00:00+08:00',address=1,channel=1,status='ERROR',output='输出状态未知',error='timeout'))
            recorder.close()
            with (recorder.path/'samples.csv').open(encoding='utf-8-sig') as stream:
                row = next(csv.DictReader(stream))
            self.assertEqual(row['voltage'],'')
            self.assertEqual(row['source'],'SIMULATION')

    def test_reconnection_does_not_write(self):
        self.transport.offline.add(1)
        with self.assertRaises(ProtocolError):
            self.service.sample(1,1)
        self.transport.offline.clear()
        self.service.sample(1,1)
        self.assertTrue(all(r[1] == 3 for r in self.transport.requests))

    def test_ack_without_effect_fails_readback(self):
        original = self.transport.exchange
        def exchange(request):
            if request[1] == 16:
                return frame(request[:6])
            return original(request)
        self.transport.exchange = exchange
        with self.assertRaisesRegex(ProtocolError, '回读不一致'):
            self.service.apply(1,1,self.settings)

    def test_protection_and_output_polarity(self):
        self.service.apply(1,2,Settings(1,1,2,2,False,True))
        actual = self.service.settings(1,2)
        self.assertFalse(actual.ovp_enabled)
        self.assertTrue(actual.ocp_enabled)
        self.assertEqual(self.service.sample(1,2)['output'],'关闭')

    def test_forbidden_broadcast(self):
        with self.assertRaises(ValueError):
            Modbus(self.transport).write(0,0,[1])
        self.assertEqual(self.transport.requests,[])


if __name__ == '__main__':
    unittest.main()
