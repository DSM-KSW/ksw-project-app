import asyncio
from typing import TypedDict

import flet as ft

import backend_client
import components
from view.key_codes import vks_from_key_event
from view.keyboard_view import TOOLTIP_HIDE_DELAY, vk_label

# Figma MS-1/MS-2(1920x1080) 수치를 키보드 화면과 같이 2/3로 줄여서 쓴다
SCALE = 2 / 3
MOUSE_WIDTH = 320 * SCALE
MOUSE_HEIGHT = 482.222 * SCALE

# 툴팁이 마우스 밖까지 나가도 Stack 안에 있어야 마우스 이벤트를 받으므로 여백을 둔다
STACK_MARGIN_X = components.TOOLTIP_WIDTH
STACK_MARGIN_TOP = 110

BUTTON_HIGHLIGHT_COLOR = components.KEY_HIGHLIGHT_COLOR
HINT_TEXT = "마우스 버튼에 마우스를 올리고 + 를 눌러 리매핑을 추가하세요"
LEFT_CLICK = "왼쪽 클릭"


class MouseButtonData(TypedDict):
    id: str
    name: str  # 백엔드가 쓰는 마우스 입력 이름 (backend/app.py MOUSE_NAMES)
    src: str
    x: float
    y: float
    width: float
    height: float


# Figma 레이어: MB1 왼쪽, MB2 오른쪽, MB5 측면 앞으로(X2), MB4 측면 뒤로(X1)
IMAGE_BUTTONS: list[MouseButtonData] = [
    {
        "id": "mb1",
        "name": LEFT_CLICK,
        "src": "mouse/mb1-left.svg",
        "x": 49.63,
        "y": 11.11,
        "width": 124.444,
        "height": 234.444,
    },
    {
        "id": "mb2",
        "name": "오른쪽 클릭",
        "src": "mouse/mb2-right.svg",
        "x": 186.67,
        "y": 10,
        "width": 122.222,
        "height": 234.444,
    },
    {
        "id": "mb5",
        "name": "마우스 X2",
        "src": "mouse/mb5-forward.svg",
        "x": 14.07,
        "y": 183.7,
        "width": 27.7778,
        "height": 68.8889,
    },
    {
        "id": "mb4",
        "name": "마우스 X1",
        "src": "mouse/mb4-back.svg",
        "x": 8.14,
        "y": 233.33,
        "width": 27.7778,
        "height": 72.2222,
    },
]
WHEEL_NAME = "가운데 클릭"  # MB3 휠 클릭

MOUSE_LABELS = {
    LEFT_CLICK: "왼쪽 버튼",
    "오른쪽 클릭": "오른쪽 버튼",
    WHEEL_NAME: "휠 클릭",
    "마우스 X1": "측면 뒤로 버튼",
    "마우스 X2": "측면 앞으로 버튼",
}


def s(value: float) -> float:
    return value * SCALE


def binding_for_button(bindings: list[dict], name: str) -> list[dict]:
    return [b for b in bindings if b.get("mouse") == name and not b["keys"]]


def place(control: ft.Control, x: float, y: float, width: float, height: float):
    control.left = STACK_MARGIN_X + s(x)
    control.top = STACK_MARGIN_TOP + s(y)
    control.width = s(width)
    control.height = s(height)
    return control


def make_image(src: str, x: float, y: float, width: float, height: float):
    return place(ft.Image(src=src, fit=ft.BoxFit.FILL), x, y, width, height)


def make_wheel():
    # MB3 · 휠 클릭: Figma에서 이미지가 아니라 도형으로 그려져 있다
    wheel = ft.Container(
        width=s(24.444),
        height=s(103.333),
        left=s(7.77),
        top=s(7.78),
        bgcolor="#E5E7EB",
        border=ft.Border.all(s(1.111), "#B4B4B4"),
        border_radius=ft.BorderRadius.all(s(11.111)),
    )
    treads = [
        ft.Container(
            left=s(11.11),
            top=s(24.45 + 10 * i),
            width=s(17.778),
            height=s(2.222),
            bgcolor="#9CA3AF",
            border_radius=ft.BorderRadius.all(s(1.111)),
        )
        for i in range(8)
    ]
    recess = ft.Container(
        width=s(40),
        height=s(125.556),
        bgcolor="#F3F4F6",
        border=ft.Border.all(s(0.741), "#B4B4B4"),
        border_radius=ft.BorderRadius.all(s(15.556)),
    )
    return wheel, ft.Stack(controls=[recess, wheel, *treads])


