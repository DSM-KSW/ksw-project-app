import ctypes
import json
import os
import sys
import threading
import webbrowser
from ctypes import wintypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

try:
    from . import ipc
except ImportError:  # Direct `python app.py` prototype launch.
    import ipc

ROOT = Path(__file__).resolve().parent
CONFIG = (ipc.DATA_DIR if "--background" in sys.argv else ROOT) / "bindings.json"
macro = ctypes.CDLL(str(ROOT / "macro_combo.dll"))
macro.send_keys.argtypes = [ctypes.POINTER(ctypes.c_ushort), ctypes.c_uint,
                            ctypes.c_ushort, ctypes.POINTER(ctypes.c_longlong)]
macro.send_keys.restype = ctypes.c_int
macro.counter_frequency.argtypes = []
macro.counter_frequency.restype = ctypes.c_longlong
FREQUENCY = macro.counter_frequency()

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
WH_KEYBOARD_LL, WH_MOUSE_LL = 13, 14
WM_KEYDOWN, WM_KEYUP, WM_SYSKEYDOWN, WM_SYSKEYUP = 0x0100, 0x0101, 0x0104, 0x0105
WM_LBUTTONDOWN, WM_LBUTTONUP = 0x0201, 0x0202
WM_RBUTTONDOWN, WM_RBUTTONUP = 0x0204, 0x0205
WM_MBUTTONDOWN, WM_MBUTTONUP = 0x0207, 0x0208
WM_MOUSEWHEEL, WM_XBUTTONDOWN, WM_XBUTTONUP = 0x020A, 0x020B, 0x020C
VK_F12 = 0x7B

