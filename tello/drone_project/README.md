# Drone Project

**Version:** 1.1.2-alpha

## Dependencies

To run this project, you'll need to install the following Python packages:

- `djitellopy==2.5.0`
- `numpy==2.1.2`
- `opencv_contrib_python==4.10.0.84`
- `opencv_python==4.10.0.84`
- `PyQt6==6.7.1`
- `PyQt6_sip==13.8.0`
- `pyudev==0.24.0`
- `tello==1.2`
- `WMI==1.4.9`

## Setup Instructions

1. **Unzip project**:
2. **Install the required dependencies**:
   You can install the dependencies using pip. It is recommended to use a virtual environment. Here’s how you can do it:

   ```bash
   python -m venv venv        # Create a virtual environment
   source venv/bin/activate   # Activate the virtual environment (Linux/Mac)
   venv\Scripts\activate       # Activate the virtual environment (Windows)
   pip install -r requirements.txt  # Install dependencies
   ```

   Alternatively, you can install dependencies individually:
   ```bash
   pip install djitellopy==2.5.0 numpy==2.1.2 opencv_contrib_python==4.10.0.84 opencv_python==4.10.0.84 PyQt6==6.7.1 PyQt6_sip==13.8.0 pyudev==0.24.0 tello==1.2 WMI==1.4.9
   ```

3. **Run the main application**:
   Once all dependencies are installed, you can run the application using the following command:

   ```bash
   python main.py
   ```