import importlib
import os
import signal
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


@unittest.skipUnless(sys.platform == "win32", "Windows one-file executable")
class PackagedWorkerTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get("KSW_PACKAGED_EXE"), "Build executable first")
    def test_worker_survives_packaged_parent_exit(self):
        executable = Path(os.environ["KSW_PACKAGED_EXE"])
        self.assertTrue(executable.is_file())
        with tempfile.TemporaryDirectory() as directory:
            env = {**os.environ, "LOCALAPPDATA": directory}
            launcher = subprocess.run(
                [str(executable), "--background-probe"],
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                capture_output=False,
                check=False,
                timeout=180,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW,
            )
            self.assertEqual(launcher.returncode, 0)
            with patch.dict(os.environ, {"LOCALAPPDATA": directory}):
                # The module may already be loaded by another test with a different path.
                from backend import ipc

                ipc = importlib.reload(ipc)
                response = ipc.request("ping")
                self.assertTrue(response["ok"])
                pid = response["pid"]
                try:
                    self.assertTrue(
                        ipc.request(
                            "set_binding",
                            binding={"keys": [71], "mouse": None, "output": [17, 37]},
                        )["ok"]
                    )
                finally:
                    os.kill(pid, signal.SIGTERM)


if __name__ == "__main__":
    unittest.main()
