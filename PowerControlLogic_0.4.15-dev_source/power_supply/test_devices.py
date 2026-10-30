import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from .devices import Device, DeviceCatalog
from .core import Simulator, Modbus, PowerService, Settings, ProtocolError
from .runtime import RecordingController, Worker
from .schedule import ScheduleBook


class DeviceTests(unittest.TestCase):
    def test_catalog_add_remove_persist(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'devices.json'
            catalog = DeviceCatalog(path)
            self.assertEqual(catalog.devices,[])
            for address in (7,42,255):
                catalog.add(f'电源{address}',address)
            with self.assertRaises(ValueError):
                catalog.add('重复',7)
            self.assertEqual(DeviceCatalog(path).devices,catalog.devices)
            for address in (7,42,255):
                catalog.remove(address)
            self.assertEqual(DeviceCatalog(path).devices,[])

    def test_address_and_name_validation(self):
        for address in (0,256,-1,True,'1',1.5):
            with self.assertRaises(ValueError):
                Device('电源',address)
        for name in ('',' '*2,'x'*49):
            with self.assertRaises(ValueError):
                Device(name,1)

    def test_failed_save_keeps_catalog(self):
        with tempfile.TemporaryDirectory() as folder:
            catalog = DeviceCatalog(Path(folder)/'devices.json')
            catalog.add('原设备',7)
            with patch.object(Path,'replace',side_effect=OSError('disk error')):
                with self.assertRaises(OSError):
                    catalog.add('新设备',42)
            self.assertEqual(DeviceCatalog(catalog.path).devices,[Device('原设备',7)])
            self.assertEqual(catalog.devices,[Device('原设备',7)])

    def test_arbitrary_addresses_and_readback(self):
        service = PowerService(Modbus(Simulator((7,42,255))))
        settings = Settings(12,2,28,8,True,False)
        for address in (7,42,255):
            for channel in (1,2):
                service.apply(address,channel,settings)
                sample = service.sample(address,channel)
                self.assertEqual(sample['set_voltage'],12)
                self.assertEqual(sample['set_current'],2)
                self.assertEqual(sample['ovp'],28)
                self.assertEqual(sample['ocp'],8)
                self.assertFalse(sample['ocp_enabled'])
                self.assertEqual(sample['output'],'关闭')

    def test_cancel_before_output_write(self):
        simulator = Simulator((7,))
        service = PowerService(Modbus(simulator))
        with self.assertRaises(ProtocolError):
            service.output(7,1,True,cancelled=lambda:True)
        self.assertEqual(simulator.registers[7][0x109],1)
        self.assertFalse(any(r[1]==6 and r[2:4]==b'\x01\x09' for r in simulator.requests))

    def test_worker_rejects_unconfigured_target(self):
        worker = Worker('TEST','unused',devices=[Device('电源',42)],recording=False)
        with self.assertRaises(ValueError):
            worker.submit('output',[(7,1)],True)
        self.assertEqual(worker.targets,{(42,1),(42,2)})

    def test_delete_device_invalidates_plans(self):
        book = ScheduleBook()
        deleted = book.add(110,True,[(42,1)],100,12.0,2.0)
        retained = book.add(120,True,[(7,1)],100,12.0,2.0)
        book.invalidate(42)
        self.assertEqual(deleted.state,'已取消')
        self.assertEqual(retained.state,'等待')

    def test_record_off_on_off_resume(self):
        with tempfile.TemporaryDirectory() as folder:
            controller = RecordingController(folder,'TEST',False)
            controller.sample(dict(address=7,channel=1))
            self.assertEqual(list(Path(folder).iterdir()),[])
            controller.set_enabled(True)
            controller.sample(dict(address=7,channel=1))
            first = controller.recorder.path/'samples.csv'
            controller.set_enabled(False)
            controller.sync()
            saved = first.read_bytes()
            controller.sample(dict(address=42,channel=2))
            self.assertEqual(first.read_bytes(),saved)
            controller.set_enabled(True)
            controller.sample(dict(address=255,channel=2))
            second = controller.recorder.path/'samples.csv'
            controller.close()
            self.assertNotEqual(first,second)
            with second.open(encoding='utf-8-sig') as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(rows[0]['address'],'255')

    def test_record_error_does_not_escape(self):
        errors = []
        controller = RecordingController('unused','TEST',True,on_error=errors.append)
        with patch('power_supply.runtime.Recorder',side_effect=OSError('disk full')):
            controller.sample(dict(address=7))
        self.assertFalse(controller.requested.is_set())
        self.assertEqual(errors,['disk full'])

