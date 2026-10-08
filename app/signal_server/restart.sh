#!/usr/bin/env bash
# Restart the signal server inside the sandbox (image has no ps/pkill). Usage: SIGNAL_TOKEN=... bash restart.sh
cd /home/daytona/signal || exit 1
for p in /proc/[0-9]*; do
  pid=${p#/proc/}
  [ "$pid" = "$$" ] && continue
  if tr '\0' ' ' < "$p/cmdline" 2>/dev/null | grep -q '[u]vicorn main:app'; then kill "$pid" && echo "killed $pid"; fi
done
sleep 1
setsid nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 < /dev/null &
echo $! > server.pid
sleep 3
curl -s localhost:8000/health
