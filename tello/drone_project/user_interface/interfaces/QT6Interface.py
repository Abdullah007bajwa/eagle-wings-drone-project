from time import time
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QGridLayout
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtSvgWidgets import QSvgWidget

from ultralytics import YOLO
import cv2
import numpy as np

from config.settings import debug, FRAME_SIZE, MAX_DISTANCE, FRAME_RATE

# 
# Globals
# 

K = Qt.Key
max_distances = {
    'x': FRAME_SIZE[0] // 2,
    'y': FRAME_SIZE[1] // 2,
    'z': MAX_DISTANCE
}

# Load YOLOv8 Model
MODEL_PATH = r"C:\Users\arees\OneDrive\Desktop\Object_Tracking_Tello\tello\drone_project\local\YoloV8Tracker_model.pt"
yolo_model = YOLO(MODEL_PATH)

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
        self.TELLO_STATUS_INTERVAL = 1

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

        # WASD Controls
        wasd_layout = QGridLayout()
        wasd_buttons = {
            (0, 1): 'W', (1, 0): 'A', (1, 1): 'S', (1, 2): 'D',
            (2, 0): 'Q', (2, 2): 'E', (0, 3): 'I', (2, 3): 'K'
        }
        for position, label in wasd_buttons.items():
            btn = QT6Elements.pushbutton(label, self.on_button)
            wasd_layout.addWidget(btn, *position)
        
        controls_sublayout.addLayout(wasd_layout)

        # Actions
        actions = QHBoxLayout()
        for label in ["Connect", "Take Off", "Stream On", "Stream Off", "Land", "Stop", "Close"]:
            actions.addWidget(QT6Elements.pushbutton(label, self.on_button))

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
        if start:
            self.start_loop()

    def start_loop(self):
        self.timer.start(self.frame_rate)

    def stop_loop(self):
        self.timer.stop()

    # 
    # Core
    # 

    def set_camera(self, camera):
        self.camera = camera

    def add_on_boundary(self, callback):
        """ Register a callback for when the boundary is set. """
        self.on_boundary_listeners.append(callback)

    def add_frame_listener(self, callback):
        self.on_frame_listeners.append(callback)

    def detect_face(self, frame):
        """ Detects face using YOLOv8 and sets bounding box. """
        results = yolo_model(frame)

        for r in results:
            for box, conf, cls in zip(r.boxes.xyxy, r.boxes.conf, r.boxes.cls):
                x1, y1, x2, y2 = map(int, box[:4])  # Extract bounding box coordinates
                confidence = float(conf)  # Extract confidence score
                class_id = int(cls)  # Extract class ID

                if confidence > 0.5:  # Set a confidence threshold
                    self.boundary = (x1, y1, x2 - x1, y2 - y1)
                    self.center = (x1 + (x2 - x1) // 2, y1 + (y2 - y1) // 2)

                    # Draw Bounding Box on Frame
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"areesha {confidence:.2f}", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    def update_image(self, frame):
        """ Updates QLabel with the current frame. """
        height, width, _ = frame.shape
        q_img = QImage(frame.data, width, height, width * 3, QImage.Format.Format_BGR888)
        pixmap = QPixmap.fromImage(q_img)
        self.image_label.setPixmap(pixmap)

    def on_frame(self, frame):
        self.detect_face(frame)  # Detect face automatically
        self.update_image(frame)

    # 
    # App Callbacks
    # 

    def on_button(self, label):
        if debug:
            print("[DBG] On Button Callback : label =", label)

        if label == 'Close':
            self.close()
        else:
            print("[INF] Unknown Button Action", label)

    # 
    # Close
    # 

    def close(self):
        print("Closing Application")

    # 
    # The "Loop"
    # 

    def loop(self):
        if self.is_closed:
            return

        # Get Frame
        current_frame = self.camera.frame()

        # Detect Face & Update UI
        self.detect_face(current_frame)
        self.update_image(current_frame)

        # Notify Listeners
        for callback in self.on_frame_listeners:
            callback(current_frame)
