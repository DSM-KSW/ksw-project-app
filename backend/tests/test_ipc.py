import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(sys.platform == "win32", "Windows named pipes and hooks")
class BackgroundIpcTests(unittest.TestCase):
    def test_lifecycle_and_mapping_calls(self):
        with tempfile.TemporaryDirectory() as directory:
            env = os.environ.copy()
            env["LOCALAPPDATA"] = directory
            # Import after LOCALAPPDATA is isolated so this test never edits real settings.
            script = f"""
import os, subprocess, sys, time, json
sys.path.insert(0, {str(ROOT)!r})
import ipc
p = subprocess.Popen([sys.executable, '-B', {str(ROOT / 'app.py')!r}, '--background'],
                     cwd={str(ROOT)!r}, env=os.environ.copy(),
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, close_fds=True,
                     creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW)
try:
    for _ in range(100):
        try:
            answer = ipc.request('ping')
            if answer.get('ok'): break
        except (OSError, EOFError): pass
        if p.poll() is not None: raise AssertionError('background exited')
        time.sleep(.05)
    else: raise AssertionError('background did not open IPC')
    assert answer['pid'] == p.pid
    binding = {{'keys':[65], 'mouse':None, 'output':[17,84]}}
    assert ipc.request('set_binding', binding=binding)['ok']
    assert ipc.request('list_bindings')['bindings'] == [binding]
    assert ipc.request('set_active', active=False)['active'] is False
    assert ipc.request('delete_binding', source={{'keys':[65], 'mouse':None}})['bindings'] == []
    assert p.poll() is None
    print(p.pid)
finally:
    p.terminate()
    p.wait(timeout=5)
"""
            result = subprocess.run(
                [sys.executable, "-B", "-c", script], env=env,
                capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            saved = json.loads((Path(directory) / "DSM-KSW" / "bindings.json").read_text())
            self.assertEqual(saved, {"bindings": []})


if __name__ == "__main__":
    unittest.main()
