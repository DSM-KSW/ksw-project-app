"""Temporary, dependency-free Windows mouse/keyboard/HID input inspector.

Run with run_mouse_probe.bat. It never blocks or remaps input and saves no log.
"""

import ctypes
import struct
from ctypes import wintypes


user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
PTR = ctypes.c_ssize_t
ULONG_PTR = ctypes.c_size_t

WH_KEYBOARD_LL, WH_MOUSE_LL = 13, 14
WM_INPUT, WM_DESTROY = 0x00FF, 0x0002
WM_KEYDOWN, WM_SYSKEYDOWN = 0x0100, 0x0104
WM_LBUTTONDOWN, WM_LBUTTONUP = 0x0201, 0x0202
WM_LBUTTONDBLCLK = 0x0203
WM_RBUTTONDOWN, WM_RBUTTONUP, WM_RBUTTONDBLCLK = 0x0204, 0x0205, 0x0206
WM_MBUTTONDOWN, WM_MBUTTONUP, WM_MBUTTONDBLCLK = 0x0207, 0x0208, 0x0209
WM_MOUSEWHEEL, WM_XBUTTONDOWN, WM_XBUTTONUP = 0x020A, 0x020B, 0x020C
WM_XBUTTONDBLCLK, WM_MOUSEHWHEEL = 0x020D, 0x020E
RID_INPUT, RIDI_DEVICEINFO, RIDI_DEVICENAME = 0x10000003, 0x2000000B, 0x20000007
RIM_TYPEMOUSE, RIM_TYPEKEYBOARD, RIM_TYPEHID = 0, 1, 2
RIDEV_INPUTSINK = 0x00000100

MOUSE_MESSAGES = {
    513: "LEFT_DOWN", 514: "LEFT_UP", 515: "LEFT_DOUBLE",
    516: "RIGHT_DOWN", 517: "RIGHT_UP", 518: "RIGHT_DOUBLE",
    519: "MIDDLE_DOWN", 520: "MIDDLE_UP", 521: "MIDDLE_DOUBLE",
    522: "WHEEL", 523: "X_DOWN", 524: "X_UP", 525: "X_DOUBLE",
    526: "H_WHEEL",
}
RAW_FLAGS = {
    0x0001: "B1_DOWN", 0x0002: "B1_UP", 0x0004: "B2_DOWN", 0x0008: "B2_UP",
    0x0010: "B3_DOWN", 0x0020: "B3_UP", 0x0040: "B4_DOWN", 0x0080: "B4_UP",
    0x0100: "B5_DOWN", 0x0200: "B5_UP", 0x0400: "WHEEL", 0x0800: "H_WHEEL",
}


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("vkCode", wintypes.DWORD), ("scanCode", wintypes.DWORD),
                ("flags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ULONG_PTR)]


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("pt", wintypes.POINT), ("mouseData", wintypes.DWORD),
                ("flags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ULONG_PTR)]


class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [("dwType", wintypes.DWORD), ("dwSize", wintypes.DWORD),
                ("hDevice", wintypes.HANDLE), ("wParam", wintypes.WPARAM)]


class RAWINPUTDEVICELIST(ctypes.Structure):
    _fields_ = [("hDevice", wintypes.HANDLE), ("dwType", wintypes.DWORD)]


class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [("usUsagePage", wintypes.USHORT), ("usUsage", wintypes.USHORT),
                ("dwFlags", wintypes.DWORD), ("hwndTarget", wintypes.HWND)]


WNDPROC = ctypes.WINFUNCTYPE(PTR, wintypes.HWND, wintypes.UINT,
                            wintypes.WPARAM, wintypes.LPARAM)
HOOKPROC = ctypes.WINFUNCTYPE(PTR, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)


class WNDCLASSW(ctypes.Structure):
    _fields_ = [("style", wintypes.UINT), ("lpfnWndProc", WNDPROC),
                ("cbClsExtra", ctypes.c_int), ("cbWndExtra", ctypes.c_int),
                ("hInstance", wintypes.HINSTANCE), ("hIcon", wintypes.HICON),
                ("hCursor", wintypes.HCURSOR), ("hbrBackground", wintypes.HBRUSH),
                ("lpszMenuName", wintypes.LPCWSTR), ("lpszClassName", wintypes.LPCWSTR)]


user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
user32.SetWindowsHookExW.restype = wintypes.HHOOK
user32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
user32.CallNextHookEx.restype = PTR
user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
user32.UnhookWindowsHookEx.restype = wintypes.BOOL
user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
user32.RegisterClassW.restype = wintypes.ATOM
user32.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR,
                                   wintypes.DWORD, ctypes.c_int, ctypes.c_int,
                                   ctypes.c_int, ctypes.c_int, wintypes.HWND,
                                   wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID]
user32.CreateWindowExW.restype = wintypes.HWND
user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.DefWindowProcW.restype = PTR
user32.GetRawInputData.argtypes = [wintypes.HANDLE, wintypes.UINT, wintypes.LPVOID,
                                   ctypes.POINTER(wintypes.UINT), wintypes.UINT]
user32.GetRawInputData.restype = wintypes.UINT
user32.GetRawInputDeviceList.argtypes = [ctypes.POINTER(RAWINPUTDEVICELIST),
                                         ctypes.POINTER(wintypes.UINT), wintypes.UINT]
user32.GetRawInputDeviceList.restype = wintypes.UINT
user32.GetRawInputDeviceInfoW.argtypes = [wintypes.HANDLE, wintypes.UINT,
                                          wintypes.LPVOID, ctypes.POINTER(wintypes.UINT)]
user32.GetRawInputDeviceInfoW.restype = wintypes.UINT
user32.RegisterRawInputDevices.argtypes = [ctypes.POINTER(RAWINPUTDEVICE), wintypes.UINT, wintypes.UINT]
user32.RegisterRawInputDevices.restype = wintypes.BOOL
user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND,
                               wintypes.UINT, wintypes.UINT]
