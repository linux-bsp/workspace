import unittest


class IntervalTests(unittest.TestCase):
    def make(self):
        from .schedule import IntervalBook
        self.clock = [0.0]
        self.wall = [100.0]
        return IntervalBook(clock=lambda:self.clock[0],wall_clock=lambda:self.wall[0])

    def test_immediate_start_duration_and_two_rounds(self):
        book=self.make()
        book.add(2,True,[(1,1)],0,5,1)
        book.add(3,False,[(1,1)],0)
        book.start(True,2,100)
        self.assertEqual([p.due for p in book.history],[100,102])
        first=book.ready(100,True)
        self.assertIsNotNone(first)
        book.complete(first,dict(success=1,failure=0,skipped=0))
        self.assertEqual(first.state,'持续中')
        self.clock[0]=1
        self.assertIsNone(book.ready(101,True))
        self.clock[0]=2;self.wall[0]=102
        second=book.ready(102,True)
        self.assertEqual(first.state,'完成')
        book.complete(second,dict(success=1,failure=0,skipped=0))
        self.clock[0]=5;self.wall[0]=105
        third=book.ready(105,True)
        self.assertEqual(len(book.history),4)
        self.assertIsNot(first,third)
        self.assertEqual((first.state,first.due),('完成',100))
        self.assertEqual([p.due for p in book.history],[100,102,105,107])
        book.complete(third,dict(success=1,failure=0,skipped=0))
        self.clock[0]=7;self.wall[0]=107
        fourth=book.ready(107,True)
        book.complete(fourth,dict(success=1,failure=0,skipped=0))
        self.clock[0]=9
        self.assertIsNone(book.ready(109,True));self.assertTrue(book.running)
        self.clock[0]=10
        self.assertIsNone(book.ready(110,True));self.assertFalse(book.running)
        self.assertTrue(all(p.state=='完成' for p in book.history))

    def test_slow_command_shifts_estimate_and_clock_jump_does_not_trigger(self):
        book=self.make();book.add(2,False,[(1,1)],0);book.add(3,False,[(1,1)],0)
        book.start(now=100);a=book.ready(100,True)
        self.clock[0]=4;self.wall[0]=104
        book.complete(a,dict(success=1,failure=0,skipped=0))
        self.assertEqual(book.history[1].due,106)
        self.clock[0]=5
        self.assertIsNone(book.ready(90000,True))
        self.clock[0]=6
        self.assertIsNotNone(book.ready(106,True))

    def test_stop_disconnect_and_restart_no_replay(self):
        book=self.make();book.add(2,False,[(1,1)],0);book.add(3,False,[(1,1)],0)
        book.start(True,2);a=book.ready(100,True)
        book.complete(a,dict(success=1,failure=0,skipped=0));book.disconnect()
        self.assertEqual([p.state for p in book.history],['已停止','已取消'])
        self.clock[0]=100
        self.assertIsNone(book.ready(200,True))
        book.start(now=200)
        self.assertIsNotNone(book.ready(200,True))
        self.assertEqual(len(book.history),2)

    def test_failure_not_pass_and_final_duration(self):
        book=self.make();book.add(2,False,[(1,1)],0);book.start()
        a=book.ready(100,True);book.complete(a,dict(success=0,failure=1,skipped=0))
        self.assertEqual(a.state,'失败 / 未完成')
        self.clock[0]=2;book.ready(102,True)
        self.assertFalse(book.running);self.assertEqual(a.state,'失败 / 未完成')

    def test_stop_during_command_cannot_claim_completed_duration(self):
        book=self.make();book.add(2,False,[(1,1)],0);book.start()
        row=book.ready(100,True);book.stop()
        book.complete(row,dict(success=1,failure=0,skipped=0))
        self.assertEqual(row.state,'已停止')
        self.assertIsNone(book.ready(999,True))

    def test_validation_and_offline_stop(self):
        book=self.make();p=book.add(2,False,[(1,1)],0)
        for count in (0,10000,-1):
            with self.assertRaises(ValueError):book.start(True,count)
        book.start(True,2)
        with self.assertRaises(ValueError):book.edit(p,3,False,[(1,1)],0)
        self.assertIsNone(book.ready(100,False));self.assertFalse(book.running)
        self.assertEqual(book.history[0].state,'已取消')

from .schedule import ScheduleBook


