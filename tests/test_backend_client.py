import ctypes
import os
import signal
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(sys.platform == "win32", "Windows background process")
class BackendClientTests(unittest.TestCase):
    def test_worker_survives_front_process_and_reconnects(self):
        with tempfile.TemporaryDirectory() as directory:
            env = os.environ.copy()
            env["LOCALAPPDATA"] = directory
            launch_code = (
                "import backend_client; backend_client.ensure_background(); "
                "print(backend_client.call('ping')['pid'])"
            )
            launcher = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-c",
                    launch_code,
                ],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            self.assertEqual(launcher.returncode, 0, launcher.stderr)
            pid = int(launcher.stdout.strip())
            try:
                user32 = ctypes.WinDLL("user32")
                windows = []
                callback_type = ctypes.WINFUNCTYPE(
                    ctypes.c_bool, ctypes.c_void_p, ctypes.c_ssize_t
                )
                user32.GetWindowThreadProcessId.argtypes = [
                    ctypes.c_void_p,
                    ctypes.POINTER(ctypes.c_ulong),
                ]
                user32.IsWindowVisible.argtypes = [ctypes.c_void_p]
                user32.EnumWindows.argtypes = [callback_type, ctypes.c_ssize_t]

                @callback_type
                def inspect_window(hwnd, unused):
                    owner = ctypes.c_ulong()
                    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
                    if owner.value == pid and user32.IsWindowVisible(hwnd):
                        windows.append(hwnd)
                    return True

                user32.EnumWindows(inspect_window, 0)
                self.assertEqual(windows, [], "백엔드에 표시되는 창이 있습니다")
                check_code = (
                    "import backend_client; "
                    f"assert backend_client.call('ping')['pid'] == {pid}; "
                    "assert backend_client.set_binding([71], [17, 37])['ok']; "
                    "assert backend_client.list_bindings()[0]['output'] == [17, 37]"
                )
                checker = subprocess.run(
                    [
                        sys.executable,
                        "-B",
                        "-c",
                        check_code,
                    ],
                    cwd=ROOT,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
                self.assertEqual(checker.returncode, 0, checker.stderr)
            finally:
                os.kill(pid, signal.SIGTERM)


if __name__ == "__main__":
    unittest.main()