user32.GetMessageW.restype = ctypes.c_int
kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = wintypes.HMODULE


def log(message):
    print(message, flush=True)


def device_name(handle):
    size = wintypes.UINT()
    user32.GetRawInputDeviceInfoW(handle, RIDI_DEVICENAME, None, ctypes.byref(size))
    if not size.value or size.value > 32768:
        return "unknown"
    buf = ctypes.create_unicode_buffer(size.value)
    if user32.GetRawInputDeviceInfoW(handle, RIDI_DEVICENAME, buf, ctypes.byref(size)) == 0xFFFFFFFF:
        return "unknown"
    return buf.value


seen_devices = set()


def raw_input(lparam):
    size = wintypes.UINT()
    header_size = ctypes.sizeof(RAWINPUTHEADER)
    if user32.GetRawInputData(lparam, RID_INPUT, None, ctypes.byref(size), header_size) == 0xFFFFFFFF:
        return
    if size.value < header_size or size.value > 65536:
        return
    buf = ctypes.create_string_buffer(size.value)
    if user32.GetRawInputData(lparam, RID_INPUT, buf, ctypes.byref(size), header_size) == 0xFFFFFFFF:
        return
    header = RAWINPUTHEADER.from_buffer_copy(buf)
    handle = header.hDevice
    if handle not in seen_devices:
        seen_devices.add(handle)
        log(f"DEVICE {handle!s} {device_name(handle)}")
    body = buf.raw[header_size:size.value]
    if header.dwType == RIM_TYPEMOUSE and len(body) >= 8:
        flags, data = struct.unpack_from("<HH", body, 4)
        if flags:
            labels = "+".join(name for bit, name in RAW_FLAGS.items() if flags & bit)
            signed_data = ctypes.c_short(data).value
            log(f"RAW_MOUSE device={handle} flags=0x{flags:04X} [{labels}] data={signed_data}")
    elif header.dwType == RIM_TYPEHID and len(body) >= 8:
        report_size, count = struct.unpack_from("<II", body)
        reports = body[8:8 + min(report_size * count, 64)]
        log(f"RAW_HID device={handle} report_size={report_size} count={count} hex={reports.hex(' ')}")


@WNDPROC
def window_proc(hwnd, message, wparam, lparam):
    if message == WM_INPUT:
        raw_input(lparam)
    elif message == WM_DESTROY:
        user32.PostQuitMessage(0)
    return user32.DefWindowProcW(hwnd, message, wparam, lparam)


