from typing import TYPE_CHECKING

from dashy.services import ServiceProvider
from dashy.vendor.asyncpio import pi  # type: ignore

if TYPE_CHECKING:
    pi = type  # noqa: F811


class AsyncpioProvider(ServiceProvider[pi]):
    pi: pi

    async def start(self) -> pi:
        self.pi = pi()
        await self.pi.connect()
        return self.pi

    async def stop(self) -> None:
        await self.pi.stop()


__all__ = ["AsyncpioProvider", "pi"]
