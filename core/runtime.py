from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from time import sleep

import ui.splash as splash
import ui.splash_menu as splash_menu
import ui.splash_edit as splash_edit
import core.config as config
from core.input import ButtonInput
from core.app_manager import AppManager
from apps.main.app import MainMenuApp
from apps.settings.app import SettingsApp
from apps.wifi.app import WifiApp
from apps.status.app import StatusApp
from apps.status.splash_icons import StatusSplashApp
from apps.status.menu_icons import StatusMenusApp
from apps.splash.app import SplashSettingsApp

PARENTS = {
    "settings": "main",
    "wifi": "main",
    "status": "settings",
    "status_splash": "status",
    "status_menus": "status",
    "splash_settings": "settings",
}

OPEN_ACTIONS = {
    "wifi": "wifi",
    "settings": "settings",
    "status_bar": "status",
    "status_splash": "status_splash",
    "status_menus": "status_menus",
    "splash_settings": "splash_settings",
}

SCROLL_APPS = {
    "status_splash",
    "status_menus",
    "main",
    "settings",
    "wifi",
    "status",
    "splash_settings",
}

BUTTON_ORDER = ("UP", "DOWN", "LEFT", "RIGHT", "OK", "BACK")


def run():
    serial = i2c(port=1, address=0x3D)
    device = ssd1306(serial)
    buttons = ButtonInput()

    def run_splash():
        splash.show(device, buttons.get("OK"))

    def poll_button():
        for name in BUTTON_ORDER:
            if buttons.is_pressed(name):
                return name
        return None

    def get_max_idx(legacy):
        if legacy == "splash_edit_pick":
            return len(splash_menu.get_edit_items()) - 1
        if legacy == "splash_edit_save":
            return len(splash_edit.SAVE_ITEMS) - 1
        return 0

    def redraw_legacy(legacy, selected, scroll_offset):
        if legacy == "splash_edit_pick":
            return splash_menu.draw_edit_pick(device, selected, scroll_offset)
        if legacy == "splash_edit_save":
            return draw_save_menu(selected, scroll_offset)
        return scroll_offset

    def draw_save_menu(selected, scroll_offset):
        from luma.core.render import canvas
        from PIL import ImageFont
        font_title = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12
        )
        font_item = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11
        )
        items = splash_edit.SAVE_ITEMS
        with canvas(device) as draw:
            draw.rectangle(device.bounding_box, outline="black", fill="black")
            draw.text((4, 0), "Save Edit", font=font_title, fill="white")
            draw.line((0, 14, 127, 14), fill="white")
            for i, item in enumerate(items):
                y = 16 + (i * 15)
                if i == selected:
                    draw.rectangle((1, y, 126, y + 14), fill="white")
                    draw.text((5, y + 2), item, font=font_item, fill="black")
                else:
                    draw.text((5, y + 2), item, font=font_item, fill="white")
        return scroll_offset

    print("KeyCrow starting...")
    run_splash()

    manager = AppManager()
    apps = [
        MainMenuApp(),
        SettingsApp(),
        WifiApp(),
        StatusApp(),
        StatusSplashApp(),
        StatusMenusApp(),
        SplashSettingsApp(),
    ]
    for app in apps:
        app.device = device
        app.buttons = buttons
        manager.register(app)

    manager.open("main")
    manager.current().draw(device)

    legacy = None
    selected = 0
    scroll_offset = 0
    pending_edit = None

    def navigate(action):
        nonlocal legacy, selected, scroll_offset

        if action is None:
            return

        if action == "splash":
            run_splash()
            manager.open("main")
            manager.current().draw(device)
            return

        if action == "splash_edit_pick":
            legacy = "splash_edit_pick"
            selected = 0
            scroll_offset = 0
            scroll_offset = redraw_legacy(legacy, selected, scroll_offset)
            return

        if action == "back":
            parent = PARENTS.get(manager.current_name())
            if parent:
                manager.open(parent)
                manager.current().draw(device)
            return

        target = OPEN_ACTIONS.get(action)
        if target:
            manager.open(target)
            manager.current().draw(device)

    try:
        while True:
            # ===== LEGACY: splash edit only =====
            if legacy is not None:
                btn = poll_button()
                if btn == "UP":
                    max_idx = get_max_idx(legacy)
                    selected = (selected - 1) % (max_idx + 1)
                    scroll_offset = redraw_legacy(legacy, selected, scroll_offset)
                    sleep(0.18)
                elif btn == "DOWN":
                    max_idx = get_max_idx(legacy)
                    selected = (selected + 1) % (max_idx + 1)
                    scroll_offset = redraw_legacy(legacy, selected, scroll_offset)
                    sleep(0.18)
                elif btn == "OK":
                    if legacy == "splash_edit_pick":
                        items = splash_menu.get_edit_items()
                        choice = items[selected]
                        if choice == "Back":
                            legacy = None
                            manager.open("splash_settings")
                            manager.current().draw(device)
                        else:
                            result = splash_edit.run_edit(device, buttons, choice)
                            if result is None:
                                scroll_offset = redraw_legacy(legacy, selected, scroll_offset)
                            else:
                                values, raw_frames = result
                                pending_edit = (choice, values, raw_frames)
                                legacy = "splash_edit_save"
                                selected = 0
                                scroll_offset = 0
                                scroll_offset = redraw_legacy(legacy, selected, scroll_offset)
                    elif legacy == "splash_edit_save":
                        choice = splash_edit.SAVE_ITEMS[selected]
                        name, values, raw_frames = pending_edit
                        if choice == "Save as New":
                            splash_edit.save_edit(name, values, raw_frames, mode="new")
                        elif choice == "Replace Original":
                            splash_edit.save_edit(name, values, raw_frames, mode="replace")
                        pending_edit = None
                        legacy = "splash_edit_pick"
                        selected = 0
                        scroll_offset = 0
                        scroll_offset = redraw_legacy(legacy, selected, scroll_offset)
                    sleep(0.25)
                elif btn == "BACK":
                    if legacy == "splash_edit_pick":
                        legacy = None
                        manager.open("splash_settings")
                        manager.current().draw(device)
                    elif legacy == "splash_edit_save":
                        pending_edit = None
                        legacy = "splash_edit_pick"
                        selected = 0
                        scroll_offset = 0
                        scroll_offset = redraw_legacy(legacy, selected, scroll_offset)
                    sleep(0.2)
                else:
                    sleep(0.04)
                continue

            # ===== GENERIC APP LOOP =====
            app = manager.current()
            if app is None:
                sleep(0.04)
                continue

            btn = poll_button()
            if btn:
                action = app.handle_input(btn)
                if action:
                    navigate(action)
                else:
                    app.draw(device)
                if btn in ("UP", "DOWN", "LEFT", "RIGHT"):
                    sleep(0.18)
                elif btn == "OK":
                    sleep(0.25)
                else:
                    sleep(0.2)
            else:
                if manager.current_name() in SCROLL_APPS:
                    app.draw(device)
                sleep(0.04)

    except KeyboardInterrupt:
        pass

    device.clear()
    print("Bye")
