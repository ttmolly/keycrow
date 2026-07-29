from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from time import sleep

serial = i2c(port=1, address=0x3C)
device = ssd1306(serial)

print("Full white (all pixels on)...")
with canvas(device) as draw:
    draw.rectangle(device.bounding_box, outline="white", fill="white")
sleep(3)

print("Full black (all pixels off)...")
with canvas(device) as draw:
    draw.rectangle(device.bounding_box, outline="black", fill="black")
sleep(2)

print("Inverted...")
device.invert(True)
with canvas(device) as draw:
    draw.rectangle(device.bounding_box, outline="white", fill="white")
sleep(3)

device.invert(False)
device.clear()
print("Done")
