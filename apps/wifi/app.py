from core.app import BaseApp
import ui.wifi_menu as wifi_menu
from apps.wifi_scan import scan_networks


class WifiApp(BaseApp):
    name = "wifi"

    def __init__(self):
        self.selected = 0
        self.scroll_offset = 0
        self.device = None
        self.buttons = None

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
                print("Scanning WiFi...")
                nets = scan_networks()
                print("Found:", nets)
                return None
            if choice == "Connect":
                try:
                    import ui.wifi_setup as wifi_setup
                    if self.device and self.buttons:
                        wifi_setup.run(self.device, self.buttons)
                except Exception as e:
                    print("WiFi setup error:", e)
                return None
            if choice == "Back":
                return "back"
            return None

        if button == "BACK":
            return "back"

        return None
