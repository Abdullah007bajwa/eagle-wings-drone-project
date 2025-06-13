import sys, os, time
from os.path import join, dirname, abspath
sys.path.append(abspath(join(dirname(__file__), "../../")))

from PyQt6.QtWidgets import (
    QApplication, QLabel, QWidget, QVBoxLayout, QPushButton,
    QHBoxLayout, QGridLayout
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtSvgWidgets import QSvgWidget

# Attempt to load the YOLO model. If unavailable, suppress the error.
try:
    from ultralytics import YOLO
    MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'local', 'YoloV8Tracker_model.pt')
    yolo_model = YOLO(MODEL_PATH)
    print("YOLO model loaded successfully.")
except Exception as e:
    print(f"[INFO] YOLO model not loaded or not required: {e}")
    yolo_model = None

import cv2
import numpy as np
from config.settings import debug, FRAME_SIZE, MAX_DISTANCE, FRAME_RATE

# Global key constants and maximum distances for each axis
K = Qt.Key
max_distances = {
    'x': FRAME_SIZE[0] // 2,
    'y': FRAME_SIZE[1] // 2,
    'z': MAX_DISTANCE
}

# Helper class for creating UI elements
class QT6Elements:
    @staticmethod
    def pushbutton(label: str, callback) -> QPushButton:
        button = QPushButton(label)
        button.clicked.connect(lambda: callback(label))
        return button

# Custom QLabel that emits a clicked signal with x and y coordinates
class ClickableLabel(QLabel):
    clicked = pyqtSignal(int, int)  # Emits (x, y) coordinates

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()  # Returns a QPointF
            self.clicked.emit(int(pos.x()), int(pos.y()))
        super().mousePressEvent(event)