def mouse_view(page: ft.Page):
    # name: 툴팁이 떠 있는 버튼, editing: 편집 중인 {"mouse": 이름, "output": [VK]}
    state: dict = {
        "name": None,
        "hide_task": None,
        "bindings": [],
        "editing": None,
        "message": None,
    }
    buttons: dict[str, ft.Container] = {}

    def load_bindings():
        try:
            state["bindings"] = backend_client.list_bindings()
        except (OSError, RuntimeError, TimeoutError) as error:
            state["bindings"] = []
            state["message"] = f"백엔드 연결 실패: {error}"

    def set_highlight(names: set[str]):
        for name, button in buttons.items():
            on = name in names
            if name == WHEEL_NAME:
                wheel.bgcolor = BUTTON_HIGHLIGHT_COLOR if on else "#E5E7EB"
            else:
                image = button.content
                image.color = BUTTON_HIGHLIGHT_COLOR if on else None
                image.color_blend_mode = ft.BlendMode.MODULATE if on else None

    def render_panel():
        editing = state["editing"]
        if editing is None:
            text = state["message"] or HINT_TEXT
            set_highlight(set())
        else:
            output = vk_label(editing["output"]) or "(바꿀 키 조합을 키보드로 누르세요)"
            text = f"{MOUSE_LABELS[editing['mouse']]} → {output}"
            if state["message"]:
                text += f"   ·   {state['message']}"
            set_highlight({editing["mouse"]})
        components.set_edit_panel(panel, text, editing is not None)

    def update_all():
        render_panel()
        panel.update()
        mouse_stack.update()

    def cancel_hide():
        if state["hide_task"] is not None:
            state["hide_task"].cancel()
            state["hide_task"] = None

    def hide_tooltip():
        state["name"] = None
        tooltip_thing.visible = False
        if state["editing"] is None:
            set_highlight(set())
        mouse_stack.update()

    def schedule_hide():
        cancel_hide()

        async def hide_later():
            await asyncio.sleep(TOOLTIP_HIDE_DELAY)
            state["hide_task"] = None
            hide_tooltip()

        state["hide_task"] = page.run_task(hide_later)

    def start_edit(name: str, output: list[int]):
        cancel_hide()
        state["name"] = None
        tooltip_thing.visible = False
        state["editing"] = {"mouse": name, "output": output}
        state["message"] = (
            "주의: 왼쪽 클릭을 바꾸면 F12로 일시정지하기 전까지 클릭이 바뀝니다"
            if name == LEFT_CLICK
            else None
        )
        update_all()

    def finish_edit(message: str | None = None):
        state["editing"] = None
        state["message"] = message
        update_all()

    def save_edit():
        editing = state["editing"]
        if not editing["output"]:
            state["message"] = "바꿀 키를 하나 이상 누르세요"
            update_all()
            return
        try:
            backend_client.set_binding([], editing["output"], mouse=editing["mouse"])
        except (OSError, RuntimeError, TimeoutError) as error:
            state["message"] = f"저장 실패: {error}"
            update_all()
            return
        load_bindings()
        finish_edit(
            f"저장됨: {MOUSE_LABELS[editing['mouse']]} → {vk_label(editing['output'])}"
        )

    # 편집 중에는 실제 키보드로 누른 조합을 결과 키로 받는다
    def on_keyboard(e: ft.KeyboardEvent):
        if state["editing"] is None or page.route != "/mouse":
            return
        output = vks_from_key_event(e.key, e.shift, e.ctrl, e.alt, e.meta)
        if output is None:
            state["message"] = f"지원하지 않는 키: {e.key}"
        else:
            state["editing"]["output"] = output
            state["message"] = None
        update_all()

    page.on_keyboard_event = on_keyboard

    def refresh_tooltip():
        name = state["name"]
        rows = binding_for_button(state["bindings"], name)

        def on_delete(index: int):
            try:
                backend_client.delete_binding([], mouse=name)
                state["message"] = None
            except (OSError, RuntimeError, TimeoutError) as error:
                state["message"] = f"삭제 실패: {error}"
            load_bindings()
            render_panel()
            panel.update()
            refresh_tooltip()
            place_tooltip(buttons[name])
            set_highlight({name})
            mouse_stack.update()

        components.set_tooltip_remappings(
            tooltip_thing,
            {
                "labels": [f"→ {vk_label(b['output'])}" for b in rows],
                "on_add": lambda: start_edit(name, []),
                "on_edit": lambda index: start_edit(name, list(rows[index]["output"])),
                "on_delete": on_delete,
                "on_row_hover": lambda index: None,
                "on_row_out": lambda index: None,
            },
        )

    # 버튼 바로 위에 툴팁을 붙인다. Stack 밖으로 나가지 않게 좌우를 당긴다.
    def place_tooltip(button: ft.Container):
        rows = binding_for_button(state["bindings"], button.data)
        height = components.tooltip_height(len(rows))
        left = button.left + (button.width - components.TOOLTIP_WIDTH) / 2
        tooltip_thing.left = min(max(left, 0), stack_width - components.TOOLTIP_WIDTH)
        tooltip_thing.top = max(button.top - height, 0)

    def show_tooltip(button: ft.Container):
        if state["editing"] is not None:
            return
        cancel_hide()
        state["name"] = button.data
        refresh_tooltip()
        place_tooltip(button)
        tooltip_thing.visible = True
        set_highlight({button.data})
        mouse_stack.update()

    def on_hover(e: ft.Event[ft.Container]):
        if components.is_hover_enter(e):
            show_tooltip(e.control)
        elif state["name"] == e.control.data:
            schedule_hide()

    tooltip_thing = components.make_tooltip(
        {"on_hover": cancel_hide, "on_out": schedule_hide}
    )
    tooltip_thing.visible = False

    for data in IMAGE_BUTTONS:
        image = ft.Image(src=data["src"], fit=ft.BoxFit.FILL)
        buttons[data["name"]] = place(
            ft.Container(content=image, data=data["name"], on_hover=on_hover),
            data["x"],
            data["y"],
            data["width"],
            data["height"],
        )

    wheel, wheel_stack = make_wheel()
    buttons[WHEEL_NAME] = place(
        ft.Container(content=wheel_stack, data=WHEEL_NAME, on_hover=on_hover),
        158.89,
        41.11,
        40,
        125.556,
    )

    stack_width = MOUSE_WIDTH + STACK_MARGIN_X * 2
    mouse_stack = ft.Stack(
        controls=[
            make_image("mouse/chassis.svg", 22.96, 0, 297.046, 482.222),
            make_image("mouse/palm-shell.svg", 35.55, 8.89, 274.444, 461.111),
            buttons[LEFT_CLICK],
            buttons["오른쪽 클릭"],
            # 휠은 왼쪽/오른쪽 버튼 영역과 겹치므로 그 위에 둔다
            buttons[WHEEL_NAME],
            buttons["마우스 X2"],
            buttons["마우스 X1"],
            make_image("mouse/shell-parting-line.svg", 57.77, 262.15, 242.581, 14.9818),
            tooltip_thing,
        ],
        width=stack_width,
        height=MOUSE_HEIGHT + STACK_MARGIN_TOP,
        clip_behavior=ft.ClipBehavior.NONE,
    )

    panel = components.make_edit_panel(
        {"width": 760, "on_save": save_edit, "on_cancel": finish_edit}
    )

    load_bindings()
    render_panel()

    return ft.View(
        route="/mouse",
        bgcolor="#595959",
        padding=ft.Padding.all(20),
        controls=[
            ft.Column(
                controls=[
                    components.make_nav_bar({"push_route": page.push_route}),
                    ft.Container(
                        content=ft.Column(
                            controls=[panel, mouse_stack],
                            spacing=0,
                            tight=True,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        alignment=ft.Alignment.CENTER,
                        expand=True,
                    ),
                ],
                expand=True,
            )
        ],
    )
