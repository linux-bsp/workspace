import struct,unittest
from power_supply.core import Modbus,Simulator,PowerService,ProtocolError,frame
class RegisterDiagnostics(unittest.TestCase):
 def test_closed_link_does_not_attribute_prior_reply_to_failed_request(self):
  sim=Simulator((11,));records=[];exchange=sim.exchange
  def first(request):
   response=exchange(request);sim.last_exchange={'tx':request.hex(),'rx':response.hex()};return response
  sim.exchange=first;bus=Modbus(sim,lambda row:records.append(row) or True)
  bus.read(11,0x109,1)
  def closed(request):raise ProtocolError('closed before sending')
  sim.exchange=closed
  with self.assertRaises(ProtocolError):bus.read(11,0x109,1)
  self.assertFalse(records[-1].get('rx'))

 def test_first_state_read_recorded_once_and_again_when_recording_becomes_available(self):
  sim=Simulator((1,)); records=[]; enabled=[False]
  def record(item):
   if not enabled[0]:return False
   records.append(item);return True
  bus=Modbus(sim,record);bus.context={'action':'采样','channel':1}
  bus.read(1,0x101,10);self.assertEqual(records,[])
  enabled[0]=True;bus.read(1,0x101,10);bus.read(1,0x101,10)
  self.assertEqual(len(records),1);self.assertEqual(records[0]['register'],0x101)
 def test_state_change_records_new_value_not_repeated_unchanged(self):
  sim=Simulator((1,));records=[]
  def record(item):records.append(item);return True
  bus=Modbus(sim,record);bus.context={'action':'采样','channel':1}
  bus.read(1,0x101,10);bus.read(1,0x101,10);sim.registers[1][0x109]=0;bus.read(1,0x101,10)
  self.assertEqual(len(records),2)

 def test_state_evidence_contains_wire_frames_and_decoded_registers(self):
  sim=Simulator((11,)); records=[]
  bus=Modbus(sim,lambda row:records.append(row) or True)
  bus.context={'action':'采样','channel':1}
  bus.read(11,0x101,10)
  row=records[0]
  self.assertEqual(row['tx'],sim.requests[0].hex())
  self.assertEqual(row['registers']['0x0109'],1)
  self.assertEqual(row['output_state'],{'register':'0x0109','raw':1,'interpreted':'未使能'})
  self.assertEqual(bytes.fromhex(row['rx'])[:3],bytes([11,3,20]))
  self.assertEqual(len(sim.requests),1)

 def test_local_release_records_ack_without_any_readback_or_claim_of_panel_state(self):
  sim=Simulator((11,));sim.registers[11][0]=1; exchange=sim.exchange; records=[]
  def ignored(request):
   if request[1]==6:sim.requests.append(request);return request
   return exchange(request)
  sim.exchange=ignored
  bus=Modbus(sim,lambda row:records.append(row) or True);bus.context={'action':'退出远控'}
  PowerService(bus).local(11)
  self.assertEqual([r['phase'] for r in records],['local_write'])
  self.assertEqual(records[0]['verification'],'write_ack_only_no_followup_read')
  self.assertNotIn('registers',records[0])
  self.assertEqual(records[0]['tx'],records[0]['rx'])
  self.assertEqual(len(sim.requests),1)

 def test_real_tcp_transport_frames_reach_recording_file(self):
  import tempfile,json
  from unittest.mock import patch,MagicMock
  from pathlib import Path
  from power_supply.tcp_bus import TcpTransport,TcpEndpoint
  from power_supply.runtime import RecordingController
  sim=Simulator((11,)); sock=MagicMock();buffer=[b'']
  sock.sendall.side_effect=lambda request:buffer.__setitem__(0,sim.exchange(request))
  def recv(count):
   data=buffer[0][:count];buffer[0]=buffer[0][count:];return data
  sock.recv.side_effect=recv
  with tempfile.TemporaryDirectory() as folder,patch('power_supply.tcp_bus.socket.create_connection',return_value=sock),patch('power_supply.tcp_bus.select.select',return_value=([],[],[])):
   transport=TcpTransport(TcpEndpoint('192.0.2.1',4008));recording=RecordingController(folder,'TEST',True)
   bus=Modbus(transport,recording.diagnostic);bus.context={'action':'采样','channel':1};bus.recording_generation=lambda:recording.generation
   bus.read(11,0x101,10);bus.read(11,0x101,10)
   sim.registers[11][0x109]=0;bus.read(11,0x101,10)
   paths=list(Path(folder).glob('*/communication.jsonl'));records=[json.loads(v) for v in paths[0].read_text(encoding='utf-8').splitlines()]
   self.assertEqual([r['output_state']['raw'] for r in records],[1,0]);self.assertTrue(all(r['tx'] and r['rx'] for r in records))
   self.assertTrue(all(r['transport']=='TCP RTU' and r['started_at'] for r in records))
   recording.set_enabled(False);recording.sync();bus.read(11,0x101,10)
   recording.set_enabled(True);bus.read(11,0x101,10);recording.close();transport.close()
   self.assertEqual(len(list(Path(folder).glob('*/communication.jsonl'))),2)

 def test_real_serial_transport_preserves_state_frames_and_bad_crc(self):
  from unittest.mock import patch
  from power_supply.test_serial import SendCompletionTests
  from power_supply.serial_bus import SerialTransport
  sim=Simulator((11,));port=SendCompletionTests().port();buffer=[b''];records=[]
  def write(request):buffer[0]=sim.exchange(request);return len(request)
  port.write.side_effect=write;port.waitForReadyRead.return_value=True;port.readAll.side_effect=lambda:buffer[0]
  with patch('power_supply.serial_bus.QSerialPort',return_value=port):
   transport=SerialTransport('FAKE');bus=Modbus(transport,lambda r:records.append(r) or True);bus.context={'action':'采样','channel':2}
   bus.read(11,0x10b,10)
   self.assertEqual(records[0]['registers']['0x0113'],1)
   self.assertEqual(records[0]['tx'],sim.requests[0].hex());self.assertEqual(records[0]['rx'],buffer[0].hex())
   port.readAll.side_effect=lambda:buffer[0][:-1]+bytes([buffer[0][-1]^1])
   with self.assertRaises(ProtocolError):bus.read(11,0x10b,10)
   self.assertIn('CRC',records[-1]['error']);self.assertTrue(records[-1]['rx'])
   transport.close()

 def test_rotation_and_record_failure_do_not_claim_success(self):
  import tempfile,json
  from pathlib import Path
  from unittest.mock import patch
  from power_supply.runtime import Recorder,RecordingController
  with tempfile.TemporaryDirectory() as folder:
   r=Recorder(folder,'TEST')
   for i in range(5):
    (r.path/'communication.jsonl').write_bytes(b' '* (10*1024*1024))
    r.diagnostic({'index':i})
   self.assertEqual(len(list(r.path.glob('communication*.jsonl'))),4)
   self.assertEqual(json.loads((r.path/'communication.jsonl').read_text())['index'],4);r.close()
   errors=[];c=RecordingController(folder,'TEST',True,on_error=errors.append);c.sync()
   with patch.object(c.recorder,'diagnostic',side_effect=OSError('disk full')):
    self.assertFalse(c.diagnostic({'sample':1}))
   self.assertEqual(errors,['disk full']);self.assertFalse(c.requested.is_set())
