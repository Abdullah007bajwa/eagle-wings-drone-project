import sys
import os
import time
import logging
from dotenv import load_dotenv

# ——————————————————————————
# Configuration & Logging
# ——————————————————————————
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# default interface & model; camera auto-detected
DEFAULT_INTERFACE = "QT6Interface"
DEFAULT_MODEL     = "LightCNNTracker"

# these get set at runtime
camera_type    = None
interface_type = os.getenv("INTERFACE", DEFAULT_INTERFACE)
model_type     = os.getenv("MODEL",     DEFAULT_MODEL)

# globals
tello = None
app = None
camera = None
controller = None
interface = None
model = None
navigator = None
guide = None


# ——————————————————————————
# Auto-detect best camera
# ——————————————————————————
def detect_camera():
    # 1) Try Tello
    try:
        from djitellopy import Tello
        test_tello = Tello()
        test_tello.connect()
        battery = test_tello.get_battery()
        logger.info(f"Tello detected! Battery: {battery}%")
        test_tello.end()
        return "TelloCam"
    except Exception as e:
        logger.warning(f"Tello not available: {e}")

    # 2) Try laptop webcam
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        ok, _ = cap.read()
        if ok:
            cap.release()
            logger.info("WebCam detected.")
            return "WebCam"
        cap.release()
    except Exception as e:
        logger.warning(f"WebCam test failed: {e}")

    # 3) Fallback
    logger.info("Falling back to SimCam.")
    return "SimCam"


# ——————————————————————————
# Tello setup/shutdown
# ——————————————————————————
def setup_tello():
    global tello
    from djitellopy import Tello
    tello = Tello()
    tello.connect()
    if os.getenv("AUTO_STREAMON", "1") == "1":
        tello.streamon()
    if os.getenv("AUTO_TAKEOFF", "0") == "1":
        tello.takeoff()
    logger.info("Tello initialized.")


def tello_shutdown():
    global tello
    if tello and os.getenv("AUTO_STREAMON", "1") == "1":
        tello.streamoff()
        tello.land()
        logger.info("Tello shutdown complete.")


# ——————————————————————————
# Component setup functions
# ——————————————————————————
def setup_camera():
    global camera
    logger.info(f"Initializing camera: {camera_type}")
    if camera_type == "TelloCam":
        from drone_project.object_detector.input.TelloCam import TelloCam
        camera = TelloCam(tello)
    elif camera_type == "WebCam":
        from drone_project.object_detector.input.WebCam import WebCam
        camera = WebCam()
    elif camera_type == "SimCam":
        from drone_project.object_detector.input.SimCam import SimCam
        camera = SimCam()
    else:
        raise ImportError(f"Unknown camera type: {camera_type}")
    logger.info(f"Camera set to {type(camera)}")


def setup_controller():
    global controller
    logger.info(f"Initializing controller for: {camera_type}")
    if camera_type == "TelloCam":
        from drone_project.core.controllers.TelloControllerSmooth import TelloControllerSmooth
        controller = TelloControllerSmooth(tello, False)
    elif camera_type == "WebCam":
        from drone_project.core.controllers.DummyController import DummyController
        controller = DummyController()
    else:  # SimCam
        from drone_project.core.controllers.SimController import SimController
        controller = SimController()
    logger.info(f"Controller set to {type(controller)}")


def setup_interface():
    global app, interface
    logger.info(f"Initializing interface: {interface_type}")
    if interface_type == "QT6Interface":
        from PyQt6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        from drone_project.user_interface.interfaces.QT6Interface import QT6Interface
        interface = QT6Interface(controller)
    elif interface_type == "CV2Interface":
        from drone_project.user_interface.interfaces.CV2Interface import CV2Interface
        interface = CV2Interface()
    else:
        raise ImportError(f"Unknown interface: {interface_type}")
    logger.info(f"Interface set to {type(interface)}")


def setup_model():
    global model
    logger.info(f"Loading model: {model_type}")
    try:
        from drone_project.object_detector.models.LightCNNTracker import LightCNNTracker
        model = LightCNNTracker(interface)
    except Exception:
        # fallback by model_type
        if model_type == "DaSiamMultipleTracker":
            from drone_project.object_detector.models.DaSiamMultipleTracker import DaSiamMultipleTracker
            model = DaSiamMultipleTracker(interface)
        elif model_type == "DaSiamRPNTracker":
            from drone_project.object_detector.models.DaSiamRPNTracker import DaSiamRPNTracker
            model = DaSiamRPNTracker(interface)
        elif model_type == "CSRTTracker":
            from drone_project.object_detector.models.CSRTTracker import CSRTTracker
            model = CSRTTracker(interface)
        elif model_type == "YoloV8Tracker":
            from drone_project.object_detector.models.YoloV8Tracker import YoloV8Tracker
            model = YoloV8Tracker(interface)
        else:
            # default fallback
            from drone_project.object_detector.models.LightCNNTracker import LightCNNTracker
            model = LightCNNTracker(interface)
    logger.info(f"Model initialized: {type(model)}")


def setup_navigator():
    global navigator
    from drone_project.navigation_plan.navigators.GridNavigator import GridNavigator
    navigator = GridNavigator(model)
    logger.info("Navigator initialized.")


def setup_guide():
    global guide
    from drone_project.flight_guide.guide.GridGuide import GridGuide
    guide = GridGuide(navigator, controller)
    logger.info("Guide initialized.")


def bind_listeners():
    if interface is None or camera is None:
        raise RuntimeError("Interface and camera must be initialized first")
    interface.set_camera(camera)
    interface.add_on_boundary(model.set_object)
    interface.add_frame_listener(model.on_frame)
    interface.add_frame_listener(navigator.navigate)
    interface.add_frame_listener(guide.update_grid)
    logger.info("Listeners bound.")


# ——————————————————————————
# Main Initialization & Loop
# ——————————————————————————
def initialize_system():
    global camera_type
    # auto-detect
    camera_type = detect_camera()
    os.environ["CAMERA"] = camera_type

    # if drone, start it
    if camera_type == "TelloCam":
        setup_tello()

    # core setup
    setup_camera()
    setup_controller()
    setup_interface()
    setup_model()
    setup_navigator()
    setup_guide()
    bind_listeners()

    return camera, model


def loop():
    # QT6Interface run
    if interface_type == "QT6Interface":
        from PyQt6.QtCore import QTimer
        from drone_project.config.settings import MAIN_LOOP_RATE

        def _tick():
            guide.loop()
            controller.loop()

        timer = QTimer()
        timer.timeout.connect(_tick)
        timer.start(MAIN_LOOP_RATE)
        app.exec()
        tello_shutdown()
        return

    # CV2Interface run
    try:
        while not interface.is_closed:
            interface.loop()
            guide.loop()
            controller.loop()
            time.sleep(0.01)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        tello_shutdown()


# ——————————————————————————
# Entry Point
# ——————————————————————————
if __name__ == "__main__":
    initialize_system()
    loop()
