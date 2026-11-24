"""리매핑 편집 중 실제 키보드로 누른 조합을 백엔드 훅에서 받아온다.

Flet 키 이벤트로는 Win+Z처럼 Windows가 먼저 가로채는 조합을 받을 수 없고,
이미 저장된 리매핑이 적용된 키가 들어온다. 그래서 백엔드 키보드 훅이 키를 먹으면서
모아 둔 조합을 짧은 간격으로 가져온다. poll이 끊기면 백엔드가 알아서 캡처를 푼다.
"""

import asyncio
from collections.abc import Callable

import flet as ft

import backend_client

POLL_INTERVAL = 0.05  # 초
ERRORS = (OSError, RuntimeError, TimeoutError, EOFError)


class KeyCapture:
    def __init__(
        self,
        page: ft.Page,
        route: str,
        on_keys: Callable[[list[int]], None],
        on_cancel: Callable[[], None],
        on_error: Callable[[str], None],
    ):
        self.page = page
        self.route = route  # 다른 화면으로 가면 캡처를 끝낸다
        self.on_keys = on_keys
        self.on_cancel = on_cancel
        self.on_error = on_error
        self.task = None
        self.running = False
        self.started = False  # 백엔드에 실제로 capture_start를 보냈는지

    def start(self):
        if self.running:
            return
        self.running = True
        self.task = self.page.run_task(self.run)

    def stop(self):
        self.running = False
        if self.task is not None:
            self.task.cancel()
            self.task = None
        if self.started:
            self.started = False
            try:
                backend_client.capture_cancel()
            except ERRORS:
                pass

    async def run(self):
        try:
            await asyncio.to_thread(backend_client.capture_start)
            self.started = True
            while self.running:
                await asyncio.sleep(POLL_INTERVAL)
                if self.page.route != self.route:
                    self.stop()
                    return
                result = await asyncio.to_thread(backend_client.capture_poll)
                if not self.running:
                    return
                if result["state"] == "captured":
                    self.on_keys(result["keys"])
                    if self.running:
                        await asyncio.to_thread(backend_client.capture_start)
                elif result["state"] == "cancelled":
                    self.running = False
                    self.started = False
                    self.on_cancel()
                elif result["state"] == "idle":
                    # 다른 화면이 캡처를 끝냈거나 시간이 지나 풀렸으면 다시 건다
                    await asyncio.to_thread(backend_client.capture_start)
        except ERRORS as error:
            self.running = False
            self.started = False
            self.on_error(f"키 입력 받기 실패: {error}")
