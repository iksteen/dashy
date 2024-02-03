from dashy.services import ServiceProvider
from dashy.vendor import asyncpio


class AsyncpioProvider(ServiceProvider[asyncpio.pi]):
    pi: asyncpio.pi

    async def start(self) -> asyncpio.pi:
        self.pi = asyncpio.pi()
        await self.pi.connect()
        return self.pi

    async def stop(self) -> None:
        await self.pi.stop()
