from djitellopy import Tello
import time
from config.settings import FRAME_SIZE, MAX_DISTANCE, debug

# 
# Helper Class
# 

class TSCHelper:
    @staticmethod
    def map_axis(x_axis: float, y_axis: float, z_axis: float, mx=FRAME_SIZE[0], my=FRAME_SIZE[1], mz=MAX_DISTANCE*2):
        return \
            x_axis / mx, \
            y_axis / my, \
            z_axis / mz

    @staticmethod
    def calculate_speed(value, map_value, low, high, scale):
        direction = -1 if value < 0 else 1
        speed = max(
            low, 
            min(high, abs(value) * scale)
        )
        return int(map_value * speed * direction)

# 
# The "TelloControllerBasic" class
# 

class TelloControllerBasic:

    # 
    # Config
    # 

    TIMEOUT = 1
    MIN_UPDATE_INTERVAL = 0.1


    # 
    # Constructor
    # 

    def __init__(self, tello: Tello, auto_start=True):
        # Arguments
        self.tello = tello
        self.is_loop_enabled = True
        self.is_changing_course = False
        self.is_stopped = True

        # Timestamps
        self.last_move_time = 0
        self.move_deadline = time.time() + self.TIMEOUT

        # Takeoff if needed
        if auto_start:
            self.start()

    def start(self):
        print("[DBG] TelloBasic: Taking Off.")
        self.tello.connect()
        self.tello.takeoff()

    def stop(self, immediately=False):
        if immediately:
            self.tello.send_rc_control(0, 0, 0, 0)
            self.is_stopped = True
            if debug:
                print("[DBG] Immediate stop command issued.")
        else:
            self.is_stopped = True

    # 
    # Core methods
    # 

    def  enable_loop(self): self.is_loop_enabled = True
    def disable_loop(self): self.is_loop_enabled = False

    # 
    # The "Move"
    # 
    
    def move(self, x_axis, y_axis, z_axis, travel=20):

        # current timestamp
        current_time = time.time()

        # skip if interval not reachded
        if current_time - self.last_move_time < self.MIN_UPDATE_INTERVAL: return False
        
        # lock
        self.last_move_time = current_time

        # stop
        if x_axis == 0 and y_axis == 0 and z_axis == 0:
            self.stop(True)
            return True

        # x
        if x_axis < 0:   self.tello.move_left(travel)
        elif x_axis > 0: self.tello.move_right(travel)

        # y
        if y_axis < 0:   self.tello.move_back(travel)
        elif y_axis > 0: self.tello.move_forward(travel)

        # z
        if z_axis < 0:   self.tello.move_down(travel)
        elif z_axis > 0: self.tello.move_up(travel)

        # deadline
        self.move_deadline = current_time + self.TIMEOUT
        self.is_stopped = False
        return False

    # 
    # The "Loop"
    # 

    def loop(self):

        if not self.is_loop_enabled: return

        # stop on timeout
        if time.time() > self.move_deadline and not self.is_stopped:
            if debug: print("[DBG] TelloBasic: Timeout.")
            self.stop(True)
