# Client Implementation

This document provides details about the implementation of the PolyClash client, including the GUI, game logic, and network communication.

## Overview

The PolyClash client is a PyQt5 desktop application that provides a graphical interface for playing the game. It uses PyVista/VTK for 3D visualization of the game board.

## Main Components

### Main Window

The `MainWindow` class (`polyclash/gui/main.py`) is the entry point of the application. It:

- Sets up the main window with menus, status bar, and central widget
- Contains the sphere view, overlay info, and overlay map
- Handles network notifications and game events
- Provides methods for starting local and network games

```python
class MainWindow(QMainWindow):
    def __init__(self, parent=None, controller=None):
        # Initialize the main window
        # Set up the GUI components
        # Connect signals and slots
```

### 3D Visualization

The 3D visualization is handled by the `SphereView` class and its subclasses (`polyclash/gui/view_sphere.py`):

- `SphereView`: Base class for 3D visualization
- `ActiveSphereView`: Interactive view for gameplay
- `PassiveSphereView`: Off-screen rendering for the overlay map

```python
class SphereView(QtInteractor):
    def __init__(self, parent=None, off_screen=False):
        # Initialize the 3D view
        # Set up the mesh and spheres
        # Handle notifications from the game board
```

The 3D mesh is created in `polyclash/gui/mesh.py`:

```python
# Create the mesh from the vertices and faces
mesh = pv.PolyData(cities, np.hstack(faces_list))

# Initialize the colors for the mesh
face_colors = init_colors()
```

### Overlay Components

Two overlay components provide additional information and controls:

- `OverlayInfo` (`polyclash/gui/overly_info.py`): Displays game information (score, current player)
- `OverlayMap` (`polyclash/gui/overly_map.py`): Provides thumbnail views from different angles

```python
class OverlayInfo(QWidget):
    def __init__(self, parent=None):
        # Initialize the overlay
        # Set up the display elements
        # Handle notifications from the game board
```

```python
class OverlayMap(QWidget):
    def __init__(self, parent=None, rows=4, columns=2):
        # Initialize the overlay
        # Set up the grid of images
        # Handle mouse clicks to change the view
```

### Game Controller

The `SphericalGoController` class (`polyclash/game/controller.py`) manages the game flow and player interactions:

```python
class SphericalGoController(QObject):
    # Define signals for game events
    gameStarted = pyqtSignal()
    playerPlaced = pyqtSignal(int, int)
    gameResigned = pyqtSignal(int)
    gameEnded = pyqtSignal()
    gameClosed = pyqtSignal()
    
    def __init__(self, mode=LOCAL, board=None):
        # Initialize the controller
        # Set up the game board and players
        # Connect signals and slots
```

The controller supports different game modes:
- `LOCAL`: Local game with human and/or AI players
- `NETWORK`: Network game with remote players
- `VIEW`: View mode for spectating games

### Game Board

The `Board` class (`polyclash/game/board.py`) represents the game board and implements the game rules:

```python
class Board:
    def __init__(self):
        # Initialize the board
        # Set up the data structures for the game state
        # Register observers for notifications
        
    def play(self, point, player, turn_check=True):
        # Validate the move
        # Update the board state
        # Check for captures
        # Notify observers
```

The board uses the Observer pattern to notify components of changes to the game state.

### Players

The `Player` class and its subclasses (`polyclash/game/player.py`) represent the different types of players:

```python
class Player(QObject):
    stonePlaced = pyqtSignal(int)  # Signal emitted when a stone is placed
    
    def __init__(self, kind, **kwargs):
        # Initialize the player
        # Set up the player's properties
        # Connect signals and slots
```

Player types:
- `HumanPlayer`: Local human player
- `AIPlayer`: Computer player with AI logic
- `RemotePlayer`: Player connected over the network

### AI Implementation

The AI is implemented in the `AIPlayer` class and the `AIPlayerWorker` class (`polyclash/workers/ai_play.py`):

```python
class AIPlayerWorker(QThread):
    trigger = pyqtSignal()
    
    def __init__(self, player):
        # Initialize the worker thread
        # Set up the thread synchronization
        # Connect signals and slots
```

The AI uses a simple algorithm to evaluate moves based on score and potential.

### Network Communication

Network communication is handled by the `api.py` module (`polyclash/util/api.py`) and the `NetworkWorker` class (`polyclash/workers/network.py`):

```python
# API functions for communicating with the server
def connect(server, token):
    # Connect to the server
    # Create a new game
    # Return the game keys

def join(server, role, token):
    # Join an existing game
    # Return the status
```

```python
class NetworkWorker(QThread):
    messageReceived = pyqtSignal(str, object)
    
    def __init__(self, parent=None, server=None, role=None, key=None):
        # Initialize the worker thread
        # Set up the Socket.IO client
        # Connect event handlers
```

## Initialization Flow

The client initialization flow is as follows:

1. The `main()` function in `polyclash/client.py` is called
2. A `QApplication` is created
3. A `SphericalGoController` is created
4. Players are added to the controller
5. A `MainWindow` is created with the controller
6. The window is sized and positioned
7. The board is reset
8. The window is shown
9. The application event loop is started

```python
def main():
    app = QApplication(sys.argv)
    
    controller = SphericalGoController()
    controller.add_player(BLACK, kind=HUMAN)
    controller.add_player(WHITE, kind=AI)
    
    window = MainWindow(controller=controller)
    
    # Size and position the window
    
    controller.board.reset()
    window.show()
    sys.exit(app.exec_())
```

## Game Flow

### Local Game Flow

1. User selects "Local Mode" from the menu
2. A dialog is shown to configure the players
3. The controller is set to `LOCAL` mode
4. Players are added to the controller
5. The game is started
6. Players take turns making moves
7. The board updates the game state and notifies observers
8. GUI components update to reflect the new state

### Network Game Flow

1. User selects "Network Mode" > "New" or "Join" from the menu
2. A dialog is shown to configure the network game
3. The controller is set to `NETWORK` mode
4. The client connects to the server
5. Players join the game
6. Players mark themselves as ready
7. The game is started
8. Players take turns making moves
9. Moves are sent to the server and broadcast to all clients
10. The board updates the game state and notifies observers
11. GUI components update to reflect the new state

## User Interaction

### Mouse Interaction

The `ActiveSphereView` class handles mouse interaction for placing stones:

```python
def left_button_press_event(self, obj, event):
    # Get the click position
    # Find the nearest city (vertex)
    # Try to place a stone at that position
```

### Menu Interaction

The `MainWindow` class sets up the menus and handles menu actions:

```python
def initMenu(self):
    # Create the menu bar
    # Add menu items
    # Connect menu actions to methods
```

## Customization

The client can be customized in several ways:

- Colors can be changed in `polyclash/gui/constants.py`
- The board visualization can be modified in `polyclash/gui/mesh.py`
- The AI algorithm can be improved in `polyclash/game/board.py` and `polyclash/workers/ai_play.py`
- The UI layout can be adjusted in `polyclash/gui/main.py`

## Error Handling

The client includes error handling for various scenarios:

- Invalid moves are caught and displayed in the status bar
- Network errors are caught and displayed in dialogs
- Exceptions are logged using the `loguru` library

## Logging

The client uses the `loguru` library for logging (`polyclash/util/logging.py`):

```python
def setup_logging():
    # Set up the logging directory
    # Configure the logger
    # Return the logger
```

Logs are stored in the user's home directory:
- Windows: `%USERPROFILE%\.polyclash\app.log`
- macOS/Linux: `~/.polyclash/app.log`
