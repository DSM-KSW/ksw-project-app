import asyncio
from typing import NotRequired, TypedDict

import flet as ft

import components


class KeyButtonData(TypedDict):
    id: str
    name: str
    # 아래 값들은 모두 키 1칸(KEY_UNIT_X, KEY_UNIT_Y) 기준 배수
    x: NotRequired[float]  # 이 키 앞의 가로 간격
    y: NotRequired[float]  # 이 줄 위의 세로 간격 (줄의 첫 키에만 지정)
    width: NotRequired[float]
    height: NotRequired[float]


# Figma(1920x1200) 수치를 창 크기(1280x720)에 맞게 2/3로 줄인 값
KEY_UNIT_X = 50  # 키 1칸의 가로 간격(px)
KEY_UNIT_Y = 55  # 키 1줄의 세로 간격(px)
KEY_GAP = 6  # 키 사이 여백(px)

TOOLTIP_HIDE_DELAY = 0.2  # 툴팁에서 마우스가 벗어난 뒤 숨길 때까지 기다리는 시간(초)

# 키 id -> 리매핑 목록 (각 리매핑은 키 id 조합)
# TODO: 실제 리매핑 저장/적용 기능이 생기면 그쪽 데이터로 교체
REMAPPINGS: dict[str, list[list[str]]] = {}

# US ANSI 104키 풀배열
KEYBOARD_BUTTON_DATA: list[list[KeyButtonData]] = [
    [
        {"id": "esc", "name": "Esc"},
        {"id": "func-1", "name": "F1", "x": 1},
        {"id": "func-2", "name": "F2"},
        {"id": "func-3", "name": "F3"},
        {"id": "func-4", "name": "F4"},
        {"id": "func-5", "name": "F5", "x": 0.5},
        {"id": "func-6", "name": "F6"},
        {"id": "func-7", "name": "F7"},
        {"id": "func-8", "name": "F8"},
        {"id": "func-9", "name": "F9", "x": 0.5},
        {"id": "func-10", "name": "F10"},
        {"id": "func-11", "name": "F11"},
        {"id": "func-12", "name": "F12"},
        {"id": "print-screen", "name": "PrtSc", "x": 0.25},
        {"id": "scroll-lock", "name": "Scroll"},
        {"id": "pause", "name": "Pause"},
    ],
    [
        {"id": "backtick", "name": "~", "y": 0.15},
        {"id": "one", "name": "1"},
        {"id": "two", "name": "2"},
        {"id": "three", "name": "3"},
        {"id": "four", "name": "4"},
        {"id": "five", "name": "5"},
        {"id": "six", "name": "6"},
        {"id": "seven", "name": "7"},
        {"id": "eight", "name": "8"},
        {"id": "nine", "name": "9"},
        {"id": "zero", "name": "0"},
        {"id": "hyphen", "name": "-"},
        {"id": "equal-sign", "name": "="},
        {"id": "backspace", "name": "Backspace", "width": 2},
        {"id": "insert", "name": "Insert", "x": 0.25},
        {"id": "home", "name": "Home"},
        {"id": "page-up", "name": "PgUp"},
        {"id": "num-lock", "name": "Num", "x": 0.25},
        {"id": "numpad-slash", "name": "/"},
        {"id": "numpad-asterisk", "name": "*"},
        {"id": "numpad-hyphen", "name": "-"},
    ],
    [
        {"id": "tab", "name": "Tab", "width": 1.5},
        {"id": "q", "name": "Q"},
        {"id": "w", "name": "W"},
        {"id": "e", "name": "E"},
        {"id": "r", "name": "R"},
        {"id": "t", "name": "T"},
        {"id": "y", "name": "Y"},
        {"id": "u", "name": "U"},
        {"id": "i", "name": "I"},
        {"id": "o", "name": "O"},
        {"id": "p", "name": "P"},
        {"id": "left-bracket", "name": "["},
        {"id": "right-bracket", "name": "]"},
        {"id": "backslash", "name": "\\", "width": 1.5},
        {"id": "delete", "name": "Delete", "x": 0.25},
        {"id": "end", "name": "End"},
        {"id": "page-down", "name": "PgDn"},
        {"id": "numpad-seven", "name": "7", "x": 0.25},
        {"id": "numpad-eight", "name": "8"},
        {"id": "numpad-nine", "name": "9"},
        {"id": "numpad-plus", "name": "+", "height": 2},
    ],
    [
        {"id": "caps-lock", "name": "Caps", "width": 1.75},
        {"id": "a", "name": "A"},
        {"id": "s", "name": "S"},
        {"id": "d", "name": "D"},
        {"id": "f", "name": "F"},
        {"id": "g", "name": "G"},
        {"id": "h", "name": "H"},
        {"id": "j", "name": "J"},
        {"id": "k", "name": "K"},
        {"id": "l", "name": "L"},
        {"id": "semicolon", "name": ";"},
        {"id": "quote", "name": "'"},
        {"id": "enter", "name": "Enter", "width": 2.25},
        {"id": "numpad-four", "name": "4", "x": 3.5},
        {"id": "numpad-five", "name": "5"},
        {"id": "numpad-six", "name": "6"},
    ],
    [
        {"id": "left-shift", "name": "Shift", "width": 2.25},
        {"id": "z", "name": "Z"},
        {"id": "x", "name": "X"},
        {"id": "c", "name": "C"},
        {"id": "v", "name": "V"},
        {"id": "b", "name": "B"},
        {"id": "n", "name": "N"},
        {"id": "m", "name": "M"},
        {"id": "comma", "name": ","},
        {"id": "period", "name": "."},
        {"id": "slash", "name": "/"},
        {"id": "right-shift", "name": "Shift", "width": 2.75},
        {"id": "arrow-up", "name": "↑", "x": 1.25},
        {"id": "numpad-one", "name": "1", "x": 1.25},
        {"id": "numpad-two", "name": "2"},
        {"id": "numpad-three", "name": "3"},
        {"id": "numpad-enter", "name": "Enter", "height": 2},
    ],
    [
        {"id": "left-ctrl", "name": "Ctrl", "width": 1.25},
        {"id": "left-win", "name": "Win", "width": 1.25},
        {"id": "left-alt", "name": "Alt", "width": 1.25},
        {"id": "space", "name": "", "width": 6.25},
        {"id": "right-alt", "name": "Alt", "width": 1.25},
        {"id": "right-win", "name": "", "width": 1.25},
        {"id": "menu", "name": "Menu", "width": 1.25},
        {"id": "right-ctrl", "name": "Ctrl", "width": 1.25},
        {"id": "arrow-left", "name": "←", "x": 0.25},
        {"id": "arrow-down", "name": "↓"},
        {"id": "arrow-right", "name": "→"},
        {"id": "numpad-zero", "name": "0", "x": 0.25, "width": 2},
        {"id": "numpad-period", "name": "."},
    ],
]

