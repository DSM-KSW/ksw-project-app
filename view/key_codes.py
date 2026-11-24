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

# F12는 백엔드가 리매핑 켜기/끄기 키로 쓰므로 원래 키로도 결과 키로도 쓸 수 없다.
RESERVED_SOURCE_VK = 0x7B
RESERVED_VK = RESERVED_SOURCE_VK
ESCAPE_VK = 0x1B

# 화면 키보드에 없는 키 (매크로 키보드 등이 보내는 F13~F24, 미디어 키 등).
# "직접 매핑하기"에서 결과 키로 고를 수 있다.
EXTRA_VK_NAMES: dict[int, str] = {
    **{0x7B + n: f"F{12 + n}" for n in range(1, 13)},  # F13(0x7C) ~ F24(0x87)
    0xAD: "음소거",
    0xAE: "볼륨 -",
    0xAF: "볼륨 +",
    0xB3: "재생/일시정지",
    0xB2: "미디어 정지",
    0xB0: "다음 트랙",
    0xB1: "이전 트랙",
    0xA6: "브라우저 뒤로",
    0xA7: "브라우저 앞으로",
    0xA8: "브라우저 새로고침",
    0xAA: "브라우저 검색",
    0xAB: "브라우저 즐겨찾기",
    0xAC: "브라우저 홈",
    0xB4: "메일",
    0xB6: "앱 실행 1",
    0xB7: "앱 실행 2",
    0x5F: "절전",
    0x15: "한/영",
    0x19: "한자",
}

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


# Flet 키보드 이벤트의 key(Flutter 키 이름) -> VK. 글자·숫자 한 글자는 따로 처리한다.
FLET_KEY_VK: dict[str, int] = {
    **{f"F{n}": 0x6F + n for n in range(1, 25)},
    "Escape": 0x1B,
    "Enter": 0x0D,
    "Numpad Enter": 0x0D,
    "Tab": 0x09,
    "Backspace": 0x08,
    " ": 0x20,
    "Space": 0x20,
    "Insert": 0x2D,
    "Delete": 0x2E,
    "Home": 0x24,
    "End": 0x23,
    "Page Up": 0x21,
    "Page Down": 0x22,
    "Arrow Left": 0x25,
    "Arrow Up": 0x26,
    "Arrow Right": 0x27,
    "Arrow Down": 0x28,
    "Caps Lock": 0x14,
    "Num Lock": 0x90,
    "Scroll Lock": 0x91,
    "Pause": 0x13,
    "Print Screen": 0x2C,
    "Context Menu": 0x5D,
    **{f"Numpad {n}": 0x60 + n for n in range(10)},
    "Numpad Multiply": 0x6A,
    "Numpad Add": 0x6B,
    "Numpad Subtract": 0x6D,
    "Numpad Decimal": 0x6E,
    "Numpad Divide": 0x6F,
    "`": 0xC0,
    "-": 0xBD,
    "=": 0xBB,
    "[": 0xDB,
    "]": 0xDD,
    "\\": 0xDC,
    ";": 0xBA,
    "'": 0xDE,
    ",": 0xBC,
    ".": 0xBE,
    "/": 0xBF,
    "Shift Left": 0xA0,
    "Shift Right": 0xA1,
    "Control Left": 0xA2,
    "Control Right": 0xA3,
    "Alt Left": 0xA4,
    "Alt Right": 0xA5,
    "Meta Left": 0x5B,
    "Meta Right": 0x5C,
}


def vks_from_key_event(key: str, shift: bool, ctrl: bool, alt: bool, meta: bool):
    """실제 키보드로 누른 조합을 백엔드 출력 형식 [VK, ...]로 바꾼다. 모르는 키면 None."""
    if len(key) == 1 and key.isalnum() and key.isascii():
        main = ord(key.upper())
    else:
        main = FLET_KEY_VK.get(key)
    if main is None:
        return None
    output = [
        vk
        for pressed, vk in ((ctrl, 0xA2), (meta, 0x5B), (alt, 0xA4), (shift, 0xA0))
        if pressed and canonical_vk(vk) != canonical_vk(main)
    ]
    output.append(main)
    return output
