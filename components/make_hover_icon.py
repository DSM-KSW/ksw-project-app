from collections.abc import Awaitable, Callable
from typing import NotRequired, TypedDict

import flet as ft


class HoverIconParameters(TypedDict):
    src: str  # 평소 아이콘 (assets 기준 경로)
    hover_src: str  # 마우스를 올렸을 때 아이콘
    width: float
    height: float
    on_click: NotRequired[Callable[[], Awaitable[None] | None]]


def is_hover_enter(e: ft.Event) -> bool:
    # 들어올 때 True, 나갈 때 False ("true"/"false" 문자열로 오는 경우도 처리)
    return e.data is True or e.data == "true"


def make_hover_icon(param: HoverIconParameters):
    image = ft.Image(src=param["src"], width=param["width"], height=param["height"])

    def on_hover(e: ft.Event[ft.Container]):
        image.src = param["hover_src"] if is_hover_enter(e) else param["src"]
        image.update()

    return ft.Container(
        content=image, on_hover=on_hover, on_click=param.get("on_click")
    )
