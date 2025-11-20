import customtkinter as ctk
import yaml
from customtkinter import *
from svgpathtools import svg2paths2
import os
from tkinter import filedialog
from tkinter import PhotoImage
from PIL import Image, ImageTk
import math
import sys
from pathlib import Path

from ui_components import TrackCanvas
from ui_components import CanvasObjects
from ui_components.ToolFrame import ToolFrame, GenerateFrame, DragAndDropFrame

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
class Window(CTk):
    """
    Main application window for the Track Builder.
    Manages the canvas, toolbars, and overall application state.
    """

    def __init__(self):
        """
        Initialize the main application window.
        Sets up the canvas, toolbars, and initializes basic variables.
        """
        super().__init__()
        #ctk configuration
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # create application window
        self.title("TRACKBUILDER")
        self.geometry("1080x1080")
        self.configure(width=1920, height=1080, bg="#353434")

        # create canvas
        self.placing_canvas = TrackCanvas.TrackCanvas(self)
        self.placing_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.scale = self.placing_canvas.grid_size / self.placing_canvas.logic_grid_step

        # drag and drop tool frame and generate tool frame
        self.drag_drop_tool_frame = DragAndDropFrame(self)
        self.generate_tool_frame = GenerateFrame(self)
        self.drag_drop_tool_visible = False
        self.generate_tool_visible = False

        # main tool frame
        self.tool_frame = ToolFrame(self, self.placing_canvas)
        self.tool_frame.place(relx=1.0, rely=0.0, anchor="ne", x=-30, y=30)
        self.placing_canvas.set_tool_frame(self.tool_frame)

        # basic variables
        self.cones = []
        self.current_file = None
        self.current_tool = None
        self.car = None

        # ensure frames are on top of canvas
        self.drag_drop_tool_frame.lift()
        self.generate_tool_frame.lift()
        self.tool_frame.lift()

    def set_selected_tool(self, tool):
        """
        Updates the current tool.
        
        Args:
            tool: New tool to apply
        """

        self.current_tool = tool
        
        '''
        # log the tool change for debugging
        if tool:
            print(f"Selected tool: {tool}")
        else:
            print("Tool selection cleared")
        '''
        
        # if a specific tool is selected, ensure the drag and drop frame is visible
        if tool in ["blue", "yellow", "car"]:
            if not self.drag_drop_tool_visible:
                self.manage_drag_drop_tool_frame(True)
                # update the appropriate button in drag drop frame
                if tool == "blue":
                    self.drag_drop_tool_frame.blue_cone_tool()
                elif tool == "yellow":
                    self.drag_drop_tool_frame.yellow_cone_tool()
                elif tool == "car":
                    self.drag_drop_tool_frame.place_car()

    def save_track(self):
        """
        Saves the track to a YAML file.
        If no file is selected, a dialog will prompt the user to select a file.

        """
        if not hasattr(self, 'cones'):
            return

        cones_left = []
        cones_right = []
        starting_pose = []

        scale = self.placing_canvas.grid_size / self.placing_canvas.logic_grid_step

        for cone in self.cones:
            # convert coordinates to meters and ensure they are simple float values
            x = float(cone.position_x/self.scale)
            y = float(cone.position_y/self.scale)
            # create nested list for each coordinate pair
            cone_data = [
                round(x, 4),
                round(y, 4)
            ]

            if cone.cone_type == "blue":
                cones_left.append(cone_data)
            elif cone.cone_type == "yellow":
                cones_right.append(cone_data)

        if hasattr(self, 'car') and self.car:
            # convert car coordinates to meters and ensure they are simple float values
            car_x = float(self.car.position_x/self.scale)
            car_y = float(self.car.position_y/self.scale)
            car_angle = float(self.car.yaw_angle)
            starting_pose = [round(car_x, 4), round(car_y, 4), round(car_angle, 4)]

        track_data = {
            "cones_left": cones_left,
            "cones_right": cones_right,
            "starting_pose": starting_pose
        }

        if self.current_file:
            with open(self.current_file, "w") as file:
                yaml.dump(track_data, file, default_flow_style=False, indent=2)
            print("Track saved successfully! with the name: " + self.current_file)
        else:
            file_name = filedialog.asksaveasfilename(title="Save Track File", defaultextension=".yaml", initialfile="trackdraft",
                                                     filetypes=(("YAML files", "*.yaml"), ("All files", "*.*")))
            if file_name:
                self.current_file = file_name
                with open(self.current_file, "w") as file:
                    yaml.dump(track_data, file, default_flow_style=False, indent=2)
                print("Track saved successfully! with the name: " + self.current_file)

        self.tool_frame.current_file_name.set(os.path.basename(self.current_file))

    #load-functionality
    def load_track(self):
        """
        Loads a track from a YAML file.
        If the file is loaded successfully, the track will be visualized on the canvas.

        """
        file_name = filedialog.askopenfilename(title="Select Track File", filetypes=(("YAML files", "*.yaml"), ("All files", "*.*")))

        if file_name:
            self.current_file = file_name
            track_data = self.open_yaml_file(file_name)
            self.visualize(track_data)

        self.tool_frame.current_file_name.set(os.path.basename(self.current_file))


    def open_yaml_file(self, file_name):
        """
        Opens a YAML file and returns the track data.
        
        Args:
            file_name: Name of the YAML file to open

        """
        with open(file_name, "r") as file:
            track_data = yaml.safe_load(file)
            return track_data

    def visualize(self, track_data):
        """
        Clears the canvas and visualizes the track data on the canvas.

        Args:
            track_data: Dictionary containing the positions of cones and the starting pose of the car
        """
        if not hasattr(self, 'clear_canvas'):
            return
        
        self.clear_canvas()
        car_position = []
        
        try:
            for cone_data in track_data.get("cones_left", []):
                cone = CanvasObjects.Cone(self.placing_canvas, "blue", cone_data[0] * self.scale, cone_data[1] * self.scale)
            for cone_data in track_data.get("cones_right", []):
                cone = CanvasObjects.Cone(self.placing_canvas, "yellow", cone_data[0] * self.scale, cone_data[1] * self.scale)
            for cone_data in track_data.get("starting_pose", []):
                car_position.append(cone_data)

            if car_position and len(car_position) >= 3:
                self.car = CanvasObjects.Car(self.placing_canvas, car_position[0], car_position[1], car_position[2])
                self.car.update_zoom(self.placing_canvas.zoom_factor)
                print("car successfully loaded!")

            # method handles grid resizing and focusing
            self.placing_canvas.fit_to_track()

            if hasattr(self, 'cones'):
                for cone in self.cones:
                    cone.update_zoom(self.placing_canvas.zoom_factor)

            print("Load successful!")
            
        except Exception as e:
            print(f"Error loading track: {e}")



    def clear_canvas(self):
        """
        Clears the canvas and removes all objects from the canvas.
        """
        if not hasattr(self, 'cones'):
            return
        
        for cone in self.cones:
            self.placing_canvas.delete(cone.id)

        if hasattr(self, 'car') and self.car:
            self.placing_canvas.delete(self.car.id)
            self.car = None
        self.cones.clear()
        print("canvas cleared")

    def update_zoom(self, zoom):
        """
        Update zoom level for all objects on the canvas.
        
        Args:
            zoom: New zoom factor to apply
        """
        if not hasattr(self, 'cones'):
            return
        
        for cone in self.cones:
            cone.update_zoom(zoom)

        if self.car:
            self.car.update_zoom(zoom)

    def manage_drag_drop_tool_frame(self, is_visible: bool):
        """
        Handle the visibility of the drag and drop tool frame.
        Ensures proper tool state management when showing/hiding the frame.
        
        Args:
            is_visible: Whether the frame should be visible
        """
        if is_visible:
            # hide generate tool frame if it's visible
            if self.generate_tool_visible:
                self.generate_tool_frame.place_forget()
                self.generate_tool_visible = False
                if hasattr(self.tool_frame, 'generate_tool_button'):
                    self.tool_frame.generate_tool_button.configure(border_color="#141414")
            
            # show drag and drop frame
            if not self.drag_drop_tool_visible:
                self.drag_drop_tool_frame.place(relx=1.0, rely=0.1, anchor="ne", x=-30)
                self.drag_drop_tool_visible = True
                
                # deactivate all tools by default when opening the frame
                self.drag_drop_tool_frame.deactivate_all_buttons()
        else:
            # hide the frame
            if self.drag_drop_tool_visible:
                self.drag_drop_tool_frame.place_forget()
                self.drag_drop_tool_visible = False
                self.set_selected_tool(None)  # clear tool selection

    def manage_generate_tool_frame(self, is_visible: bool):
        """
        Handle the visibility of the generate tool frame.
        Ensures proper tool state management when showing/hiding the frame.
        
        Args:
            is_visible: Whether the frame should be visible
        """
        if is_visible:
            # hide drag-and-drop frame if it's visible
            if self.drag_drop_tool_visible:
                self.drag_drop_tool_frame.place_forget()
                self.drag_drop_tool_visible = False
                if hasattr(self.tool_frame, 'drag_tool_button'):
                    self.tool_frame.drag_tool_button.configure(border_color="#141414")
            
            # show generate frame
            if not self.generate_tool_visible:
                self.generate_tool_frame.place(relx=1.0, rely=0.1, anchor="ne", x=-30)
                self.generate_tool_visible = True
                
                # show welcome message
                if hasattr(self.generate_tool_frame, 'status_var'):
                    self.generate_tool_frame.status_var.set("Ready to generate track. Select an image to continue.")
                
                print("Generate tool panel opened")
        else:
            # hide the frame
            if self.generate_tool_visible:
                self.generate_tool_frame.place_forget()
                self.generate_tool_visible = False
                print("Generate tool panel closed")

    def close_all_tool_frames(self):
        """
        Close all tool frames and reset their states.
        Ensures proper cleanup of tool states and button appearances.
        """
        if self.drag_drop_tool_visible:
            self.drag_drop_tool_frame.place_forget()
            self.drag_drop_tool_visible = False
            if hasattr(self.tool_frame, 'drag_tool_button'):
                self.tool_frame.drag_tool_button.configure(border_color="#141414")
        
        if self.generate_tool_visible:
            self.generate_tool_frame.place_forget()
            self.generate_tool_visible = False
            if hasattr(self.tool_frame, 'generate_tool_button'):
                self.tool_frame.generate_tool_button.configure(border_color="#141414")
        
        self.current_tool = None

    def generate_cones_from_points(self, points, track_width=5.0):
        """
        Generate blue and yellow cones from a list of track points.
        Places cones along the track boundaries based on the provided points.
        
        Args:
            points: List of (x, y) coordinates defining the track centerline
            track_width: Width of the track in meters (default: 5.0)
        """
        if not hasattr(self, 'clear_canvas'):
            return
        
        self.clear_canvas()

        # use the canvas's scale for consistent coordinate system
        scale = self.placing_canvas.grid_size / self.placing_canvas.logic_grid_step
        offset = (track_width * scale) / 2
        
        try:
            for i in range(len(points) - 1):
                p1, p2 = points[i], points[i + 1]

                # calculate direction vector
                dx = p2[0] - p1[0]
                dy = p2[1] - p1[1]

                # skip if points are too close
                length = math.hypot(dx, dy)
                if length < 1:
                    continue

                # normalize direction vector
                dx /= length
                dy /= length

                # calculate normal vector (perpendicular)
                nx, ny = -dy, dx

                # calculate midpoint
                mx = (p1[0] + p2[0]) / 2
                my = (p1[1] + p2[1]) / 2

                # place cones using the canvas's scale
                blue_cone = CanvasObjects.Cone(self.placing_canvas, "blue", mx + nx * offset, my + ny * offset)
                yellow_cone = CanvasObjects.Cone(self.placing_canvas, "yellow", mx - nx * offset, my - ny * offset)

                # ensure cones are in master's list
                if blue_cone not in self.cones:
                    self.cones.append(blue_cone)
                if yellow_cone not in self.cones:
                    self.cones.append(yellow_cone)

            # update zoom for all cones
            for cone in self.cones:
                cone.update_zoom(self.placing_canvas.zoom_factor)
            
            # fit view to show all cones with a larger margin for better visibility
            self.placing_canvas.fit_to_track(margin=1000)
            
            print(f"Generated track with {len(self.cones)} cones")
            
        except Exception as e:
            print(f"Error generating cones: {e}")
            import traceback
            traceback.print_exc()


def main():
    app = Window()
    app.mainloop()

if __name__ == "__main__":
    main()