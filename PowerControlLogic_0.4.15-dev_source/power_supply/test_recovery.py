"""Approved short-disconnection behavior, using register-level simulation."""
import tempfile
import unittest
from pathlib import Path
from .core import Modbus, PowerService, Simulator, Settings, ResponseTimeout
from .schedule import Plan
from .recovery import Program, RecoveryWindow


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.clock = [0.0]
        self.wall = [100.0]
        self.path = Path(self.temp.name)/'program.jsonl'
        self.program = Program(self.path, clock=lambda:self.clock[0], wall=lambda:self.wall[0])
        self.sim = Simulator((1,2))
        self.service = PowerService(Modbus(self.sim))

    def on(self,due=100,targets=((1,1),)):
        return Plan(due,True,targets,5,1,(20,5,True,True))

    def off(self,due=110,targets=((1,1),)):
        return Plan(due,False,targets)

    def start(self,plans,mode='time',cycles=1):
        self.program.start(plans,mode,cycles,'TEST')

    def writes(self):
        return [r for r in self.sim.requests if r[1] in (6,16)]

    def test_window_is_absolute_and_retry_is_half_second(self):
        window=RecoveryWindow(lambda:self.clock[0]);self.assertEqual(window.begin(),5)
        self.clock[0]=2;self.assertEqual(window.begin(),5)
        window.retry();self.assertEqual(window.next_attempt,2.5)
        self.clock[0]=5;self.assertEqual(window.remaining(),0)

    def test_recovered_interval_highlights_current_and_completes_previous(self):
        a=self.on();a.delay_seconds=60;b=self.off();b.delay_seconds=60
        self.start([a,b],'interval',2)
        self.program.step(self.service)
        self.program.pause('重连核验中')
        self.program.verify(self.service,1)
        self.program.step(self.service)
        self.assertEqual(self.program.state['rows'][0]['state'],'持续中')
        self.clock[0]=65;self.program.step(self.service)
        self.assertEqual([p['state'] for p in self.program.state['rows']],['完成','持续中','等待','等待'])
        self.clock[0]=125;self.program.step(self.service)
        self.assertEqual([p['state'] for p in self.program.state['rows']],['完成','完成','持续中','等待'])
        self.clock[0]=245;self.program.step(self.service)
        self.assertTrue(all(p['state']=='完成' for p in self.program.state['rows']))
        self.assertEqual(self.program.state['status'],'已结束')

    def test_new_client_never_loads_previous_program(self):
        self.start([self.on()]);self.program.pause()
        new=Program(self.path)
        self.assertEqual(new.state['rows'],[])

    def test_restart_reads_whole_list_but_never_replays_past_time(self):
        plans=[self.on(90),self.off(110)]
        self.start(plans);self.program.step(self.service)
        self.assertEqual(self.writes(),[])
        self.assertEqual(self.program.state['rows'][0]['state'],'时间已过')
        first=self.program.state['run_id'];self.program.stop()
        self.wall[0]=120;self.start(plans);self.program.step(self.service)
        self.assertNotEqual(first,self.program.state['run_id'])
        self.assertEqual(self.writes(),[])
        self.assertTrue(all(r['state']=='时间已过' for r in self.program.state['rows']))
        self.assertEqual(self.program.state['status'],'已结束')

    def test_user_pause_finishes_current_duration_and_skips_expired_on_start(self):
        a=self.on();a.delay_seconds=10;b=self.off();b.delay_seconds=10
        self.start([a,b],'interval',2);self.program.step(self.service)
        self.clock[0]=3;self.program.request_pause()
        self.clock[0]=9;self.program.step(self.service)
        self.assertEqual(self.program.state['status'],'暂停中，当前时段继续')
        self.clock[0]=10;self.program.step(self.service)
        self.assertEqual(self.program.state['status'],'已暂停')
        self.assertEqual(self.program.state['rows'][0]['state'],'完成')
        self.assertEqual(self.sim.registers[1][0x109],0)
        count=len(self.writes());self.clock[0]=25
        self.program.verify(self.service,1,manual=True)
        self.program.step(self.service)
        self.assertEqual(len(self.writes()),count)
        self.assertEqual([r['state'] for r in self.program.state['rows']][1:3],['时间已过','时间已过'])
        self.clock[0]=30;self.program.step(self.service)
        self.assertEqual(self.sim.registers[1][0x109],1)

    def test_multiple_overdue_actions_only_align_final_off(self):
        self.start([self.on(),self.off()]);self.wall[0]=115
        self.program.step(self.service)
        self.assertEqual(self.writes(),[])
        self.assertEqual(self.program.state['rows'][0]['state'],'完成')
        self.assertEqual(self.program.state['rows'][0]['evidence']['1/1'],'执行情况未确认')
        self.assertIn('历史回读缺口保留',self.program.state['rows'][0]['detail'])
        self.assertEqual(self.program.state['status'],'已结束')

    def test_failed_device_cannot_inherit_other_devices_progress(self):
        self.start([self.on(targets=((1,1),(2,1))),self.off(targets=((1,1),(2,1)))])
        self.wall[0]=115;self.sim.offline.add(2)
        self.program.step(self.service)
        self.assertNotEqual(self.program.state['rows'][0]['state'],'完成')
        self.assertNotEqual(self.program.state['rows'][1]['state'],'完成')

    def test_pause_removes_current_highlight_but_preserves_completed_rows(self):
        a=self.on();a.delay_seconds=60;b=self.off();b.delay_seconds=60
        self.start([a,b],'interval',2)
        self.clock[0]=65;self.program.step(self.service)
        self.assertEqual(self.program.state['rows'][0]['state'],'完成')
        self.program.pause('重连核验中')
        self.assertEqual(self.program.state['rows'][0]['state'],'完成')
        self.assertEqual(self.program.state['rows'][1]['state'],'重连核验中')
        self.program.pause('待人工恢复')
        self.assertEqual(self.program.state['rows'][1]['state'],'待人工恢复')
        self.program.stop()
        self.assertEqual(self.program.state['rows'][1]['state'],'已取消')

    def test_current_on_applies_once_and_keeps_next_due(self):
        self.start([self.on(),self.off()]);self.wall[0]=105
        self.program.step(self.service);count=len(self.writes())
        self.program.step(self.service)
        self.assertEqual(len(self.writes()),count)
        self.assertEqual(self.sim.registers[1][0x109],0)
        self.assertEqual(self.program.state['rows'][1]['due'],110)

    def test_matching_state_needs_no_control_write(self):
        self.service.apply(1,1,Settings(5,1,20,5,True,True));self.service.output(1,1,True)
        self.sim.requests.clear();self.start([self.on()]);self.program.step(self.service)
        self.assertEqual(self.writes(),[])

    def test_per_channel_latest_goal_and_unmentioned_channel_untouched(self):
        self.start([self.on(targets=((1,1),(2,1))),self.off(targets=((1,1),))])
        self.wall[0]=115;self.program.step(self.service)
        self.assertEqual(self.sim.registers[1][0x109],1)
        self.assertEqual(self.sim.registers[2][0x109],0)
        self.assertEqual(self.sim.registers[2][0x113],1)

    def test_interval_keeps_timeline_and_ignores_wall_clock_jump(self):
        a=self.on();a.delay_seconds=60;b=self.off();b.delay_seconds=60
        self.start([a,b],'interval',2)
        self.clock[0]=65;self.wall[0]=50000
        self.program.step(self.service)
        self.assertEqual(self.writes(),[])
        self.assertEqual([r['due'] for r in self.program.state['rows']],[100,160,220,280])

    def test_late_verification_never_enables_program(self):
        self.start([self.on()]);self.program.pause('重连核验中')
        original=self.service.sample
        def slow(a,c):
            result=original(a,c);self.clock[0]=5.1;return result
        self.service.sample=slow
        with self.assertRaises(Exception):self.program.verify(self.service,1,5)
        self.assertNotEqual(self.program.state['devices']['1'],'运行中')
        self.assertEqual(self.writes(),[])

    def test_stop_cannot_be_revived(self):
        self.start([self.on()]);self.program.stop()
        self.program.verify(self.service,1,manual=True);self.program.step(self.service)
        self.assertEqual(self.program.state['devices']['1'],'已终止')
        self.assertEqual(self.writes(),[])
        self.assertEqual(self.program.state['rows'][0]['state'],'已取消')

    def test_protection_lock_requires_manual_recheck(self):
        self.start([self.on()]);self.program.latch(1,1)
        with self.assertRaises(Exception):self.program.verify(self.service,1)
        self.program.step(self.service);self.assertEqual(self.writes(),[])
        self.program.verify(self.service,1,manual=True);self.program.step(self.service)
        self.assertEqual(self.sim.registers[1][0x109],0)

    def test_bad_device_does_not_stop_good_device(self):
        self.start([self.on(targets=((1,1),(2,1)))]);self.sim.offline.add(1)
        self.program.step(self.service)
        self.assertEqual(self.program.state['devices']['1'],'待人工处理')
        self.assertEqual(self.sim.registers[2][0x109],0)

    def test_program_protection_read_failure_does_not_create_trip_lock(self):
        self.start([self.on(),self.off()])
        exchange=self.sim.exchange
        def drop(request):
            if request[1]==3 and request[2:4]==b'\x01\x20':
                raise ResponseTimeout('protection unavailable')
            return exchange(request)
        self.sim.exchange=drop
        self.service.bus.on_error=lambda error:self.program.pause('重连核验中')
        self.program.step(self.service)
        self.assertEqual(self.program.state['locks'],[])
        self.assertEqual(self.program.state['devices']['1'],'重连核验中')
        self.assertEqual(self.writes(),[])
        self.sim.exchange=exchange
        self.program.verify(self.service,1)
        self.program.step(self.service)
        self.assertEqual(self.sim.registers[1][0x109],0)

    def test_invalid_protection_values_pause_without_fabricating_trip(self):
        self.start([self.on(),self.off()])
        self.sim.registers[1][0x122]=2
        self.program.step(self.service)
        self.assertEqual(self.program.state['devices']['1'],'待人工处理')
        self.assertEqual(self.program.state['locks'],[])
        self.assertEqual(self.writes(),[])

    def test_each_write_rechecks_stage(self):
        self.start([self.on(),self.off()])
        exchange=self.sim.exchange
        def next_stage(request):
            response=exchange(request)
            if request[1] in (6,16):self.wall[0]=111
            return response
        self.sim.exchange=next_stage
        self.program.step(self.service);self.program.step(self.service)
        self.assertFalse(any(r[1]==6 and r[2:6]==b'\x01\x09\x00\x00' for r in self.writes()))

    def test_write_ack_loss_reads_back_without_duplicate(self):
        self.start([self.on()]);exchange=self.sim.exchange;lost=[]
        def drop(request):
            response=exchange(request)
            if request[1]==6 and request[2:4]==b'\x01\x09' and not lost:
                lost.append(True);raise ResponseTimeout('lost ack')
            return response
        self.sim.exchange=drop;self.program.step(self.service)
        self.assertEqual(sum(r[1]==6 and r[2:4]==b'\x01\x09' for r in self.writes()),1)
        self.assertEqual(self.program.state['devices']['1'],'已结束')
