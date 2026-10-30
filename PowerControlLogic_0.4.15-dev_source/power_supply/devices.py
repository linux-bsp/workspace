"""Persistent device definitions; never changes a physical device's address."""
import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
import tempfile


def valid_address(address):
    return type(address) is int and 1 <= address <= 255


@dataclass(frozen=True)
class Device:
    name: str
    address: int

    def __post_init__(self):
        if not isinstance(self.name,str) or not self.name.strip() or len(self.name)>48:
            raise ValueError('设备名称需为1–48个字符')
        if not valid_address(self.address):
            raise ValueError('地址号需为1–255，0为广播地址，禁止使用')


class DeviceCatalog:
    def __init__(self, path):
        self.path = Path(path)
        self.devices = []
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding='utf-8'))
            if not isinstance(data,dict) or data.get('version') != 1 or not isinstance(data.get('devices'),list):
                raise ValueError('设备配置格式不正确')
            self.devices = [Device(**row) for row in data['devices']]
            if len({d.address for d in self.devices}) != len(self.devices):
                raise ValueError('设备配置存在重复地址')

    def _save(self, devices):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=self.path.parent,
                                             prefix='devices-',suffix='.tmp',delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(dict(version=1,devices=[asdict(d) for d in devices]),stream,ensure_ascii=False,indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            temporary.replace(self.path)
            self.devices = list(devices)
        finally:
            if temporary and temporary.exists():
                temporary.unlink()

    def add(self, name, address):
        device = Device(name.strip(),address)
        if any(d.address==address for d in self.devices):
            raise ValueError('该地址号已存在，同一总线地址必须唯一')
        self._save([*self.devices,device])

    def remove(self, address):
        self.remove_many([address])

    def remove_many(self, addresses):
        selected=set(addresses)
        if not selected or not selected.issubset({d.address for d in self.devices}):
            raise ValueError('未找到待删除设备')
        self._save([d for d in self.devices if d.address not in selected])
