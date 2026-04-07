import asyncio
import threading
from aiowebostv import WebOsClient
from lib.config import TV_IP, load_key, save_key


class TVConnection:
    def __init__(self, ip=TV_IP):
        self.ip = ip
        self.client = None
        self.loop = None
        self._thread = None

    def start(self, on_connected=None, on_failed=None):
        self._thread = threading.Thread(
            target=self._run, args=(on_connected, on_failed), daemon=True
        )
        self._thread.start()

    def _run(self, on_connected, on_failed):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        async def connect():
            key = load_key(self.ip)
            self.client = WebOsClient(self.ip, client_key=key)
            await self.client.connect()
            if self.client.client_key and self.client.client_key != key:
                save_key(self.client.client_key, self.ip)

        try:
            self.loop.run_until_complete(connect())
            if on_connected:
                on_connected()
        except Exception as e:
            if on_failed:
                on_failed(e)
            return

        self.loop.run_forever()

    def run_async(self, coro):
        if self.loop and self.client:
            asyncio.run_coroutine_threadsafe(coro, self.loop)

    @property
    def tv(self):
        return self.client
