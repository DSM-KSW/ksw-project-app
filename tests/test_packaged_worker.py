import importlib
import os
import signal
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


@unittest.skipUnless(sys.platform == "win32", "Windows packaged executable")
class PackagedWorkerTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get("KSW_PACKAGED_EXE"), "Build executable first")
    def test_worker_survives_packaged_parent_exit(self):
        executable = Path(os.environ["KSW_PACKAGED_EXE"])
        self.assertTrue(executable.is_file())
        with tempfile.TemporaryDirectory() as directory:
            probe_log = Path(directory) / "probe.log"
            env = {
                **os.environ,
                "LOCALAPPDATA": directory,
                "KSW_PROBE_LOG": str(probe_log),
            }
            launcher = subprocess.Popen(
                [str(executable), "--background-probe"],
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW,
            )
            try:
                returncode = launcher.wait(timeout=90)
            except subprocess.TimeoutExpired as error:
                progress = (
                    probe_log.read_text(encoding="utf-8")
                    if probe_log.exists()
                    else "no probe log"
                )
                processes = subprocess.run(
                    [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        (
                            "Get-CimInstance Win32_Process | "
                            "Where-Object Name -eq 'dsm-ksw-project.exe' | "
                            "Select-Object ProcessId,ParentProcessId,CommandLine | "
                            "ConvertTo-Json -Compress"
                        ),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    check=False,
                )
                raise AssertionError(
                    f"Launcher did not exit; progress={progress!r}; "
                    f"processes={processes.stdout.strip()!r}"
                ) from error
            self.assertEqual(returncode, 0)
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
