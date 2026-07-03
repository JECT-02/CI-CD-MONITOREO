#!/bin/bash
# Alternative launcher - uses screen or dtach to keep process alive

# First try screen
if command -v screen &> /dev/null; then
    screen -dmS rollback-exp bash -c 'cd /home/ject/proyecto && bash runner.sh > experimento/runner.log 2>&1'
    echo "Launched with screen in session 'rollback-exp'"
    exit 0
fi

# Fallback: nohup in a new session
cd /home/ject/proyecto
nohup setsid bash -c 'bash runner.sh > experimento/runner.log 2>&1' &
echo "Launched via setsid, PID=$!"
