#!/bin/bash

# Import logger
source "$(dirname ${BASH_SOURCE[0]})/logger.bash"

# Log Functions
log_info   () { log "INFO"    "$1"; }
log_error  () { log "ERROR"   "$1"; }
log_success() { log "SUCCESS" "$1"; }
log_warning() { log "WARNING" "$1"; }

# Spinner
spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='|/-\'
    
    while kill -0 "$pid" 2>/dev/null; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

# Progress
show_progress() {
    local total=$1
    local current=$2
    local progress=$(( current * 100 / total ))
    local bar_width=50
    local filled=$(( progress * bar_width / 100 ))
    local empty=$(( bar_width - filled ))
    
    local fill_str=$(printf "%0.s#" $(seq 1 $filled))
    local empty_str=$(printf "%0.s-" $(seq 1 $empty))
    
    printf "\rProgress: [${fill_str}${empty_str}] ${progress}%%"; echo
}

# execute commands with progress & spiner
# example: run_next 'ls' must
run_next() {
    
    # Vars
    local CMD="$1"
    local MUST="$2"
    current_step=$((current_step + 1))

    # Start msg
    log_info "Starting: $CMD"

    # skip spinner for sudo (causes input glitch)
    if [[ "$CMD" == *"sudo"* ]]; then
        bash -c "$CMD" &>/dev/null
    else
        bash -c "$CMD" &>/dev/null &
        local CMD_PID=$!
        spinner $CMD_PID &
        wait $CMD_PID
        kill $! 2>/dev/null
    fi

    local EXIT_STATUS=$?
    if [ $EXIT_STATUS -eq 0 ]; then
        log_success "Completed: $CMD"
    else
        if [ "$MUST" == "must" ]; then
            log_error "Failed: $CMD"
            exit 1
        else
            log_warning "Warning: $CMD encountered an issue but continuing."
        fi
    fi

    show_progress $total_steps $current_step
}

# Export the show_progress and run_next functions
export -f show_progress
export -f run_next
