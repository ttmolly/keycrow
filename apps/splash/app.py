from core.app import BaseApp
import ui.splash_menu as splash_menu
import core.config as config


class SplashSettingsApp(BaseApp):
    """
    Splash Settings menu.
    Owns Current / Edit / Back.
    Edit still hands off to legacy edit flow for now.
    """

    name = "splash_settings"

    def __init__(self):
        self.selected = 0
        self.scroll_offset = 0

    def on_enter(self):
        self.selected = 0
        self.scroll_offset = 0

    def draw(self, device):
        self.scroll_offset = splash_menu.draw(
            device, self.selected, self.scroll_offset
        )

    def handle_input(self, button: str):
        # 0 = Current, 1 = Edit, 2 = Back
        if button == "UP":
            self.selected = (self.selected - 1) % 3
            return None

        if button == "DOWN":
            self.selected = (self.selected + 1) % 3
            return None

        if button in ("LEFT", "RIGHT") and self.selected == 0:
            available = splash_menu.get_available_splashes()
            current_name = config.get_splash()
            try:
                idx = available.index(current_name)
            except ValueError:
                idx = 0
            if button == "LEFT":
                idx = (idx - 1) % len(available)
            else:
                idx = (idx + 1) % len(available)
            config.set_splash(available[idx])
            return None

        if button == "OK":
            if self.selected == 1:
                return "splash_edit_pick"
            if self.selected == 2:
                return "back"
            return None

        if button == "BACK":
            return "back"

        return None
