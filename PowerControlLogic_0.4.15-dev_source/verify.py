"""Headless regression runner; simulated devices and localhost TCP only."""
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent
evidence = root / '.verification'
evidence.mkdir(exist_ok=True)
env = dict(os.environ, TEMP=str(evidence), TMP=str(evidence), PYTHONDONTWRITEBYTECODE='1')
env.pop('PYTHONPATH', None)
modules = ['power_supply.test_power', 'power_supply.test_schedule', 'power_supply.test_devices', 'power_supply.test_runtime', 'power_supply.test_serial', 'power_supply.test_disconnect', 'power_supply.test_recovery', 'power_supply.test_recovery_worker', 'power_supply.test_tcp', 'test_power_register_diagnostics']
failures = []
for module in modules:
    with (evidence / (module + '.log')).open('w', encoding='utf-8') as output:
        try:
            result = subprocess.run([sys.executable, '-m', 'unittest', module, '-v'],
                                    cwd=root, env=env, stdout=output, stderr=subprocess.STDOUT, timeout=60)
            code = result.returncode
        except subprocess.TimeoutExpired:
            code = 'timeout'
    print(module, code, flush=True)
    if code != 0:
        failures.append(module)
raise SystemExit(1 if failures else 0)
