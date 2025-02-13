#!/bin/bash

# Variables
total_steps=8
current_step=0

# Import Scripts
cd "$(dirname "$0")"
source "$(dirname ${BASH_SOURCE[0]})/scripts/logger.bash"
source "$(dirname ${BASH_SOURCE[0]})/scripts/progress.bash"

# Welcome Message
log_info "Installation started."

# Steps
run_next "sudo apt update" must
run_next "sudo apt install -y python3-pip python3-venv" must
run_next "rm -rf venv"
run_next "python3 -m venv venv" must
run_next "source drone_project/venv/bin/activate && pip install --upgrade setuptools wheel" must
run_next "source drone_project/venv/bin/activate && pip install -r requiremnets.txt" must
run_next "source drone_project/venv/bin/activate && pip install opencv-python" must

# Build
PWD=$(pwd)
run_next "source drone_project/venv/bin/activate && pyinstaller --noconfirm --onefile \"${PWD}/drone_project/main.py\"" must
# run_next "cp -r \"${PWD}/drone_project/assets\" \"${PWD}/dist/\"" "optional" # copy assets


# Success
log_success "Installation complete! Logs can be found at $LOG_FILE"
echo "Done., Send the log file $LOG_FILE"

# Exit
exit 0
