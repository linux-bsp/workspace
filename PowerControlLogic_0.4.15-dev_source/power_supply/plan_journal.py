"""Durable program evidence independent of optional sample recording."""
import json,time,uuid,threading
from pathlib import Path
from dataclasses import asdict
from datetime import datetime,timezone,timedelta
from . import VERSION

class PlanJournal:
    def __init__(self,root,mode,plans,cycles,devices,loop=None):
        self.run_id=uuid.uuid4().hex
        self.path=Path(root)/'program-logs'/('program_'+self.run_id+'.jsonl')
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.lock=threading.Lock();self.seen={};self.holds={};self.closed=False;self.mirrors=set()
        from core import VERSION as client_version
        self.emit('plan_start',mode=mode,cycles=cycles,loop=loop,client_version=client_version,power_version=VERSION,
                  devices=devices,duration_semantics='动作回读结束后开始持续计时' if mode=='interval' else '不适用',plans=[dict(asdict(p),row_id=i+1) for i,p in enumerate(plans)])
    def emit(self,event,**values):
        row=dict(run_id=self.run_id,event=event,time=datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='milliseconds'),monotonic_seconds=time.perf_counter(),**values)
        with self.lock:
            payload=json.dumps(row,ensure_ascii=False)+'\n'
            for path in (self.path,*self.mirrors):
                with path.open('a',encoding='utf-8') as stream:
                    stream.write(payload);stream.flush()
    def mirror(self,folder):
        path=Path(folder)/self.path.name
        with self.lock:
            if path not in self.mirrors:
                path.write_bytes(self.path.read_bytes())
                self.mirrors.add(path)
    def observe(self,book):
        rows=getattr(book,'history',None) or book.plans
        clock=getattr(book,'clock',time.perf_counter)
        holding=getattr(book,'holding',None)
        for i,p in enumerate(rows):
            state=(p.state,p.due,p.detail)
            if p is holding and i not in self.holds:
                self.holds[i]=clock()
                self.emit('duration_start',execution_row=i+1,row_id=(i % len(book.plans))+1,cycle=p.cycle,duration_seconds=p.delay_seconds)
            elif i in self.holds and p is not holding:
                self.emit('duration_end',execution_row=i+1,row_id=(i % len(book.plans))+1,cycle=p.cycle,actual_duration_seconds=clock()-self.holds.pop(i),state=p.state)
            if self.seen.get(i)!=state:
                previous=self.seen.get(i)
                values=asdict(p);values.pop('template_id',None)
                values['row_id']=(i % len(book.plans))+1
                self.emit('row_state',execution_row=i+1,change_reason=('初始预计时间' if previous is None else '实际触发' if p.state=='执行中' else '动作完成后顺延预计时间' if previous[1]!=p.due else '执行状态更新'),**values)
                self.seen[i]=state
    def finish(self,reason):
        if not self.closed:
            self.emit('plan_end',reason=reason);self.closed=True
