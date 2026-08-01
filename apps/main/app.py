from core.app import BaseApp
import ui.main_menu as main_menu


class MainMenuApp(BaseApp):
    """
    First real KeyCrow application.
    Owns the Main Menu workflow.
    Still uses ui.main_menu for drawing (temporary).
    """

    name = "main"

    def __init__(self):
        self.selected = 0
        self.scroll_offset = 0

    def on_enter(self):
        self.selected = 0
        self.scroll_offset = 0

    def draw(self, device):
        self.scroll_offset = main_menu.draw(
            device, self.selected, self.scroll_offset
        )

    def handle_input(self, button: str):
        max_idx = len(main_menu.ITEMS) - 1

        if button == "UP":
            self.selected = (self.selected - 1) % (max_idx + 1)
            return None

        if button == "DOWN":
            self.selected = (self.selected + 1) % (max_idx + 1)
            return None

        if button == "OK":
            choice = main_menu.ITEMS[self.selected]
            if choice == "WiFi Tools":
                return "wifi"
            if choice == "Settings":
                return "settings"
            print(f"Selected: {choice}")
            return None

        if button == "BACK":
            return "splash"

        return None
