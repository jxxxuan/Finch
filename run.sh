#!/bin/bash

#LOG_DIR="/home/jxxxuan/gdrive/stock/logs/$(date +%Y)/$(date +%m)/$(date +%d)"
LOG_DIR="/mnt/predictor/stock_data/logs/$(date +%Y)/$(date +%m)/$(date +%d)"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/$(date +%Y-%m-%d).log"

SESSION="predictor"

tmux has-session -t $SESSION 2>/dev/null

if ! tmux has-session -t "$SESSION" 2>/dev/null; then
        tmux new -d -s $SESSION
fi

tmux send-keys -t $SESSION "cd /home/jxxxuan/Github/predictor/symbol" C-m
tmux send-keys -t $SESSION "/home/jxxxuan/Github/predictor/venv/bin/python3 -m main 2>&1 | tee -a \"$LOG_FILE\"" C-m