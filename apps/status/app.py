from core.app import BaseApp
import ui.status_menu as status_menu


class StatusApp(BaseApp):
    """
    Status Bar menu application.
    Owns only the top-level Status Bar list (Splash / Menus / Back).
    Sub-screens stay on the legacy path for now.
    """

    name = "status"

    def __init__(self):
        self.selected = 0
        self.scroll_offset = 0

    def on_enter(self):
        self.selected = 0
        self.scroll_offset = 0

    def draw(self, device):
        self.scroll_offset = status_menu.draw(
            device, self.selected, self.scroll_offset, mode="main"
        )

    def handle_input(self, button: str):
        items = status_menu.get_main_items()
        max_idx = len(items) - 1

        if button == "UP":
            self.selected = (self.selected - 1) % (max_idx + 1)
            return None

        if button == "DOWN":
            self.selected = (self.selected + 1) % (max_idx + 1)
            return None

        if button == "OK":
            choice = items[self.selected]
            if choice == "Splash":
                return "status_splash"
            if choice == "Menus":
                return "status_menus"
            if choice == "Back":
                return "back"
            return None

        if button == "BACK":
            return "back"

        return None
