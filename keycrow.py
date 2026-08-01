from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from time import sleep

import ui.splash as splash
import ui.main_menu as main_menu
import ui.wifi_menu as wifi_menu
import ui.settings_menu as settings_menu
import ui.splash_menu as splash_menu
import ui.splash_edit as splash_edit
import ui.status_menu as status_menu
import core.config as config
from core.input import ButtonInput
from core.app_manager import AppManager
from apps.main.app import MainMenuApp
from apps.settings.app import SettingsApp
from apps.wifi.app import WifiApp
from apps.status.app import StatusApp
from apps.wifi_scan import scan_networks

# ===== Hardware =====
serial = i2c(port=1, address=0x3D)
device = ssd1306(serial)
buttons = ButtonInput()


def run_splash():
    splash.show(device, buttons.get("OK"))


def get_max_idx(current):
    if current == "splash_settings":
        return 2
    elif current == "splash_edit_pick":
        return len(splash_menu.get_edit_items()) - 1
    elif current == "splash_edit_save":
        return len(splash_edit.SAVE_ITEMS) - 1
    elif current == "status_splash":
        return len(status_menu.get_splash_items()) - 1
    elif current == "status_menus":
        return len(status_menu.get_menu_items()) - 1
    return 0


def redraw(current, selected, scroll_offset):
    if current == "splash_settings":
        return splash_menu.draw(device, selected, scroll_offset)
    elif current == "splash_edit_pick":
        return splash_menu.draw_edit_pick(device, selected, scroll_offset)
    elif current == "splash_edit_save":
        return draw_save_menu(selected, scroll_offset)
    elif current == "status_splash":
        return status_menu.draw(device, selected, scroll_offset, mode="splash")
    elif current == "status_menus":
        return status_menu.draw(device, selected, scroll_offset, mode="menus")
    return scroll_offset


def draw_save_menu(selected, scroll_offset):
    from luma.core.render import canvas
    from PIL import ImageFont
    font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
    font_item = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
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

# ===== App system =====
manager = AppManager()
manager.register(MainMenuApp())
manager.register(SettingsApp())
manager.register(WifiApp())
manager.register(StatusApp())
manager.push("main")

# App-owned: main, settings_app, wifi_app, status_app
# Legacy: status_splash, status_menus, splash_settings, splash_edit_*
current = "main"
selected = 0
scroll_offset = 0
pending_edit = None

manager.current_app().draw(device)

