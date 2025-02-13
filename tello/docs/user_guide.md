# User Guide

## Overview
This project enables real-time object tracking and navigation for drones, supporting both physical and simulated environments. It allows users to select from multiple cameras, interfaces, and object-tracking models.

## Features
- **Camera Types**:
  - **WebCam**: Use your system's webcam.
  - **TelloCam**: DJI Tello drone camera.
  - **SimCam**: Simulated 3D drone in the browser.
- **Interfaces**:
  - **QT6Interface**: PyQt6-based graphical interface.
  - **CV2Interface**: OpenCV-based visual interface.
- **Models**: DaSiam and CSRT object tracking.
- **Grid Navigation**: Guidance using a 3x3 grid system.

## Camera Switching
You can switch the camera type via the command line or `.env` file:
1. **Command Line**:
   ```bash
   python main.py [CAMERA]
   ```
   Examples:
   - `TelloCam`: For DJI Tello drone.
   - `SimCam`: For 3D simulation.
   - `WebCam`: Default system webcam.

2. **Environment File**:
   - Edit `.env` to configure the camera:
     ```env
     CAMERA=WebCam
     ```

**Note**: If the selected camera type is not implemented, you will receive an error.

## Prerequisites
1. Python 3.8+
2. Required libraries:
   - `djitellopy`
   - `opencv-python`
   - `PyQt6`
   - `numpy`
   - `websockets`
   - `dotenv`
3. Node.js (for SimCam simulation).

## Setup
1. **Simulator (Optional)**:
   - Extract `three_sim.zip`.
   - Navigate to the folder and run:
     ```bash
     npm install
     npm start
     ```

2. **Environment Configuration**:
   - Edit `.env` to set:
     ```env
     CAMERA=TelloCam
     INTERFACE=QT6Interface
     MODEL=DaSiamRPNTracker
     AUTO_STREAMON=1
     AUTO_TAKEOFF=0
     ```

3. **Run the Program**:
   ```bash
   python main.py [CAMERA] [INTERFACE] [MODEL]
   ```
   - Examples:
     - Tello with QT6:
       ```bash
       python main.py TelloCam QT6Interface DaSiamRPNTracker
       ```
     - Simulator with OpenCV:
       ```bash
       python main.py SimCam CV2Interface CSRTTracker
       ```

4. **Shutdown**:
   - Run the shutdown script:
     ```bash
     python scripts/shutdown_sequence.py
     ```

## Controls
- **QT6Interface**:
  - Movement: WASD keys.
  - Actions:
    - Connect: `Z`
    - Take Off: `N`
    - Land: `M`
    - Stream On: `1`
    - Stream Off: `0`
    - Stop: `X`
    - Close: `4`
- **CV2Interface**:
  - Input Boundary: Press `b`.
  - Exit: Press `x`.
