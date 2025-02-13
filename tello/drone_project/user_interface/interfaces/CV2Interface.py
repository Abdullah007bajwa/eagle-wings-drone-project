import cv2
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from config.settings import debug

# 
# The "CV2Interface" class
# 

class CV2Interface:

    COLORS = {
        'blue': (255, 0, 0),
        'green': (0, 255, 0),
        'red': (0, 0, 255),
    }

    # 
    # Constructor
    # 

    def __init__(self):

        # config
        self.window_label = "Object Tracker"

        # States
        self.is_closed = False
        self.is_drawing_boundary = False

        self.is_boundary_hidden = True
        self.is_center_hidden = True

        # Variables
        self.camera = None
        self.ix, self.iy = -1, -1
        self.boundary = None
        self.boundary_color = self.COLORS['green']
        self.boundary_frame = None
        self.center = None
        self.center_color = self.COLORS['blue']

        # Listeners
        self.on_boundary_listeners = []
        self.on_frame_listeners = []

    # 
    # Core
    # 

    def set_camera(self, camera): self.camera = camera
    def update_image(self, frame): cv2.imshow(self.window_label, frame)

    def add_on_boundary   (self, callback): self.on_boundary_listeners.append(callback)
    def add_frame_listener(self, callback): self.on_frame_listeners.append(callback)

    # Input Boundary
    def input_boundary(self):
        self.boundary_frame = self.camera.frame()

        cv2.namedWindow(self.window_label)
        cv2.setMouseCallback(self.window_label, self.input_boundary_callback)

        while True:
            frame = self.boundary_frame.copy()
            self.draw_boundary(frame, force=True)
            self.update_image(frame)

            key = cv2.waitKey(1) & 0xFF
            if key == 13 or key == 32 or key == ord('g'): self.confirm_boundary(); break
            if                           key == ord('x'): self.cancel_boundary (); break

    # Input Boundary: Callback
    def input_boundary_callback(self, event, x, y, *_, **__):
        
        # Mouse Down
        if event == cv2.EVENT_LBUTTONDOWN:
            self.ix, self.iy = x, y
            self.is_drawing_boundary = True

        # Mouse Move
        elif event == cv2.EVENT_MOUSEMOVE and self.is_drawing_boundary:
            w, h = abs(x - self.ix), abs(y - self.iy)
            self.update_boundary(min(self.ix, x), min(self.iy, y), w, h)

        # Mouse Up
        elif event == cv2.EVENT_LBUTTONUP:
            w, h = abs(x - self.ix), abs(y - self.iy)
            x, y = min(self.ix, x), min(self.iy, y)
            self.boundary = (x, y, w, h)

    # Confirm Boundary
    def confirm_boundary(self):
        if self.boundary and self.is_drawing_boundary:
            for callback in self.on_boundary_listeners:
                callback()
        self.is_drawing_boundary = False
    
    # Cancel Boundary
    def cancel_boundary(self):
        self.is_drawing_boundary = False


    # 
    # Boundary and Center methods
    # 

    def update_boundary(self, x, y, w, h, color=None, show=False):
        self.boundary = (x, y, w, h)
        if color: self.boundary_color = self.COLORS[color]
        if show: self.show_boundary()

    def update_center(self, cx, cy, color=None, show=False):
        self.center = (cx, cy)
        if color: self.center_color = self.COLORS[color]
        if show: self.show_center()

    def show_boundary(self): self.is_boundary_hidden = False
    def hide_boundary(self): self.is_boundary_hidden = True
    def show_center(self): self.is_center_hidden = False
    def hide_center(self): self.is_center_hidden = True

    def draw_boundary(self, frame, force=False):
        if frame is not None and self.boundary and (force or not self.is_boundary_hidden):
            x, y, w, h = self.boundary
            cv2.rectangle(frame, (x, y), (x + w, y + h), self.boundary_color, 2)

    def draw_center(self, frame, force=False):
        if frame is not None and self.center and (force or not self.is_center_hidden):
            frame_center = (frame.shape[1] // 2, frame.shape[0] // 2)
            cv2.line(frame, frame_center, self.center, self.center_color, 2)
            cv2.circle(frame, self.center, radius=5, color=self.center_color, thickness=-1)

    def draw(self, frame):
        self.draw_boundary(frame)
        self.draw_center(frame)

    # 
    # Close
    # 
    
    def close(self):
        if debug: print("[DBG] Closing CV2Interface.")

        self.is_closed = True
        self.camera.stop()
        cv2.destroyAllWindows()

    # 
    # The "Loop"
    # 

    def loop(self):


        # Condition
        if self.is_closed or self.is_drawing_boundary:
            return

        # Camera Frame
        frame = self.camera.frame()

        for callback in self.on_frame_listeners: callback(frame)
        self.draw(frame)

        self.update_image(frame)


        key = cv2.waitKey(1)
        if key == ord('b'):   self.input_boundary()
        elif key == ord('x'): self.close()

        # close
        try:
            if cv2.getWindowProperty(self.window_label, cv2.WND_PROP_VISIBLE) < 1:
                self.close()
        except: self.close()

    # 
    # dunders
    # 

    def __str__(self):
        return(f"CV2Interface: [boundary={self.boundary}, drawing={self.is_drawing_boundary}, on_boundary={len(self.on_boundary_listeners)}, on_frame={len(self.on_frame_listeners)}")
