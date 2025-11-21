from customtkinter import *
from PIL import Image, ImageTk
import math

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Cone:
    """
    Represents a cone object on the canvas. Cones are used to mark the track boundaries.
    Supports dragging, info display, and deletion.
    """

    def __init__(self, canvas, cone_type, position_x, position_y):
        """
        Initialize a new cone object.
        
        Args:
            canvas: The canvas to draw the cone on
            cone_type: Type of cone ('blue' or 'yellow')
            position_x: Initial x position in logical coordinates
            position_y: Initial y position in logical coordinates
        """
        self.canvas = canvas
        self.cone_type = cone_type
        self.position_x = position_x
        self.position_y = position_y

        self.radius = 3
        self.id = None

        self.color_map = {
            "red" : "#C61818",
            "blue" : "#3A8CC4",
            "yellow" : "#FFD630"
        }

        self.draw_cone()
        
        # ensure the cone is added to master's list
        if hasattr(self.canvas.master, 'cones'):
            if self not in self.canvas.master.cones:  # prevent duplicates
                self.canvas.master.cones.append(self)

        self.drag_data = {"x": 0, "y": 0}
        self.canvas.tag_bind(self.id, "<ButtonPress-1>", self.on_click_cone)
        self.canvas.tag_bind(self.id, "<B1-Motion>", self.on_drag_cone)
        self.canvas.tag_bind(self.id, "<ButtonRelease-1>", self.on_release_cone)

        # info frame that shows coordinates and delete button
        self.info_frame = None
        self.info_frame_visible = False
        self.coord_x_var = StringVar()
        self.coord_y_var = StringVar()
        self._create_info_frame()


    def _create_info_frame(self):
        """Creates the frame containing cone info and actions."""
        self.info_frame = CTkFrame(self.canvas.master, fg_color="#1C1C1C", border_width=1, border_color="#4A4A4A", corner_radius=6)

        # coordinate display
        x_label = CTkLabel(self.info_frame, text="X:", font=("Roboto", 11), text_color="#D3D3D3")
        x_label.grid(row=0, column=0, padx=(8, 2), pady=(5, 2), sticky="w")
        x_value = CTkLabel(self.info_frame, textvariable=self.coord_x_var, font=("Roboto", 11, "bold"), text_color="#FFFFFF", width=10)
        x_value.grid(row=0, column=1, padx=(0, 5), pady=(5, 2), sticky="w")

        y_label = CTkLabel(self.info_frame, text="Y:", font=("Roboto", 11), text_color="#D3D3D3")
        y_label.grid(row=1, column=0, padx=(8, 2), pady=(2, 5), sticky="w")
        y_value = CTkLabel(self.info_frame, textvariable=self.coord_y_var, font=("Roboto", 11, "bold"), text_color="#FFFFFF", width=10)
        y_value.grid(row=1, column=1, padx=(0, 5), pady=(2, 5), sticky="w")

        # separator
        separator = CTkFrame(self.info_frame, width=1, height=30, fg_color="#4A4A4A")
        separator.grid(row=0, column=2, rowspan=2, pady=5, padx=(5,8), sticky="ns")

        # delete button
        ASSET_TRASH_PATH = os.path.join(BASE_DIR, "assets", "trash.png")
        self.delete_icon = CTkImage(Image.open(ASSET_TRASH_PATH))
        self.delete_button = CTkButton(self.info_frame, command=self.delete_cone, text="",
                                       image=self.delete_icon, width=24, height=24, fg_color="transparent", hover_color="#B22222")
        self.delete_button.grid(row=0, column=3, rowspan=2, padx=(0, 8), pady=5)


    def draw_cone(self):
        """Draw or redraw the cone on the canvas."""
        if self.id:
            self.canvas.delete(self.id)

        zx, zy = self.canvas.to_zoom_coords(self.position_x, self.position_y)

        self.id = self.canvas.create_oval(
            zx - self.radius,
            zy - self.radius,
            zx + self.radius,
            zy + self.radius,
            fill=self.color_map[self.cone_type],
            outline="",
            tags="cone"
            )

    def update_zoom(self, zoom_factor):
        """
        Update the cone's position and size based on the new zoom factor.
        
        Args:
            zoom_factor: New zoom level to apply
        """
        if self.info_frame_visible:
            self.hide_info_frame()

        zx, zy = self.canvas.to_zoom_coords(self.position_x, self.position_y)

        self.canvas.coords(
            self.id,
            zx - self.radius,
            zy - self.radius,
            zx + self.radius,
            zy + self.radius
        )

    def move(self, new_x, new_y):
        """
        Move the cone to a new position.
        
        Args:
            new_x: New x position in logical coordinates
            new_y: New y position in logical coordinates
        """
        zx, zy = move_object(self, new_x, new_y)

        self.canvas.coords(
            self.id,
            zx - self.radius,
            zy - self.radius,
            zx + self.radius,
            zy + self.radius
        )
        if self.info_frame_visible:
            self.update_info_frame()

    def on_click_cone(self, event):
        """
        Handle mouse click on the cone. Shows/hides info frame if drag tool is active.
        
        Args:
            event: Mouse event containing coordinates
        """
        on_click_object(self, event)
        # only show/hide the info frame if the drag tool is selected
        if self.canvas.master.current_tool == "drag":
            if self.info_frame_visible:
                self.hide_info_frame()
            else:
                self.show_info_frame()

    def on_drag_cone(self, event):
        """
        Handle dragging of the cone.
        
        Args:
            event: Mouse event containing coordinates
        """
        on_drag_object(self, event)

    def on_release_cone(self, event):
        """
        Handle release of mouse after dragging the cone.
        
        Args:
            event: Mouse event containing coordinates
        """
        on_release_object(self, event)


    def delete_cone(self):
        """Delete the cone from the canvas and remove it from the master's cone list."""
        #deletes visualization of cone on the canvas
        self.canvas.delete(self.id)
        #deletes the cone from the masters list
        if hasattr(self.canvas.master, 'cones') and self in self.canvas.master.cones:
            self.canvas.master.cones.remove(self)

        if self.info_frame_visible:
            self.info_frame.destroy()

    def show_info_frame(self):
        """Show the info frame displaying cone coordinates."""
        if not self.info_frame_visible:
            self.update_info_frame() # update content and position
            self.info_frame.lift()
            self.info_frame_visible = True

    def hide_info_frame(self):
        """Hide the info frame."""
        if self.info_frame_visible:
            self.info_frame.place_forget()
            self.info_frame_visible = False

    def update_info_frame(self):
        """Updates the coordinate display and repositions the frame."""
        scale = 1.0  # default to 1.0
        if hasattr(self.canvas.master, 'scale'):
            scale = self.canvas.master.scale

        # prevent division by zero (if scale somehow not set)
        if scale == 0:
            scale = 1.0

        # update coordinate values, formatted to 2 decimal places
        meter_x = self.position_x / scale
        meter_y = self.position_y / scale
        self.coord_x_var.set(f"{meter_x:.2f}")
        self.coord_y_var.set(f"{meter_y:.2f}")

        # reposition the frame
        zx, zy = self.canvas.to_zoom_coords(self.position_x, self.position_y)
        # using winfo_reqheight() to get the required height after content is set
        self.info_frame.update_idletasks()
        frame_height = self.info_frame.winfo_reqheight()
        self.info_frame.place(x=zx + self.radius * 2.5, y=zy - frame_height / 2)

