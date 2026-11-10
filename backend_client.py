"""Start the persistent Windows remapper and send it JSON calls."""

import os
import subprocess
import sys
import threading
import time
from pathlib import Path

_startup_lock = threading.Lock()


def _ipc():
    from backend import ipc

    return ipc


def _ping():
    try:
        return _ipc().request("ping").get("ok") is True
    except (OSError, EOFError, ConnectionError):
        return False


def ensure_background(timeout=5.0):
    """Reconnect if possible, otherwise launch a windowless independent child."""
    if sys.platform != "win32":
        raise RuntimeError("리매핑 백엔드는 Windows에서만 실행됩니다")
    if _ping():
        return
    with _startup_lock:
        if _ping():
            return
        if getattr(sys, "frozen", False):
            command = [sys.executable, "--background"]
        else:
            windowless_python = Path(sys.executable).with_name("pythonw.exe")
            command = [
                str(
                    windowless_python if windowless_python.exists() else sys.executable
                ),
                "-B",
                str(Path(__file__).resolve().parent / "main.py"),
                "--background",
            ]
        process = subprocess.Popen(
            command,
            cwd=str(Path(__file__).resolve().parent),
            env={**os.environ, "PYINSTALLER_RESET_ENVIRONMENT": "1"}
            if getattr(sys, "frozen", False)
            else os.environ.copy(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW,
        )
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if _ping():
                return
            if process.poll() is not None:
                raise RuntimeError(
                    f"백그라운드 시작 실패 (종료 코드 {process.returncode})"
                )
            time.sleep(0.05)
        raise TimeoutError("백그라운드 연결 시간이 초과되었습니다")


def call(operation, **parameters):
    ensure_background()
    try:
        response = _ipc().request(operation, **parameters)
    except (OSError, EOFError, ConnectionError):
        ensure_background()
        response = _ipc().request(operation, **parameters)
    if not response.get("ok"):
        raise RuntimeError(response.get("error", "백그라운드 요청 실패"))
    return response


def set_binding(keys, output, mouse=None):
    return call("set_binding", binding={"keys": keys, "mouse": mouse, "output": output})


def delete_binding(keys, mouse=None):
    return call("delete_binding", source={"keys": keys, "mouse": mouse})


def list_bindings():
    return call("list_bindings")["bindings"]
