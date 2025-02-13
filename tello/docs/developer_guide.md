# Developer Guide

## Overview
This project is modular, with clear separation of components for cameras, interfaces, models, navigation, and guides. Developers can extend the functionality by adding new components.

## Directory Structure
```
├── main.py                # Entry point
├── .env                   # Environment variables
├── config/                # Configuration files
│   └── settings.py        # Application settings
├── scripts/               # Utility scripts
│   └── shutdown_sequence.py
├── object_detector/       # Object detection modules
│   ├── input/             # Camera inputs (TelloCam, SimCam, WebCam)
│   ├── models/            # Object tracking models
├── user_interface/        # Interfaces (QT6, CV2)
│   └── interfaces/
├── navigation_plan/       # Navigation logic
│   ├── navigators/        # Grid-based navigation
│   └── util/              # Utility functions (e.g., grid drawing)
├── flight_guide/          # Guidance system
└── core/                  # Base classes for cameras and controllers
```

## Adding Components

### 1. **Adding a New Camera**
- Create a new class in `object_detector/input/`.
- Implement a `frame()` method that returns a video frame.
- Add the new camera type to `setup_camera()` in `main.py`.

### 2. **Adding a New Interface**
- Create an interface class in `user_interface/interfaces/`.
- Implement methods for visualization and interaction.
- Add the interface type to `setup_interface()` in `main.py`.

### 3. **Adding a New Model**
- Create a new class in `object_detector/models/`.
- Implement the methods `on_frame()` and `set_object()`.
- Add the model to `setup_model()` in `main.py`.

### 4. **Adding a New Navigator**
- Create a new class in `navigation_plan/navigators/`.
- Implement the `navigate(frame)` method to define the navigation logic.

### 5. **Adding a New Guide**
- Create a new class in `flight_guide/guide/`.
- Implement:
  - `update_grid(frame)` for visual updates.
  - `loop()` for continuous guidance logic.

## Simulator Notes
- The simulator uses `three.js` for 3D rendering.
- Run the simulator (`npm start`) and use the `SimCam` camera type to interact with it.

## Debugging
- Enable debug mode with the `--debug` flag:
  ```bash
  python main.py --debug
  ```
- Print logs in key classes like `GridNavigator` and `GridGuide` to trace errors.

## Core Loop
1. Initializes components (camera, model, interface, etc.).
2. Starts the main loop based on the interface type:
   - **QT6Interface**: Uses a `QTimer` loop.
   - **CV2Interface**: Runs a while loop with frame processing.
