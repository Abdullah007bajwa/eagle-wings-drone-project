from djitellopy import Tello

print("Shutdown Sequence Initialized..")

# Instantiate Globals
tello = Tello()
tello.connect()
tello.land()
tello.streamoff()
tello.end()

print("Shutdown Sequence Completed. Closing Window..")