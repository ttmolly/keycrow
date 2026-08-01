from core.app import BaseApp
import ui.settings_menu as settings_menu


class SettingsApp(BaseApp):
    """
    Second KeyCrow application.
    Owns the Settings menu workflow.
    Still uses ui.settings_menu for drawing (temporary).
    """

    name = "settings"

    def __init__(self):
        self.selected = 0
        self.scroll_offset = 0

    def on_enter(self):
        self.selected = 0
        self.scroll_offset = 0

    def draw(self, device):
        self.scroll_offset = settings_menu.draw(
            device, self.selected, self.scroll_offset
        )

    def handle_input(self, button: str):
        max_idx = len(settings_menu.ITEMS) - 1

        if button == "UP":
            self.selected = (self.selected - 1) % (max_idx + 1)
            return None

        if button == "DOWN":
            self.selected = (self.selected + 1) % (max_idx + 1)
            return None

        if button == "OK":
            choice = settings_menu.ITEMS[self.selected]
            if choice == "Status Bar":
                return "status_bar"
            if choice == "Splash":
                return "splash_settings"
            if choice == "Back":
                return "back"
            return None

        if button == "BACK":
            return "back"

        return None
