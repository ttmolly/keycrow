#!/bin/bash
LOG=/tmp/pisugar-btn.log
LOCK=/tmp/keycrow-tap.lock

# ignore taps within 1s of the last one (debounce)
if [ -f "$LOCK" ]; then
  LAST=$(cat "$LOCK")
  NOW=$(date +%s)
  if [ $((NOW - LAST)) -lt 1 ]; then
    echo "$(date) START button fired - ignored (debounce)" >> "$LOG"
    exit 0
  fi
fi
date +%s > "$LOCK"

echo "$(date) START button fired" >> "$LOG"
export XDG_RUNTIME_DIR=/run/user/1000
export HOME=/home/keycrow
cd /home/keycrow/keycrow || exit 1
if pgrep -f "python.*keycrow.py" > /dev/null; then
  echo "$(date) already running" >> "$LOG"
  exit 0
fi
/home/keycrow/keycrow/venv/bin/python /home/keycrow/keycrow/keycrow.py >> /tmp/keycrow.log 2>&1 &
echo "$(date) started pid $!" >> "$LOG"
