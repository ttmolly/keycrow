from gpiozero import Button
from time import sleep

# Button mapping (same as we planned earlier)
buttons = {
    "UP":    Button(17, pull_up=True, bounce_time=0.05),
    "DOWN":  Button(27, pull_up=True, bounce_time=0.05),
    "LEFT":  Button(22, pull_up=True, bounce_time=0.05),
    "RIGHT": Button(23, pull_up=True, bounce_time=0.05),
    "OK":    Button(24, pull_up=True, bounce_time=0.05),
    "BACK":  Button(25, pull_up=True, bounce_time=0.05),
}

print("Press the buttons one by one. Press Ctrl+C to stop.\n")

try:
    while True:
        for name, btn in buttons.items():
            if btn.is_pressed:
                print(f"→ {name} pressed")
                sleep(0.2)   # simple debounce
        sleep(0.05)
except KeyboardInterrupt:
    print("\nButton test finished.")
