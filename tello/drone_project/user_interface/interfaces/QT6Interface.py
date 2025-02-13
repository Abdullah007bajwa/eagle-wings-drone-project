from time import time
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QGridLayout
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtSvgWidgets import QSvgWidget

from config.settings import debug, FRAME_SIZE, MAX_DISTANCE, FRAME_RATE

# 
# Globals
# 

K = Qt.Key
max_distances = {
    'x': FRAME_SIZE[0]/2,
    'y': FRAME_SIZE[1]/2,
    'z': MAX_DISTANCE
}

# 
# Elements Helper
# 

class QT6Elements:

    @staticmethod
    def pushbutton(label: str, callback) -> QPushButton:
        button = QPushButton(label)
        button.clicked.connect(lambda: callback(label))
        return button

# 
# The "QT6Interface" class
# 

class QT6Interface(QWidget):

    # 
    # Constructor
    # 

    def __init__(self, controller, frame_rate=FRAME_RATE):
        super().__init__()

        # Config
        self.TELLO_STATUS_INTERVAL=1

        # Arguments
        self.controller = controller
        self.frame_rate = frame_rate

        # Listeners
        self.on_boundary_listeners = []
        self.on_frame_listeners = []

        # States
        self.is_closed = False
        self.is_drawing = False
        self.is_drawing_boundary = False

        # SVG states and variables
        self.center = None  # (x, y)
        self.boundary = None  # (x, y, w, h)
        self.center_color = 'blue'
        self.boundary_color = 'green'
        self.is_boundary_hidden = True
        self.is_center_hidden = True

        # Variables
        self.tello_status_updated_at = 0
        self.camera = None

        # Setup QT6 App
        self.setLayout(self.make_layout())
        self.setup_loop(start=True)
        self.update_status("Initialized")

        # Show UI
        self.show()

    # 
    # Layout
    # 

    def make_layout(self):
        main_layout = QVBoxLayout()
        top_layout = QHBoxLayout()

        top_layout.addLayout(self.get_image_sublayout())
        top_layout.addLayout(self.get_controls_sublayout())

        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.get_status_widget())

        return main_layout


    def get_image_sublayout(self):
        # Label (Image)
        self.image_label = QLabel(self)

        # SVG (Boundary)
        self.svg_widget = QSvgWidget(self)
        self.svg_widget.hide()
        self.svg_widget_boundary = QSvgWidget(self)
        self.svg_widget_boundary.hide()

        # Layout
        image_layout = QVBoxLayout()
        self.image_label.setPixmap(QPixmap())
        image_layout.addWidget(self.image_label)
        return image_layout

    def get_controls_sublayout(self):
        controls_sublayout = QVBoxLayout()

        # WASD

        wasd_layout = QGridLayout()
        wasd_buttons = {
            (0, 1): 'W',
            (1, 0): 'A',
            (1, 1): 'S',
            (1, 2): 'D',
            (2, 0): 'Q',
            (2, 2): 'E',
            (0, 3): 'I',
            (2, 3): 'K'
        }
        for position, label in wasd_buttons.items():
            btn = QT6Elements.pushbutton(label, self.on_button)
            wasd_layout.addWidget(btn, *position)
        
        controls_sublayout.addLayout(wasd_layout)

        # Actions

        actions = QHBoxLayout()
        for label in [
            "Connect",
            "Take Off",
            "Stream On",
            "Stream Off",
            "Land",
            "Stop",
            "Close",
        ]:  actions.addWidget(QT6Elements.pushbutton(label, self.on_button))

        controls_sublayout.addLayout(actions)
        return controls_sublayout

    def get_status_widget(self):
        self.status_label = QLabel(self)
        return self.status_label

    # 
    # Status
    # 

    def update_status(self, status_message):
        self.status_label.setText(status_message)

    # 
    # Loop Timer
    # 

    def setup_loop(self, start=False):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.loop)
        if start: self.start_loop()

    def start_loop(self):
        self.timer.start(self.frame_rate)

    def stop_loop(self):
        self.timer.stop()

        
    # 
    # Core
    # 

    # Camera
    def set_camera(self, camera):
        self.camera = camera

    # Set Callbacks
    def add_on_boundary   (self, callback): self.on_boundary_listeners.append(callback)
    def add_frame_listener(self, callback): self.on_frame_listeners.append(callback)

    # Camera: Update Frame
    def update_image(self, frame):
        """ Helper function to update the QLabel with the current frame. """
        height, width, channel = frame.shape
        q_img = QImage(frame.data, width, height, width * 3, QImage.Format.Format_BGR888)
        pixmap = QPixmap.fromImage(q_img)
        self.image_label.setPixmap(pixmap)

    # Boundary: Start Input
    def input_boundary(self):
        """ Activate boundary input mode. """
        self.stop_loop()
        self.is_drawing_boundary = True

        self.boundary_frame = self.camera.frame()
        self.frame = self.boundary_frame.copy()
        self.update_image(self.boundary_frame)
        self.show_boundary()

    # Boundary: Confirm and Stop Input
    def confirm_boundary(self):
        """ Confirm the boundary input. """

        self.hide_boundary()
        if self.is_drawing_boundary and self.boundary is not None:

            for callback in self.on_boundary_listeners:
                callback()

        self.is_drawing_boundary = False
        self.start_loop()

    # Boundary: Cancel and Stop Input
    def cancel_boundary(self):
        """ Cancel boundary input and close. """
        self.is_drawing_boundary = False
        self.hide_boundary()

    # 
    # App Events
    # 

    # Mouse: Press
    def mousePressEvent(self, event):
        if self.is_drawing_boundary and event.button() == Qt.MouseButton.LeftButton:
            self.is_drawing = True
            self.ix, self.iy = event.pos().x(), event.pos().y()

    # Mouse: Move
    def mouseMoveEvent(self, event):
        if self.is_drawing and self.is_drawing_boundary:
            x, y, w, h = self.ix, self.iy, event.pos().x() - self.ix, event.pos().y() - self.iy
            self.update_boundary(x, y, w, h)

    # Mouse: Release
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_drawing:
            self.is_drawing = False
            self.boundary = (self.ix, self.iy, event.pos().x() - self.ix, event.pos().y() - self.iy)
            self.update_boundary(*self.boundary)

    # Keyboard: Key Press
    def keyPressEvent(self, event):
        key = event.key()

        key_buttons_map = {
            K.Key_W: 'W',
            K.Key_A: 'A',
            K.Key_S: 'S',
            K.Key_D: 'D',
            K.Key_Q: 'Q',
            K.Key_E: 'E',
            K.Key_I: 'I',
            K.Key_K: 'K',
            K.Key_Z: 'Connect',
            K.Key_N: 'Take Off',
            K.Key_M: 'Land',
            K.Key_1: 'Stream On',
            K.Key_0: 'Stream Off',
            K.Key_X: 'Stop',
            K.Key_4: 'Close',
        }

        # Boundary Actions

        if self.is_drawing_boundary:
            if key in [K.Key_Return, K.Key_Space, K.Key_G]: self.confirm_boundary()
            elif key == K.Key_X:                            self.cancel_boundary ()
            return

        # Generic Actions

        if key == K.Key_B:
            self.input_boundary()

        elif key in key_buttons_map:
            self.on_button(key_buttons_map[key])

        else:
            print("No Action assigned for Key", key)


    # 
    # SVG Methods
    # 

    def update_boundary(self, x, y, w, h, color=None, show=False):
        """ Update the boundary rectangle and refresh SVG. """
        self.boundary = (x, y, w, h)
        if color: self.boundary_color = color
        self.set_svg(show)

    def update_center(self, x, y, color=None, show=False):
        """ Update the center point and refresh SVG. """
        self.center = (x, y)
        if color: self.center_color = color
        self.set_svg(show)

    def hide_boundary(self):
        self.is_boundary_hidden = True
        if self.is_center_hidden: self.hide_svg()

    def hide_center(self):
        self.is_center_hidden = True
        if self.is_boundary_hidden: self.hide_svg()

    def show_boundary(self):
        self.is_boundary_hidden = False
        self.show_svg()

    def show_center(self):
        self.is_center_hidden = False
        self.show_svg()

    def show_svg(self):
        self.svg_widget.show()

    def hide_svg(self):
        self.svg_widget.hide()

    # SVG Setter
    def set_svg(self, show=False):
        """ Generate and set SVG based on current boundary and center settings. """
        svg_elements = []

        # Boundary (Rect)
        if not self.is_boundary_hidden and self.boundary:
            x, y, w, h = self.boundary
            color = self.boundary_color if self.boundary_color else 'green'
            svg_elements.append(
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" style="fill:none;stroke:{color};stroke-width:2"/>'
            )

        # Center (Line)
        if not self.is_center_hidden and self.center:
            cx, cy = self.center
            color = self.center_color if self.center_color else 'blue'
            svg_elements.append(
                f'<line x1="{self.image_label.width() // 2}" y1="{self.image_label.height() // 2}" x2="{cx}" y2="{cy}" style="stroke:{color};stroke-width:2"/>'
            )
            svg_elements.append(
                f'<circle cx="{cx}" cy="{cy}" r="3" fill="{color}"/>'
            )

        # SVG
        svg_content = f"""
            <svg width="{self.image_label.width()}" height="{self.image_label.height()}" xmlns="http://www.w3.org/2000/svg">
                {''.join(svg_elements)}
            </svg>
        """
        self.svg_widget.load(bytearray(svg_content, encoding='utf-8'))
        self.svg_widget.setGeometry(0, 0, self.image_label.width(), self.image_label.height())
        if show: self.show_svg()


    # 
    # App Callbacks
    # 

    def on_button(self, label):
        if debug: print("[DBG] On Button Callback : label =", label)

        if label == 'Close':
            self.close()

        elif self.controller:
            if   label == 'W': self.controller.move( 0,                   max_distances['y'],   0                  )
            elif label == 'A': self.controller.move(-max_distances['x'],  0,                    0                  )
            elif label == 'S': self.controller.move( 0,                   -max_distances['y'],  0                  )
            elif label == 'D': self.controller.move( max_distances['x'],  0,                    0                  )
            elif label == 'Q': print("Pending Q")
            elif label == 'E': print("Pending E")
            elif label == 'I': self.controller.move( 0,                   0,                     max_distances['z'])
            elif label == 'K': self.controller.move( 0,                   0,                    -max_distances['z'])

            elif label == "Connect"   : self.controller.connect   ()
            elif label == "Take Off"  : self.controller.takeoff   ()
            elif label == "Stream On" : self.controller.streamon  ()
            elif label == "Stream Off": self.controller.streamoff ()
            elif label == "Land"      : self.controller.land      ()
            elif label == "Stop"      : self.controller.stop      ()

            else:
                print("[INF] Unknown Button Action", label)
        
        else: print("[WRN] No Controller.")

 
    def update_tello_status(self):
        if self.controller and self.controller.tello and hasattr(self.controller.tello, 'get_current_state'):
            status = self.controller.tello.get_current_state()
            if status:
                self.update_status(str(status))


    # 
    # Close
    # 
    
    def close(self):
        print("Close")


    # 
    # The "Loop"
    # 

    def loop(self):

        # Condition
        if self.is_closed or self.is_drawing_boundary:
            return

        # Camera Frame
        current_frame = self.camera.frame()

        for callback in self.on_frame_listeners: callback(current_frame)

        self.update_image(current_frame)

        # Status Update
        if self.TELLO_STATUS_INTERVAL is not None:
            current_time = time()
            if current_time > self.tello_status_updated_at + self.TELLO_STATUS_INTERVAL:
                self.update_tello_status()
                self.tello_status_updated_at = current_time