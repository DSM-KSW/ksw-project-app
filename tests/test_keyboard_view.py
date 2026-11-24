"""키보드 화면이 리매핑을 백엔드(backend_client)에 실제로 저장·삭제하는지 확인한다."""

import asyncio
import importlib
import unittest
from types import SimpleNamespace
from unittest import mock

import flet as ft

from view.key_codes import KEY_VK, VK_KEY, canonical_vk

# view/__init__.py가 같은 이름의 함수를 내보내므로 모듈은 importlib로 가져온다
kv = importlib.import_module("view.keyboard_view")

G, CTRL, WIN, LEFT, Z, C, F23 = 0x47, 0xA2, 0x5B, 0x25, 0x5A, 0x43, 0x86


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
    route = "/keyboard"
    on_keyboard_event = None

    def __init__(self):
        self.tasks = []

    def run_task(self, handler):
        self.tasks.append(handler)
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
            capture_start=mock.Mock(),
            capture_poll=mock.Mock(side_effect=self.fake_poll),
            capture_cancel=mock.Mock(),
        )
        self.polls = []
        client.start()
        self.addCleanup(client.stop)
        no_update = mock.patch.object(ft.BaseControl, "update", lambda self: None)
        no_update.start()
        self.addCleanup(no_update.stop)
        self.build_view()

    def build_view(self):
        self.page = FakePage()
        view = kv.keyboard_view(self.page)
        top, container = view.controls[0].controls
        self.extra_keys, self.direct_button = top.controls[1].controls
        self.panel, keyboard, self.offscreen = container.content.controls
        stack = keyboard.content
        self.keys = {c.data: c for c in stack.controls[:-1]}
        self.tooltip = stack.controls[-1]

    def fake_poll(self):
        # 준비해 둔 결과를 차례로 돌려주고, 다 쓰면 화면을 떠난 것처럼 해서 캡처 루프를 끝낸다
        if self.polls:
            return self.polls.pop(0)
        self.page.route = "/elsewhere"
        return {"state": "waiting", "keys": []}

    def run_capture(self, *results):
        self.polls = list(results)
        asyncio.run(self.page.tasks[-1]())
        self.page.route = "/keyboard"

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

    def test_pressed_combo_becomes_output(self):
        # Win+Z처럼 Windows가 가로채는 조합도 백엔드 훅 캡처로 받는다
        hover(self.keys["g"])
        self.tooltip_rows()[-1].on_click()
        self.run_capture({"state": "captured", "keys": [WIN, Z]})
        text, save, _ = self.panel_parts()
        self.assertEqual(text.value, "G → Win+Z")
        save.on_click()
        kv.backend_client.set_binding.assert_called_once_with([G], [WIN, Z])
        kv.backend_client.capture_cancel.assert_called()

    def test_escape_cancels_edit(self):
        hover(self.keys["g"])
        self.tooltip_rows()[-1].on_click()
        self.run_capture({"state": "cancelled", "keys": []})
        text, save, _ = self.panel_parts()
        self.assertFalse(save.visible)
        self.assertEqual(text.value, kv.CANCEL_TEXT)

    def test_escape_key_event_cancels_without_backend_capture(self):
        hover(self.keys["g"])
        self.tooltip_rows()[-1].on_click()
        self.page.on_keyboard_event(
            SimpleNamespace(
                key="Escape", shift=False, ctrl=False, alt=False, meta=False
            )
        )
        self.assertFalse(self.panel_parts()[1].visible)

    def test_f12_cannot_be_an_output_key(self):
        hover(self.keys["g"])
        self.tooltip_rows()[-1].on_click()
        f12 = self.keys["func-12"]
        f12.on_click(SimpleNamespace(control=f12))
        text, _, _ = self.panel_parts()
        self.assertIn("F12", text.value)
        self.assertTrue(text.value.startswith("G → ("))

    def test_direct_mapping_for_offscreen_key(self):
        self.assertFalse(self.offscreen.visible)
        self.direct_button.on_click()
        self.assertEqual(self.panel_parts()[0].value, kv.SOURCE_HINT_TEXT)
        self.assertFalse(self.extra_keys.visible)

        # 원래 키(F23)를 누르고, 바꿀 키는 Ctrl+C를 누른다
        self.run_capture(
            {"state": "captured", "keys": [F23]},
            {"state": "captured", "keys": [CTRL, C]},
        )
        text, save, _ = self.panel_parts()
        self.assertEqual(text.value, "F23 → Ctrl+C")
        self.assertTrue(self.extra_keys.visible)
        save.on_click()
        kv.backend_client.set_binding.assert_called_once_with([F23], [CTRL, C])

        # 화면에 없는 키라서 아래 줄에 따로 보인다
        self.assertTrue(self.offscreen.visible)
        chip = self.offscreen.controls[1].content.controls
        self.assertEqual(chip[0].value, "F23 → Ctrl+C")
        chip[2].on_click()  # 삭제
        kv.backend_client.delete_binding.assert_called_once_with([F23], None)
        self.assertFalse(self.offscreen.visible)

    def test_special_key_from_dropdown(self):
        hover(self.keys["g"])
        self.tooltip_rows()[-1].on_click()
        self.extra_keys.value = str(F23)
        self.extra_keys.on_select(SimpleNamespace(control=self.extra_keys))
        self.assertEqual(self.panel_parts()[0].value, "G → F23")


if __name__ == "__main__":
    unittest.main()
