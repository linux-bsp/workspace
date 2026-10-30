"""One-shot output plans. Targets are captured; missed plans never replay."""
from dataclasses import dataclass, replace
import time
from .devices import valid_address


@dataclass
class Plan:
    due: float
    enabled: bool
    targets: tuple
    voltage: float | None = None
    current: float | None = None
    protection: tuple | None = None
    state: str = '等待'
    detail: str = ''
    delay_seconds: int = 0
    template_id: int = 0
    cycle: int = 0


class ScheduleBook:
    def __init__(self):
        self.plans = []
        self.history = []

    def expand(self, cycles, gap=60):
        """Materialize complete rounds; Start will execute this list once."""
        if not self.plans:raise ValueError('请先添加程序步骤')
        if not isinstance(cycles,int) or not 1 <= cycles or cycles*len(self.plans)>10000:
            raise ValueError('展开后程序须为1–10000行')
        period=0 if isinstance(self,IntervalBook) else max(p.due for p in self.plans)-min(p.due for p in self.plans)+gap
        if not isinstance(self,IntervalBook) and gap<2:raise ValueError('轮间隔至少2秒')
        self.plans = [replace(p,due=p.due+cycle*period,state='等待',detail='',template_id=0,cycle=cycle+1)
                      for cycle in range(cycles) for p in self.plans]
        self.history = []

    def add(self, due, enabled, targets, now, voltage=None, current=None, protection=None):
        targets = tuple(sorted(set(targets)))
        if due <= now:
            raise ValueError('请选择未来时间')
        if not targets or any(not valid_address(a) or c not in (1,2) for a,c in targets):
            raise ValueError('请勾选有效通道')
        for old in self.plans:
            if old.state=='等待' and abs(old.due-due) < 2:
                raise ValueError('同一总线的计划请至少间隔2秒')
        if enabled and (voltage is None or current is None or not 0 <= voltage <= 30 or not 0 <= current <= 10):
            raise ValueError('接通电源须设置 0–30 V、0–10 A')
        plan = Plan(due,bool(enabled),targets,voltage,current,protection)
        self.plans.append(plan)
        self.plans.sort(key=lambda p:p.due)
        return plan

    def edit(self, plan, due, enabled, targets, now, voltage=None, current=None, protection=None):
        if not any(p is plan for p in self.plans) or plan.state != '等待':
            raise ValueError('只能编辑等待中的计划')
        validation = ScheduleBook()
        validation.plans = [p for p in self.plans if p is not plan]
        updated = validation.add(due,enabled,targets,now,voltage,current,protection)
        for name in ('due','enabled','targets','voltage','current','protection'):
            setattr(plan,name,getattr(updated,name))
        self.plans.sort(key=lambda p:p.due)

    def add_interval(self, now, on_seconds, off_seconds, cycles, targets, voltage, current, protection):
        if any(p.state in ('等待','执行中') for p in self.plans):
            raise ValueError('请先完成或删除已有等待计划')
        if (not isinstance(cycles,int) or not 1 <= cycles <= 1000
                or not 60 <= on_seconds <= 604800 or not 60 <= off_seconds <= 604800):
            raise ValueError('接通/断开时长须为60秒至7天，次数1–1000')
        pending = ScheduleBook()
        for i in range(cycles):
            start = now+i*(on_seconds+off_seconds)
            pending.add(start,True,targets,now-1,voltage,current,protection)
            pending.add(start+on_seconds,False,targets,now-1,voltage,current,protection)
        self.plans.extend(pending.plans)
        self.plans.sort(key=lambda p:p.due)

    def ready(self, now, available):
        result = None
        for plan in sorted(self.plans, key=lambda p:p.due):
            if plan.state != '等待' or plan.due > now:
                continue
            if now-plan.due > 2:
                plan.state,plan.detail = '未执行','错过时间，不补发'
            elif not available or result is not None:
                plan.state,plan.detail = '未执行','断线或忙碌，不补发'
            else:
                plan.state = '执行中'
                result = plan
        return result

    def cancel(self, plan):
        if plan.state == '等待':
            plan.state,plan.detail = '已取消','用户取消'

    def disconnect(self):
        for plan in self.plans:
            if plan.state == '等待':
                plan.state,plan.detail = '已取消','连接结束，需重新添加'

    def invalidate(self, address):
        for plan in self.plans:
            if plan.state=='等待' and any(a==address for a,c in plan.targets):
                plan.state,plan.detail = '已取消','设备配置已删除'

    def complete(self, plan, result):
        plan.state = '完成' if result['failure']==0 and result['skipped']==0 else '失败 / 未完成'
        if result['success'] and (result['failure'] or result['skipped']):
            plan.state = '部分失败'
        plan.detail = f"成功 {result['success']}，失败 {result['failure']}，未执行 {result['skipped']}"
        for item in result.get('channels',()):
            plan.detail += f"\n{item['address']}/CH{item['channel']} {item['state']}：{item.get('detail','')}"