class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("vkCode", wintypes.DWORD), ("scanCode", wintypes.DWORD),
                ("flags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_size_t)]

class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("pt", wintypes.POINT), ("mouseData", wintypes.DWORD),
                ("flags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_size_t)]

HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
user32.SetWindowsHookExW.restype = wintypes.HHOOK
user32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
user32.CallNextHookEx.restype = ctypes.c_ssize_t
user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
user32.UnhookWindowsHookEx.restype = wintypes.BOOL
user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
user32.GetMessageW.restype = ctypes.c_int
kernel32.QueryPerformanceCounter.argtypes = [ctypes.POINTER(ctypes.c_longlong)]
kernel32.QueryPerformanceCounter.restype = wintypes.BOOL

def key_name(vk):
    if 0x30 <= vk <= 0x39 or 0x41 <= vk <= 0x5A:
        return chr(vk)
    if 0x70 <= vk <= 0x87:
        return f"F{vk - 0x6F}"
    names = {0x08: "Backspace", 0x09: "Tab", 0x0D: "Enter", 0x10: "Shift",
             0x11: "Ctrl", 0x12: "Alt", 0x1B: "Esc", 0x20: "Space",
             0x25: "←", 0x26: "↑", 0x27: "→", 0x28: "↓", 0x2E: "Delete",
             0x5B: "Windows", 0x5C: "오른쪽 Windows",
             0xA0: "왼쪽 Shift", 0xA1: "오른쪽 Shift", 0xA2: "왼쪽 Ctrl",
             0xA3: "오른쪽 Ctrl", 0xA4: "왼쪽 Alt", 0xA5: "오른쪽 Alt"}
    return names.get(vk, f"VK 0x{vk:02X}")


def binding_name(binding):
    parts = [key_name(vk) for vk in binding["keys"]]
    if binding["mouse"]:
        parts.append(binding["mouse"])
    return " + ".join(parts)


def output_name(keys):
    return " + ".join(key_name(vk) for vk in keys)


def canonical_key(vk):
    """Treat left/right modifier variants as one key for remapping."""
    if vk in (0xA0, 0xA1):
        return 0x10
    if vk in (0xA2, 0xA3):
        return 0x11
    if vk in (0xA4, 0xA5):
        return 0x12
    if vk == 0x5C:
        return 0x5B
    return vk


MOUSE_NAMES = {"왼쪽 클릭", "오른쪽 클릭", "가운데 클릭", "마우스 X1", "마우스 X2", "휠 위", "휠 아래"}


def valid_binding(item):
    if not isinstance(item, dict):
        return False
    keys, mouse, output = item.get("keys"), item.get("mouse"), item.get("output")
    if not isinstance(keys, list) or not isinstance(output, list):
        return False
    if not all(type(vk) is int and 1 <= vk <= 255 for vk in keys + output):
        return False
    return ((1 <= len(keys) <= 8 and mouse is None and VK_F12 not in keys or
             len(keys) == 0 and mouse in MOUSE_NAMES) and
            1 <= len(output) <= 8 and
            len({canonical_key(vk) for vk in output}) == len(output))


def load_bindings():
    if not CONFIG.exists():
        return []
    try:
        bindings = json.loads(CONFIG.read_text(encoding="utf-8"))["bindings"]
        # Read settings from the earlier A-only prototype as well.
        for item in bindings:
            if isinstance(item, dict) and type(item.get("output")) is int:
                item["output"] = [item["output"]]
        if not isinstance(bindings, list) or not all(valid_binding(item) for item in bindings):
            raise ValueError("invalid bindings")
        return bindings
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Could not load bindings.json: {exc}", flush=True)
        return []


def save_bindings(bindings):
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    temporary = CONFIG.with_suffix(".json.tmp")
    temporary.write_text(json.dumps({"bindings": bindings}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, CONFIG)


state = {
    "status": "입력 감지 준비 중", "count": 0, "key": None,
    "milliseconds": None, "sent": None, "active": True,
    "capturing": False, "selected": None, "selected_name": None,
    "selected_output": [], "selected_output_name": None,
    "keyboard_hook": False, "mouse_hook": False, "bindings": load_bindings(),
}
state_lock = threading.RLock()
suppressed_keys = set()
suppressed_mouse = set()
f12_held = False
capture_keys = []
capture_held = set()
capture_mouse = None
held_keys = set()
raw_held_keys = set()
held_mouse = set()
triggered = set()

def begin_capture():
    global capture_mouse
    with state_lock:
        capture_keys.clear()
        capture_held.clear()
        capture_mouse = None
        state["capturing"] = True
        state["selected"] = None
        state["selected_name"] = None
        state["status"] = "바꿀 원래 키 하나를 누르세요"


def finish_capture():
    global capture_mouse
    with state_lock:
        if not capture_keys and capture_mouse is None:
            return
        draft = {"keys": capture_keys[:1], "mouse": capture_mouse}
        state["selected"] = draft
        state["selected_name"] = binding_name(draft)
        state["capturing"] = False
        state["status"] = f"원래 입력 {state['selected_name']} 선택됨"
        capture_keys.clear()
        capture_held.clear()
        capture_mouse = None


def capture_key(vk, pressed):
    with state_lock:
        if not state["capturing"]:
            return False
        if pressed:
            if capture_mouse is not None:
                return True
            if not capture_keys and capture_mouse is None:
                capture_keys.append(vk)
            capture_held.add(vk)
            state["status"] = key_name(capture_keys[0]) + " · 놓으면 선택 완료"
        else:
            capture_held.discard(vk)
            if not capture_held:
                finish_capture()
        return True


def capture_mouse_event(name, pressed):
    global capture_mouse
    with state_lock:
        if not state["capturing"]:
            return False
        if pressed:
            if not capture_keys:
                capture_mouse = name
            state["status"] = name + " · 놓으면 선택 완료"
            if name.startswith("휠") and not capture_held:
                finish_capture()
        elif capture_mouse == name and not capture_held:
            finish_capture()
        return True


def clear_triggered():
    with state_lock:
        for index in list(triggered):
            if index >= len(state["bindings"]):
                triggered.discard(index)
                continue
            binding = state["bindings"][index]
            if not {canonical_key(v) for v in binding["keys"]}.issubset(held_keys) or (binding["mouse"] and binding["mouse"] not in held_mouse):
                triggered.discard(index)


def remap_if_match(source, code, trigger_vk=0):
    with state_lock:
        if not state["active"] or state["capturing"]:
            return False
        candidates = []
        for index, binding in enumerate(state["bindings"]):
            if index in triggered or not {canonical_key(v) for v in binding["keys"]}.issubset(held_keys):
                continue
            if binding["mouse"] is not None and binding["mouse"] != code:
                continue
            if binding["mouse"] is None and (source != "keyboard" or canonical_key(code) not in {canonical_key(v) for v in binding["keys"]}):
                continue
            candidates.append((len(binding["keys"]) + bool(binding["mouse"]), index, binding))
        if not candidates:
            return False
        _, index, binding = max(candidates)
        triggered.add(index)
    start = ctypes.c_longlong()
    kernel32.QueryPerformanceCounter(ctypes.byref(start))
    entry = ctypes.c_longlong()
    output = binding["output"]
    output_array = (ctypes.c_ushort * len(output))(*output)
    sent = bool(macro.send_keys(output_array, len(output), trigger_vk, ctypes.byref(entry)))
    ms = (entry.value - start.value) * 1000 / FREQUENCY
    with state_lock:
        state.update(count=state["count"] + 1,
                     key=f"{binding_name(binding)} → {output_name(output)}",
                     milliseconds=ms, sent=sent)
    return sent

def keyboard_proc(code, wparam, lparam):
    global f12_held
    if code < 0 or wparam not in (WM_KEYDOWN, WM_SYSKEYDOWN, WM_KEYUP, WM_SYSKEYUP):
        return user32.CallNextHookEx(None, code, wparam, lparam)
    info = ctypes.cast(lparam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
    if info.dwExtraInfo == 0x43414D41:  # Let only our own A pass through.
        return user32.CallNextHookEx(None, code, wparam, lparam)
    pressed = wparam in (WM_KEYDOWN, WM_SYSKEYDOWN)
    key_id = (int(info.vkCode), int(info.scanCode), bool(info.flags & 0x01))
    if info.vkCode == VK_F12:
        if pressed and not f12_held:
            f12_held = True
            with state_lock:
                state["active"] = not state["active"]
                state["capturing"] = False
                state["status"] = "치환 작동 중" if state["active"] else "일시 정지 · F12로 재개"
        elif not pressed:
            f12_held = False
        return 1
    vk = int(info.vkCode)
    if pressed:
        raw_held_keys.add(vk)
    else:
        raw_held_keys.discard(vk)
    held_keys.clear()
    held_keys.update(canonical_key(v) for v in raw_held_keys)
    if capture_key(vk, pressed):
        if pressed:
            suppressed_keys.add(key_id)
        else:
            suppressed_keys.discard(key_id)
        return 1
    if not pressed:
        clear_triggered()
        if key_id in suppressed_keys:
            suppressed_keys.remove(key_id)
            return 1
        return user32.CallNextHookEx(None, code, wparam, lparam)
    if remap_if_match("keyboard", vk, vk):
        suppressed_keys.add(key_id)
        return 1
    return user32.CallNextHookEx(None, code, wparam, lparam)

MOUSE_DOWN = {WM_LBUTTONDOWN: "왼쪽 클릭", WM_RBUTTONDOWN: "오른쪽 클릭",
              WM_MBUTTONDOWN: "가운데 클릭"}
MOUSE_UP = {WM_LBUTTONUP: "왼쪽 클릭", WM_RBUTTONUP: "오른쪽 클릭",
            WM_MBUTTONUP: "가운데 클릭"}

def mouse_proc(code, wparam, lparam):
    if code < 0:
        return user32.CallNextHookEx(None, code, wparam, lparam)
    info = ctypes.cast(lparam, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
    if info.flags & 0x01:  # Ignore injected mouse events.
        return user32.CallNextHookEx(None, code, wparam, lparam)
    name = MOUSE_DOWN.get(wparam)
    is_down = name is not None
    is_up = wparam in MOUSE_UP or wparam == WM_XBUTTONUP
    if wparam in (WM_XBUTTONDOWN, WM_XBUTTONUP):
        xbutton = (info.mouseData >> 16) & 0xFFFF
        name = f"마우스 X{xbutton}"
        is_down = wparam == WM_XBUTTONDOWN
    elif wparam == WM_MOUSEWHEEL:
        delta = ctypes.c_short((info.mouseData >> 16) & 0xFFFF).value
        name = "휠 위" if delta > 0 else "휠 아래"
        is_down = True
    elif is_up:
        name = MOUSE_UP[wparam]
    if name is None:
        return user32.CallNextHookEx(None, code, wparam, lparam)
    if is_down and wparam != WM_MOUSEWHEEL:
        held_mouse.add(name)
    elif is_up:
        held_mouse.discard(name)
    if capture_mouse_event(name, is_down):
        if is_down and wparam != WM_MOUSEWHEEL:
            suppressed_mouse.add(name)
        elif is_up:
            suppressed_mouse.discard(name)
        return 1
    if is_up:
        clear_triggered()
        if name in suppressed_mouse:
            suppressed_mouse.remove(name)
            return 1
        return user32.CallNextHookEx(None, code, wparam, lparam)
    if remap_if_match("mouse", name):
        if wparam != WM_MOUSEWHEEL:
            suppressed_mouse.add(name)
        else:
            triggered.clear()
        return 1
    return user32.CallNextHookEx(None, code, wparam, lparam)

keyboard_callback = HOOKPROC(keyboard_proc)
mouse_callback = HOOKPROC(mouse_proc)

def run_hook(hook_type, callback, label):
    hook = user32.SetWindowsHookExW(hook_type, callback, None, 0)
    if not hook:
        with state_lock:
            state["status"] = f"{label} 감지 실패 (Windows 오류 {ctypes.get_last_error()})"
        return
    with state_lock:
        state["keyboard_hook" if hook_type == WH_KEYBOARD_LL else "mouse_hook"] = True
    msg = wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
        pass
    user32.UnhookWindowsHookEx(hook)

class Handler(BaseHTTPRequestHandler):
    def reply(self, data=None, status=200):
        body = b"" if data is None else json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            body = (ROOT / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/state":
            with state_lock:
                self.reply(state)
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/capture":
            begin_capture()
            return self.reply(status=204)
        if self.path == "/capture-event":
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 256:
                    raise ValueError()
                data = json.loads(self.rfile.read(size))
                source, code, pressed = data["source"], data["code"], data["pressed"]
                if type(pressed) is not bool:
                    raise ValueError()
                if source == "keyboard" and type(code) is int and 1 <= code <= 255 and code != VK_F12:
                    capture_key(code, pressed)
                elif source == "mouse" and code in MOUSE_NAMES:
                    capture_mouse_event(code, pressed)
                else:
                    raise ValueError()
            except (ValueError, TypeError, KeyError, json.JSONDecodeError):
                return self.reply({"error": "잘못된 입력"}, 400)
            return self.reply(status=204)
        if self.path == "/draft":
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 1024:
                    raise ValueError()
                data = json.loads(self.rfile.read(size))
                role = data["role"]
                keys = data["keys"]
                mouse = data.get("mouse")
                if not isinstance(keys, list) or not all(type(vk) is int and 1 <= vk <= 255 for vk in keys):
                    raise ValueError()
                if role == "input":
                    if len(keys) > 1 or (mouse is not None and mouse not in MOUSE_NAMES) or (keys and mouse) or VK_F12 in keys:
                        raise ValueError()
                elif role == "output":
                    if mouse is not None or len(keys) > 8 or len({canonical_key(v) for v in keys}) != len(keys):
                        raise ValueError()
                else:
                    raise ValueError()
            except (ValueError, TypeError, KeyError, json.JSONDecodeError):
                return self.reply({"error": "키 선택이 잘못되었습니다"}, 400)
            with state_lock:
                if role == "input":
                    draft = {"keys": keys, "mouse": mouse}
                    state["selected"] = draft if keys or mouse else None
                    state["selected_name"] = binding_name(draft) if keys or mouse else None
                else:
                    state["selected_output"] = keys.copy()
                    state["selected_output_name"] = output_name(keys) if keys else None
                state["capturing"] = False
                state["status"] = "원래 입력과 바꿀 키를 고른 뒤 저장하세요"
            return self.reply(status=204)
        if self.path == "/save":
            with state_lock:
                selected = state["selected"]
                draft = ({"keys": selected["keys"].copy(), "mouse": selected["mouse"],
                          "output": state["selected_output"].copy()} if selected else None)
                if not valid_binding(draft) or state["capturing"]:
                    return self.reply({"error": "원래 입력과 바꿀 키를 모두 선택하세요"}, 400)
                signature = (frozenset(draft["keys"]), draft["mouse"])
                updated = [item for item in state["bindings"]
                           if (frozenset(item["keys"]), item["mouse"]) != signature]
                updated.append(draft.copy())
                try:
                    save_bindings(updated)
                except OSError as exc:
                    return self.reply({"error": str(exc)}, 500)
                state["bindings"] = updated
                state["status"] = f"{binding_name(draft)} → {output_name(draft['output'])} 저장됨"
                triggered.clear()
            return self.reply(status=204)
        if self.path == "/delete":
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 64:
                    raise ValueError()
                index = json.loads(self.rfile.read(size))["index"]
                if type(index) is not int:
                    raise ValueError()
            except (ValueError, TypeError, KeyError, json.JSONDecodeError):
                return self.reply({"error": "잘못된 번호"}, 400)
            with state_lock:
                if not 0 <= index < len(state["bindings"]):
                    return self.reply({"error": "없는 항목"}, 404)
                updated = state["bindings"][:index] + state["bindings"][index + 1:]
                try:
                    save_bindings(updated)
                except OSError as exc:
                    return self.reply({"error": str(exc)}, 500)
                state["bindings"] = updated
                state["status"] = "리매핑이 삭제됨"
                triggered.clear()
            return self.reply(status=204)
        self.send_error(404)

    def log_message(self, format, *args):
        pass


def dispatch_ipc(message):
    """Apply a remapping call received by the independent IPC thread."""
    operation = message.get("op")
    with state_lock:
        if operation == "ping":
            return {"ok": True, "pid": os.getpid()}
        if operation == "status":
            return {"ok": True, "active": state["active"],
                    "keyboard_hook": state["keyboard_hook"], "mouse_hook": state["mouse_hook"],
                    "binding_count": len(state["bindings"])}
        if operation == "list_bindings":
            return {"ok": True, "bindings": [dict(item) for item in state["bindings"]]}
        if operation == "set_active":
            if type(message.get("active")) is not bool:
                return {"ok": False, "error": "active_must_be_boolean"}
            state["active"] = message["active"]
            state["status"] = "치환 작동 중" if state["active"] else "일시 정지"
            return {"ok": True, "active": state["active"]}
        if operation == "set_binding":
            binding = message.get("binding")
            if not valid_binding(binding):
                return {"ok": False, "error": "invalid_binding"}
            signature = (frozenset(canonical_key(key) for key in binding["keys"]), binding["mouse"])
            updated = [item for item in state["bindings"] if
                       (frozenset(canonical_key(key) for key in item["keys"]), item["mouse"]) != signature]
            updated.append({"keys": binding["keys"].copy(), "mouse": binding["mouse"],
                            "output": binding["output"].copy()})
        elif operation == "delete_binding":
            source = message.get("source")
            if not isinstance(source, dict) or not isinstance(source.get("keys"), list):
                return {"ok": False, "error": "invalid_source"}
            keys, mouse = source["keys"], source.get("mouse")
            if not all(type(key) is int for key in keys):
                return {"ok": False, "error": "invalid_source"}
            signature = (frozenset(canonical_key(key) for key in keys), mouse)
            updated = [item for item in state["bindings"] if
                       (frozenset(canonical_key(key) for key in item["keys"]), item["mouse"]) != signature]
            if len(updated) == len(state["bindings"]):
                return {"ok": False, "error": "not_found"}
        else:
            return {"ok": False, "error": "unknown_operation"}
        try:
            save_bindings(updated)
        except OSError as error:
            return {"ok": False, "error": f"save_failed: {error}"}
        state["bindings"] = updated
        triggered.clear()
        return {"ok": True, "bindings": [dict(item) for item in updated]}


def start_hooks():
    threading.Thread(target=run_hook, args=(WH_KEYBOARD_LL, keyboard_callback, "키보드"), daemon=True).start()
    threading.Thread(target=run_hook, args=(WH_MOUSE_LL, mouse_callback, "마우스"), daemon=True).start()
    with state_lock:
        state["status"] = f"저장된 리매핑 {len(state['bindings'])}개 · 입력을 선택하세요"


def run_background():
    """Keep remapping alive after the front-end process exits."""
    mutex_name = "Local\\" + ipc.PIPE_NAME
    kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
    kernel32.CreateMutexW.restype = wintypes.HANDLE
    mutex = kernel32.CreateMutexW(None, False, mutex_name)
    if not mutex:
        raise ctypes.WinError(ctypes.get_last_error())
    if ctypes.get_last_error() == 183:  # Another instance owns the hooks and pipe.
        kernel32.CloseHandle(mutex)
        return
    start_hooks()
    threading.Thread(target=ipc.serve, args=(dispatch_ipc,), name="remap-ipc", daemon=True).start()
    threading.Event().wait()


if __name__ == "__main__":
    if "--background" in sys.argv:
        run_background()
        raise SystemExit(0)
    start_hooks()
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("Open: http://127.0.0.1:8765", flush=True)
    print("Stop: close this window", flush=True)
    url = "http://127.0.0.1:8765"
    try:
        os.startfile(url)
    except OSError:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


