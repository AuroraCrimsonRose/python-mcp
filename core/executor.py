from __future__ import annotations

import asyncio
import threading
from typing import Any, TypeVar, Coroutine

T = TypeVar("T")


class LoopExecutor:
    def __init__(self):
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None

    # -------------------------
    # START LOOP
    # -------------------------

    def start(self):
        if self._loop:
            return

        def runner():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()

        self._thread = threading.Thread(target=runner, daemon=True)
        self._thread.start()

        while self._loop is None:
            pass

    # -------------------------
    # SUBMIT COROUTINE
    # -------------------------

    def submit(self, coro: Coroutine[Any, Any, T]):
        if not self._loop:
            raise RuntimeError("Executor not started")

        return asyncio.run_coroutine_threadsafe(coro, self._loop)

    # -------------------------
    # SYNC BRIDGE
    # -------------------------

    def run_sync(self, coro: Coroutine[Any, Any, T]) -> T:
        future = self.submit(coro)
        return future.result()

    # -------------------------
    # STOP
    # -------------------------

    def stop(self):
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._loop = None


executor = LoopExecutor()