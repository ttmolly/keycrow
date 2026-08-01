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
from apps.wifi_scan import scan_networks


def run():
    # ===== Hardware =====
    serial = i2c(port=1, address=0x3D)
    device = ssd1306(serial)
    buttons = ButtonInput()

    def run_splash():
        splash.show(device, buttons.get("OK"))

    def get_max_idx(legacy):
        if legacy == "splash_settings":
            return 2
        elif legacy == "splash_edit_pick":
            return len(splash_menu.get_edit_items()) - 1
        elif legacy == "splash_edit_save":
            return len(splash_edit.SAVE_ITEMS) - 1
        return 0

    def redraw_legacy(legacy, selected, scroll_offset):
        if legacy == "splash_settings":
            return splash_menu.draw(device, selected, scroll_offset)
        elif legacy == "splash_edit_pick":
            return splash_menu.draw_edit_pick(device, selected, scroll_offset)
        elif legacy == "splash_edit_save":
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

    # ===== Start =====
    print("KeyCrow starting...")
    run_splash()

    manager = AppManager()
    manager.register(MainMenuApp())
    manager.register(SettingsApp())
    manager.register(WifiApp())
    manager.register(StatusApp())
    manager.register(StatusSplashApp())
    manager.register(StatusMenusApp())

    manager.open("main")
    manager.current().draw(device)

    # Only used for screens not yet converted
    legacy = None
    selected = 0
    scroll_offset = 0
    pending_edit = None

    try:
        while True:
            # If we're on a real app, handle it here
            name = manager.current_name()

            # ---------- MAIN ----------
            if legacy is None and name == "main":
                app = manager.current()
                action = None

                if buttons.is_pressed("UP"):
                    action = app.handle_input("UP")
                    app.draw(device)
                    sleep(0.18)
                elif buttons.is_pressed("DOWN"):
                    action = app.handle_input("DOWN")
                    app.draw(device)
                    sleep(0.18)
                elif buttons.is_pressed("OK"):
                    action = app.handle_input("OK")
                    sleep(0.25)
                elif buttons.is_pressed("BACK"):
                    action = app.handle_input("BACK")
                    sleep(0.2)

                if action == "wifi":
                    manager.open("wifi")
                    manager.current().draw(device)
                elif action == "settings":
                    manager.open("settings")
                    manager.current().draw(device)
                elif action == "splash":
                    run_splash()
                    manager.open("main")
                    manager.current().draw(device)

                sleep(0.04)
                continue

            # ---------- SETTINGS ----------
            if legacy is None and name == "settings":
                app = manager.current()
                action = None

                if buttons.is_pressed("UP"):
                    action = app.handle_input("UP")
                    app.draw(device)
                    sleep(0.18)
                elif buttons.is_pressed("DOWN"):
                    action = app.handle_input("DOWN")
                    app.draw(device)
                    sleep(0.18)
                elif buttons.is_pressed("OK"):
                    action = app.handle_input("OK")
                    sleep(0.25)
                elif buttons.is_pressed("BACK"):
                    action = app.handle_input("BACK")
                    sleep(0.2)

                if action == "status_bar":
                    manager.open("status")
                    manager.current().draw(device)
                elif action == "splash_settings":
                    legacy = "splash_settings"
                    selected = 0
                    scroll_offset = 0
                    scroll_offset = redraw_legacy(legacy, selected, scroll_offset)
                elif action == "back":
                    manager.open("main")
                    manager.current().draw(device)

                sleep(0.04)
                continue

            # ---------- WIFI ----------
            if legacy is None and name == "wifi":
                app = manager.current()
                action = None

                if buttons.is_pressed("UP"):
                    action = app.handle_input("UP")
                    app.draw(device)
                    sleep(0.18)
                elif buttons.is_pressed("DOWN"):
                    action = app.handle_input("DOWN")
                    app.draw(device)
                    sleep(0.18)
                elif buttons.is_pressed("OK"):
                    action = app.handle_input("OK")
                    sleep(0.25)
                elif buttons.is_pressed("BACK"):
                    action = app.handle_input("BACK")
                    sleep(0.2)

                if action == "scan":
                    print("Scanning WiFi...")
                    nets = scan_networks()
                    print("Found:", nets)
                    app.draw(device)
                elif action == "connect":
                    try:
                        import ui.wifi_setup as wifi_setup
                        wifi_setup.run(device, buttons)
                    except Exception as e:
                        print("WiFi setup error:", e)
                    app.draw(device)
                elif action == "back":
                    manager.open("main")
                    manager.current().draw(device)

                sleep(0.04)
                continue

            # ---------- STATUS ----------
            if legacy is None and name == "status":
                app = manager.current()
                action = None

                if buttons.is_pressed("UP"):
                    action = app.handle_input("UP")
                    app.draw(device)
                    sleep(0.18)
                elif buttons.is_pressed("DOWN"):
                    action = app.handle_input("DOWN")
                    app.draw(device)
                    sleep(0.18)
                elif buttons.is_pressed("OK"):
                    action = app.handle_input("OK")
                    sleep(0.25)
                elif buttons.is_pressed("BACK"):
                    action = app.handle_input("BACK")
                    sleep(0.2)

                if action == "status_splash":
                    manager.open("status_splash")
                    manager.current().draw(device)
                elif action == "status_menus":
                    manager.open("status_menus")
                    manager.current().draw(device)
                elif action == "back":
                    manager.open("settings")
                    manager.current().draw(device)

                sleep(0.04)
                continue

            # ---------- STATUS SPLASH ----------
            if legacy is None and name == "status_splash":
                app = manager.current()
                action = None

                if buttons.is_pressed("UP"):
                    action = app.handle_input("UP")
                    app.draw(device)
                    sleep(0.18)
                elif buttons.is_pressed("DOWN"):
                    action = app.handle_input("DOWN")
                    app.draw(device)
                    sleep(0.18)
                elif buttons.is_pressed("OK"):
                    action = app.handle_input("OK")
                    app.draw(device)
                    sleep(0.25)
                elif buttons.is_pressed("BACK"):
                    action = app.handle_input("BACK")
                    sleep(0.2)

                if action == "back":
                    manager.open("status")
                    manager.current().draw(device)

                sleep(0.04)
                continue

            # ---------- STATUS MENUS ----------
            if legacy is None and name == "status_menus":
                app = manager.current()
                action = None

                if buttons.is_pressed("UP"):
                    action = app.handle_input("UP")
                    app.draw(device)
                    sleep(0.18)
                elif buttons.is_pressed("DOWN"):
                    action = app.handle_input("DOWN")
                    app.draw(device)
                    sleep(0.18)
                elif buttons.is_pressed("OK"):
                    action = app.handle_input("OK")
                    app.draw(device)
                    sleep(0.25)
                elif buttons.is_pressed("BACK"):
                    action = app.handle_input("BACK")
                    sleep(0.2)

                if action == "back":
                    manager.open("status")
                    manager.current().draw(device)

                sleep(0.04)
                continue

            # ---------- LEGACY: splash settings / edit ----------
            if legacy is not None:
                if buttons.is_pressed("UP"):
                    max_idx = get_max_idx(legacy)
                    selected = (selected - 1) % (max_idx + 1)
                    scroll_offset = redraw_legacy(legacy, selected, scroll_offset)
                    sleep(0.18)

                elif buttons.is_pressed("DOWN"):
                    max_idx = get_max_idx(legacy)
                    selected = (selected + 1) % (max_idx + 1)
                    scroll_offset = redraw_legacy(legacy, selected, scroll_offset)
                    sleep(0.18)

                elif buttons.is_pressed("LEFT") or buttons.is_pressed("RIGHT"):
                    if legacy == "splash_settings" and selected == 0:
                        available = splash_menu.get_available_splashes()
                        current_name = config.get_splash()
                        try:
                            idx = available.index(current_name)
                        except ValueError:
                            idx = 0
                        if buttons.is_pressed("LEFT"):
                            idx = (idx - 1) % len(available)
                        else:
                            idx = (idx + 1) % len(available)
                        config.set_splash(available[idx])
                        scroll_offset = redraw_legacy(legacy, selected, scroll_offset)
                        sleep(0.18)

                elif buttons.is_pressed("OK"):
                    if legacy == "splash_settings":
                        if selected == 1:
                            legacy = "splash_edit_pick"
                            selected = 0
                            scroll_offset = 0
                            scroll_offset = redraw_legacy(legacy, selected, scroll_offset)
                        elif selected == 2:
                            legacy = None
                            manager.open("settings")
                            manager.current().draw(device)

                    elif legacy == "splash_edit_pick":
                        items = splash_menu.get_edit_items()
                        choice = items[selected]
                        if choice == "Back":
                            legacy = "splash_settings"
                            selected = 0
                            scroll_offset = 0
                            scroll_offset = redraw_legacy(legacy, selected, scroll_offset)
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

                elif buttons.is_pressed("BACK"):
                    if legacy == "splash_settings":
                        legacy = None
                        manager.open("settings")
                        manager.current().draw(device)
                    elif legacy == "splash_edit_pick":
                        legacy = "splash_settings"
                        selected = 0
                        scroll_offset = 0
                        scroll_offset = redraw_legacy(legacy, selected, scroll_offset)
                    elif legacy == "splash_edit_save":
                        pending_edit = None
                        legacy = "splash_edit_pick"
                        selected = 0
                        scroll_offset = 0
                        scroll_offset = redraw_legacy(legacy, selected, scroll_offset)
                    sleep(0.2)

                if legacy == "splash_settings":
                    scroll_offset = redraw_legacy(legacy, selected, scroll_offset)
                    sleep(0.05)
                else:
                    sleep(0.04)
                continue

            sleep(0.04)

    except KeyboardInterrupt:
        pass

    device.clear()
    print("Bye")