# Main interface class using QWidget
class QT6Interface(QWidget):
    def __init__(self, controller, frame_rate=FRAME_RATE):
        super().__init__()

        # Store the controller and frame rate
        self.controller = controller
        self.frame_rate = frame_rate

        # Listeners for boundary and frame updates
        self.on_boundary_listeners = []
        self.on_frame_listeners = []

        # UI state for overlays
        self.center = None      # (x, y) coordinate of the target center
        self.boundary = None    # (x, y, w, h) bounding box of the target
        self.center_color = 'blue'
        self.boundary_color = 'green'
        self.is_boundary_hidden = True
        self.is_center_hidden = True

        # Camera and tracker references
        self.camera = None
        self.tracker = None

        # Application state attributes (missing before)
        self.is_closed = False
        self.is_drawing = False
        self.is_drawing_boundary = False

        # Setup UI
        self.setLayout(self.make_layout())
        self.setup_loop(start=True)
        self.update_status("Initialized")
        self.show()

    def set_tracker(self, tracker):
        """Connect tracker signals to UI update slots."""
        self.tracker = tracker
        tracker.boundaryUpdated.connect(self.update_boundary)
        tracker.centerUpdated.connect(self.update_center)
        tracker.trackingLost.connect(self.handle_tracking_lost)

    def make_layout(self):
        """Build and return the main UI layout."""
        main_layout = QVBoxLayout()
        top_layout = QHBoxLayout()

        top_layout.addLayout(self.get_image_sublayout())
        top_layout.addLayout(self.get_controls_sublayout())
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.get_status_widget())
        return main_layout

    def get_image_sublayout(self):
        """Create a layout for the image display."""
        self.image_label = ClickableLabel(self)
        self.image_label.setPixmap(QPixmap())
        self.image_label.clicked.connect(self.handle_image_click)
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        return layout

    def get_controls_sublayout(self):
        """Create a layout for control buttons."""
        controls_layout = QVBoxLayout()

        # Create a grid of WASD control buttons
        wasd_layout = QGridLayout()
        wasd_buttons = {
            (0, 1): 'W', (1, 0): 'A', (1, 1): 'S', (1, 2): 'D',
            (2, 0): 'Q', (2, 2): 'E', (0, 3): 'I', (2, 3): 'K'
        }
        for position, label in wasd_buttons.items():
            btn = QT6Elements.pushbutton(label, self.on_button)
            wasd_layout.addWidget(btn, *position)
        controls_layout.addLayout(wasd_layout)

        # Create a horizontal layout for action buttons
        actions_layout = QHBoxLayout()
        for label in ["Connect", "Take Off", "Stream On", "Stream Off", "Land", "Stop", "Close"]:
            actions_layout.addWidget(QT6Elements.pushbutton(label, self.on_button))
        controls_layout.addLayout(actions_layout)

        return controls_layout

    def get_status_widget(self):
        """Return a QLabel to display status messages."""
        self.status_label = QLabel(self)
        return self.status_label

    def update_status(self, status_message):
        """Update the status label with the provided message."""
        self.status_label.setText(status_message)

    def setup_loop(self, start=False):
        """Initialize the UI update loop using a QTimer."""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.loop)
        if start:
            self.start_loop()

    def start_loop(self):
        """Start the timer loop."""
        self.timer.start(self.frame_rate)

    def stop_loop(self):
        """Stop the timer loop."""
        self.timer.stop()

    def set_camera(self, camera):
        """Assign a camera instance."""
        self.camera = camera

    def add_on_boundary(self, callback):
        """Register a callback for boundary events."""
        self.on_boundary_listeners.append(callback)

    def add_frame_listener(self, callback):
        """Register a callback for frame updates."""
        self.on_frame_listeners.append(callback)

    def update_image(self, frame):
        """Convert and display the current frame on the image label."""
        height, width, _ = frame.shape
        q_img = QImage(frame.data, width, height, width * 3, QImage.Format.Format_BGR888)
        pixmap = QPixmap.fromImage(q_img)
        self.image_label.setPixmap(pixmap)

    def update_boundary(self, boundary):
        """Slot: update the displayed boundary overlay."""
        self.boundary = boundary
        print(f"UI: Boundary updated to {boundary}")

    def update_center(self, center):
        """Slot: update the displayed center overlay."""
        self.center = center
        print(f"UI: Center updated to {center}")

    def handle_tracking_lost(self):
        """Slot: clear overlays when tracking is lost."""
        self.boundary = None
        self.center = None
        print("UI: Tracking lost, hiding overlays.")

    def handle_image_click(self, x, y):
        """Handle image clicks to select a face."""
        print(f"Image clicked at ({x}, {y})")
        if self.tracker:
            sel = self.tracker.select_face(x, y)
            if sel:
                self.update_boundary(sel["box"])
                self.update_center(sel["center"])
            else:
                print("No face selected on click.")

    def on_button(self, label):
        """Map button labels to controller actions."""
        if debug:
            print("[DBG] On Button Callback : label =", label)
        if label == 'Close':
            self.close()
        elif label == 'Take Off':
            self.controller.takeoff()
        elif label == 'Land':
            self.controller.land()
        elif label == 'Stream On':
            self.controller.stream_on()
        elif label == 'Stream Off':
            self.controller.stream_off()
        elif label == 'Connect':
            self.controller.connect()
        elif label == 'Stop':
            self.controller.stop()
        elif label in ['W', 'A', 'S', 'D', 'Q', 'E', 'I', 'K']:
            self.controller.handle_direction(label)
        else:
            print("[INF] Unknown Button Action", label)

    def close(self):
        """Close the application."""
        print("Closing Application")
        self.is_closed = True

    def loop(self):
        """Main UI loop: capture a frame, process it, and update the display."""
        if self.is_closed:
            return

        current_frame = self.camera.frame()
        if current_frame is None:
            print("[WARN] Camera frame is None, skipping update.")
            return

        # Process frame through all registered frame listeners
        for callback in self.on_frame_listeners:
            processed_frame = callback(current_frame)
            if processed_frame is not None:
                current_frame = processed_frame

        self.update_image(current_frame)
