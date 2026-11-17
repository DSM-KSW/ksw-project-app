from collections.abc import Callable
from typing import TypedDict

import flet as ft

PANEL_COLOR = "#2F2F2F"
PANEL_HEIGHT = 52


class EditPanelParameters(TypedDict):
    width: float
    on_save: Callable[[], None]
    on_cancel: Callable[[], None]


# 키보드/마우스 위 안내·편집 줄.
# 평소에는 안내 문구, 리매핑 편집 중에는 "G → Ctrl+Win+←"와 저장·취소 버튼을 보여준다.
def make_edit_panel(param: EditPanelParameters):
    text = ft.Text("", size=16, color="#FFFFFF")
    save = ft.Button(content="저장", on_click=lambda: param["on_save"]())
    cancel = ft.TextButton(
        content="취소",
        on_click=lambda: param["on_cancel"](),
        style=ft.ButtonStyle(color="#FFFFFF"),
    )
    return ft.Container(
        content=ft.Row(
            controls=[text, save, cancel],
            spacing=12,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        width=param["width"],
        height=PANEL_HEIGHT,
        bgcolor=PANEL_COLOR,
        border_radius=ft.BorderRadius.all(12),
        padding=ft.Padding.symmetric(horizontal=16),
    )


def set_edit_panel(panel: ft.Container, text: str, editing: bool):
    label, save, cancel = panel.content.controls
    label.value = text
    save.visible = editing
    cancel.visible = editing