try:
    while True:
        # ---------- MAIN MENU APP ----------
        if current == "main":
            app = manager._apps["main"]
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
                current = "wifi_app"
                manager._apps["wifi"].on_enter()
                manager._apps["wifi"].draw(device)
            elif action == "settings":
                current = "settings_app"
                manager._apps["settings"].on_enter()
                manager._apps["settings"].draw(device)
            elif action == "splash":
                run_splash()
                manager._apps["main"].on_enter()
                manager._apps["main"].draw(device)

            sleep(0.04)
            continue

        # ---------- SETTINGS APP ----------
        if current == "settings_app":
            app = manager._apps["settings"]
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
                current = "status_app"
                manager._apps["status"].on_enter()
                manager._apps["status"].draw(device)
            elif action == "splash_settings":
                current = "splash_settings"
                selected = 0
                scroll_offset = 0
                scroll_offset = redraw(current, selected, scroll_offset)
            elif action == "back":
                current = "main"
                manager._apps["main"].on_enter()
                manager._apps["main"].draw(device)

            sleep(0.04)
            continue

        # ---------- WIFI APP ----------
        if current == "wifi_app":
            app = manager._apps["wifi"]
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
                current = "main"
                manager._apps["main"].on_enter()
                manager._apps["main"].draw(device)

            sleep(0.04)
            continue

        # ---------- STATUS APP ----------
        if current == "status_app":
            app = manager._apps["status"]
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
                current = "status_splash"
                selected = 0
                scroll_offset = 0
                scroll_offset = redraw(current, selected, scroll_offset)
            elif action == "status_menus":
                current = "status_menus"
                selected = 0
                scroll_offset = 0
                scroll_offset = redraw(current, selected, scroll_offset)
            elif action == "back":
                current = "settings_app"
                manager._apps["settings"].draw(device)

            sleep(0.04)
            continue

        # ---------- LEGACY SCREENS ----------
        if buttons.is_pressed("UP"):
            max_idx = get_max_idx(current)
            selected = (selected - 1) % (max_idx + 1)
            scroll_offset = redraw(current, selected, scroll_offset)
            sleep(0.18)

        elif buttons.is_pressed("DOWN"):
            max_idx = get_max_idx(current)
            selected = (selected + 1) % (max_idx + 1)
            scroll_offset = redraw(current, selected, scroll_offset)
            sleep(0.18)

        elif buttons.is_pressed("LEFT") or buttons.is_pressed("RIGHT"):
            if current == "splash_settings" and selected == 0:
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
                scroll_offset = redraw(current, selected, scroll_offset)
                sleep(0.18)

        elif buttons.is_pressed("OK"):
            if current == "status_splash":
                items = status_menu.get_splash_items()
                if selected == len(items) - 1:
                    current = "status_app"
                    manager._apps["status"].draw(device)
                else:
                    status_menu.toggle("splash", selected)
                    scroll_offset = redraw(current, selected, scroll_offset)

            elif current == "status_menus":
                items = status_menu.get_menu_items()
                if selected == len(items) - 1:
                    current = "status_app"
                    manager._apps["status"].draw(device)
                else:
                    status_menu.toggle("menus", selected)
                    scroll_offset = redraw(current, selected, scroll_offset)

            elif current == "splash_settings":
                if selected == 1:
                    current = "splash_edit_pick"
                    selected = 0
                    scroll_offset = 0
                    scroll_offset = redraw(current, selected, scroll_offset)
                elif selected == 2:
                    current = "settings_app"
                    manager._apps["settings"].draw(device)

            elif current == "splash_edit_pick":
                items = splash_menu.get_edit_items()
                choice = items[selected]
                if choice == "Back":
                    current = "splash_settings"
                    selected = 0
                    scroll_offset = 0
                    scroll_offset = redraw(current, selected, scroll_offset)
                else:
                    result = splash_edit.run_edit(device, buttons, choice)
                    if result is None:
                        scroll_offset = redraw(current, selected, scroll_offset)
                    else:
                        values, raw_frames = result
                        pending_edit = (choice, values, raw_frames)
                        current = "splash_edit_save"
                        selected = 0
                        scroll_offset = 0
                        scroll_offset = redraw(current, selected, scroll_offset)

            elif current == "splash_edit_save":
                choice = splash_edit.SAVE_ITEMS[selected]
                name, values, raw_frames = pending_edit
                if choice == "Save as New":
                    splash_edit.save_edit(name, values, raw_frames, mode="new")
                elif choice == "Replace Original":
                    splash_edit.save_edit(name, values, raw_frames, mode="replace")
                pending_edit = None
                current = "splash_edit_pick"
                selected = 0
                scroll_offset = 0
                scroll_offset = redraw(current, selected, scroll_offset)

            sleep(0.25)

        elif buttons.is_pressed("BACK"):
            if current in ["status_splash", "status_menus"]:
                current = "status_app"
                manager._apps["status"].draw(device)
            elif current == "splash_settings":
                current = "settings_app"
                manager._apps["settings"].draw(device)
            elif current == "splash_edit_pick":
                current = "splash_settings"
                selected = 0
                scroll_offset = 0
                scroll_offset = redraw(current, selected, scroll_offset)
            elif current == "splash_edit_save":
                pending_edit = None
                current = "splash_edit_pick"
                selected = 0
                scroll_offset = 0
                scroll_offset = redraw(current, selected, scroll_offset)
            sleep(0.2)

        if current in ["splash_settings", "status_splash", "status_menus"]:
            scroll_offset = redraw(current, selected, scroll_offset)
            sleep(0.05)
        else:
            sleep(0.04)

except KeyboardInterrupt:
    pass

device.clear()
print("Bye")
