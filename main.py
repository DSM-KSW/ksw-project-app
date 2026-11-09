from __future__ import annotations

import os
import sys

import backend_client

if "--background" not in sys.argv and "--background-probe" not in sys.argv:
    import flet as ft

    import view

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def main(page: ft.Page):
    page.title = "dsm ksw project"
    try:
        backend_client.ensure_background()
    except (OSError, RuntimeError, TimeoutError) as error:
        page.title += " (백엔드 연결 실패)"
        print(f"Backend connection failed: {error}", file=sys.stderr)
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "0x595959"
    page.padding = ft.Padding.all(16)

    page.window.width = 1280
    page.window.height = 720

    def route_change(e: ft.RouteChangeEvent | None = None):
        page.views.clear()

        # stack
        match page.route:
            case "/":
                page.views.append(view.home_view(page))

            case "/keyboard":
                page.views.append(view.home_view(page))
                page.views.append(view.keyboard_view(page))

            case "/mouse":
                page.views.append(view.home_view(page))
                page.views.append(view.mouse_view(page))

            case "/settings":
                page.views.append(view.home_view(page))
                page.views.append(view.settings_view(page))

        page.update()

    # 뒤로가기
    async def view_pop(e: ft.ViewPopEvent):
        page.views.pop()
        top_view = page.views[-1]
        await page.push_route(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    # 맨 처음 이동할 때는 await page.push_route("/")가 안 되더라구요.
    # / -> /라서 변경 없음으로 처리한다나 뭐라나.
    route_change()


if __name__ == "__main__":
    if "--background" in sys.argv:
        from backend.app import run_background

        run_background()
    elif "--background-probe" in sys.argv:
        probe_log = os.environ.get("KSW_PROBE_LOG")
        if probe_log:
            with open(probe_log, "a", encoding="utf-8") as log:
                log.write("entered\n")
        backend_client.ensure_background()
        if probe_log:
            with open(probe_log, "a", encoding="utf-8") as log:
                log.write("connected\n")
    else:
        ft.run(main, assets_dir=ASSETS_DIR)
