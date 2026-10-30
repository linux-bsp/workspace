"""Real QThread + faulted transport. No physical connections."""
import tempfile
import time
import unittest
from pathlib import Path
from PySide6.QtCore import QCoreApplication
from .core import Simulator, ProtocolError, ResponseTimeout, Settings
from .devices import Device
from .runtime import Worker
from .schedule import Plan


class Link:
    def __init__(self, simulator):
        self.simulator=simulator
        self.closed=False
        self.fail=False
        self.drop_write=False
        self.fail_protection=False
        self.deadline=None

    def exchange(self,request):
        if self.closed:raise ProtocolError('closed')
        if self.fail:
            self.closed=True;raise ResponseTimeout('Wi-Fi interrupted')
        if self.fail_protection and request[1]==3 and request[2:4]==b'\x01\x20':
            self.fail_protection=False
            self.closed=True;raise ResponseTimeout('protection read interrupted')
        result=self.simulator.exchange(request)
        if self.drop_write and request[1]==6 and request[2:4]==b'\x01\x09':
            self.drop_write=False;self.closed=True;raise ResponseTimeout('write acknowledged too late')
        return result

    def close(self):self.closed=True


class WorkerRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QCoreApplication.instance() or QCoreApplication([])

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.sim=Simulator((1,));self.links=[];self.refuse=False
        def factory():
            if self.refuse:raise ProtocolError('Wi-Fi unavailable')
            link=Link(self.sim);self.links.append(link);return link
        self.worker=Worker('TEST',self.temp.name,devices=[Device('one',1)],recording=False,transport_factory=factory)
        self.messages=[];self.snapshots=[];self.results=[]
        self.worker.recovery_changed.connect(self.messages.append)
        self.worker.program_changed.connect(self.snapshots.append)
        self.worker.operation_done.connect(self.results.append)
        self.addCleanup(self.shutdown)

    def shutdown(self):
        self.worker.requestInterruption();self.assertTrue(self.worker.wait(7000))
        self.app.processEvents()

    def wait_for(self,predicate,timeout=3):
        end=time.monotonic()+timeout
        while time.monotonic()<end:
            self.app.processEvents()
            if predicate():return
            time.sleep(.01)
        self.fail('condition timed out; '+str(self.messages))

    def start_program(self):
        self.worker.start();self.wait_for(lambda:bool(self.links))
        now=time.time()+.3
        self.worker.program_request('start',([Plan(now,True,((1,1),),5,1,(20,5,True,True)),Plan(now+60,False,((1,1),))],'time',1))
        self.wait_for(lambda:self.sim.registers[1][0x109]==0)

    def test_wifi_reconnect_keeps_program_and_does_not_repeat_on(self):
        self.start_program()
        due=self.worker.program.state['rows'][1]['due']
        before=len([r for r in self.sim.requests if r[1] in (6,16)])
        self.links[0].fail=True
        self.wait_for(lambda:any(m.startswith('连接恢复') for m in self.messages))
        self.wait_for(lambda:self.worker.program.state['devices']['1']=='运行中')
        self.assertEqual(len([r for r in self.sim.requests if r[1] in (6,16)]),before)
        self.assertEqual(self.worker.program.state['rows'][1]['due'],due)
        self.assertEqual(len(self.links),2)

    def test_five_second_failure_stops_attempts_and_pauses(self):
        self.start_program();self.refuse=True;self.links[0].fail=True
        self.wait_for(lambda:any('5秒' in m for m in self.messages))
        began=time.monotonic()
        self.wait_for(lambda:not self.worker.isRunning(),7)
        elapsed=time.monotonic()-began
        self.assertLess(elapsed,5.6)
        self.assertGreater(elapsed,4.5)
        self.assertEqual(self.worker.program.state['devices']['1'],'待人工恢复')

    def test_protection_read_timeout_recovers_without_false_trip_or_replay(self):
        self.worker.set_recording(True)
        samples=[];self.worker.sample_ready.connect(samples.append)
        self.start_program()
        # Inject during periodic sampling, after the initial program alignment
        # has finished its own protection reads.
        self.wait_for(lambda:self.worker.program.state['rows'][0]['evidence'].get('1/1')=='回读确认')
        due=self.worker.program.state['rows'][1]['due']
        before=len([r for r in self.sim.requests if r[1] in (6,16)])
        self.links[0].fail_protection=True
        self.wait_for(lambda:any(m.startswith('连接恢复') for m in self.messages))
        self.wait_for(lambda:self.worker.program.state['devices']['1']=='运行中')
        self.assertEqual(self.worker.program.state['locks'],[])
        self.assertEqual(len([r for r in self.sim.requests if r[1] in (6,16)]),before)
        self.assertEqual(self.worker.program.state['rows'][1]['due'],due)
        self.assertTrue(any(r.get('protection_error') and r['status']=='ERROR' for r in samples))
        events=list(Path(self.temp.name).glob('*/events.jsonl'))
        self.assertTrue(any('连接恢复' in p.read_text(encoding='utf-8') for p in events))

    def test_manual_write_loss_never_replays_after_reconnect(self):
        self.worker.start();self.wait_for(lambda:bool(self.links))
        self.links[0].drop_write=True
        self.worker.submit('output',[(1,1)],True)
        self.wait_for(lambda:any(m.startswith('连接恢复') for m in self.messages))
        writes=[r for r in self.sim.requests if r[1]==6 and r[2:4]==b'\x01\x09']
        self.assertEqual(len(writes),1)
        self.assertEqual(self.sim.registers[1][0x109],0)

    def test_recovery_protection_timeout_can_retry_inside_same_window(self):
        self.start_program()
        original=self.worker.transport_factory
        def factory():
            link=original()
            if len(self.links)==2:link.fail_protection=True
            return link
        self.worker.transport_factory=factory
        self.links[0].fail=True
        self.wait_for(lambda:any(m.startswith('连接恢复') for m in self.messages))
        self.assertEqual(len(self.links),3)
        self.assertEqual(self.worker.program.state['locks'],[])
        self.assertEqual(self.worker.program.state['devices']['1'],'运行中')

    def test_real_threshold_trip_stays_latched_after_normal_reconnect(self):
        self.start_program()
        # Simulated measured voltage follows the setpoint. Lower OVP below it.
        self.sim.registers[1][0x124]=4000
        self.wait_for(lambda:[1,1] in self.worker.program.state['locks'])
        self.wait_for(lambda:self.sim.registers[1][0x109]==1)
        self.sim.registers[1][0x124]=20000
        before=len([r for r in self.sim.requests if r[1] in (6,16)])
        self.links[0].fail=True
        self.wait_for(lambda:not self.worker.isRunning(),7)
        self.assertEqual(self.worker.program.state['locks'],[[1,1]])
        self.assertEqual(self.worker.program.state['devices']['1'],'待人工处理')
        self.assertEqual(len([r for r in self.sim.requests if r[1] in (6,16)]),before)

    def test_stop_during_reconnect_cannot_resume(self):
        self.start_program();self.links[0].fail=True;self.refuse=True
        self.wait_for(lambda:bool(self.messages))
        self.worker.program_request('stop');self.refuse=False
        self.wait_for(lambda:not self.worker.isRunning() or self.worker.program.state['devices']['1']=='已终止',7)
        if self.worker.isRunning():
            self.assertEqual(self.worker.program.state['devices']['1'],'已终止')
        else:
            self.assertEqual(self.worker.program.state['status'],'已停止')

    def test_active_disconnect_does_not_reconnect(self):
        self.start_program();self.worker.requestInterruption()
        self.wait_for(lambda:not self.worker.isRunning())
        self.assertEqual(len(self.links),1)
        self.assertEqual(self.worker.program.state['devices']['1'],'待人工恢复')

    def test_queued_manual_command_is_discarded_on_fault(self):
        from .recovery import Program
        self.worker.program=Program(Path(self.temp.name)/'queued.jsonl')
        self.worker.submit('output',[(1,1)],True)
        self.worker.connection_fault(ResponseTimeout('lost before send'))
        self.assertTrue(self.worker.commands.empty())
        self.assertEqual(self.results[-1]['skipped'],1)
        with self.assertRaises(ValueError):self.worker.submit('output',[(1,1)],True)
        self.assertFalse(self.sim.requests)

    def test_rejected_resume_always_acknowledges_request(self):
        done=[];self.worker.program_request_done.connect(lambda:done.append(True))
        self.worker.start();self.wait_for(lambda:bool(self.links))
        for expected in (1,2):
            self.worker.program_request('resume')
            self.wait_for(lambda:len(done)==expected)
        self.assertTrue(self.worker.isRunning())

    def test_unreachable_second_device_does_not_block_first(self):
        from .recovery import Program
        from .recovery import RecoveryWindow
        simulator=Simulator((1,2)); links=[]
        class Partial(Link):
            def exchange(self,request):
                if request[0]==2:
                    self.closed=True;raise ResponseTimeout('second unavailable')
                return super().exchange(request)
        def factory():
            link=Partial(simulator);links.append(link);return link
        worker=Worker('TEST',self.temp.name,devices=[Device('a',1),Device('b',2)],recording=False,transport_factory=factory)
        worker.program=Program(Path(self.temp.name)/'multi.jsonl')
        worker.program.start([Plan(time.time(),False,((1,1),(2,1)))],'time',1,'TEST')
        worker.connection_fault(ResponseTimeout('lost'))
        link,service=worker.reconnect(None)
        try:
            self.assertEqual(worker.program.state['devices']['1'],'运行中')
            self.assertEqual(worker.program.state['devices']['2'],'待人工恢复')
            self.assertEqual(worker.unavailable_addresses,{2})
        finally:link.close()
