import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

WIN, Z, CTRL, ESC, F12 = 0x5B, 0x5A, 0xA2, 0x1B, 0x7B


@unittest.skipUnless(sys.platform == "win32", "Windows hook DLL")
class ComboCaptureTests(unittest.TestCase):
    def setUp(self):
        from backend import app

        self.app = app
        app.combo_cancel()

    def press(self, *keys):
        return [self.app.combo_key(vk, True) for vk in keys]

    def release(self, *keys):
        return [self.app.combo_key(vk, False) for vk in keys]

    def test_not_capturing_lets_keys_through(self):
        self.assertEqual(self.press(Z), [False])

    def test_win_z_is_captured_after_all_keys_released(self):
        self.app.combo_start()
        self.assertEqual(self.press(WIN, Z), [True, True])
        self.release(Z)
        self.assertEqual(self.app.combo_poll()["state"], "held")
        self.release(WIN)
        self.assertEqual(self.app.combo_poll(), {"state": "captured", "keys": [WIN, Z]})
        # 한 번 가져가면 끝난다
        self.assertEqual(self.app.combo_poll()["state"], "idle")
        self.assertEqual(self.press(Z), [False])

    def test_left_and_right_modifier_count_once(self):
        self.app.combo_start()
        self.press(CTRL, 0xA3, Z)
        self.release(Z, 0xA3, CTRL)
        self.assertEqual(self.app.combo_poll()["keys"], [CTRL, Z])

    def test_escape_alone_cancels(self):
        self.app.combo_start()
        self.assertEqual(self.press(ESC), [True])
        self.assertEqual(self.app.combo_poll()["state"], "cancelled")

    def test_escape_inside_a_combo_is_a_key(self):
        self.app.combo_start()
        self.press(CTRL, ESC)
        self.release(ESC, CTRL)
        self.assertEqual(self.app.combo_poll()["keys"], [CTRL, ESC])

    def test_capture_expires_when_ui_stops_polling(self):
        self.app.combo_start()
        with mock.patch.object(self.app.time, "monotonic", return_value=1e12):
            self.assertEqual(self.press(Z), [False])
        self.assertEqual(self.app.combo_poll()["state"], "idle")

    def test_f12_cannot_be_an_output(self):
        binding = {"keys": [0x47], "mouse": None, "output": [F12]}
        with mock.patch.object(self.app, "save_bindings") as save:
            response = self.app.dispatch_ipc({"op": "set_binding", "binding": binding})
        self.assertEqual(response, {"ok": False, "error": "reserved_key"})
        save.assert_not_called()

    def test_capture_ipc_calls(self):
        self.assertTrue(self.app.dispatch_ipc({"op": "capture_start"})["ok"])
        self.assertEqual(
            self.app.dispatch_ipc({"op": "capture_poll"}),
            {"ok": True, "state": "waiting", "keys": []},
        )
        self.assertTrue(self.app.dispatch_ipc({"op": "capture_cancel"})["ok"])
        self.assertEqual(self.app.dispatch_ipc({"op": "capture_poll"})["state"], "idle")


if __name__ == "__main__":
    unittest.main()
