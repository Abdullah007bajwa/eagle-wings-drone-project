import asyncio
import websockets
import json
import threading

class Simulator:
    def __init__(self, run_on_start=True):
        self.connection = None
        self.loop = asyncio.new_event_loop()  # Create a new event loop
        self.lock = threading.Lock()  # For thread-safe operations
        if run_on_start:
            self.start_server()  # Start the server in a separate thread

    def start_server(self, port=8092):
        """Start the WebSocket server in a separate thread."""
        thread = threading.Thread(target=self.run_server, args=(port,))
        thread.daemon = True  # Daemon thread to exit with the main program
        thread.start()

    def run_server(self, port):
        """Run the WebSocket server."""
        asyncio.set_event_loop(self.loop)  # Set the new event loop
        self.loop.run_until_complete(self.run_websocket_server(port))

    async def run_websocket_server(self, port):
        async with websockets.serve(self.handle_connection, "0.0.0.0", port):
            print(f"Simulator listening on ws://0.0.0.0:{port}")
            await asyncio.Future()  # Run forever

    async def connect(self, websocket):
        self.connection = websocket
        print("Simulator connected.")
        await self.send_message({"status": "connected"})

    async def end(self):
        if self.connection:
            await self.connection.close()
            print("Simulator connection ended.")

    async def streamon(self):
        print("Simulator video stream started.")
        await self.send_message({"status": "streaming"})

    async def streamoff(self):
        print("Simulator video stream stopped.")
        await self.send_message({"status": "not streaming"})

    async def send_message(self, message):
        if self.connection:
            await self.connection.send(json.dumps(message))

    def execute_in_loop(self, coro):
        """Helper to execute a coroutine in the event loop from outside."""
        with self.lock:  # Ensure thread-safe access to the loop
            return asyncio.run_coroutine_threadsafe(coro, self.loop).result()

    # Wrappers for external calls without needing async/await
    def takeoff(self):
        self.execute_in_loop(self._takeoff())

    def land(self):
        self.execute_in_loop(self._land())

    def move_forward(self, duration):
        self.execute_in_loop(self._move_forward(duration))

    def move_back(self, duration):
        self.execute_in_loop(self._move_back(duration))

    def move_right(self, duration):
        self.execute_in_loop(self._move_right(duration))

    def move_left(self, duration):
        self.execute_in_loop(self._move_left(duration))

    def move_up(self, duration):
        self.execute_in_loop(self._move_up(duration))

    def move_down(self, duration):
        self.execute_in_loop(self._move_down(duration))

    def rotate_clockwise(self, duration):
        self.execute_in_loop(self._rotate_clockwise(duration))

    def rotate_counter_clockwise(self, duration):
        self.execute_in_loop(self._rotate_counter_clockwise(duration))

    def rc_control(self, left_right, forward_backward, up_down, yaw):
        """Execute RC control with velocities."""
        self.execute_in_loop(self._rc_control(left_right, forward_backward, up_down, yaw))

    # aliases
    def rotate_cw(self, duration):
        self.rotate_clockwise(duration)

    def rotate_ccw(self, duration):
        self.rotate_counter_clockwise(duration)


    # Actual coroutine implementations
    async def _takeoff(self):
        print("Simulator taking off.")
        await self.send_message({"command": "takeoff"})

    async def _land(self):
        print("Simulator landing.")
        await self.send_message({"command": "land"})

    async def _move_forward(self, duration):
        print(f"Simulator moving forward for {duration} seconds.")
        await self.send_message({"command": "move_forward", "duration": duration})

    async def _move_back(self, duration):
        print(f"Simulator moving back for {duration} seconds.")
        await self.send_message({"command": "move_back", "duration": duration})

    async def _move_right(self, duration):
        print(f"Simulator moving right for {duration} seconds.")
        await self.send_message({"command": "move_right", "duration": duration})

    async def _move_left(self, duration):
        print(f"Simulator moving left for {duration} seconds.")
        await self.send_message({"command": "move_left", "duration": duration})

    async def _move_up(self, duration):
        print(f"Simulator moving up for {duration} seconds.")
        await self.send_message({"command": "move_up", "duration": duration})

    async def _move_down(self, duration):
        print(f"Simulator moving down for {duration} seconds.")
        await self.send_message({"command": "move_down", "duration": duration})

    async def _rotate_clockwise(self, duration):
        print(f"Simulator rotating clockwise for {duration} seconds.")
        await self.send_message({"command": "rotate_clockwise", "duration": duration})

    async def _rotate_counter_clockwise(self, duration):
        print(f"Simulator rotating counter-clockwise for {duration} seconds.")
        await self.send_message({"command": "rotate_counter_clockwise", "duration": duration})

    async def _rc_control(self, left_right, forward_backward, up_down, yaw):
        """Coroutine to handle RC control."""
        print(f"Simulator RC control: lr={left_right}, fb={forward_backward}, ud={up_down}, yaw={yaw}")
        await self.send_message({
            "command": "rc",
            "params": {
                "left_right": left_right,
                "forward_backward": forward_backward,
                "up_down": up_down,
                "yaw": yaw
            }
        })


    async def handle_connection(self, websocket, path):
        await self.connect(websocket)
        try:
            async for message in websocket:
                data = json.loads(message)
                command = data.get("command")
                duration = data.get("duration")  # Optional duration
                await self.handle_commands(command, duration)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await self.end()

    async def handle_commands(self, command, duration=None):
        commands = {
            "takeoff": self._takeoff,
            "land": self._land,
            "move_forward": self._move_forward,
            "move_back": self._move_back,
            "move_right": self._move_right,
            "move_left": self._move_left,
            "move_up": self._move_up,
            "move_down": self._move_down,
            "rotate_clockwise": self._rotate_clockwise,
            "rotate_counter_clockwise": self._rotate_counter_clockwise,
        }

        if command in commands:
            if duration is not None:
                await commands[command](duration)
            else:
                await commands[command]()
        if command == "rc" and isinstance(duration, dict):
            await self._rc_control(duration["left_right"], duration["forward_backward"], duration["up_down"], duration["yaw"])
        else:
            print(f"Unknown command: {command}")
