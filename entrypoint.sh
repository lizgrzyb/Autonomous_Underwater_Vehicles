#!/bin/bash
# Start Xvfb on display :99 with screen 0 with 1024x768x16
Xvfb :99 -screen 0 1024x768x16 &
export DISPLAY=:99

# Execute the main command
exec "$@"