class ScheduleTests(unittest.TestCase):
    def test_interval_starts_now_and_ends_off(self):
        book=ScheduleBook()
        book.add_interval(100,120,60,3,[(1,1)],5,1,(6,2,True,True))
        self.assertEqual([p.due for p in book.plans],[100,220,280,400,460,580])
        self.assertEqual([p.enabled for p in book.plans],[True,False]*3)
        self.assertIs(book.ready(100,True),book.plans[0])
        with self.assertRaises(ValueError):
            book.add_interval(200,120,60,1,[(1,1)],5,1,None)
        self.assertEqual(len(book.plans),6)

    def test_edit_sorts_and_preserves_identity(self):
        book=ScheduleBook()
        later=book.add(130,False,[(1,1)],100)
        earlier=book.add(110,False,[(1,2)],100)
        self.assertEqual(book.plans,[earlier,later])
        book.edit(later,105,True,[(2,1)],100,5,1,(6,2,True,True))
        self.assertIs(book.plans[0],later)
        self.assertEqual((later.targets,later.voltage),(((2,1),),5))
        with self.assertRaises(ValueError):
            book.edit(later,110,False,[(1,1)],100)
        self.assertEqual(later.due,105)
        later.state='执行中'
        with self.assertRaises(ValueError):
            book.edit(later,140,False,[(1,1)],100)

    def test_partial_failure_keeps_channel_reason(self):
        book=ScheduleBook()
        plan=book.add(110,True,[(1,1),(1,2)],100,12,2)
        book.complete(plan,dict(success=1,failure=1,skipped=0,channels=[dict(address=1,channel=2,state='未知',detail='核对超时')]))
        self.assertEqual(plan.state,'部分失败')
        self.assertIn('1/CH2 未知：核对超时',plan.detail)
        self.assertIsNone(book.ready(111,True))

    def test_program_setpoints_are_frozen(self):
        book = ScheduleBook()
        plan = book.add(110,True,[(1,1)],100,12.5,2.25,(20.0,5.0,True,True))
        self.assertEqual((plan.voltage,plan.current,plan.protection),(12.5,2.25,(20.0,5.0,True,True)))
        with self.assertRaises(ValueError):
            book.add(120,True,[(1,1)],100)

    def test_target_snapshot_and_once(self):
        book = ScheduleBook()
        targets = [(1,1),(1,2)]
        plan = book.add(110,True,targets,100,12.0,2.0)
        targets.clear()
        self.assertIsNone(book.ready(109,True))
        self.assertIs(book.ready(110,True),plan)
        self.assertEqual(plan.targets,((1,1),(1,2)))
        self.assertIsNone(book.ready(111,True))
        book.complete(plan,dict(success=2,failure=0,skipped=0))
        self.assertEqual(plan.state,'完成')

    def test_missed_never_replays(self):
        book = ScheduleBook()
        plan = book.add(110,True,[(1,1)],100,12.0,2.0)
        self.assertIsNone(book.ready(113,True))
        self.assertEqual(plan.state,'未执行')
        self.assertIsNone(book.ready(110,True))

    def test_offline_or_busy_skips(self):
        book = ScheduleBook()
        plan = book.add(110,False,[(2,2)],100)
        self.assertIsNone(book.ready(110,False))
        self.assertEqual(plan.state,'未执行')
        self.assertIsNone(book.ready(111,True))

    def test_disconnect_cancels_waiting(self):
        book = ScheduleBook()
        plan = book.add(110,False,[(1,1)],100)
        book.disconnect()
        self.assertEqual(plan.state,'已取消')
        self.assertIsNone(book.ready(110,True))

    def test_invalid_time_targets_and_conflict(self):
        book = ScheduleBook()
        for due,targets in [(99,[(1,1)]),(110,[]),(110,[(256,1)]),(110,[(0,1)])]:
            with self.assertRaises(ValueError):
                book.add(due,True,targets,100)
        book.add(110,True,[(1,1)],100,12.0,2.0)
        with self.assertRaises(ValueError):
            book.add(111,False,[(2,1)],100)

    def test_cancel_and_failure(self):
        book = ScheduleBook()
        plan = book.add(110,True,[(1,1)],100,12.0,2.0)
        book.cancel(plan)
        self.assertIsNone(book.ready(110,True))
        plan = book.add(120,True,[(1,1)],100,12.0,2.0)
        book.ready(120,True)
        book.complete(plan,dict(success=0,failure=1,skipped=0))
        self.assertEqual(plan.state,'失败 / 未完成')

    def test_open_and_close_distinct_times(self):
        book = ScheduleBook()
        start = book.add(110,True,[(2,1)],100,12.0,2.0)
        stop = book.add(115,False,[(2,1)],100)
        self.assertTrue(book.ready(110,True).enabled)
        book.complete(start,dict(success=1,failure=0,skipped=0))
        self.assertFalse(book.ready(115,True).enabled)
        self.assertEqual(stop.state,'执行中')