@HOOKPROC
def mouse_hook(code, message, lparam):
    if code >= 0 and message in MOUSE_MESSAGES:
        info = ctypes.cast(lparam, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
        detail = 0
        if message in (WM_XBUTTONDOWN, WM_XBUTTONUP, WM_XBUTTONDBLCLK):
            detail = (info.mouseData >> 16) & 0xFFFF
        elif message in (WM_MOUSEWHEEL, WM_MOUSEHWHEEL):
            detail = ctypes.c_short((info.mouseData >> 16) & 0xFFFF).value
        log(f"HOOK_MOUSE id={message} (0x{message:04X}) {MOUSE_MESSAGES[message]} "
            f"detail={detail} injected={bool(info.flags & 1)}")
    return user32.CallNextHookEx(None, code, message, lparam)


@HOOKPROC
def keyboard_hook(code, message, lparam):
    if code >= 0 and message in (WM_KEYDOWN, WM_SYSKEYDOWN):
        info = ctypes.cast(lparam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
        log(f"HOOK_KEY vk={info.vkCode} (0x{info.vkCode:02X}) "
            f"scan={info.scanCode} injected={bool(info.flags & 0x10)}")
    return user32.CallNextHookEx(None, code, message, lparam)


def hid_usages():
    count = wintypes.UINT()
    if user32.GetRawInputDeviceList(None, ctypes.byref(count), ctypes.sizeof(RAWINPUTDEVICELIST)) == 0xFFFFFFFF:
        return set()
    if not count.value:
        return set()
    devices = (RAWINPUTDEVICELIST * count.value)()
    found = user32.GetRawInputDeviceList(devices, ctypes.byref(count), ctypes.sizeof(RAWINPUTDEVICELIST))
    if found == 0xFFFFFFFF:
        return set()
    usages = set()
    for device in devices[:found]:
        if device.dwType != RIM_TYPEHID:
            continue
        info = ctypes.create_string_buffer(64)
        ctypes.cast(info, ctypes.POINTER(wintypes.DWORD))[0] = 64
        size = wintypes.UINT(64)
        if user32.GetRawInputDeviceInfoW(device.hDevice, RIDI_DEVICEINFO, info, ctypes.byref(size)) == 0xFFFFFFFF:
            continue
        page, usage = struct.unpack_from("<HH", info.raw, 20)
        if page and usage:
            usages.add((page, usage))
    return usages


def main():
    instance = kernel32.GetModuleHandleW(None)
    name = "CodexMouseInputProbe"
    klass = WNDCLASSW(lpfnWndProc=window_proc, hInstance=instance, lpszClassName=name)
    if not user32.RegisterClassW(ctypes.byref(klass)):
        raise ctypes.WinError(ctypes.get_last_error())
    hwnd = user32.CreateWindowExW(0, name, name, 0, 0, 0, 0, 0, None, None, instance, None)
    if not hwnd:
        raise ctypes.WinError(ctypes.get_last_error())

    usages = {(0x01, 0x02)} | hid_usages()  # Mouse plus attached HID collections.
    registered = []
    for page, usage in sorted(usages):
        device = RAWINPUTDEVICE(page, usage, RIDEV_INPUTSINK, hwnd)
        if user32.RegisterRawInputDevices(ctypes.byref(device), 1, ctypes.sizeof(device)):
            registered.append(f"{page:04X}:{usage:04X}")
        else:
            log(f"Raw Input {page:04X}:{usage:04X} failed: {ctypes.WinError(ctypes.get_last_error())}")
    log("Registered Raw Input collections: " + (", ".join(registered) or "none"))

    keyboard = user32.SetWindowsHookExW(WH_KEYBOARD_LL, keyboard_hook, instance, 0)
    mouse = user32.SetWindowsHookExW(WH_MOUSE_LL, mouse_hook, instance, 0)
    if not keyboard or not mouse:
        raise ctypes.WinError(ctypes.get_last_error())
    log("Press mouse buttons one at a time. Compare the lines that appear. Close this console to stop.")
    msg = wintypes.MSG()
    try:
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    finally:
        user32.UnhookWindowsHookEx(mouse)
        user32.UnhookWindowsHookEx(keyboard)


if __name__ == "__main__":
    main()
