"""In-session power program timeline and bounded reconnect policy.

Only the bus worker mutates this object. The UI sends requests and receives copies.
"""
import json
import time
import uuid
from dataclasses import asdict
from pathlib import Path
from .core import Settings, ProtocolError


class RecoveryWindow:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.deadline = None
        self.next_attempt = 0

    def begin(self):
        if self.deadline is None:
            self.deadline = self.clock() + 5
        return self.deadline

    def remaining(self):
        return max(0, self.deadline - self.clock()) if self.deadline is not None else 0

    def retry(self):
        self.next_attempt = self.clock() + .5

    def clear(self):
        self.deadline = None
        self.next_attempt = 0


def protection_ok(row):
    if row.get('protection_error') or any(row.get(k) is None for k in
            ('voltage', 'current', 'ovp', 'ocp', 'ovp_enabled', 'ocp_enabled')):
        return False
    return not protection_tripped(row)


def protection_tripped(row):
    """Only measured threshold evidence can create a protection latch."""
    if row.get('protection_error'):
        return False
    return any(row.get(enabled) and row.get(value) is not None and
               row.get(limit) is not None and row[value] >= row[limit]
               for enabled, value, limit in (('ovp_enabled','voltage','ovp'),
                                              ('ocp_enabled','current','ocp')))


def matches(plan, row):
    if not plan['enabled']:
        return row.get('output') == '关闭'
    return (row.get('output') == '开启' and
            round(row.get('set_voltage', -1) * 1000) == round(plan['voltage'] * 1000) and
            round(row.get('set_current', -1) * 1000) == round(plan['current'] * 1000))


