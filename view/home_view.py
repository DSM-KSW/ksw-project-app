import flet as ft


# 임시 테스트용 화면: 각 화면으로 이동하는 버튼만 둔다
def home_view(page: ft.Page):
    def make_route_button(route: str):
        async def on_click():
            await page.push_route(route)

        return ft.Button(content=route, on_click=on_click)

    return ft.View(
        route="/",
        controls=[
            make_route_button("/keyboard"),
            make_route_button("/mouse"),
            make_route_button("/settings"),
        ],
    )
