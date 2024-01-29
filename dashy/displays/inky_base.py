from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Literal, Protocol, Union

from dashy.displays import Display

if TYPE_CHECKING:
    from PIL import Image

    from dashy.sensors.gpio_button import GPIOButton


class InkyBaseDisplay(Protocol):
    resolution: tuple[int, int]

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
    buttons: dict[str, GPIOButton]

    def __init__(self, device: InkyDisplay, *, saturation: float = 0.75) -> None:
        self.device = device
        self.buttons = {}
        self.saturation = saturation

    async def start(self) -> None:
        await super().start()
        for button in self.buttons.values():
            await button.start()

    async def stop(self) -> None:
        await super().stop()
        for button in self.buttons.values():
            await button.stop()

    @property
    def resolution(self) -> tuple[int, int]:
        return self.device.resolution

    async def show_image(self, image: Image) -> None:
        def render_image() -> None:
            if self.device.colour == "multi":
                self.device.set_image(image, saturation=self.saturation)
            else:
                self.device.set_image(image)
            self.device.show()

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, render_image)
