from inky.inky_ac073tc1a import Inky

from dashy.displays.inky_base import InkyBase, InkyDisplay


class Impressions73(InkyBase):
    def __init__(self, *, saturation: float = 0.75) -> None:
        super().__init__(saturation=saturation)
        self._device: InkyDisplay = Inky()

    @property
    def device(self) -> InkyDisplay:
        return self._device
