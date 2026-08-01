from core.app import BaseApp
import ui.status_menu as status_menu


class StatusMenusApp(BaseApp):
    """Menu Icons settings (legacy status_menus)."""

    name = "status_menus"

    def __init__(self):
        self.selected = 0
        self.scroll_offset = 0

    def on_enter(self):
        self.selected = 0
        self.scroll_offset = 0

    def draw(self, device):
        self.scroll_offset = status_menu.draw(
            device, self.selected, self.scroll_offset, mode="menus"
        )

    def handle_input(self, button: str):
        items = status_menu.get_menu_items()
        max_idx = len(items) - 1

        if button == "UP":
            self.selected = (self.selected - 1) % (max_idx + 1)
            return None

        if button == "DOWN":
            self.selected = (self.selected + 1) % (max_idx + 1)
            return None

        if button == "OK":
            if self.selected == max_idx:  # Back
                return "back"
            status_menu.toggle("menus", self.selected)
            return None

        if button == "BACK":
            return "back"

        return None
