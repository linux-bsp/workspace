"""Offline worker integration checks; no physical serial port is opened."""
import tempfile
import time
import unittest
from pathlib import Path
from PySide6.QtCore import QCoreApplication
from .core import PowerService, Settings, Simulator, ResponseTimeout
from .devices import Device
from .runtime import Worker


class WorkerTests(unittest.TestCase):
    def test_one_failed_channel_does_not_block_remaining(self):
        app=QCoreApplication.instance() or QCoreApplication([])
        bus=Simulator((7,8));original=bus.exchange
        def exchange(request):
            if request[0]==7 and request[1]==16 and request[2:4]==b'\x01\x0b':
                raise ResponseTimeout('lost settings write')
            return original(request)
        bus.exchange=exchange
        with tempfile.TemporaryDirectory() as root:
            worker=Worker('TEST',root,devices=[Device('A',7),Device('B',8)],transport_factory=lambda:bus)
            results=[];worker.operation_done.connect(results.append)
            worker.submit('program_on',[(7,1),(7,2),(8,1)],Settings(12,2,20,5,True,True))
            worker.start()
            try:
                until=time.monotonic()+5
                while time.monotonic()<until and not results:app.processEvents();time.sleep(.01)
                self.assertTrue(results)
                self.assertEqual([r['state'] for r in results[0]['channels']],['成功','失败','成功'])
                self.assertEqual(bus.registers[7][0x113],1)
                self.assertEqual(bus.registers[8][0x109],0)
            finally:worker.requestInterruption();self.assertTrue(worker.wait(3000))
            self.assertTrue(list(Path(root).glob('*/communication.jsonl')))

    def test_program_applies_setpoints_then_connects(self):
        app = QCoreApplication.instance() or QCoreApplication([])
        bus = Simulator((7,))
        test_dir = Path(__file__).resolve().parents[1]/'.tmp'
        test_dir.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=test_dir) as root:
            worker = Worker('TEST',root,devices=[Device('测试',7)],recording=False,
                            transport_factory=lambda:bus)
            results = []
            worker.operation_done.connect(results.append)
            worker.start()
            try:
                worker.submit('program_on',[(7,1)],Settings(12,2,20,5,True,True))
                until = time.monotonic()+6
                while time.monotonic()<until and not results:
                    app.processEvents()
                    time.sleep(.01)
                self.assertTrue(results)
                self.assertEqual(results[0]['success'],1)
                base,_ = PowerService.registers(1)
                self.assertEqual(bus.registers[7][base+8],0)
                self.assertEqual(bus.registers[7][base+1],12000)
                self.assertEqual(bus.registers[7][base+3],2000)
            finally:
                worker.requestInterruption()
                self.assertTrue(worker.wait(3000))

    def test_threshold_closes_output_and_records_event(self):
        app = QCoreApplication.instance() or QCoreApplication([])
        bus = Simulator((7,))
        test_dir = Path(__file__).resolve().parents[1]/'.tmp'
        test_dir.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=test_dir) as root:
            worker = Worker('TEST',root,devices=[Device('测试',7)],recording=True,
                            transport_factory=lambda:bus)
            results, samples = [],[]
            worker.operation_done.connect(results.append)
            worker.sample_ready.connect(samples.append)
            worker.start()
            try:
                worker.submit('program_on',[(7,1)],Settings(12,2,11,5,True,True))
                until = time.monotonic()+6
                while time.monotonic()<until and not any(r.get('protection_trip') for r in samples):
                    app.processEvents()
                    time.sleep(.01)
                self.assertTrue(results)
                self.assertEqual(results[0]['success'],1)
                self.assertTrue(any(r.get('protection_trip')=='已补关并回读' for r in samples))
                base,_ = PowerService.registers(1)
                self.assertEqual(bus.registers[7][base+8],1)
            finally:
                worker.requestInterruption()
                self.assertTrue(worker.wait(3000))
            self.assertTrue(any('客户端补发关闭输出' in p.read_text(encoding='utf-8')
                                for p in Path(root).glob('*/events.jsonl')))
