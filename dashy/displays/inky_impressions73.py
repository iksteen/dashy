from inky.inky_ac073tc1a import Inky

from dashy.displays.inky_base import InkyBase
from dashy.sensors.gpio_button import GPIOButton


class Impressions73(InkyBase):
    def __init__(self, *, saturation: float = 0.75) -> None:
        super().__init__(Inky(), saturation=saturation)

        self.buttons = {
            "A": GPIOButton(5),
            "B": GPIOButton(6),
            "C": GPIOButton(16),
            "D": GPIOButton(24),
        }
