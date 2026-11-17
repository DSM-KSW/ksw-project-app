from collections.abc import Callable
from typing import TypedDict

import flet as ft

from components.make_hover_icon import is_hover_enter, make_hover_icon

TOOLTIP_WIDTH = 216
TOOLTIP_GAP = 8  # 키와 툴팁 사이 여백(px)

# 툴팁 높이를 미리 계산하기 위한 값들 (set_tooltip_remappings가 만드는 구조와 맞춰야 한다)
_PADDING_Y = 8  # 흰 박스 위/아래 안쪽 여백
_SPACING = 12  # 줄 사이 간격
_ROW_HEIGHT = 24  # 리매핑 한 줄 높이 (삭제 아이콘 높이)
_ADD_HEIGHT = 24  # 추가 버튼 높이


class TooltipParameters(TypedDict):
    on_hover: Callable[[], None]
    on_out: Callable[[], None]


class RemappingListParameters(TypedDict):
    labels: list[str]  # "리매핑 1: Ctrl+G+C" 같은 표시용 문자열
    on_add: Callable[[], None]
    on_edit: Callable[[int], None]
    on_delete: Callable[[int], None]
    on_row_hover: Callable[[int], None]
    on_row_out: Callable[[int], None]


# 투명 여백까지 포함한 툴팁 전체 높이 (툴팁을 띄울 자리를 고를 때 쓴다)
def tooltip_height(remapping_count: int):
    row_count = remapping_count + 1  # 리매핑 목록 + 추가 버튼

    return (
        _PADDING_Y * 2
        + _ROW_HEIGHT * remapping_count
        + _ADD_HEIGHT
        + _SPACING * (row_count - 1)
        + TOOLTIP_GAP * 2
    )


# 키 위에 뜨는 리매핑 목록 (내용은 set_tooltip_remappings로 채움)
def make_tooltip(param: TooltipParameters):
    def on_hover(e: ft.Event[ft.Container]):
        if is_hover_enter(e):
            param["on_hover"]()
        else:
            param["on_out"]()

    box = ft.Container(
        content=ft.Column(
            controls=[],
            spacing=_SPACING,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        width=TOOLTIP_WIDTH,
        bgcolor="#FFFFFF",
        border_radius=ft.BorderRadius.all(10),
        padding=ft.Padding.symmetric(horizontal=10, vertical=_PADDING_Y),
        shadow=ft.BoxShadow(
            blur_radius=10,
            spread_radius=6,
            color=ft.Colors.with_opacity(0.25, "#000000"),
            offset=ft.Offset(0, 4),
        ),
    )

    # 키에서 툴팁으로 마우스를 옮기는 중에 호버가 끊기지 않게,
    # 위아래로 TOOLTIP_GAP만큼 투명한 여백을 두고 그 영역까지 호버 판정에 넣는다.
    # (키와 맞닿는 쪽이 이 여백이라 마우스가 빈 곳을 지나지 않는다)
    return ft.Container(
        content=box,
        width=TOOLTIP_WIDTH,
        padding=ft.Padding.symmetric(vertical=TOOLTIP_GAP),
        on_hover=on_hover,
    )


def _list_column(tooltip: ft.Container) -> ft.Column:
    # make_tooltip이 만든 구조: 투명 여백 Container > 흰 박스 Container > Column
    return tooltip.content.content


def _make_remapping_row(index: int, label: str, param: RemappingListParameters):
    def on_hover(e: ft.Event[ft.Container]):
        if is_hover_enter(e):
            param["on_row_hover"](index)
        else:
            param["on_row_out"](index)

    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Text(
                    label,
                    size=16,
                    color="#000000",
                    width=140,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                ft.Row(
                    controls=[
                        make_hover_icon(
                            {
                                "src": "icons/setting-off.svg",
                                "hover_src": "icons/setting-on.svg",
                                "width": 22,
                                "height": 22,
                                "on_click": lambda: param["on_edit"](index),
                            }
                        ),
                        make_hover_icon(
                            {
                                "src": "icons/delete-off.svg",
                                "hover_src": "icons/delete-on.svg",
                                "width": 24,
                                "height": 24,
                                "on_click": lambda: param["on_delete"](index),
                            }
                        ),
                    ],
                    spacing=4,
                ),
            ],
            spacing=8,
        ),
        on_hover=on_hover,
    )


def set_tooltip_remappings(tooltip: ft.Container, param: RemappingListParameters):
    rows: list[ft.Control] = [
        _make_remapping_row(i, label, param) for i, label in enumerate(param["labels"])
    ]

    rows.append(
        make_hover_icon(
            {
                "src": "icons/add-off.svg",
                "hover_src": "icons/add-on.svg",
                "width": 196,
                "height": 24,
                "on_click": param["on_add"],
            }
        )
    )

    _list_column(tooltip).controls = rows
