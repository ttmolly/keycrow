#!/bin/bash
echo "$(date) START button fired" >> /tmp/pisugar-btn.log
export XDG_RUNTIME_DIR=/run/user/1000
export HOME=/home/keycrow
cd /home/keycrow/keycrow || exit 1
if pgrep -f "python.*keycrow.py" > /dev/null; then
  echo "$(date) already running" >> /tmp/pisugar-btn.log
  exit 0
fi
/home/keycrow/keycrow/venv/bin/python /home/keycrow/keycrow/keycrow.py >> /tmp/keycrow.log 2>&1 &
echo "$(date) started pid $!" >> /tmp/pisugar-btn.log
