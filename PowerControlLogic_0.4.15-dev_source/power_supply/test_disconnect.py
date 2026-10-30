"""Offline disconnect contract; never opens a device."""
import tempfile,unittest,struct
from PySide6.QtCore import QCoreApplication
from .core import Simulator,PowerService,Modbus,ProtocolError
from .runtime import Worker
from .devices import Device

class StoppingWorker(Worker):
    def isInterruptionRequested(self):return True

class LocalTests(unittest.TestCase):
    def setUp(self):self.app=QCoreApplication.instance() or QCoreApplication([])
    def test_disconnect_stays_local_when_a_query_activates_remote_mode(self):
        bus=Simulator((1,7));exchange=bus.exchange;messages=[]
        def query_enters_remote(request):
            if request[1]==3:bus.registers[request[0]][0]=1
            return exchange(request)
        bus.exchange=query_enters_remote
        with tempfile.TemporaryDirectory() as root:
            worker=StoppingWorker('TEST',root,devices=[Device('A',1),Device('B',7)],recording=False,transport_factory=lambda:bus)
            worker.message.connect(messages.append);worker.run()
        self.assertEqual([bus.registers[a][0] for a in (1,7)],[0,0])
        self.assertEqual([p[1] for p in bus.requests],[6,6])
        self.assertFalse(any('已回读本地模式' in m for m in messages))

    def test_local_timeout_sends_once_and_never_reads_to_verify(self):
        from .core import ResponseTimeout,StateUnknown
        bus=Simulator((1,));requests=[]
        def timeout(request):
            requests.append(request);raise ResponseTimeout('late response')
        bus.exchange=timeout
        with self.assertRaises(StateUnknown):PowerService(Modbus(bus)).local(1)
        self.assertEqual(len(requests),1)
        self.assertEqual(requests[0][1],6)

    def test_disconnect_releases_each_address_before_close_without_output_write(self):
        bus=Simulator((1,7));closed=[]
        for memory in bus.registers.values():memory[0]=1;memory[0x109]=0;memory[0x113]=0
        before={a:dict(m) for a,m in bus.registers.items()}
        bus.close=lambda:closed.append([bus.registers[a][0] for a in (1,7)])
        with tempfile.TemporaryDirectory() as root:
            worker=StoppingWorker('TEST',root,devices=[Device('A',1),Device('B',7)],recording=False,transport_factory=lambda:bus)
            worker.run()
        self.assertEqual(closed,[[0,0]])
        for a,memory in bus.registers.items():
            self.assertEqual({r:v for r,v in memory.items() if r!=0},{r:v for r,v in before[a].items() if r!=0})
        writes=[p for p in bus.requests if p[1] in (6,16)]
        self.assertEqual([(p[0],struct.unpack('>HH',p[2:6])) for p in writes],[(1,(0,0)),(7,(0,0))])
    def test_already_local_release_does_not_query_and_reactivate_remote(self):
        bus=Simulator((1,));PowerService(Modbus(bus)).local(1)
        self.assertEqual(len(bus.requests),1)
        self.assertEqual(bus.requests[0][1:6],b'\x06\0\0\0\0')
    def test_closed_transport_does_not_reconnect_or_write(self):
        bus=Simulator((1,));bus.closed=True;errors=[]
        with tempfile.TemporaryDirectory() as root:
            worker=StoppingWorker('TEST',root,devices=[Device('A',1)],recording=False,transport_factory=lambda:bus)
            worker.failed.connect(errors.append);worker.run()
        self.assertEqual(bus.requests,[]);self.assertTrue(any('远控' in e for e in errors))
    def test_mismatched_local_ack_is_failure_without_readback(self):
        from .core import frame
        bus=Simulator((1,));bus.registers[1][0]=1;exchange=bus.exchange
        def ignore_write(request):
            if request[1]==6:bus.requests.append(request);return frame(request[:5]+b'\x01')
            return exchange(request)
        bus.exchange=ignore_write
        with self.assertRaises(ProtocolError):PowerService(Modbus(bus)).local(1)
        self.assertEqual(sum(p[1]==6 for p in bus.requests),1)
        self.assertEqual(len(bus.requests),1)

    def test_one_device_release_failure_does_not_skip_other_device(self):
        bus=Simulator((1,7));bus.offline.add(1);bus.registers[7][0]=1;errors=[]
        with tempfile.TemporaryDirectory() as root:
            worker=StoppingWorker('TEST',root,devices=[Device('A',1),Device('B',7)],recording=True,transport_factory=lambda:bus)
            worker.failed.connect(errors.append);worker.run()
            logs=''.join(p.read_text(encoding='utf-8') for p in __import__('pathlib').Path(root).glob('*/events.jsonl'))
        self.assertTrue(errors);self.assertIn('退出远控未确认',logs)
        self.assertEqual(bus.registers[7][0],0)
