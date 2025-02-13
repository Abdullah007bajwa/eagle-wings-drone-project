import sys, os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from config.settings import FRAME_SIZE, MAX_DISTANCE

# 
# Helper Class
# 

class VelocityMapper:
    @staticmethod
    def map_axis(x_axis: float, y_axis: float, z_axis: float, mx=FRAME_SIZE[0], my=FRAME_SIZE[1], mz=MAX_DISTANCE*2):
        return \
            x_axis / mx, \
            y_axis / my, \
            z_axis / mz

    @staticmethod
    def calculate_speed(value, map_value, low, high, scale):
        
        if value == 0: return 0

        direction = -1 if value < 0 else 1
        speed = max( \
            low, \
            min(high, abs(value) * scale) \
        )
        
        return int(map_value * speed * direction)
