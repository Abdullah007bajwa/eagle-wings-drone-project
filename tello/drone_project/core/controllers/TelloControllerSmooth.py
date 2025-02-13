# 
# Imports
# 

import os, sys, time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from djitellopy import Tello
from config.settings import debug
from core.util.classes.VelocityMapper import VelocityMapper

# 
# The "TelloControllerSmooth" class
# 

class TelloControllerSmooth:

    # 
    # Config
    # 
    
    SPEED = {
        'x': 30, 
        'y': 30, 
        'z': 30,
    }

    TIMEOUT = 1
    MIN_UPDATE_INTERVAL = 0.1

    speed_factors = {
        'x': {'low': 0.1, 'high': 1, 'scale': 1.5},
        'y': {'low': 0.1, 'high': 1, 'scale': 1.5},
        'z': {'low': 0.1, 'high': 1, 'scale': 1.5}
    }

    # 
    # Constructor
    # 

    def __init__(self, tello: Tello, takeoff_on_start=True):
        
        # Arguments
        self.tello = tello
        if takeoff_on_start: self.takeoff()

        # States
        self.is_loop_enabled = True
        self.is_changing_course = False
        self.velocities_changed = False
        self.is_stopped = True

        # timestamps
        self.last_move_time = 0
        self.velocities_deadline = time.time() + self.TIMEOUT

        # Velocities
        self.velocities = {
            'a': 0, # Right
            'b': 0, # Forward
            'c': 0, # Up
            'd': 0, # Clockwise
        }
        

    #
    # Tello wraps
    #

    def connect  (self): self.tello.connect   ()
    def end      (self): self.tello.end       ()
    def takeoff  (self): self.tello.takeoff   ()
    def land     (self): self.tello.land      ()
    def streamon (self): self.tello.streamon  ()
    def streamoff(self): self.tello.streamoff ()

    # 
    # Remote Control
    # 

    def rc(self, a, b, c, d): self.tello.send_rc_control(a, b, c, d)
    def stop_raw(self): self.rc(0, 0, 0, 0)

    # 
    # Controls
    # 

    def stop(self, immediately=False):
        for k in self.velocities: self.velocities[k] = 0
        
        if immediately: self.stop_raw()
        else: self.velocities_changed = True

    # 
    # Core methods
    # 

    def  enable_loop(self): self.is_loop_enabled = True
    def disable_loop(self): self.is_loop_enabled = False

    # 
    # The "Move"
    # 
    
    def move(self, x_axis, y_axis, z_axis):

        # skip if another "move" call is executing
        if self.is_changing_course: return False

        # current timestamp
        current_time = time.time()

        # skip if interval not reachded
        if current_time - self.last_move_time < self.MIN_UPDATE_INTERVAL: return False

        # lock
        self.is_changing_course = True
        self.last_move_time = current_time

        # map
        x, y, z = VelocityMapper.map_axis(x_axis, y_axis, z_axis)

        # stop
        if x_axis == 0 and y_axis == 0 and z_axis == 0:
            self.stop(True)
            return True

        # update velocities
        self.velocities['b'] = VelocityMapper.calculate_speed(z, self.SPEED['z'], **self.speed_factors['z'])
        self.velocities['c'] = VelocityMapper.calculate_speed(y, self.SPEED['y'], **self.speed_factors['y'])
        self.velocities['d'] = VelocityMapper.calculate_speed(x, self.SPEED['x'], **self.speed_factors['x'])

        # Set Timeouts
        self.velocities_deadline = current_time + self.TIMEOUT
        self.is_stopped = False

        # release
        self.is_changing_course = False

        # trigger
        self.velocities_changed = True
        return True

    # 
    # The "Loop"
    # 

    def loop(self):

        # Skip if loop disabled
        if not self.is_loop_enabled: return

        # wait for velocity updation process
        if not self.is_changing_course:

            # stop drone on timeout
            if time.time() > self.velocities_deadline and not self.is_stopped:
                self.stop(immediately=True)
                if debug: print("[DBG] Stop on Timeout")
                self.is_stopped = True
                return

            # if velocities changed
            if self.velocities_changed:

                # update velocities
                self.rc(**self.velocities)
                if debug: print("[DBG] Updated Drone Velocities:", self.velocities)

                self.velocities_changed = False

