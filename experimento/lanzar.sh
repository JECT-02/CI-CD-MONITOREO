#!/bin/bash
set -euo pipefail

LOGFILE="/home/ject/proyecto/experimento/runner.log"
PIDFILE="/home/ject/proyecto/experimento/runner.pid"

cd /home/ject/proyecto
nohup bash runner.sh > "$LOGFILE" 2>&1 &
echo $! > "$PIDFILE"
echo "Runner launched, PID=$(cat $PIDFILE)"
