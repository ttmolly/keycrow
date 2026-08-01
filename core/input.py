from gpiozero import Button

# Hardware pin map – isolated here so future PCB changes touch one file
PINS = {
    "UP": 17,
    "DOWN": 27,
    "LEFT": 22,
    "RIGHT": 23,
    "OK": 24,
    "BACK": 25,
}


class ButtonInput:
    """
    Owns the physical buttons.
    Isolates GPIO pin mapping from the rest of the system.
    """

    def __init__(self, bounce_time=0.08):
        self._buttons = {
            name: Button(pin, pull_up=True, bounce_time=bounce_time)
            for name, pin in PINS.items()
        }

    def is_pressed(self, name: str) -> bool:
        btn = self._buttons.get(name)
        return btn is not None and btn.is_pressed

    def get(self, name: str):
        """
        Return raw Button object.
        Temporary compatibility for systems like splash that need direct access.
        """
        return self._buttons.get(name)