class Program:
    def __init__(self, path, clock=time.monotonic, wall=time.time):
        self.path = Path(path)
        self.clock, self.wall = clock, wall
        self.state = dict(version=1, run_id='', mode='time', rows=[], devices={}, locks=[],
                          status='未开始', end=0, recovered=False, endpoint='')
        self.anchor = None
        self.stop_requested = lambda: False
        self.notify = lambda snapshot: None
        self._seen_rows = {}
        self.pause_at = None

    def save(self, reason):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        updates = []
        seen = dict(self._seen_rows)
        for index, row in enumerate(self.state['rows']):
            encoded = json.dumps(row,ensure_ascii=False)
            if self._seen_rows.get(index) != encoded:
                updates.append(dict(execution_row=index+1,**row))
                seen[index] = encoded
        # Evidence only; never loaded to restore a program in another client session.
        with self.path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(dict(time=self.wall(), run_id=self.state['run_id'],
                                        event=reason, rows=updates,
                                        **{k:v for k,v in self.state.items() if k not in ('run_id','rows')}), ensure_ascii=False) + '\n')
            stream.flush()
        self._seen_rows = seen
        self.notify(json.loads(json.dumps(self.state)))

    def now(self):
        if self.state['mode'] == 'interval' and self.anchor is not None:
            return self.anchor[0] + self.clock() - self.anchor[1]
        return self.wall()

    def start(self, plans, mode, cycles, endpoint):
        if any(v not in ('已结束','已终止') for v in self.state['devices'].values()):
            raise ValueError('请先恢复或停止原程序')
        start = self.wall()
        rows = []
        due = start
        for cycle in range(cycles if mode == 'interval' else 1):
            for plan in plans:
                row = asdict(plan)
                row.update(state='等待', detail='', cycle=plan.cycle or (cycle + 1 if mode == 'interval' else 0),
                           evidence={}, due=due if mode == 'interval' else plan.due)
                row.pop('actual_started_at',None)
                row.pop('actual_completed_at',None)
                if mode == 'time' and plan.due < start:
                    row.update(state='时间已过',detail='本次开始时已过期，不执行')
                rows.append(row)
                if mode == 'interval':
                    due += plan.delay_seconds
        if not rows or len(rows) > 10000:
            raise ValueError('程序行数须为1–10000')
        self.state.update(run_id=uuid.uuid4().hex, mode=mode, rows=rows,
                          devices={str(a): '运行中' for p in rows for a, c in p['targets']},
                          status='运行中', end=due if mode == 'interval' else max(p['due'] for p in rows),
                          recovered=False, endpoint=str(endpoint))
        self._seen_rows.clear()
        self.pause_at = None
        self.anchor = (start, self.clock()) if mode == 'interval' else None
        self.save('程序开始；固定时间表')

    def request_pause(self):
        """Finish the already started segment; admit no later segment."""
        active = [r for r in self.state['rows'] if r['state'] in ('执行中','持续中')]
        self.pause_at = max((r['due']+r['delay_seconds'] for r in active),default=self.now())
        self.state['status'] = '暂停中，当前时段继续'
        self.save('用户请求暂停')
        self.finish_pause()

    def finish_pause(self):
        if self.pause_at is None or self.now() < self.pause_at:
            return False
        self.update_rows()
        for a,s in self.state['devices'].items():
            if s == '运行中':self.state['devices'][a] = '已暂停'
        self.state['status'] = '已暂停'
        self.save('当前时段结束，已暂停；输出保持')
        return True

    def pause(self, reason='待人工恢复', addresses=None):
        changed = False
        for a, status in self.state['devices'].items():
            if addresses is not None and int(a) not in addresses:
                continue
            if status == '待人工处理' and reason in ('待人工恢复','重连核验中'):
                continue
            if status not in ('已终止', '已结束') and status != reason:
                self.state['devices'][a] = reason
                changed = True
        if changed:
            self.state['status'] = reason
            self.state['recovered'] = True
            self.update_rows()
            self.save(reason)

    def stop(self):
        self.pause_at = None
        for a in self.state['devices']:
            if self.state['devices'][a] != '已结束':
                self.state['devices'][a] = '已终止'
        for p in self.state['rows']:
            if p['state'] in ('等待','执行中','持续中','重连核验中','待人工恢复','待人工处理','已暂停'):
                p['state'] = '已取消'
        self.state['status'] = '已停止'
        self.save('用户停止；不可恢复')

    def latch(self, address, channel):
        key = [address, channel]
        if key not in self.state['locks']:
            self.state['locks'].append(key)
            self.save('保护锁定')
        self.pause('待人工处理', {address})

    def latest(self, now=None):
        result = {}
        now = self.now() if now is None else now
        for i, plan in enumerate(self.state['rows']):
            if plan['state'] in ('时间已过','已取消'):
                continue
            if self.pause_at is not None and plan['due'] >= self.pause_at:
                continue
            if plan['due'] <= now:
                for a, c in plan['targets']:
                    result[a, c] = i
        return result

    def verify(self, service, address, deadline=None, manual=False, resume=True):
        rows = {}
        for channel in (1, 2):
            if self.stop_requested() or (deadline is not None and self.clock() >= deadline):
                raise ProtocolError('恢复核验已取消或超过5秒')
            service.protection_cache.pop((address, channel), None)
            row = service.sample(address, channel)
            if deadline is not None and self.clock() >= deadline:
                raise ProtocolError('核验返回超过5秒，不恢复控制')
            if not protection_ok(row):
                if protection_tripped(row):
                    self.latch(address, channel)
                    raise ProtocolError(f'{address}/CH{channel} 达到保护阈值，待人工处理')
                raise ProtocolError(f'{address}/CH{channel} 保护状态未确认：' +
                                    (row.get('protection_error') or '保护参数不完整'))
            rows[address, channel] = row
        if any(k[0] == address for k in self.state['locks']):
            if not manual:
                raise ProtocolError('存在保护锁定，待人工恢复')
            self.state['locks'] = [k for k in self.state['locks'] if k[0] != address]
        status = self.state['devices'].get(str(address))
        if resume and status not in (None, '已终止', '已结束'):
            self.resume_verified(address, manual=manual)
        self.save('人工核验通过' if manual else '重连核验通过')
        return rows

    def resume_verified(self, address, manual=False):
        if manual:
            self.pause_at = None
            for row in self.state['rows']:
                if row['due'] < self.now() and row['state'] not in ('完成','已取消','时间已过'):
                    # A finished action may continue its existing hold; never
                    # replay an unexecuted or uncertain action after a user pause.
                    confirmed = all(row['evidence'].get(f'{a}/{c}') in ('回读确认','恢复后状态确认') for a,c in row['targets'])
                    if not confirmed:row.update(state='时间已过',detail='再次开始时已过期，不补执行；原证据保留')
        for key, index in self.latest().items():
            if key[0] == address and not manual:
                self.state['rows'][index]['evidence'].pop(f'{key[0]}/{key[1]}', None)
        self.state['devices'][str(address)] = '运行中'
        self.state['recovered'] = True
        self.state['status'] = '运行中'

    def update_rows(self):
        """Display timeline progress separately from the unchanged readback evidence."""
        latest = self.latest()
        confirmed = ('回读确认', '恢复后状态确认')
        changed = False
        for index, plan in enumerate(self.state['rows']):
            if plan['due'] > self.now() or plan['state'] in ('已取消','完成','时间已过'):
                continue
            if self.pause_at is not None and plan['due'] >= self.pause_at:
                continue
            completed = []
            advanced = False
            for a, c in plan['targets']:
                key = f'{a}/{c}'
                own = plan['evidence'].get(key) in confirmed
                current = latest.get((a,c), index)
                later = (current > index and
                         self.state['devices'].get(str(a)) in ('运行中','已结束') and
                         self.state['rows'][current]['evidence'].get(key) in confirmed)
                completed.append(own or later)
                advanced |= later and not own
            complete = bool(completed) and all(completed)
            ongoing = self.state['mode'] == 'interval' and self.now() < plan['due']+plan['delay_seconds']
            statuses = {self.state['devices'].get(str(a)) for a,c in plan['targets']}
            state = '持续中' if complete and ongoing else ('完成' if complete else '执行情况未确认')
            if ongoing or not complete:
                for paused in ('待人工处理','待人工恢复','重连核验中'):
                    if paused in statuses:
                        state = paused
                        break
            detail = '\n'.join(f'{k} {v}' for k,v in plan['evidence'].items())
            if complete and advanced:
                detail += '\n后续阶段已核验并继续，按程序推进显示完成；历史回读缺口保留。'
            changed |= plan['state'] != state or plan['detail'] != detail
            plan.update(state=state, detail=detail)
        return changed

    def step(self, service):
        """Align each channel once. Every protocol write checks current phase."""
        if self.pause_at is not None and self.now() >= self.pause_at:
            if any(s=='运行中' for s in self.state['devices'].values()):self.finish_pause()
            return
        if not any(status == '运行中' for status in self.state['devices'].values()):
            return
        latest = self.latest()
        changed = False
        for i, plan in enumerate(self.state['rows']):
            if plan['state'] in ('时间已过','已取消'):continue
            if plan['due'] > self.now():
                break
            for a, c in plan['targets']:
                key = f'{a}/{c}'
                if latest.get((a, c)) != i and key not in plan['evidence']:
                    plan['evidence'][key] = '执行情况未确认'
                    changed = True
        for (a, c), index in latest.items():
            if self.stop_requested():
                break
            if self.state['devices'].get(str(a)) != '运行中':
                continue
            plan = self.state['rows'][index]
            key = f'{a}/{c}'
            if plan['evidence'].get(key) in ('回读确认', '恢复后状态确认'):
                continue
            def valid():
                return (not self.stop_requested() and self.state['devices'].get(str(a)) == '运行中'
                        and self.latest().get((a, c)) == index)
            old_guard = service.bus.write_allowed
            service.bus.write_allowed = valid
            service.bus.context = dict(action='程序状态对齐',run_id=self.state['run_id'],row_id=index+1,cycle=plan['cycle'],channel=c)
            writing = False
            try:
                plan['state'] = '执行中'
                self.save(f'开始核对 {a}/CH{c} 第{index+1}行')
                service.protection_cache.pop((a, c), None)
                row = service.sample(a, c)
                if protection_tripped(row):
                    self.latch(a, c)
                    continue
                if not protection_ok(row):
                    raise ProtocolError('保护状态未确认：' + (row.get('protection_error') or '保护参数不完整'))
                if any(k[0] == a for k in self.state['locks']):
                    self.pause('待人工处理', {a})
                    continue
                if not valid():
                    continue
                if not matches(plan, row):
                    plan['actual_started_at'] = self.wall()
                    self.save(f'准备对齐 {a}/CH{c} 第{index+1}行')
                    writing = True
                    if plan['enabled']:
                        settings = Settings(plan['voltage'], plan['current'], *plan['protection'])
                        service.apply(a, c, settings)
                        service.output(a, c, True, cancelled=lambda: not valid())
                    else:
                        service.output(a, c, False, cancelled=lambda: not valid())
                row = service.sample(a, c)
                if not matches(plan, row):
                    raise ProtocolError('恢复回读未达到目标')
                plan['evidence'][key] = '恢复后状态确认' if self.state['recovered'] else '回读确认'
                plan['actual_completed_at'] = self.wall()
                changed = True
            except Exception as error:
                if self.latest().get((a,c)) != index and not self.stop_requested():
                    continue
                if self.state['devices'].get(str(a)) == '重连核验中' and not writing:
                    continue
                plan['evidence'][key] = '执行情况未确认：' + str(error)
                # Do not re-send this failed correction, even if a later reconnect succeeds.
                self.pause('待人工处理', {a})
                changed = True
            finally:
                service.bus.write_allowed = old_guard
        changed |= self.update_rows()
        if changed:
            self.save('程序状态更新')
        if self.now() >= self.state['end']:
            final = self.latest()
            ended = False
            for a, status in list(self.state['devices'].items()):
                if status != '运行中':
                    continue
                targets = [(key, i) for key, i in final.items() if key[0] == int(a)]
                if all(self.state['rows'][i]['evidence'].get(f'{key[0]}/{key[1]}') in
                                   ('回读确认', '恢复后状态确认') for key, i in targets):
                    self.state['devices'][a] = '已结束'
                    ended = True
            if ended:
                self.state['status'] = ('结束，存在未完成阶段' if
                    any(p['state'] not in ('完成','时间已过') for p in self.state['rows']) else '已结束')
                self.save('设备程序结束')
