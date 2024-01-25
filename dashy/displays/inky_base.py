import abc
import asyncio
from typing import Literal, Protocol, Tuple, Union

from PIL import Image

from dashy.displays import Display


class InkyBaseDisplay(Protocol):
    resolution: Tuple[int, int]

    def show(self) -> None:
        ...


class InkyMonoDisplay(InkyBaseDisplay):
    colour: Literal["red", "black", "yellow"]

    def set_image(self, image: Image) -> None:
        ...


class InkyColourDisplay(InkyBaseDisplay):
    colour: Literal["multi"]

    def set_image(self, image: Image, saturation: float = 0.5) -> None:
        ...


InkyDisplay = Union[InkyMonoDisplay, InkyColourDisplay]


class InkyBase(Display):
    @property
    @abc.abstractmethod
    def device(self) -> InkyDisplay:
        ...

    @property
    def resolution(self) -> Tuple[int, int]:
        return self.device.resolution

    async def show_image(self, image: Image) -> None:
        def render_image() -> None:
            if self.device.colour == "multi":
                self.device.set_image(image, saturation=0.75)
            else:
                self.device.set_image(image)
            self.device.show()

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, render_image)
