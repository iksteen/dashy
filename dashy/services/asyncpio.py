from dashy.services import ServiceProvider
from dashy.vendor.asyncpio import pi


class AsyncpioProvider(ServiceProvider[pi]):
    _pi: pi

    async def start(self) -> pi:
        self._pi = pi()
        await self._pi.connect()
        return self._pi

    async def stop(self) -> None:
        await self._pi.stop()
