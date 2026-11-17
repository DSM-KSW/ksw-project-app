from collections.abc import Awaitable, Callable
from typing import TypedDict

import flet as ft

NAV_COLOR = "#2F2F2F"


class NavBarParameters(TypedDict):
    push_route: Callable[[str], Awaitable[None]]


# 화면 왼쪽 위 메뉴. ">"를 누르면 펼쳐지고 "<"를 누르면 접힌다.
def make_nav_bar(param: NavBarParameters):
    def make_icon(src: str, width: float, height: float, padding: float, on_click):
        return ft.Container(
            content=ft.Image(src=src, width=width, height=height),
            width=44,
            height=44,
            padding=ft.Padding.all(padding),
            alignment=ft.Alignment.CENTER,
            on_click=on_click,
        )

    def make_route_click(route: str):
        async def on_click():
            await param["push_route"](route)

        return on_click

    def toggle():
        expanded = not collapse_icon.visible

        collapse_icon.visible = expanded
        route_icons.visible = expanded
        expand_icon.visible = not expanded

        nav_bar.update()

    expand_icon = make_icon("icons/nav-expand.svg", 44, 44, 0, toggle)
    collapse_icon = make_icon("icons/nav-collapse.svg", 44, 44, 0, toggle)
    route_icons = ft.Row(
        controls=[
            make_icon(
                "icons/nav-settings.svg", 36, 36, 4, make_route_click("/settings")
            ),
            make_icon("icons/nav-mouse.svg", 32, 32, 6, make_route_click("/mouse")),
            make_icon(
                "icons/nav-keyboard.svg",
                28.9267,
                21.46,
                6,
                make_route_click("/keyboard"),
            ),
        ],
        spacing=10,
    )

    collapse_icon.visible = False
    route_icons.visible = False

    nav_bar = ft.Container(
        content=ft.Row(
            controls=[expand_icon, collapse_icon, route_icons], spacing=10, tight=True
        ),
        bgcolor=NAV_COLOR,
        border_radius=ft.BorderRadius.all(20),
        padding=ft.Padding.all(10),
    )

    return nav_bar
