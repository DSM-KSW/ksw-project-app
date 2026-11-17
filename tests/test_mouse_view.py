"""마우스 화면이 마우스 버튼 리매핑을 백엔드(backend_client)에 저장·삭제하는지 확인한다."""

import importlib
import unittest
from types import SimpleNamespace
from unittest import mock

import flet as ft

from view.key_codes import vks_from_key_event

# view/__init__.py가 같은 이름의 함수를 내보내므로 모듈은 importlib로 가져온다
mv = importlib.import_module("view.mouse_view")

CTRL, WIN, LEFT = 0xA2, 0x5B, 0x25


class KeyEventTests(unittest.TestCase):
    def test_combo_from_flet_key_event(self):
        self.assertEqual(
            vks_from_key_event("Arrow Left", False, True, False, True),
            [CTRL, WIN, LEFT],
        )
        self.assertEqual(vks_from_key_event("g", False, False, False, False), [0x47])
        # Ctrl만 누르면 Ctrl 하나 (ctrl 플래그와 중복되지 않게)
        self.assertEqual(
            vks_from_key_event("Control Left", False, True, False, False), [CTRL]
        )
        self.assertIsNone(vks_from_key_event("Launch Mail", False, False, False, False))


class FakePage:
    route = "/mouse"
    on_keyboard_event = None

    def run_task(self, handler):
        return mock.Mock()

    async def push_route(self, route):
        pass


class MouseViewTests(unittest.TestCase):
    def setUp(self):
        self.bindings = []
        client = mock.patch.multiple(
            mv.backend_client,
            list_bindings=mock.Mock(side_effect=lambda: list(self.bindings)),
            set_binding=mock.Mock(side_effect=self.fake_set),
            delete_binding=mock.Mock(side_effect=self.fake_delete),
        )
        client.start()
        self.addCleanup(client.stop)
        no_update = mock.patch.object(ft.BaseControl, "update", lambda self: None)
        no_update.start()
        self.addCleanup(no_update.stop)
        self.build_view()

    def build_view(self):
        self.page = FakePage()
        view = mv.mouse_view(self.page)
        body = view.controls[0].controls[1].content
        self.panel, self.stack = body.controls
        self.buttons = {
            c.data: c for c in self.stack.controls if isinstance(c.data, str)
        }
        self.tooltip = self.stack.controls[-1]

    def fake_set(self, keys, output, mouse=None):
        self.bindings = [b for b in self.bindings if b["mouse"] != mouse]
        self.bindings.append({"keys": keys, "mouse": mouse, "output": output})

    def fake_delete(self, keys, mouse=None):
        self.bindings = [b for b in self.bindings if b["mouse"] != mouse]

    def hover(self, name):
        button = self.buttons[name]
        button.on_hover(SimpleNamespace(data=True, control=button))

    def rows(self):
        return self.tooltip.content.content.controls

    def test_has_all_design_buttons(self):
        self.assertEqual(
            set(self.buttons),
            {"왼쪽 클릭", "오른쪽 클릭", "가운데 클릭", "마우스 X1", "마우스 X2"},
        )

    def test_add_side_button_remapping(self):
        self.hover("마우스 X1")
        self.assertTrue(self.tooltip.visible)
        self.rows()[-1].on_click()  # +
        self.page.on_keyboard_event(
            SimpleNamespace(
                key="Arrow Left", shift=False, ctrl=True, alt=False, meta=True
            )
        )
        text, save, _ = self.panel.content.controls
        self.assertEqual(text.value, "측면 뒤로 버튼 → Ctrl+Win+←")
        save.on_click()
        mv.backend_client.set_binding.assert_called_once_with(
            [], [CTRL, WIN, LEFT], mouse="마우스 X1"
        )
        self.hover("마우스 X1")
        self.assertEqual(self.rows()[0].content.controls[0].value, "→ Ctrl+Win+←")

    def test_delete_wheel_remapping(self):
        self.bindings = [{"keys": [], "mouse": "가운데 클릭", "output": [0x41]}]
        self.build_view()
        self.hover("가운데 클릭")
        self.rows()[0].content.controls[1].controls[1].on_click()  # 삭제
        mv.backend_client.delete_binding.assert_called_once_with(
            [], mouse="가운데 클릭"
        )
        self.assertEqual(len(self.rows()), 1)

    def test_left_click_shows_warning(self):
        self.hover("왼쪽 클릭")
        self.rows()[-1].on_click()
        self.assertIn("주의", self.panel.content.controls[0].value)


if __name__ == "__main__":
    unittest.main()
