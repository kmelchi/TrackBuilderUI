import PIL
from customtkinter import *
from PIL import Image, ImageTk
import math
import numpy as np
from ui_components import CanvasObjects

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class TrackCanvas(CTkCanvas):
    """
    Main canvas class for the track builder application.
    Handles grid drawing, object placement, zooming, and panning functionality.
    """

    def __init__(self, master):
        """
        Initialize the canvas with default settings and bind necessary events.
        
        Args:
            master: Parent widget that contains this canvas
        """
        super().__init__(
            master,
            width=1920,
            height=1080,
            bg="#000000",
            highlightthickness=0
        )

        #background grid & logo
        self.show_axes = False
        self.grid_size = 5
        self.logic_grid_step = 0.25
        self.zoom_factor = self.grid_size / self.logic_grid_step

        # Initialize scroll variables
        self.last_x = 0
        self.last_y = 0
        self.panning = False

        self.max_zoom_factor = 7.5 #750%
        self.min_zoom_factor = 0.25 #25%

        self.after(50, self.initialize_view)

        self.bind("<ButtonPress-1>", self.handle_mouse_press)
        self.bind("<ButtonRelease-1>", self.handle_mouse_release)
        self.bind("<B1-Motion>", self.handle_mouse_motion)
        self.bind("<MouseWheel>", self.zoom)
        self.bind("<B2-Motion>", self.scroll)
        self.bind_all("<KeyPress-r>", self.reset_view)
        self.bind("<Configure>", self.grid_to_window_size)

    def initialize_view(self):
        """
        Initialize the canvas view by setting up the initial offset and drawing the grid and logo.
        Retries initialization if canvas dimensions are not yet available.
        """
        width, height = self.winfo_width(), self.winfo_height()

        if width == 1 and height == 1:
            # canvas not ready yet
            self.after(25, self.initialize_view)
            return

        self.offset_x = width / 2
        self.offset_y = height / 2
        self.draw_grid()
        self.draw_logo()
        

    #converts zoom coords into logic coords
    def to_logic_coords(self, x, y):
        """
        Convert screen coordinates to logical coordinates.
        
        Args:
            x: Screen x-coordinate
            y: Screen y-coordinate
            
        Returns:
            tuple: (logical_x, logical_y) coordinates
        """
        lx = (x - self.offset_x) / self.zoom_factor
        ly = -(y - self.offset_y) / self.zoom_factor
        return lx, ly

    #converts logic coords into zoom coords
    def to_zoom_coords(self, x, y):
        """
        Convert logical coordinates to screen coordinates.
        
        Args:
            x: Logical x-coordinate
            y: Logical y-coordinate
            
        Returns:
            tuple: (screen_x, screen_y) coordinates
        """
        zx = x * self.zoom_factor + self.offset_x
        zy = -y * self.zoom_factor + self.offset_y
        return zx, zy

    def snap_to_grid(self, value):
        """
        Snap a value to the nearest grid point.
        
        Args:
            value: Value to snap to grid
            
        Returns:
            float: Snapped value
        """
        return round(value / self.logic_grid_step) * self.logic_grid_step

    #draws the grid -> changing of grid size with variable grid_size
    def draw_grid(self):
        """
        Draw the grid on the canvas. The grid adapts to the current zoom level
        and only draws lines within the visible area for performance.
        """
        self.delete("grid_line")

        # calculate visible area in logical coordinates
        width, height = self.winfo_width(), self.winfo_height()
        
        # convert corners of the visible area to logical coordinates
        left_x, top_y = self.to_logic_coords(0, 0)
        right_x, bottom_y = self.to_logic_coords(width, height)
        
        # add some padding to prevent grid from appearing to end at screen edges
        padding = 2 * self.grid_size  # 2 grid cells of padding
        grid_min_x = left_x - padding
        grid_max_x = right_x + padding
        grid_min_y = bottom_y - padding  # note: y is inverted in logical coords
        grid_max_y = top_y + padding


        min_pixel_step = 10  # keep grid lines at least 10 pixels apart
        step_px = self.grid_size

        if self.zoom_factor > 0 and (step_px * self.zoom_factor) < min_pixel_step:
            step_px = math.ceil(min_pixel_step / self.zoom_factor / self.grid_size) * self.grid_size

        # ensure step is not smaller than the base grid size
        step_px = max(self.grid_size, step_px)

        # calculate the start/end points for the grid, snapping to the step size
        # ensures the grid lines always align with the (0,0) axes
        start_x = math.floor(grid_min_x / step_px) * step_px
        end_x = math.ceil(grid_max_x / step_px) * step_px
        start_y = math.floor(grid_min_y / step_px) * step_px
        end_y = math.ceil(grid_max_y / step_px) * step_px

        # draw vertical lines within the visible area
        for x in np.arange(start_x, end_x + step_px, step_px):
            zx_start, zy_start = self.to_zoom_coords(x, grid_min_y)
            zx_end, zy_end = self.to_zoom_coords(x, grid_max_y)
            self.create_line(zx_start, zy_start, zx_end, zy_end, fill="#252525", tags="grid_line")

        # draw horizontal lines within the visible area
        for y in np.arange(start_y, end_y + step_px, step_px):
            zx_start, zy_start = self.to_zoom_coords(grid_min_x, y)
            zx_end, zy_end = self.to_zoom_coords(grid_max_x, y)
            self.create_line(zx_start, zy_start, zx_end, zy_end, fill="#252525", tags="grid_line")

        if self.show_axes:
            #x-achse
            _ , y0 = self.to_zoom_coords(0, 0)
            self.create_line(0, y0, self.winfo_width(), y0, fill="#D9D9D9", tags="grid_line", width=1)

            #y-achse
            x0, _ = self.to_zoom_coords(0, 0)
            self.create_line(x0, 0, x0, self.winfo_height(), fill="#D9D9D9", tags="grid_line", width=1)

    #draws the tu-fast logo
    def draw_logo(self):
        """Draw the TU Fast logo in the top-left corner of the canvas."""
        ASSET_LOGO_PATH = os.path.join(BASE_DIR, "assets", "tufastlogo.png")
        logo = Image.open(ASSET_LOGO_PATH).resize((87, 41), Image.LANCZOS)
        self.background_logo = ImageTk.PhotoImage(logo)
        self.create_image(30, 30, anchor=NW, image=self.background_logo)

    def handle_mouse_press(self, event):
        """
        Handle mouse press events. Manages toolbar interaction, object placement,
        and initiates panning if no other action is triggered.
        
        Args:
            event: Mouse event containing coordinates and state
        """
        # check if click is within bounds of any toolbar -> if so, ignore the event
        tool_frame = self.master.tool_frame
        dd_frame = self.master.drag_drop_tool_frame
        gen_frame = self.master.generate_tool_frame

        # convert event coordinates to window coordinates for proper toolbar bounds checking
        window_x = self.winfo_x() + event.x
        window_y = self.winfo_y() + event.y

        # check main toolbar
        if (tool_frame.winfo_x() <= window_x <= tool_frame.winfo_x() + tool_frame.winfo_width() and
                tool_frame.winfo_y() <= window_y <= tool_frame.winfo_y() + tool_frame.winfo_height()):
            return

        # check drag & drop toolbar if visible
        if (self.master.drag_drop_tool_visible and
                dd_frame.winfo_x() <= window_x <= dd_frame.winfo_x() + dd_frame.winfo_width() and
                dd_frame.winfo_y() <= window_y <= dd_frame.winfo_y() + dd_frame.winfo_height()):
            return

        # check generate toolbar if visible
        if (self.master.generate_tool_visible and
                gen_frame.winfo_x() <= window_x <= gen_frame.winfo_x() + gen_frame.winfo_width() and
                gen_frame.winfo_y() <= window_y <= gen_frame.winfo_y() + gen_frame.winfo_height()):
            return

        # if reached here, not clicking on any toolbar
        self.last_x = event.x
        self.last_y = event.y

        # check for items under cursor, ignore grid lines
        item_ids = self.find_overlapping(event.x - 2, event.y - 2, event.x + 2, event.y + 2)
        items = [item for item in item_ids if "grid_line" not in self.gettags(item)]

        # if clicked on an object AND drag tool is active, let the object's own bindings handle it
        if items and self.master.current_tool == "drag":
            return

        # if using a placement tool, place the object
        if self.master.current_tool in ["blue", "yellow", "car"]:
            self.place_object(event)
            return

        # all other cases (no tool, or drag tool on empty canvas) -> panning
        self.config(cursor="fleur")
        self.panning = True
    
    def handle_mouse_release(self, event):
        """
        Handle mouse release events. Ends panning and processes clicks on objects.
        
        Args:
            event: Mouse event containing coordinates and state
        """
        if self.panning:
            self.config(cursor="")
            self.panning = False
            
            # if only moved a small distance, treat as a click
            if (abs(event.x - self.last_x) < 5 and abs(event.y - self.last_y) < 5):
                clicked_items = self.find_overlapping(event.x-5, event.y-5, event.x+5, event.y+5)
                # check if there's a cone or car in this position
                for item in clicked_items:
                    tags = self.itemcget(item, "tags")
                    if "cone" in tags or "car" in tags:
                        # simulate a click on this object
                        self.event_generate("<Button-1>", x=event.x, y=event.y)
    
    def handle_mouse_motion(self, event):
        """
        Handle mouse motion events for panning the canvas.
        
        Args:
            event: Mouse event containing coordinates and state
        """
        # if in panning mode -> move canvas
        if self.panning:
            delta_x = event.x - self.last_x
            delta_y = event.y - self.last_y
            
            self.offset_x += delta_x
            self.offset_y += delta_y
            
            self.last_x = event.x
            self.last_y = event.y
            
            self.draw_grid()
            self.tag_lower("grid_line")
            self.draw_logo()
            
            # update zoom for all objects
            if hasattr(self.master, 'update_zoom'):
                self.master.update_zoom(self.zoom_factor)
    
    #places a cone on the canvas
    def place_object(self, event):
        """
        Place a new object (cone or car) on the canvas at the clicked position.
        
        Args:
            event: Mouse event containing coordinates
        """
        if self.master.current_tool is None:
            return
        
        if self.master.current_tool == "drag":
            return

        lx, ly = self.to_logic_coords(event.x, event.y)

        x = self.snap_to_grid(lx)       #(lx // self.grid_size) * self.grid_size
        y = self.snap_to_grid(ly)       #(ly // self.grid_size) * self.grid_size

        if self.master.current_tool == "blue" or self.master.current_tool == "yellow":
            new_cone = CanvasObjects.Cone(self, self.master.current_tool, x, y)
            new_cone.update_zoom(self.zoom_factor)

        if self.master.current_tool == "car" and self.master.car is None:
            new_car = CanvasObjects.Car(self, x, y, 0.0000)
            self.master.car = new_car
            new_car.update_zoom(self.zoom_factor)

    def scroll(self, event):
        """
        Handle middle-mouse scrolling for canvas panning.
        
        Args:
            event: Mouse event containing coordinates and state
        """
        if not hasattr(self, 'last_x') or not hasattr(self, 'last_y'):
            self.last_x = event.x
            self.last_y = event.y
        
        delta_x = event.x - self.last_x
        delta_y = event.y - self.last_y
        
        self.offset_x += delta_x
        self.offset_y += delta_y
        
        self.last_x = event.x
        self.last_y = event.y
        
        self.draw_grid()
        self.tag_lower("grid_line")
        self.draw_logo()
        
        # update zoom
        if hasattr(self.master, 'update_zoom'):
            self.master.update_zoom(self.zoom_factor)
        
    def zoom(self, event):
        """
        Handle mouse wheel events for zooming. If a car is selected and active,
        the wheel will rotate the car instead of zooming.
        
        Args:
            event: Mouse event containing delta for zoom direction
        """
        if hasattr(self.master, "car") and self.master.car and self.master.car.active:
            self.master.car.rotate_with_mousewheel(event)
            return

        old_zoom = self.zoom_factor

        # smaller step for smooth zooming
        step = 0.025  #0.05
        
        # calculate zoom change based on mouse wheel delta
        zoom_change = step if event.delta > 0 else -step
        new_zoom = old_zoom + zoom_change

        # ensure zoom stays within bounds
        new_zoom = max(self.min_zoom_factor, min(new_zoom, self.max_zoom_factor))

        # calculate zoom center based on mouse position
        mouse_x = self.canvasx(event.x)
        mouse_y = self.canvasy(event.y)
        
        # convert mouse position to canvas coordinates
        canvas_x = (mouse_x - self.offset_x) / old_zoom
        canvas_y = (mouse_y - self.offset_y) / old_zoom

        # update offset to zoom around mouse position
        self.offset_x = mouse_x - canvas_x * new_zoom
        self.offset_y = mouse_y - canvas_y * new_zoom

        self.zoom_factor = new_zoom

        # update display
        self.draw_grid()
        self.tag_lower("grid_line")
        self.draw_logo()

        if hasattr(self.master, 'update_zoom'):
            self.master.update_zoom(self.zoom_factor)

        if hasattr(self, "tool_frame"):
            zoom_percent = int(self.zoom_factor * 100)
            self.tool_frame.zoom_var.set(f"{zoom_percent}%")

    def reset_view(self, event):
        """
        Reset the view to its default state (centered, zoom level 1.0).
        
        Args:
            event: Key event (unused)
        """
        self.zoom_factor = 1.0
        self.offset_x = self.winfo_width() / 2
        self.offset_y = self.winfo_height() / 2

        self.draw_grid()
        self.tag_lower("grid_line")
        self.draw_logo()

        if hasattr(self.master, 'update_zoom'):
            self.master.update_zoom(self.zoom_factor)

    def fit_to_track(self, margin=500):
        """
        Centers and zooms the view to fit all cones with a margin.
        
        Args:
            margin: Padding around the track in logical units (default: 500)
        """
        if not hasattr(self.master, 'cones') or not self.master.cones:
            self.reset_view(None)
            return

        # calculate bounding box of cones
        cx = [cone.position_x for cone in self.master.cones]
        cy = [cone.position_y for cone in self.master.cones]
        min_x_cones, max_x_cones = min(cx), max(cx)
        min_y_cones, max_y_cones = min(cy), max(cy)

        # calculate dimensions with margin
        grid_width = (max_x_cones - min_x_cones) + 2 * margin
        grid_height = (max_y_cones - min_y_cones) + 2 * margin

        if grid_width == 0 or grid_height == 0:
            self.reset_view(None)  # use reset_view for this edge case
            return

        # add little extra padding to view
        view_padding_factor = 1.1
        view_width = grid_width * view_padding_factor
        view_height = grid_height * view_padding_factor

        # calculate initial zoom
        zoom_x = self.winfo_width() / view_width
        zoom_y = self.winfo_height() / view_height
        initial_zoom = min(zoom_x, zoom_y)

        # round to nearest step of 0.025
        step = 0.025
        self.zoom_factor = math.floor(initial_zoom / step) * step
        
        # ensure zoom is within bounds
        self.zoom_factor = max(self.min_zoom_factor, min(self.zoom_factor, self.max_zoom_factor))

        # center the view on the cones' center
        center_x = (min_x_cones + max_x_cones) / 2
        center_y = (min_y_cones + max_y_cones) / 2

        self.offset_x = self.winfo_width() / 2 - center_x * self.zoom_factor
        self.offset_y = self.winfo_height() / 2 + center_y * self.zoom_factor # adding here because canvas y-axis is inverted
        

        # update zoom display in tool frame if exists
        if hasattr(self, "tool_frame"):
            zoom_percent = int(self.zoom_factor * 100)
            self.tool_frame.zoom_var.set(f"{zoom_percent}%")

        # redraw everything with final, correct state
        self.draw_grid()
        self.tag_lower("grid_line")
        self.draw_logo()

        # update objects for the new zoom level
        if hasattr(self.master, 'update_zoom'):
            self.master.update_zoom(self.zoom_factor)

    def grid_to_window_size(self, event):
        """
        Adjust the grid when the window is resized.
        
        Args:
            event: Configure event containing new dimensions
        """
        self.offset_x = self.winfo_width() / 2
        self.offset_y = self.winfo_height() / 2

        self.draw_grid()
        self.tag_lower("grid_line")
        self.draw_logo()

        if hasattr(self.master, 'update_zoom'):
            self.master.update_zoom(self.zoom_factor)

    def set_zoom_factor(self, zoom):
        """
        Set the zoom factor directly and update the view.
        
        Args:
            zoom: New zoom factor to set
        """
        # limit zoom to a reasonable range
        if not self.min_zoom_factor <= zoom <= self.max_zoom_factor:
            return

        self.zoom_factor = zoom

        # recalculate offset to keep center
        self.offset_x = self.winfo_width() / 2
        self.offset_y = self.winfo_height() / 2

        self.draw_grid()
        self.tag_lower("grid_line")
        self.draw_logo()

        if hasattr(self.master, 'update_zoom'):
            self.master.update_zoom(self.zoom_factor)

    def set_tool_frame(self, tool_frame):
        self.tool_frame = tool_frame

