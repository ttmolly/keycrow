from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from gpiozero import Button
from PIL import ImageFont
from time import sleep

# ===== Hardware =====
# Confirmed via i2cdetect: this board responds at 0x3D
serial = i2c(port=1, address=0x3D)
device = ssd1306(serial)  # defaults to 128x64, which matches the Adafruit 938

font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
font_item  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)

buttons = {
    "UP":    Button(17, pull_up=True, bounce_time=0.08),
    "DOWN":  Button(27, pull_up=True, bounce_time=0.08),
    "LEFT":  Button(22, pull_up=True, bounce_time=0.08),
    "RIGHT": Button(23, pull_up=True, bounce_time=0.08),
    "OK":    Button(24, pull_up=True, bounce_time=0.08),
    "BACK":  Button(25, pull_up=True, bounce_time=0.08),
}

menu_items = [
    "WiFi Tools",
    "Sub-GHz",
    "IR Remote",
    "Archive",
    "Settings",
    "About"
]

selected = 0
scroll_offset = 0

# ===== Layout =====
LIST_TOP = 16          # y where the list area starts, just below the title line
ITEM_HEIGHT = 15        # vertical space per item (font is 11px, this gives it room to breathe)
VISIBLE_ITEMS = 3       # how many items fit in the list area at once (adjust if you change ITEM_HEIGHT)

def draw_menu():
    global scroll_offset

    # Keep the selected item inside the visible window, scrolling as needed
    if selected < scroll_offset:
        scroll_offset = selected
    elif selected >= scroll_offset + VISIBLE_ITEMS:
        scroll_offset = selected - VISIBLE_ITEMS + 1

    with canvas(device) as draw:
        # Clear
        draw.rectangle(device.bounding_box, outline="black", fill="black")

        # Title
        draw.text((4, 0), "KeyCrow", font=font_title, fill="white")
        draw.line((0, 14, 127, 14), fill="white")

        # Visible slice of the menu
        visible_slice = menu_items[scroll_offset:scroll_offset + VISIBLE_ITEMS]

        for row, item in enumerate(visible_slice):
            i = scroll_offset + row
            y = LIST_TOP + (row * ITEM_HEIGHT)
            if i == selected:
                draw.rectangle((1, y, 126, y + ITEM_HEIGHT - 1), fill="white")
                draw.text((5, y + 2), item, font=font_item, fill="black")
            else:
                draw.text((5, y + 2), item, font=font_item, fill="white")

        # Scroll indicators so it's obvious there's more content off-screen
        if scroll_offset > 0:
            draw.text((119, LIST_TOP), "^", font=font_item, fill="white")
        if scroll_offset + VISIBLE_ITEMS < len(menu_items):
            draw.text((119, LIST_TOP + (VISIBLE_ITEMS - 1) * ITEM_HEIGHT), "v", font=font_item, fill="white")

print("KeyCrow started")
draw_menu()

try:
    while True:
        if buttons["UP"].is_pressed:
            selected = max(0, selected - 1)
            draw_menu()
            sleep(0.18)
        elif buttons["DOWN"].is_pressed:
            selected = min(len(menu_items) - 1, selected + 1)
            draw_menu()
            sleep(0.18)
        elif buttons["OK"].is_pressed:
            print(f"Selected: {menu_items[selected]}")
            sleep(0.25)
        elif buttons["BACK"].is_pressed:
            break
        sleep(0.04)
except KeyboardInterrupt:
    pass

device.clear()
print("Bye")