KEY_NAMES: dict[str, str] = {
    data["id"]: data["name"] for data_list in KEYBOARD_BUTTON_DATA for data in data_list
}


def remapping_label(index: int, key_ids: list[str]):
    return f"리매핑 {index + 1}: " + "+".join(
        KEY_NAMES.get(key_id, key_id) for key_id in key_ids
    )


def keyboard_view(page: ft.Page):
    key_buttons: dict[str, ft.Container] = {}

    # 지금 툴팁이 떠 있는 키, 숨김 예약 작업
    state: dict = {"key_id": None, "hide_task": None}

    def set_highlight(key_ids: set[str]):
        for key_id, key_button in key_buttons.items():
            key_button.bgcolor = (
                components.KEY_HIGHLIGHT_COLOR
                if key_id in key_ids
                else components.KEY_COLOR
            )

    def cancel_hide():
        if state["hide_task"] is not None:
            state["hide_task"].cancel()
            state["hide_task"] = None

    def hide_tooltip():
        state["key_id"] = None
        tooltip_thing.visible = False
        set_highlight(set())
        keyboard_stack.update()

    def schedule_hide():
        cancel_hide()

        async def hide_later():
            await asyncio.sleep(TOOLTIP_HIDE_DELAY)
            state["hide_task"] = None
            hide_tooltip()

        state["hide_task"] = page.run_task(hide_later)

    def refresh_tooltip():
        key_id = state["key_id"]
        remappings = REMAPPINGS.get(key_id, [])

        def on_delete(index: int):
            remappings.pop(index)
            refresh_tooltip()
            # 줄이 줄어들면 툴팁 높이가 바뀌므로 자리도 다시 잡는다
            place_tooltip(key_buttons[key_id])
            set_highlight({key_id})
            keyboard_stack.update()

        def on_row_hover(index: int):
            set_highlight({key_id, *remappings[index]})
            keyboard_stack.update()

        def on_row_out(index: int):
            set_highlight({key_id})
            keyboard_stack.update()

        components.set_tooltip_remappings(
            tooltip_thing,
            {
                "labels": [remapping_label(i, ids) for i, ids in enumerate(remappings)],
                # TODO: 리매핑 추가/수정 화면 디자인이 나오면 연결
                "on_add": lambda: None,
                "on_edit": lambda index: None,
                "on_delete": on_delete,
                "on_row_hover": on_row_hover,
                "on_row_out": on_row_out,
            },
        )

    # 툴팁은 Stack 안에 완전히 들어가 있어야 한다.
    # Stack 밖으로 나간 자식은 보이기만 하고 마우스 이벤트를 받지 못해서,
    # 그 상태로는 툴팁 위로 마우스를 옮길 수 없고 그대로 숨겨진다.
    def place_tooltip(key_button: ft.Container):
        height = components.tooltip_height(len(REMAPPINGS.get(key_button.data, [])))

        # 가로: 키 가운데 정렬, 키보드 영역을 벗어나면 안쪽으로 당긴다
        left = key_button.left + (key_button.width - components.TOOLTIP_WIDTH) / 2
        tooltip_thing.left = min(
            max(left, 0), keyboard_width - components.TOOLTIP_WIDTH
        )

        # 세로: 키 위에 자리가 있으면 위, 없으면(맨 윗줄 등) 아래에 붙인다.
        # 툴팁의 투명 여백이 키와 맞닿으므로 마우스가 빈 곳을 지나지 않는다.
        if key_button.top >= height:
            tooltip_thing.top = None
            tooltip_thing.bottom = keyboard_height - key_button.top
        else:
            tooltip_thing.bottom = None
            tooltip_thing.top = key_button.top + key_button.height

    def show_tooltip(key_button: ft.Container):
        cancel_hide()

        state["key_id"] = key_button.data
        refresh_tooltip()
        place_tooltip(key_button)

        tooltip_thing.visible = True

        set_highlight({key_button.data})
        keyboard_stack.update()

    tooltip_thing = components.make_tooltip(
        {"on_hover": cancel_hide, "on_out": schedule_hide}
    )

    tooltip_thing.visible = False

    # 키를 격자 위에 절대 위치로 배치
    # (넘패드 +, Enter처럼 두 줄짜리 키가 있어서 Row로는 배치할 수 없음)
    keyboard_width = 0.0
    keyboard_height = 0.0
    y = 0.0

    for data_list in KEYBOARD_BUTTON_DATA:
        x = 0.0
        y += data_list[0].get("y", 0)

        for data in data_list:
            x += data.get("x", 0)
            width = data.get("width", 1)
            height = data.get("height", 1)

            key_button = components.make_key_button(
                {
                    "id": data["id"],
                    "name": data["name"],
                    "width": width * KEY_UNIT_X - KEY_GAP,
                    "height": height * KEY_UNIT_Y - KEY_GAP,
                    "on_hover": lambda e: show_tooltip(e.control),
                    # 다른 키로 바로 옮겨간 경우(그 키의 툴팁이 이미 뜬 경우)는 숨기지 않음
                    "on_out": lambda e: (
                        schedule_hide() if state["key_id"] == e.control.data else None
                    ),
                }
            )
            key_button.left = x * KEY_UNIT_X
            key_button.top = y * KEY_UNIT_Y

            key_buttons[data["id"]] = key_button

            x += width
            keyboard_width = max(keyboard_width, x * KEY_UNIT_X - KEY_GAP)
            keyboard_height = max(keyboard_height, (y + height) * KEY_UNIT_Y - KEY_GAP)

        y += 1

    keyboard_stack = ft.Stack(
        controls=[*key_buttons.values(), tooltip_thing],
        width=keyboard_width,
        height=keyboard_height,
        # 키와 툴팁 그림자가 잘리지 않게
        clip_behavior=ft.ClipBehavior.NONE,
    )

    keyboard = ft.Container(
        content=keyboard_stack,
        bgcolor="#FFFFFF",
        border=ft.Border.all(1, "#B1B1B1"),
        border_radius=ft.BorderRadius.all(8),
        clip_behavior=ft.ClipBehavior.NONE,
        padding=ft.Padding.all(14),
        shadow=[
            ft.BoxShadow(  # inner
                blur_style=ft.BlurStyle.INNER,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.8, "#000000"),
                offset=ft.Offset(1.5, 3),
            ),
            ft.BoxShadow(  # outer
                blur_radius=27,
                spread_radius=7,
                color=ft.Colors.with_opacity(0.25, "#000000"),
                offset=ft.Offset(0, 3),
            ),
        ],
    )

    return ft.View(
        route="/keyboard",
        bgcolor="#595959",
        padding=ft.Padding.all(20),
        controls=[
            ft.Column(
                controls=[
                    components.make_nav_bar({"push_route": page.push_route}),
                    ft.Container(
                        content=keyboard, alignment=ft.Alignment.CENTER, expand=True
                    ),
                ],
                expand=True,
            )
        ],
    )
