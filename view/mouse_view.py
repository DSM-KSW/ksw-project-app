import flet as ft

import components


# 디자인 확정 전 자리만 잡아둔 화면 (상단 메뉴만 있음)
def mouse_view(page: ft.Page):
    return ft.View(
        route="/mouse",
        bgcolor="#595959",
        padding=ft.Padding.all(20),
        controls=[components.make_nav_bar({"push_route": page.push_route})],
    )
