#!/usr/bin/env bash
# use this script to stop the model and bot applications

PID_FILE=$(pwd)/pids.txt

if test -f "$PID_FILE"; then
  for pid in $(cat "$PID_FILE"); do
    if [[ pid -gt 0 ]]; then
      if ! { kill "$pid" 2>/dev/null; }; then
        echo Process with the PID "$pid" doesn\'t exist
      else
        echo Killed the process with the PID "$pid"
      fi
    fi
  done
fi

# echo All existent processes have been killed
