from inky.auto import auto

from dashy.displays.inky_base import InkyBase
from dashy.sensors.gpio_button import GPIOButton


class InkyAuto(InkyBase):
    def __init__(self, *, saturation: float = 0.75) -> None:
        super().__init__(auto(), saturation=saturation)

        if self.device.colour == "multi":
            self.buttons = {
                "A": GPIOButton(5),
                "B": GPIOButton(6),
                "C": GPIOButton(16),
                "D": GPIOButton(24),
            }
