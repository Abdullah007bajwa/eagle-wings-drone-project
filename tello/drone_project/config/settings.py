import sys
import platform

# Detect Platform
platform = platform.system()

# Debug
debug = True
if '-d' in sys.argv or '--debug' in sys.argv:
    debug = True

FRAME_SIZE=(960, 720)
MAX_DISTANCE=10

FRAME_RATE=10
MAIN_LOOP_RATE=10 # Only QT6

GRID_CENTER=(300, 300)
SAFE_DISTANCE=2
