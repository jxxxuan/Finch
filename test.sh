#!/bin/bash

#LOG_DIR="/home/jxxxuan/gdrive/stock/logs/$(date +%Y)/$(date +%m)/$(date +%d)"
LOG_DIR="/home/jxxxuan/stock_data/logs/$(date +%Y)/$(date +%m)/$(date +%d)"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/test.log"

SESSION="predictor"

tmux has-session -t $SESSION 2>/dev/null

if ! tmux has-session -t "$SESSION" 2>/dev/null; then
        echo "hello"
        tmux new -d -s $SESSION
        echo "world"
fi

tmux send-keys -t $SESSION "cd /home/jxxxuan/github/Finch" C-m
tmux send-keys -t $SESSION "/home/jxxxuan/github/Finch/venv/bin/python3 test.py 2>&1 | tee -a \"$LOG_FILE\"" C-m