# test_lightcnn.py

import cv2
import os
from object_detector.models.LightCNNTracker import LightCNNTracker

# Create a minimal dummy interface with the required methods
class DummyInterface:
    def hide_boundary(self):
        print("hide_boundary called")
    
    def hide_center(self):
        print("hide_center called")

# Instantiate the dummy interface
dummy_interface = DummyInterface()

# Initialize the LightCNNTracker
# (Make sure the model_path and feature_dir paths are correct relative to your working directory)
tracker = LightCNNTracker(
    interface=dummy_interface,
    model_path=os.path.join("drone_project", "object_detector", "LightCNN_29Layers_checkpoint.pth"),
    feature_dir=os.path.join("drone_project", "data", "extracted_features")
)

# Load a test image (replace 'test_face.jpg' with the path to your test image)
test_img_path = "test_face.jpg"
test_img = cv2.imread(test_img_path)
if test_img is None:
    print(f"Test image not found at: {test_img_path}")
    exit()

# Process the frame through the tracker
output_frame = tracker.on_frame(test_img)

# Display the output
cv2.imshow("LightCNNTracker Output", output_frame)
cv2.waitKey(0)
cv2.destroyAllWindows()
