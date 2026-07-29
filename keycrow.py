from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from gpiozero import Button
from time import sleep

import ui.splash as splash
import ui.main_menu as main_menu
import ui.wifi_menu as wifi_menu
import ui.settings_menu as settings_menu
import ui.splash_menu as splash_menu
import ui.config as config
from apps.wifi_scan import scan_networks

# ===== Hardware =====
serial = i2c(port=1, address=0x3D)
device = ssd1306(serial)

buttons = {
    "UP":    Button(17, pull_up=True, bounce_time=0.08),
    "DOWN":  Button(27, pull_up=True, bounce_time=0.08),
    "LEFT":  Button(22, pull_up=True, bounce_time=0.08),
    "RIGHT": Button(23, pull_up=True, bounce_time=0.08),
    "OK":    Button(24, pull_up=True, bounce_time=0.08),
    "BACK":  Button(25, pull_up=True, bounce_time=0.08),
}

def run_splash():
    splash.show(device, buttons["OK"])

def get_max_idx(current):
    if current == "main":
        return len(main_menu.ITEMS) - 1
    elif current == "wifi":
        return len(wifi_menu.ITEMS) - 1
    elif current == "settings":
        return len(settings_menu.ITEMS) - 1
    elif current == "splash_settings":
        return len(splash_menu.get_items()) - 1
    return 0

def redraw(current, selected, scroll_offset):
    if current == "main":
        return main_menu.draw(device, selected, scroll_offset)
    elif current == "wifi":
        return wifi_menu.draw(device, selected, scroll_offset)
    elif current == "settings":
        return settings_menu.draw(device, selected, scroll_offset)
    elif current == "splash_settings":
        return splash_menu.draw(device, selected, scroll_offset)
    return scroll_offset

print("KeyCrow starting...")
run_splash()

current = "main"
selected = 0
scroll_offset = 0

scroll_offset = redraw(current, selected, scroll_offset)

try:
    while True:
        if buttons["UP"].is_pressed:
            max_idx = get_max_idx(current)
            selected = (selected - 1) % (max_idx + 1)
            scroll_offset = redraw(current, selected, scroll_offset)
            sleep(0.18)

        elif buttons["DOWN"].is_pressed:
            max_idx = get_max_idx(current)
            selected = (selected + 1) % (max_idx + 1)
            scroll_offset = redraw(current, selected, scroll_offset)
            sleep(0.18)

        elif buttons["OK"].is_pressed:
            if current == "main":
                choice = main_menu.ITEMS[selected]
                if choice == "WiFi Tools":
                    current = "wifi"
                    selected = 0
                    scroll_offset = 0
                    scroll_offset = redraw(current, selected, scroll_offset)
                elif choice == "Settings":
                    current = "settings"
                    selected = 0
                    scroll_offset = 0
                    scroll_offset = redraw(current, selected, scroll_offset)
                else:
                    print(f"Selected: {choice}")

            elif current == "wifi":
                choice = wifi_menu.ITEMS[selected]
                if choice == "Scan Networks":
                    print("Scanning WiFi...")
                    nets = scan_networks()
                    print("Found:", nets)
                elif choice == "Back":
                    current = "main"
                    selected = 0
                    scroll_offset = 0
                    scroll_offset = redraw(current, selected, scroll_offset)

            elif current == "settings":
                choice = settings_menu.ITEMS[selected]
                if choice == "Splash":
                    current = "splash_settings"
                    selected = 0
                    scroll_offset = 0
                    scroll_offset = redraw(current, selected, scroll_offset)
                elif choice == "Back":
                    current = "main"
                    selected = 0
                    scroll_offset = 0
                    scroll_offset = redraw(current, selected, scroll_offset)

            elif current == "splash_settings":
                items = splash_menu.get_items()
                choice = items[selected]
                if choice == "Back":
                    current = "settings"
                    selected = 0
                    scroll_offset = 0
                    scroll_offset = redraw(current, selected, scroll_offset)
                else:
                    config.set_splash(choice)
                    scroll_offset = redraw(current, selected, scroll_offset)

            sleep(0.25)

        elif buttons["BACK"].is_pressed:
            if current == "main":
                run_splash()
                current = "main"
                selected = 0
                scroll_offset = 0
                scroll_offset = redraw(current, selected, scroll_offset)
            elif current in ["wifi", "settings"]:
                current = "main"
                selected = 0
                scroll_offset = 0
                scroll_offset = redraw(current, selected, scroll_offset)
            elif current == "splash_settings":
                current = "settings"
                selected = 0
                scroll_offset = 0
                scroll_offset = redraw(current, selected, scroll_offset)
            sleep(0.2)

        sleep(0.04)

except KeyboardInterrupt:
    pass

device.clear()
print("Bye")
