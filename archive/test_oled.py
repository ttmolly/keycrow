from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import ImageFont
from time import sleep

serial = i2c(port=1, address=0x3C)
device = ssd1306(serial)

# Bigger font
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)

print("Drawing bigger text...")

with canvas(device) as draw:
    draw.rectangle(device.bounding_box, outline="white", fill="black")
    draw.text((18, 8), "KeyCrow", font=font_big, fill="white")
    draw.text((22, 36), "OLED OK!", font=font, fill="white")

print("How does this look?")
sleep(8)
