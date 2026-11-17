# 화면의 키 id <-> Windows 가상 키 코드(VK). 백엔드 리매핑은 VK 코드로 주고받는다.

KEY_VK: dict[str, int] = {
    "esc": 0x1B,
    **{f"func-{n}": 0x6F + n for n in range(1, 13)},  # F1(0x70) ~ F12(0x7B)
    "print-screen": 0x2C,
    "scroll-lock": 0x91,
    "pause": 0x13,
    "backtick": 0xC0,
    "one": 0x31,
    "two": 0x32,
    "three": 0x33,
    "four": 0x34,
    "five": 0x35,
    "six": 0x36,
    "seven": 0x37,
    "eight": 0x38,
    "nine": 0x39,
    "zero": 0x30,
    "hyphen": 0xBD,
    "equal-sign": 0xBB,
    "backspace": 0x08,
    "insert": 0x2D,
    "home": 0x24,
    "page-up": 0x21,
    "num-lock": 0x90,
    "numpad-slash": 0x6F,
    "numpad-asterisk": 0x6A,
    "numpad-hyphen": 0x6D,
    "tab": 0x09,
    **{letter: ord(letter.upper()) for letter in "qwertyuiopasdfghjklzxcvbnm"},
    "left-bracket": 0xDB,
    "right-bracket": 0xDD,
    "backslash": 0xDC,
    "delete": 0x2E,
    "end": 0x23,
    "page-down": 0x22,
    "numpad-zero": 0x60,
    "numpad-one": 0x61,
    "numpad-two": 0x62,
    "numpad-three": 0x63,
    "numpad-four": 0x64,
    "numpad-five": 0x65,
    "numpad-six": 0x66,
    "numpad-seven": 0x67,
    "numpad-eight": 0x68,
    "numpad-nine": 0x69,
    "numpad-plus": 0x6B,
    "numpad-period": 0x6E,
    "caps-lock": 0x14,
    "semicolon": 0xBA,
    "quote": 0xDE,
    "enter": 0x0D,
    "numpad-enter": 0x0D,  # Windows VK로는 Enter와 같은 키
    "left-shift": 0xA0,
    "comma": 0xBC,
    "period": 0xBE,
    "slash": 0xBF,
    "right-shift": 0xA1,
    "arrow-up": 0x26,
    "left-ctrl": 0xA2,
    "left-win": 0x5B,
    "left-alt": 0xA4,
    "space": 0x20,
    "right-alt": 0xA5,
    "right-win": 0x5C,
    "menu": 0x5D,
    "right-ctrl": 0xA3,
    "arrow-left": 0x25,
    "arrow-down": 0x28,
    "arrow-right": 0x27,
}

# F12는 백엔드가 리매핑 일시정지/재개 키로 쓰므로 원래 키로 지정할 수 없다.
RESERVED_SOURCE_VK = 0x7B

# 백엔드는 좌우 Shift/Ctrl/Alt/Win을 같은 키로 본다 (backend/app.py canonical_key와 동일).
_CANONICAL = {
    0xA0: 0x10,
    0xA1: 0x10,
    0xA2: 0x11,
    0xA3: 0x11,
    0xA4: 0x12,
    0xA5: 0x12,
    0x5C: 0x5B,
}


def canonical_vk(vk: int) -> int:
    return _CANONICAL.get(vk, vk)


# VK -> 화면에 그릴 키 id. 같은 VK를 쓰는 키가 여럿이면 왼쪽/기본 키를 쓴다.
VK_KEY: dict[int, str] = {}
for _key_id, _vk in KEY_VK.items():
    VK_KEY.setdefault(_vk, _key_id)
VK_KEY.update({0x10: "left-shift", 0x11: "left-ctrl", 0x12: "left-alt", 0x0D: "enter"})


def key_id_for_vk(vk: int) -> str | None:
    return VK_KEY.get(vk)
