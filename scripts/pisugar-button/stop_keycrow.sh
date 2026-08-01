#!/bin/bash
LOG=/tmp/pisugar-btn.log
echo "$(date) STOP button fired" >> "$LOG"

PID=$(pgrep -f "python.*keycrow.py")

if [ -z "$PID" ]; then
  echo "$(date) not running, nothing to stop" >> "$LOG"
else
  echo "$(date) stopping pid $PID (SIGTERM)" >> "$LOG"
  kill -TERM "$PID"

  # give it up to 5s to exit cleanly
  STOPPED=0
  for i in {1..10}; do
    if ! kill -0 "$PID" 2>/dev/null; then
      echo "$(date) stopped keycrow (pid $PID) cleanly" >> "$LOG"
      STOPPED=1
      break
    fi
    sleep 0.5
  done

  if [ "$STOPPED" -eq 0 ]; then
    echo "$(date) pid $PID did not exit, sending SIGKILL" >> "$LOG"
    kill -KILL "$PID" 2>/dev/null
    echo "$(date) force-stopped keycrow (pid $PID)" >> "$LOG"
  fi
fi

# clear the OLED so it doesn't sit on the last frozen frame
/home/keycrow/keycrow/venv/bin/python3 -c "
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
serial = i2c(port=1, address=0x3D)
device = ssd1306(serial)
device.clear()
" >> "$LOG" 2>&1

echo "$(date) display cleared" >> "$LOG"
