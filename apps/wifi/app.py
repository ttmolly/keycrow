from core.app import BaseApp
import ui.wifi_menu as wifi_menu


class WifiApp(BaseApp):
    """
    Third KeyCrow application.
    Owns the WiFi Tools menu workflow.
    Still uses ui.wifi_menu for drawing (temporary).
    Does not own scan/connect logic yet.
    """

    name = "wifi"

    def __init__(self):
        self.selected = 0
        self.scroll_offset = 0

    def on_enter(self):
        self.selected = 0
        self.scroll_offset = 0

    def draw(self, device):
        self.scroll_offset = wifi_menu.draw(
            device, self.selected, self.scroll_offset
        )

    def handle_input(self, button: str):
        max_idx = len(wifi_menu.ITEMS) - 1

        if button == "UP":
            self.selected = (self.selected - 1) % (max_idx + 1)
            return None

        if button == "DOWN":
            self.selected = (self.selected + 1) % (max_idx + 1)
            return None

        if button == "OK":
            choice = wifi_menu.ITEMS[self.selected]
            if choice == "Scan Networks":
                return "scan"
            if choice == "Connect":
                return "connect"
            if choice == "Back":
                return "back"
            return None

        if button == "BACK":
            return "back"

        return None