# drag and drop methods
def move_object(canvas_object, new_x, new_y):
    """
    Update an object's position.
    
    Args:
        canvas_object: The object to move (Cone or Car)
        new_x: New x position in logical coordinates
        new_y: New y position in logical coordinates
        
    Returns:
        tuple: Screen coordinates for the new position
    """
    canvas_object.position_x = new_x
    canvas_object.position_y = new_y

    zx, zy = canvas_object.canvas.to_zoom_coords(new_x, new_y)

    return zx, zy


def on_click_object(canvas_object, event):
    """
    Handle initial click on an object.
    
    Args:
        canvas_object: The clicked object (Cone or Car)
        event: Mouse event containing coordinates
    """
    if canvas_object.canvas.master.current_tool == "drag":
        canvas_object.drag_data["x"] = event.x
        canvas_object.drag_data["y"] = event.y

def on_drag_object(canvas_object, event):
    """
    Handle dragging of an object.
    
    Args:
        canvas_object: The object being dragged (Cone or Car)
        event: Mouse event containing coordinates
    """
    if canvas_object.canvas.master.current_tool != "drag":
        return

    # convert to logical coord
    lx1, ly1 = canvas_object.canvas.to_logic_coords(canvas_object.drag_data["x"], canvas_object.drag_data["y"])
    lx2, ly2 = canvas_object.canvas.to_logic_coords(event.x, event.y)

    # calculating distance of movement
    dx = lx2 - lx1
    dy = ly2 - ly1

    # update logical position by calling the object's move method
    new_x = canvas_object.position_x + dx
    new_y = canvas_object.position_y + dy
    if hasattr(canvas_object, 'move'):
        canvas_object.move(new_x, new_y)

    # update drag data for the next movement increment
    canvas_object.drag_data["x"] = event.x
    canvas_object.drag_data["y"] = event.y

