#!/bin/bash
# Wrapper script to run GDPval tasks without tmux
# This solves tmux version compatibility issues on SSH sessions

# Disable tmux detection by making tmux unavailable
export PATH=/usr/bin:/bin:$PATH
export OPENHANDS_TERMINAL_TYPE=basic

# Run the provided python script with arguments
python "$@"
