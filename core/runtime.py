from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from time import sleep

import ui.splash as splash
from core.input import ButtonInput
from core.app_manager import AppManager
from apps.main.app import MainMenuApp
from apps.settings.app import SettingsApp
from apps.wifi.app import WifiApp
from apps.status.app import StatusApp
from apps.status.splash_icons import StatusSplashApp
from apps.status.menu_icons import StatusMenusApp
from apps.splash.app import SplashSettingsApp
from apps.splash_edit.app import SplashEditPickApp, SplashEditSaveApp

PARENTS = {
    "settings": "main",
    "wifi": "main",
    "status": "settings",
    "status_splash": "status",
    "status_menus": "status",
    "splash_settings": "settings",
    "splash_edit_pick": "splash_settings",
    "splash_edit_save": "splash_edit_pick",
}

OPEN_ACTIONS = {
    "wifi": "wifi",
    "settings": "settings",
    "status_bar": "status",
    "status_splash": "status_splash",
    "status_menus": "status_menus",
    "splash_settings": "splash_settings",
    "splash_edit_pick": "splash_edit_pick",
    "splash_edit_save": "splash_edit_save",
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

    print("KeyCrow starting...")
    run_splash()

    manager = AppManager()
    save_app = SplashEditSaveApp()
    apps = [
        MainMenuApp(),
        SettingsApp(),
        WifiApp(),
        StatusApp(),
        StatusSplashApp(),
        StatusMenusApp(),
        SplashSettingsApp(),
        SplashEditPickApp(save_app),
        save_app,
    ]
    for app in apps:
        app.device = device
        app.buttons = buttons
        manager.register(app)

    manager.open("main")
    manager.current().draw(device)

    def navigate(action):
        if action is None:
            return

        if action == "splash":
            run_splash()
            manager.open("main")
            manager.current().draw(device)
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
