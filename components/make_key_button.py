from typing import TypedDict

import flet as ft

from components.make_hover_icon import is_hover_enter

KEY_COLOR = "#D3D3D3"
KEY_HIGHLIGHT_COLOR = "#00C3D0"


class KeyButtonParameters(TypedDict):
    id: str
    name: str
    width: float
    height: float
    on_hover: ft.ControlEventHandler[ft.Container]
    on_out: ft.ControlEventHandler[ft.Container]


def make_key_button(param: KeyButtonParameters):
    def on_hover(e: ft.Event[ft.Container]):
        if is_hover_enter(e):
            param["on_hover"](e)
        else:
            param["on_out"](e)

    return ft.Container(
        content=ft.Text(param["name"], size=12, color="#000000"),
        alignment=ft.Alignment.CENTER,
        width=param["width"],
        height=param["height"],
        bgcolor=KEY_COLOR,
        border_radius=ft.BorderRadius.all(6),
        shadow=ft.BoxShadow(
            blur_radius=4,
            color=ft.Colors.with_opacity(0.25, "#000000"),
            offset=ft.Offset(1, 2),
        ),
        data=param["id"],
        on_hover=on_hover,
    )
