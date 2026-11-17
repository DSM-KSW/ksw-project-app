"""키보드 화면이 리매핑을 백엔드(backend_client)에 실제로 저장·삭제하는지 확인한다."""

import importlib
import unittest
from types import SimpleNamespace
from unittest import mock

import flet as ft

from view.key_codes import KEY_VK, VK_KEY, canonical_vk

# view/__init__.py가 같은 이름의 함수를 내보내므로 모듈은 importlib로 가져온다
kv = importlib.import_module("view.keyboard_view")

G, CTRL, WIN, LEFT = 0x47, 0xA2, 0x5B, 0x25


class KeyCodeTests(unittest.TestCase):
    def test_every_key_on_screen_has_a_vk_code(self):
        key_ids = {d["id"] for row in kv.KEYBOARD_BUTTON_DATA for d in row}
        self.assertEqual(key_ids - KEY_VK.keys(), set())

    def test_vk_codes_map_back_to_keys(self):
        for vk in KEY_VK.values():
            self.assertIn(vk, VK_KEY)
        self.assertEqual(VK_KEY[0x11], "left-ctrl")  # 백엔드 예시가 쓰는 공용 Ctrl
        self.assertEqual(canonical_vk(0xA3), canonical_vk(0xA2))

    def test_labels(self):
        binding = {"keys": [G], "mouse": None, "output": [0x11, WIN, LEFT]}
        self.assertEqual(kv.remapping_label(binding, "g"), "→ Ctrl+Win+←")
        chord = {"keys": [CTRL, G], "mouse": None, "output": [0x41]}
        self.assertEqual(kv.remapping_label(chord, "g"), "Ctrl+G → A")
        self.assertEqual(kv.bindings_for_key([binding, chord], "left-ctrl"), [chord])


class FakePage:
    def run_task(self, handler):
        return mock.Mock()

    async def push_route(self, route):
        pass


def hover(control):
    control.on_hover(SimpleNamespace(data=True, control=control))


class KeyboardViewTests(unittest.TestCase):
    def setUp(self):
        self.bindings = []
        client = mock.patch.multiple(
            kv.backend_client,
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
        view = kv.keyboard_view(FakePage())
        body = view.controls[0].controls[1].content
        self.panel, keyboard = body.controls
        stack = keyboard.content
        self.keys = {c.data: c for c in stack.controls[:-1]}
        self.tooltip = stack.controls[-1]

    def fake_set(self, keys, output, mouse=None):
        self.bindings = [b for b in self.bindings if b["keys"] != keys]
        self.bindings.append({"keys": keys, "mouse": mouse, "output": output})

    def fake_delete(self, keys, mouse=None):
        self.bindings = [b for b in self.bindings if b["keys"] != keys]

    def tooltip_rows(self):
        return self.tooltip.content.content.controls

    def panel_parts(self):
        return self.panel.content.controls  # [text, 저장, 취소]

    def test_add_remapping_saves_to_backend(self):
        hover(self.keys["g"])
        self.assertTrue(self.tooltip.visible)
        self.tooltip_rows()[-1].on_click()  # + 버튼
        self.assertFalse(self.tooltip.visible)

        for key_id in ("left-ctrl", "left-win", "arrow-left"):
            self.keys[key_id].on_click(SimpleNamespace(control=self.keys[key_id]))
        text, save, _ = self.panel_parts()
        self.assertEqual(text.value, "G → Ctrl+Win+←")
        self.assertEqual(self.keys["g"].bgcolor, kv.KEY_SOURCE_COLOR)

        save.on_click()
        kv.backend_client.set_binding.assert_called_once_with([G], [CTRL, WIN, LEFT])
        self.assertFalse(save.visible)

        hover(self.keys["g"])
        labels = [row.content.controls[0].value for row in self.tooltip_rows()[:-1]]
        self.assertEqual(labels, ["→ Ctrl+Win+←"])

    def test_clicking_a_selected_key_again_removes_it(self):
        hover(self.keys["g"])
        self.tooltip_rows()[-1].on_click()
        ctrl = self.keys["left-ctrl"]
        ctrl.on_click(SimpleNamespace(control=ctrl))
        ctrl.on_click(SimpleNamespace(control=ctrl))
        text, save, _ = self.panel_parts()
        save.on_click()
        kv.backend_client.set_binding.assert_not_called()
        self.assertIn("하나 이상", text.value)

    def test_delete_remapping_calls_backend(self):
        self.bindings = [{"keys": [G], "mouse": None, "output": [0x41]}]
        self.build_view()  # 화면을 다시 만들어 저장된 리매핑을 읽게 한다
        hover(self.keys["g"])
        row = self.tooltip_rows()[0]
        delete_icon = row.content.controls[1].controls[1]
        delete_icon.on_click()
        kv.backend_client.delete_binding.assert_called_once_with([G], None)
        self.assertEqual(len(self.tooltip_rows()), 1)  # + 버튼만 남음

    def test_f12_cannot_be_a_source_key(self):
        hover(self.keys["func-12"])
        self.tooltip_rows()[-1].on_click()
        text, save, _ = self.panel_parts()
        self.assertFalse(save.visible)
        self.assertIn("F12", text.value)


if __name__ == "__main__":
    unittest.main()