def on_release_object(canvas_object, event):
    """
    Handle release of mouse after dragging an object.
    
    Args:
        canvas_object: The object being released (Cone or Car)
        event: Mouse event containing coordinates
    """
    if not canvas_object.canvas.master.current_tool == "drag":
        return

    snapped_x = canvas_object.canvas.snap_to_grid(canvas_object.position_x)
    snapped_y = canvas_object.canvas.snap_to_grid(canvas_object.position_y)

    canvas_object.move(snapped_x, snapped_y)

class Car:
    """
    Represents a car object on the canvas. The car is represented as a triangle
    that can be moved, rotated, and displays its position and orientation.
    """

    def __init__(self, canvas, position_x, position_y, yaw_angle):
        """
        Initialize a new car object.
        
        Args:
            canvas: The canvas to draw the car on
            position_x: Initial x position in logical coordinates
            position_y: Initial y position in logical coordinates
            yaw_angle: Initial yaw angle in degrees
        """
        self.canvas = canvas
        self.position_x = position_x
        self.position_y = position_y
        self.yaw_angle = yaw_angle

        self.car_length = 5
        self.car_width = 3

        self.id = None
        self.active = False
        self.draw_car()

        self.drag_data = {"x": 0, "y": 0}
        self.canvas.tag_bind(self.id, "<ButtonPress-1>", self.on_click_car)
        self.canvas.tag_bind(self.id, "<B1-Motion>", self.on_drag_car)
        self.canvas.tag_bind(self.id, "<ButtonRelease-1>", self.on_release_car)

        # info frame that shows coordinates and yaw angle
        self.info_frame = None
        self.info_frame_visible = False
        self.coord_x_var = StringVar()
        self.coord_y_var = StringVar()
        self.yaw_angle_var = StringVar()
        self._create_info_frame()

    def _create_info_frame(self):
        """Creates the frame containing car info and actions."""
        self.info_frame = CTkFrame(self.canvas.master, fg_color="#1C1C1C", border_width=1, border_color="#4A4A4A", corner_radius=6)

        # coordinate display
        x_label = CTkLabel(self.info_frame, text="X:", font=("Roboto", 11), text_color="#D3D3D3")
        x_label.grid(row=0, column=0, padx=(8, 2), pady=(5, 2), sticky="w")
        x_value = CTkLabel(self.info_frame, textvariable=self.coord_x_var, font=("Roboto", 11, "bold"), text_color="#FFFFFF", width=10)
        x_value.grid(row=0, column=1, padx=(0, 5), pady=(5, 2), sticky="w")

        y_label = CTkLabel(self.info_frame, text="Y:", font=("Roboto", 11), text_color="#D3D3D3")
        y_label.grid(row=1, column=0, padx=(8, 2), pady=(2, 2), sticky="w")
        y_value = CTkLabel(self.info_frame, textvariable=self.coord_y_var, font=("Roboto", 11, "bold"), text_color="#FFFFFF", width=10)
        y_value.grid(row=1, column=1, padx=(0, 5), pady=(2, 2), sticky="w")

        yaw_label = CTkLabel(self.info_frame, text="Yaw:", font=("Roboto", 11), text_color="#D3D3D3")
        yaw_label.grid(row=2, column=0, padx=(8, 2), pady=(2, 5), sticky="w")
        yaw_value = CTkLabel(self.info_frame, textvariable=self.yaw_angle_var, font=("Roboto", 11, "bold"), text_color="#FFFFFF", width=10)
        yaw_value.grid(row=2, column=1, padx=(0, 5), pady=(2, 5), sticky="w")

        # separator
        separator = CTkFrame(self.info_frame, width=1, height=45, fg_color="#4A4A4A")
        separator.grid(row=0, column=2, rowspan=3, pady=5, padx=(5,8), sticky="ns")

        # delete button
        ASSET_TRASH_PATH = os.path.join(BASE_DIR, "assets", "trash.png")
        self.delete_icon = CTkImage(Image.open(ASSET_TRASH_PATH))
        self.delete_button = CTkButton(self.info_frame, command=self.delete_car, text="",
                                     image=self.delete_icon, width=24, height=24, fg_color="transparent", hover_color="#B22222")
        self.delete_button.grid(row=0, column=3, rowspan=3, padx=(0, 8), pady=5)

    def draw_car(self):
        """Draw or redraw the car on the canvas as a triangle."""
        p1, p2, p3 = self.get_points()

        self.id = self.canvas.create_polygon(p1, p2, p3, fill='#FFFFFF', outline='#FFFFFF', width=1, tags="car")
        print("car successfully drawn")
        #self.id = self.canvas.create_polygon(p1_rot, p2_rot, p3_rot, fill='#FFFFFF', outline='black')

    def get_points(self):
        """
        Calculate the three points that form the car's triangle shape.
        Takes into account position, size, and rotation.
        
        Returns:
            tuple: Three points (x1,y1, x2,y2, x3,y3) defining the triangle
        """
        zx, zy = self.canvas.to_zoom_coords(self.position_x, self.position_y)

        zoom = self.canvas.zoom_factor
        grid_resolution = self.canvas.logic_grid_step
        length_px = (self.car_length / grid_resolution) * zoom
        width_px = (self.car_width / grid_resolution) * zoom

        p1 = (zx - (length_px / 2), zy - (width_px / 2))
        p2 = (zx - (length_px / 2), zy + (width_px / 2))
        p3 = (zx + length_px / 2, zy)

        angle_rad = math.radians(-self.yaw_angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        p1_rot = self.rotate(*p1, cos_a, sin_a, zx, zy)
        p2_rot = self.rotate(*p2, cos_a, sin_a, zx, zy)
        p3_rot = self.rotate(*p3, cos_a, sin_a, zx, zy)

        return p1_rot, p2_rot, p3_rot

    def rotate(self, px, py, cos_a, sin_a, zx, zy):
        """
        Rotate a point around a center point.
        
        Args:
            px, py: Point coordinates to rotate
            cos_a, sin_a: Precomputed cosine and sine of rotation angle
            zx, zy: Center point coordinates
            
        Returns:
            tuple: Rotated point coordinates
        """
        dx = px - zx
        dy = py - zy

        rx = dx * cos_a - dy * sin_a
        ry = dx * sin_a + dy * cos_a

        return rx + zx, ry + zy

    def update_zoom(self, zoom_factor):
        """
        Update the car's position and size based on the new zoom factor.
        
        Args:
            zoom_factor: New zoom level to apply
        """
        p1, p2, p3 = self.get_points()
        self.canvas.coords(self.id, *p1, *p2, *p3)

    def move(self, new_x, new_y):
        """
        Move the car to a new position.
        
        Args:
            new_x: New x position in logical coordinates
            new_y: New y position in logical coordinates
        """
        zx, zy = move_object(self, new_x, new_y)

        p1, p2, p3 = self.get_points()
        self.canvas.coords(self.id, *p1, *p2, *p3)
        if self.info_frame_visible:
            self.update_info_frame()

    def on_click_car(self, event):
        """
        Handle mouse click on the car. Shows/hides info frame if drag tool is active.
        
        Args:
            event: Mouse event containing coordinates
        """
        on_click_object(self, event)
        self.set_active(not self.active)
        # only show/hide the info frame if the drag tool is selected
        if self.canvas.master.current_tool == "drag":
            if self.info_frame_visible:
                self.hide_info_frame()
            else:
                self.show_info_frame()

    def on_drag_car(self, event):
        """
        Handle dragging of the car.
        
        Args:
            event: Mouse event containing coordinates
        """
        on_drag_object(self, event)

    def on_release_car(self, event):
        """
        Handle release of mouse after dragging the car.
        
        Args:
            event: Mouse event containing coordinates
        """
        on_release_object(self, event)

    def set_active(self, active: bool):
        """
        Set the car's active state, which affects its visual appearance.
        
        Args:
            active: Whether the car should be active
        """
        self.active = active
        if self.active:
            self.canvas.itemconfig(self.id, outline="#0094FF", width=3)
        else:
            self.canvas.itemconfig(self.id, outline="#000000", width=1)
        self.update_zoom(self.canvas.zoom_factor)

    def rotate_with_mousewheel(self, event):
        """
        Rotate the car using the mouse wheel when it's active.
        
        Args:
            event: Mouse wheel event containing delta for rotation direction
        """
        if not self.active:
            return

        delta = 5 if event.delta > 0 else -5
        self.yaw_angle = (self.yaw_angle + delta) % 360  # keep angle between 0 and 360
        self.update_zoom(self.canvas.zoom_factor)
        if self.info_frame_visible:
            self.update_info_frame()

    def show_info_frame(self):
        """Show the info frame displaying car coordinates and yaw angle."""
        if not self.info_frame_visible:
            self.update_info_frame() # update content and position
            self.info_frame.lift()
            self.info_frame_visible = True

    def hide_info_frame(self):
        """Hide the info frame."""
        if self.info_frame_visible:
            self.info_frame.place_forget()
            self.info_frame_visible = False

    def update_info_frame(self):
        """Update the coordinate and yaw angle display and reposition the info frame."""
        scale = 1.0 
        if hasattr(self.canvas.master, 'scale'):
            scale = self.canvas.master.scale

        # prevent division by zero (if scale somehow not set)
        if scale == 0:
            scale = 1.0

        # update coordinate values, formatted to 2 decimal places
        meter_x = self.position_x / scale
        meter_y = self.position_y / scale
        self.coord_x_var.set(f"{meter_x:.2f}")
        self.coord_y_var.set(f"{meter_y:.2f}")
        self.yaw_angle_var.set(f"{self.yaw_angle:.2f}")

        # reposition the frame
        zx, zy = self.canvas.to_zoom_coords(self.position_x, self.position_y)
        self.info_frame.update_idletasks()
        frame_height = self.info_frame.winfo_reqheight()
        self.info_frame.place(x=zx + 20, y=zy - frame_height / 2)

    def delete_car(self):
        """Delete the car from the canvas and remove it from the master's car reference."""
        # delete visualization of car on the canvas
        self.canvas.delete(self.id)
        # remove the car reference from the master
        if hasattr(self.canvas.master, 'car'):
            self.canvas.master.car = None

        if self.info_frame_visible:
            self.info_frame.destroy()



