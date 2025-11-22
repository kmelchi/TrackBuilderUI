# Track Builder UI

A Python-based graphical tool for creating and editing race track layouts using cones. Designed for autonomous racing applications, this tool provides an intuitive interface for placing, adjusting, and generating track boundaries.

<img width="1068" height="815" alt="Screenshot 2025-11-21 at 12 53 55" src="https://github.com/user-attachments/assets/296c98df-056b-4b92-ab42-afc2a41fec9e" />

## Features

- **Interactive Canvas**
  - Infinite grid system with zoom and pan functionality
  - Snap-to-grid placement for precise positioning
  - Dynamic grid density based on zoom level
  - Optional coordinate axes display

- **Object Placement**
  - Blue and yellow cones for track boundaries
  - Car object with adjustable position and orientation
  - Drag-and-drop functionality for object manipulation
  - Real-time position information display

- **Track Generation** (currently unavailablen in the UI)
  - Generate track layouts from PNG/JPEG images
  - Automatic cone placement along detected track boundaries
  - Adjustable track width parameter
  - Preview functionality for imported tracks

- **Tool Management**
  - Main toolbar for basic operations
  - Specialized drag-and-drop tool panel
  - Track generation panel with image import options
  - Tool state management and visual feedback

## Installation

1. Clone the repository
2. Install the required dependencies:
```bash
pip install customtkinter      # GUI framework
pip install Pillow            # Image processing
pip install numpy             # Numerical computations
pip install opencv-python     # Image processing and track generation
pip install pyyaml           # Track file saving/loading
pip install svgpathtools     # SVG path processing
pip install cairosvg         # SVG rendering
```

3. Ensure you have Python 3.8 or newer installed
4. Make sure you have Tkinter installed (usually comes with Python)

## Usage

### Running the Application

After installing the dependencies, you can start the application by running:

   ```bash
   python TrackBuilder.py
   ```

Make sure you are inside the TrackBuilderUI directory when running this command.

### Basic Operations

1. **Placing Objects**
   - Select blue or yellow cone from the toolbar
   - Click on the canvas to place cones
   - Use the car tool to place a single car object

2. **Navigation**
   - Pan: Middle mouse button drag or left-click drag on empty space
   - Zoom: Mouse wheel
   - Reset View: Press 'R' key

### Track Building

1. **Manual Track Creation**
   - Place blue cones on the outer track boundary
   - Place yellow cones on the inner track boundary
   - Adjust cone positions using the drag tool

### Saving and Loading Tracks

1. **Saving Tracks**
   - Click the "Save" button in the toolbar
   - If you previously loaded a track:
     - The file will be automatically overwritten with the current track layout
     - The filename in the toolbar will show the current file being edited
   - If this is a new track:
     - A file dialog will open
     - Choose a location and name for your .yaml file
     - The track will be saved in YAML format with cone positions and car placement

2. **Loading Tracks**
   - Click the "Load" button in the toolbar
   - Select a .yaml track file
   - The track will be loaded with all cones and car placement
   - Any subsequent saves will update this loaded file

3. **Track File Format**
   The track files (.yaml) contain:
   - Left boundary cone positions (blue cones)
   - Right boundary cone positions (yellow cones)
   - Car starting position and orientation (if placed)
   - All coordinates are stored in meters

### Automatic Track Generation
(Currently unavailable in the UI)
1. **Automatic Track Generation**
   - Click "GENERATE" in the toolbar
   - Select a track image file (PNG/JPEG)
   - Adjust track width if needed
   - Click "GENERATE CONES" to create the track

### Car Placement and Orientation

1. **Placing the Car**
   - Select the car tool from the toolbar
   - Click to place the car on the track
   - Use mouse wheel to rotate when car is selected

### Object Information

1. **Viewing Object Details**
   - Select the drag tool
   - Click on any object to view its coordinates
   - For the car, yaw angle is also displayed

## Project Structure

- `TrackBuilder.py`: Main application window and core functionality
- `TrackCanvas.py`: Custom canvas implementation with grid and object handling
- `CanvasObjects.py`: Cone and Car object implementations
- `ToolFrame.py`: UI components for tools and controls

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## Troubleshooting

### Known Issues

1. **Toolframe Button Responsiveness**
   - **Issue**: Sometimes toolbar buttons may not respond to a simple click
   - **Workaround**: If a button doesn't respond to clicking:
     - Click the button and slightly drag the mouse before releasing
     - The button should then respond correctly
   - This is a known bug and will be addressed in future updates


