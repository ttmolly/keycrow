from core.app import BaseApp
import ui.splash_menu as splash_menu
import ui.splash_edit as splash_edit


class SplashEditPickApp(BaseApp):
    """
    Pick which splash to edit.

    Editing itself (splash_edit.run_edit) is still a blocking call — same
    as the splash intro animation (ui/splash.py) already is. Blocking here
    is fine: it only runs while OK is held down on this one menu, same as
    WifiApp already does for its "Connect" flow. What changed is that this
    is now a normal app instead of a special case hand-rolled inside the
    main loop.
    """

    name = "splash_edit_pick"

    def __init__(self, save_app):
        self.save_app = save_app
        self.selected = 0
        self.scroll_offset = 0
        self.device = None
        self.buttons = None

    def on_enter(self):
        self.selected = 0
        self.scroll_offset = 0

    def draw(self, device):
        self.scroll_offset = splash_menu.draw_edit_pick(
            device, self.selected, self.scroll_offset
        )

    def handle_input(self, button: str):
        items = splash_menu.get_edit_items()

        if button == "UP":
            self.selected = (self.selected - 1) % len(items)
            return None

        if button == "DOWN":
            self.selected = (self.selected + 1) % len(items)
            return None

        if button == "OK":
            choice = items[self.selected]
            if choice == "Back":
                return "back"

            result = splash_edit.run_edit(self.device, self.buttons, choice)
            if result is None:
                return None

            values, raw_frames = result
            self.save_app.set_pending(choice, values, raw_frames)
            return "splash_edit_save"

        if button == "BACK":
            return "back"

        return None


class SplashEditSaveApp(BaseApp):
    """Confirm how to save an edited splash: as new, replace, or cancel."""

    name = "splash_edit_save"

    def __init__(self):
        self.selected = 0
        self.scroll_offset = 0
        self.device = None
        self.buttons = None
        self._pending = None

    def set_pending(self, name, values, raw_frames):
        self._pending = (name, values, raw_frames)

    def on_enter(self):
        self.selected = 0
        self.scroll_offset = 0

    def draw(self, device):
        self.scroll_offset = splash_edit.draw_save(
            device, self.selected, self.scroll_offset
        )

    def handle_input(self, button: str):
        items = splash_edit.SAVE_ITEMS

        if button == "UP":
            self.selected = (self.selected - 1) % len(items)
            return None

        if button == "DOWN":
            self.selected = (self.selected + 1) % len(items)
            return None

        if button == "OK":
            choice = items[self.selected]
            if self._pending is not None and choice in ("Save as New", "Replace Original"):
                name, values, raw_frames = self._pending
                mode = "new" if choice == "Save as New" else "replace"
                splash_edit.save_edit(name, values, raw_frames, mode=mode)
            self._pending = None
            return "splash_edit_pick"

        if button == "BACK":
            self._pending = None
            return "back"

        return None