class IntervalBook(ScheduleBook):
    """Finite duration sequence, with separate templates and append-only run rows."""
    def __init__(self, clock=None, wall_clock=None):
        super().__init__()
        self.clock = clock or time.perf_counter
        self.wall_clock = wall_clock or time.time
        self.running = False
        self.loop = False
        self.index = 0
        self.cycle = 0
        self.deadline = None
        self.active = None
        self.holding = None
        self.history = []
        self.round_rows = []
        self.cycles = 1

    def add(self, seconds, enabled, targets, now, voltage=None, current=None, protection=None):
        if self.running or self.active:
            raise ValueError('请先停止计划')
        if not isinstance(seconds, int) or not 1 <= seconds <= 604800:
            raise ValueError('持续时间须为1秒至7天')
        plan = ScheduleBook().add(1, enabled, targets, 0, voltage, current, protection)
        plan.delay_seconds = seconds
        self.plans.append(plan)
        return plan

    def edit(self, plan, seconds, enabled, targets, now, voltage=None, current=None, protection=None):
        if self.running or self.active or not any(p is plan for p in self.plans):
            raise ValueError('请先停止计划')
        updated = IntervalBook().add(seconds, enabled, targets, now, voltage, current, protection)
        for name in ('enabled', 'targets', 'voltage', 'current', 'protection', 'delay_seconds'):
            setattr(plan, name, getattr(updated, name))
        plan.state, plan.detail = '等待', ''

    def _append_round(self, now):
        self.round_rows = []
        for template in self.plans:
            row = replace(template, due=now, state='等待', detail=f'第{self.cycle}轮；预计执行时间',
                          template_id=id(template), cycle=self.cycle)
            self.round_rows.append(row)
            now += row.delay_seconds
        self.history.extend(self.round_rows)

    def start(self, loop=False, cycles=1, now=None):
        if self.running or self.active or not self.plans:
            raise ValueError('请先添加计划并等待当前操作结束')
        if not isinstance(cycles, int) or not 1 <= cycles <= 9999:
            raise ValueError('循环次数须为1至9999')
        count = cycles if loop else 1
        if count * len(self.plans) > 10000:
            raise ValueError('本次执行记录最多10000行，请减少循环次数或项目数')
        self.running, self.loop, self.cycles = True, bool(loop), count
        self.index, self.cycle = 0, 1
        self.history = []
        self.holding = None
        self._append_round(self.wall_clock() if now is None else now)
        self.deadline = self.clock()

    def stop(self):
        self.running = False
        self.deadline = None
        if self.holding and self.holding.state == '持续中':
            self.holding.state = '已停止'
            self.holding.detail += '；持续阶段停止，输出保持原状态'
        self.holding = None
        for row in self.history:
            if row.state == '等待':
                row.state, row.detail = '已取消', row.detail + '；计划已停止'

    def disconnect(self):
        self.stop()

    def ready(self, now, available):
        if not self.running or self.active:
            return None
        if not available:
            self.stop()
            return None
        if self.clock() < self.deadline:
            return None
        if self.holding:
            if self.holding.state == '持续中':
                self.holding.state = '完成'
            self.holding = None
            self.index += 1
            if self.index == len(self.round_rows):
                if self.cycle == self.cycles:
                    self.running = False
                    self.deadline = None
                    return None
                self.cycle += 1
                self.index = 0
                self._append_round(now)
        plan = self.round_rows[self.index]
        plan.due, plan.state = now, '执行中'
        plan.detail = f'第{self.cycle}轮；实际触发时间'
        self.active = plan
        return plan

    def complete(self, plan, result):
        super().complete(plan, result)
        plan.detail = f'第{plan.cycle}轮；' + plan.detail
        self.active = None
        if not self.running:
            if plan.state == '完成':plan.state = '已停止'
            plan.detail += '；计划已停止，未继续持续计时'
            return
        self.holding = plan
        if plan.state == '完成':
            plan.state = '持续中'
        self.deadline = self.clock() + plan.delay_seconds
        due = self.wall_clock() + plan.delay_seconds
        for row in self.round_rows[self.index+1:]:
            row.due = due
            due += row.delay_seconds
