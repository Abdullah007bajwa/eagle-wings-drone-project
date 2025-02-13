#!/bin/bash

# Create logs directory if it doesn't exist
mkdir -p logs

# Generate a timestamp
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")

# Define the log file path
LOG_FILE="logs/snap-$TIMESTAMP.log"

# Initialize the log file
touch "$LOG_FILE"

# Function to log messages with timestamp and log level
log() {
    local LOG_LEVEL="$1"
    local MESSAGE="$2"
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] [$LOG_LEVEL] $MESSAGE" | tee -a "$LOG_FILE"
}

# Export the log function for use in other scripts
export -f log
export LOG_FILE
