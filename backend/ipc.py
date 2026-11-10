"""Local JSON-over-Windows-named-pipe transport shared by UI and worker."""

import hashlib
import hmac
import json
import os
import secrets
import time
from multiprocessing.connection import Client, Listener
from pathlib import Path

DATA_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "DSM-KSW"
PIPE_NAME = "DSM-KSW-remap-" + hashlib.sha256(
    str(DATA_DIR.resolve()).lower().encode("utf-8")
).hexdigest()[:16]
ADDRESS = rf"\\.\pipe\{PIPE_NAME}"
MAX_MESSAGE = 1024 * 1024


def _secret():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / "ipc.key"
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        pass
    else:
        with os.fdopen(fd, "w", encoding="ascii") as file:
            file.write(secrets.token_hex(32))
    for _ in range(50):
        value = path.read_text(encoding="ascii").strip()
        if len(value) == 64:
            return value
        time.sleep(0.02)
    raise RuntimeError("IPC secret could not be read")


def request(operation, **parameters):
    """Send one request. The caller may retry after starting the worker."""
    message = {"version": 1, "token": _secret(), "op": operation, **parameters}
    with Client(ADDRESS, family="AF_PIPE") as connection:
        connection.send_bytes(json.dumps(message).encode("utf-8"))
        return json.loads(connection.recv_bytes(MAX_MESSAGE).decode("utf-8"))


def serve(dispatch):
    """Run on its own thread; each new UI instance can reconnect."""
    secret = _secret()
    with Listener(ADDRESS, family="AF_PIPE") as listener:
        while True:
            with listener.accept() as connection:
                try:
                    payload = json.loads(connection.recv_bytes(MAX_MESSAGE).decode("utf-8"))
                    if not isinstance(payload, dict) or not hmac.compare_digest(
                        str(payload.get("token", "")), secret
                    ):
                        response = {"ok": False, "error": "unauthorized"}
                    elif payload.get("version") != 1:
                        response = {"ok": False, "error": "unsupported_version"}
                    else:
                        response = dispatch(payload)
                    connection.send_bytes(json.dumps(response, ensure_ascii=False).encode("utf-8"))
                except (EOFError, OSError, ValueError, TypeError, UnicodeError) as error:
                    try:
                        connection.send_bytes(json.dumps({"ok": False, "error": str(error)}).encode("utf-8"))
                    except OSError:
                        pass
