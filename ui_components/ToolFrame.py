from tkinter import PhotoImage

import cairosvg
from customtkinter import *
from PIL import Image, ImageTk
import io
import math
from svgpathtools import svg2paths

import os
import cv2
import numpy as np
from ui_components import CanvasObjects

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_asset_path(filename: str) -> str:
    return os.path.join(BASE_DIR, "assets", filename)

class ToolFrame(CTkFrame):
    """
    Main toolbar frame containing buttons for various track building tools.
    Includes zoom control, coordinate axes toggle, and access to specialized tools.
    """

    def __init__(self, master, canvas):
        """
        Initialize the main tool frame.
        
        Args:
            master: Parent widget that contains this frame
            canvas: The canvas that this toolbar controls
        """
        super().__init__(
            master,
            width=300,
            height=50,
            fg_color="#000000",
            bg_color="#000000",
            corner_radius=4,
            border_width=1,
            border_color="#111111"
        )

        self.canvas = canvas

        #display filename
        self.current_file_name = StringVar(value="TRACKDRAFT.yaml")
        self.file_name = CTkLabel(self, textvariable=self.current_file_name, text="TRACKDRAFT.YAML", text_color="#FFFFFF", font=("Roboto", 12), padx=5, pady=5)
        self.file_name.grid(row=1, column=1, sticky="nsew", padx=(5, 15), pady=10)
        #self.file_name_entry = CTkEntry(self, textvariable=self.current_file_name, width=200)
        #self.file_name_entry.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        #edit zoom factor
        zoom_values = ["50%", "100%", "150%", "200%"]
        self.zoom_dropdown_var = StringVar()
        self.zoom_dropdown_var.set(zoom_values[1])
        zoom_dropdown = CTkOptionMenu(self, variable=self.zoom_dropdown_var, values=zoom_values, command=self.zoom_select, width=85, corner_radius=2)
        zoom_dropdown.grid(row=1, column=2, sticky="e", pady=10)

        self.zoom_var = StringVar(value="100%")
        vcmd = self.register(self.validate_zoom_input)
        self.zoom_entry = CTkEntry(self, textvariable=self.zoom_var, font=("Roboto", 12), width=60, validate="key", validatecommand=(vcmd, "%P"), corner_radius=0)
        self.zoom_entry.grid(row=1, column=2, sticky="w", pady=10)
        self.zoom_entry.bind("<Return>", self.zoom_from_entry)
        #self.zoom_entry.bind("<KeyRelease>", self.on_zoom_key_release)
        self.zoom_entry.bind("<FocusIn>", self.on_zoom_focus_in)

        #button to display coordinate axes
        self.axes_visible = False

        self.axes_icon = CTkImage(Image.open(get_asset_path("coord_axes.png")))
        self.coord_axes = CTkButton(self, command=self.toogle_coord_axes, text="", image=self.axes_icon, width=20, fg_color="#141414", bg_color="#000000", corner_radius=6, border_width=1, border_color="#141414", hover_color="#7A4315")
        self.coord_axes.grid(row=1, column=3, sticky="nsew", padx=(30,15), pady=10)

        #drag and drop tool
        self.drag_tool_visible = False
        self.drag_tool_button = CTkButton(self, command=self.open_drag_tool, text="DRAG AND DROP", font=("Roboto", 12),  width=120, fg_color="#141414", bg_color="#000000", corner_radius=6, border_width=1, border_color="#141414", hover_color="#7A4315")
        self.drag_tool_button.grid(row=1, column=4, sticky="nsew", padx=(15, 5), pady=10)

        #generate tool button
        self.generate_tool_visible = False
        self.generate_tool_button = CTkButton(self, command=self.open_generate_tool, text="GENERATE", font=("Roboto", 12), width=100, fg_color="#141414", bg_color="#000000", corner_radius=6, border_width=1, border_color="#141414", hover_color="#7A4315")
        #self.generate_tool_button.grid(row=1, column=5, sticky="nsew", padx=(5, 5), pady=10)

        # separator
        separator = CTkFrame(self, width=1, height=30, fg_color="#4A4A4A")
        separator.grid(row=1, column=6, sticky="ns", padx=(15, 10), pady=10)

        # save button
        self.save_button = CTkButton(self, command=lambda: self.master.save_track(), text="SAVE", font=("Roboto", 12), width=80, fg_color="#141414", bg_color="#000000", corner_radius=6, border_width=1, border_color="#141414", hover_color="#7A4315")
        self.save_button.grid(row=1, column=7, sticky="nsew", padx=(5, 5), pady=10)

        # load button
        self.load_button = CTkButton(self, command=lambda: self.master.load_track(), text="LOAD", font=("Roboto", 12), width=80, fg_color="#141414", bg_color="#000000", corner_radius=6, border_width=1, border_color="#141414", hover_color="#7A4315")
        self.load_button.grid(row=1, column=8, sticky="nsew", padx=(5, 5), pady=10)

    def validate_zoom_input(self, value):
        if value.endswith("%"):
            value = value[:-1]
        if len(value) > 3:
            return value == ""

        return value.isdigit() or value == ""

    def on_zoom_focus_in(self, event):
        digits = self.zoom_var.get()
        self.zoom_entry.icursor(len(digits))


    def zoom_from_entry(self, event):
        try:
            value = self.zoom_var.get().replace("%", "")
            zoom = int(value) / 100.0  # convert percentage to decimal
            if zoom == 0.0:
                raise ValueError
            
            # round to nearest step of 0.025
            step = 0.025
            zoom = round(zoom / step) * step
            
            # apply zoom and update display
            self.apply_zoom(zoom * 100)  # convert back to percentage
            self.zoom_var.set(f"{int(zoom * 100)}%")
        except ValueError:
            self.zoom_var.set("100%")

    def apply_zoom(self, zoom):
        self.canvas.set_zoom_factor(zoom/100)

    def zoom_select(self, event):
        self.zoom_var.set(self.zoom_dropdown_var.get())
        zoom = int(self.zoom_var.get().replace("%", ""))
        self.apply_zoom(zoom)

        return

    def toogle_coord_axes(self):
        """
        Toggle the visibility of coordinate axes on the canvas.
        Updates button appearance and redraws the grid.
        """
        self.axes_visible = not self.axes_visible
        if self.axes_visible:
            self.coord_axes.configure(border_color="#FFFFFF")
        else:
            self.coord_axes.configure(border_color="#141414")
        self.canvas.show_axes = self.axes_visible
        self.canvas.draw_grid()
        self.canvas.tag_lower("grid_line")
        self.canvas.tag_lower("axis_label")


    def open_drag_tool(self):
        """
        Toggle the visibility of the drag and drop tool frame.
        Handles button appearance and ensures proper tool state management.
        """
        # toggle the drag tool visibility
        self.drag_tool_visible = not self.drag_tool_visible
        
        # update button appearance
        if self.drag_tool_visible:
            self.drag_tool_button.configure(border_color="#FFFFFF")
            # close generate tool if open
            if self.generate_tool_visible:
                self.generate_tool_visible = False
                self.generate_tool_button.configure(border_color="#141414")
                if hasattr(self.master, 'manage_generate_tool_frame'):
                    self.master.manage_generate_tool_frame(False)
        else:
            self.drag_tool_button.configure(border_color="#141414")
        
        # ensure master has manage_drag_drop_tool_frame method before calling
        if hasattr(self.master, 'manage_drag_drop_tool_frame'):
            self.master.manage_drag_drop_tool_frame(self.drag_tool_visible)
        
        # reset current tool when closing panel
        if not self.drag_tool_visible and hasattr(self.master, 'set_selected_tool'):
            self.master.set_selected_tool(None)

    def open_generate_tool(self):
        """
        Toggle the visibility of the track generation tool frame.
        Handles button appearance and ensures proper tool state management.
        """
        # toggle the generate tool visibility
        self.generate_tool_visible = not self.generate_tool_visible
        
        # update button appearance
        if self.generate_tool_visible:
            self.generate_tool_button.configure(border_color="#FFFFFF")
            # close drag tool if open
            if self.drag_tool_visible:
                self.drag_tool_visible = False
                self.drag_tool_button.configure(border_color="#141414")
                if hasattr(self.master, 'manage_drag_drop_tool_frame'):
                    self.master.manage_drag_drop_tool_frame(False)
        else:
            self.generate_tool_button.configure(border_color="#141414")
        
        # ensure master has manage_generate_tool_frame method before calling
        if hasattr(self.master, 'manage_generate_tool_frame'):
            self.master.manage_generate_tool_frame(self.generate_tool_visible)
        
        # reset current tool when closing the panel
        if not self.generate_tool_visible and hasattr(self.master, 'set_selected_tool'):
            self.master.set_selected_tool(None)

    def deactivate_all_buttons(self):
        """
        Resets the tool selection and removes the active-state border
        from all tool buttons in this frame.
        """
        if hasattr(self.master, 'set_selected_tool'):
            self.master.set_selected_tool(None)

        self.mouse_button.configure(border_color="#111111")
        self.blue_cone_button.configure(border_color="#111111")
        self.yellow_cone_button.configure(border_color="#111111")
        self.car_button.configure(border_color="#111111")

class DragAndDropFrame(CTkFrame):
    """
    Frame containing drag and drop tools for manipulating objects on the canvas.
    Provides buttons for selecting different tools and managing object placement.
    """

    def __init__(self, master):
        """
        Initialize the drag and drop tool frame.
        
        Args:
            master: Parent widget that contains this frame
        """
        super().__init__(
            master,
            width=90,
            height=280,
            fg_color="#111111",
            bg_color="#000000",
            corner_radius=5
        )

        # title label
        self.label = CTkLabel(
            self,
            text="DRAG AND DROP",
            font=("Roboto", 8),
            text_color="#AAAAAA"
        )
        self.label.grid(row=0, column=0, sticky="nsew", padx=3, pady=(10, 5))

        # mouse tool button
        self.mouse_icon = CTkImage(Image.open(get_asset_path("zeiger.png")), size=(35, 35))  # Increased icon size
        self.mouse_button = CTkButton(
            self,
            command=self.mouse_tool,
            image=self.mouse_icon,
            width=60, 
            height=45, 
            text="",
            fg_color="#111111",
            bg_color="#111111",
            corner_radius=6,
            border_width=1,
            border_color="#AAAAAA",
            hover_color="#222222"
        )
        self.mouse_button.grid(row=1, column=0, sticky="nsew", padx=15, pady=8)

        # blue cone button
        self.blue_cone_icon = CTkImage(Image.open(get_asset_path("blue_cone.png")), size=(35, 35))  # Added size parameter
        self.blue_cone_button = CTkButton(
            self,
            command=self.blue_cone_tool,
            #image=self.blue_cone_icon,
            width=60,
            height=45,
            text="CONE LEFT",
            fg_color="#111111",
            bg_color="#111111",
            corner_radius=6,
            border_width=1,
            border_color="#AAAAAA",
            hover_color="#222222"
        )
        self.blue_cone_button.grid(row=2, column=0, sticky="nsew", padx=15, pady=8)

        # yellow cone button
        self.yellow_cone_icon = CTkImage(Image.open(get_asset_path("yellow_cone.png")), size=(35, 35))  # Added size parameter
        self.yellow_cone_button = CTkButton(
            self,
            command=self.yellow_cone_tool,
            #image=self.yellow_cone_icon,
            width=60, 
            height=45, 
            text="CONE RIGHT",
            fg_color="#111111",
            bg_color="#111111",
            corner_radius=6,
            border_width=1,
            border_color="#AAAAAA",
            hover_color="#222222"
        )
        self.yellow_cone_button.grid(row=3, column=0, sticky="nsew", padx=15, pady=8)

        # car button
        self.car_icon = CTkImage(Image.open(get_asset_path("racing-car.png")), size=(35, 35))  # Added size parameter
        self.car_button = CTkButton(
            self,
            command=self.place_car,
            #image=self.car_icon,
            width=60, 
            height=45, 
            text="CAR",
            fg_color="#111111",
            bg_color="#111111",
            corner_radius=6,
            border_width=1,
            border_color="#AAAAAA",
            hover_color="#222222"
        )
        self.car_button.grid(row=4, column=0, sticky="nsew", padx=15, pady=8)

    def mouse_tool(self):
        self.deactivate_all_buttons()
        if hasattr(self.master, 'set_selected_tool'):
            self.master.set_selected_tool("drag")
        self.mouse_button.configure(border_color="#FFFFFF")

    def blue_cone_tool(self):
        self.deactivate_all_buttons()
        if hasattr(self.master, 'set_selected_tool'):
            self.master.set_selected_tool("blue")
        self.blue_cone_button.configure(border_color="#FFFFFF")

    def yellow_cone_tool(self):
        self.deactivate_all_buttons()
        if hasattr(self.master, 'set_selected_tool'):
            self.master.set_selected_tool("yellow")
        self.yellow_cone_button.configure(border_color="#FFFFFF")

    def place_car(self):
        self.deactivate_all_buttons()
        if hasattr(self.master, 'set_selected_tool'):
            self.master.set_selected_tool("car")
        self.car_button.configure(border_color="#FFFFFF")

    def deactivate_all_buttons(self):
        """
        Resets the tool selection and removes the active-state border
        from all tool buttons in this frame.
        """
        if hasattr(self.master, 'set_selected_tool'):
            self.master.set_selected_tool(None)

        self.mouse_button.configure(border_color="#111111")
        self.blue_cone_button.configure(border_color="#111111")
        self.yellow_cone_button.configure(border_color="#111111")
        self.car_button.configure(border_color="#111111")

class GenerateFrame(CTkFrame):
    """
    Frame containing tools for generating track layouts from images.
    Provides image selection, preview, and track generation functionality.
    """

    def __init__(self, master):
        """
        Initialize the track generation frame.
        
        Args:
            master: Parent widget that contains this frame
        """
        super().__init__(
            master,
            width=300,
            height=500,
            fg_color="#111111",
            bg_color="#000000",
            corner_radius=5,
        )
        self.pack_propagate(False)

        # title label
        self.title_label = CTkLabel(
            self, text="GENERATE", font=("Roboto", 8), text_color="#AAAAAA"
        )
        self.title_label.pack(pady=(10, 5))

        # preview frame
        self.preview_frame = CTkFrame(
            self, fg_color="#0A0A0A", bg_color="#111111", corner_radius=3, height=220, width=280
        )
        self.preview_frame.pack(pady=(0, 10), padx=10)
        self.preview_frame.pack_propagate(False)
        
        # preview placeholder text
        self.preview_text = CTkLabel(
            self.preview_frame,
            text="No image selected\nPreview will appear here",
            font=("Roboto", 10),
            text_color="#AAAAAA"
        )
        self.preview_text.place(relx=0.5, rely=0.5, anchor="center")

        # select image button
        self.select_button = CTkButton(
            self,
            text="SELECT TRACK IMAGE",
            command=self.select_image,
            font=("Roboto", 12),
            fg_color="#000000",
            hover_color="#222222",
            bg_color="#111111",
            width=260,
            height=35,
            corner_radius=6,
            border_width=1,
            border_color="#AAAAAA"
        )
        self.select_button.pack(pady=(0, 5))

        # file name label
        self.filename_var = StringVar(value="No file selected")
        self.filename_label = CTkLabel(
            self,
            textvariable=self.filename_var,
            font=("Roboto", 9),
            text_color="#AAAAAA"
        )
        self.filename_label.pack(pady=(0, 10))

        # track width label and entry in a frame
        track_width_frame = CTkFrame(
            self,
            fg_color="transparent",
            bg_color="transparent"
        )
        track_width_frame.pack(pady=(5, 15))

        self.track_label = CTkLabel(
            track_width_frame,
            text="Track Width (meters)",
            font=("Roboto", 11),
            text_color="#FFFFFF"
        )
        self.track_label.pack(side="left", padx=(5, 10))

        self.track_width_var = StringVar(value="5.0")
        self.track_width_entry = CTkEntry(
            track_width_frame,
            textvariable=self.track_width_var,
            width=60,
            height=25,
            font=("Roboto", 11),
            corner_radius=4,
            border_width=1,
            justify="center"
        )
        self.track_width_entry.pack(side="left", padx=(0, 5))

        # generate button
        self.generate_button = CTkButton(
            self,
            text="GENERATE CONES",
            command=self.generate_cones,
            font=("Roboto", 12),
            fg_color="#000000",
            hover_color="#222222",
            bg_color="#111111",
            width=260,
            height=35,
            corner_radius=6,
            border_width=1,
            border_color="#AAAAAA",
            state="disabled"
        )
        self.generate_button.pack(pady=(0, 10))

        # initialize variables
        self.selected_image_path = None
        self.image_preview = None
        self.preview_label = None

    def select_image(self):
        """
        Open a file dialog to select a track image file.
        Supports PNG and JPEG formats, updates preview and enables generation.
        """
        file_path = filedialog.askopenfilename(
            title="Select Track Image",
            filetypes=(
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg;*.jpeg"),
                ("All files", "*.*")
            )
        )
        
        if file_path:
            self.selected_image_path = file_path
            self.filename_var.set(os.path.basename(file_path))
            self.show_image_preview(file_path)
            self.generate_button.configure(state="normal")
    
    def show_image_preview(self, image_path):
        """
        Display a preview of the selected track image.
        Scales the image to fit the preview area while maintaining aspect ratio.
        
        Args:
            image_path: Path to the image file to preview
        """
        try:
            # clear existing preview
            for widget in self.preview_frame.winfo_children():
                widget.destroy()
            
            # open and convert image
            image = Image.open(image_path)
            
            # get preview frame dimensions
            preview_width = self.preview_frame.winfo_width()
            preview_height = self.preview_frame.winfo_height()
            
            # calculate aspect ratios
            img_aspect = image.width / image.height
            frame_aspect = preview_width / preview_height
            
            # calculate new dimensions maintaining aspect ratio
            if img_aspect > frame_aspect:
                new_width = preview_width - 20  # padding
                new_height = int(new_width / img_aspect)
            else:
                new_height = preview_height - 20  # padding
                new_width = int(new_height * img_aspect)
            
            # resize image
            resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # convert to PhotoImage and store reference
            self.image_preview = CTkImage(
                light_image=resized,
                dark_image=resized,
                size=(new_width, new_height)
            )
            
            # create and position preview label
            self.preview_label = CTkLabel(
                self.preview_frame,
                image=self.image_preview,
                text=""
            )
            self.preview_label.place(relx=0.5, rely=0.5, anchor="center")
            
        except Exception as e:
            print(f"Error displaying image preview: {e}")
            error_label = CTkLabel(
                self.preview_frame,
                text=f"Error loading image",
                text_color="#FF5555",
                font=("Roboto", 10)
            )
            error_label.place(relx=0.5, rely=0.5, anchor="center")
            self.generate_button.configure(state="disabled")

    def generate_cones(self):
        """
        Generate track cones from the selected image.
        Processes the image to detect track boundaries and places cones accordingly.
        Uses track width setting to determine cone placement distance.
        """
        if not self.selected_image_path:
            return
        
        try:
            # get track width
            track_width = float(self.track_width_var.get())
            if track_width <= 0:
                track_width = 5.0

            # process image
            img = cv2.imread(self.selected_image_path)
            if img is None:
                return

            # convert to grayscale and process
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            _, threshold = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            edges = cv2.Canny(threshold, 50, 150)
            
            # find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                return

            # get the largest contour
            contour = max(contours, key=cv2.contourArea)
            if cv2.contourArea(contour) < 1000:
                return

            # simplify the contour
            epsilon = 0.005 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            # convert to track points using the canvas's scale
            track_points = []
            scale = self.master.placing_canvas.grid_size / self.master.placing_canvas.logic_grid_step
            center_x = img.shape[1]/2
            center_y = img.shape[0]/2

            for point in approx:
                x = (point[0][0] - center_x) * (scale / 4)  # divide by 4 to make the track size more reasonable
                y = (point[0][1] - center_y) * (scale / 4)
                track_points.append((x, y))

            # close the loop if needed
            if track_points[0] != track_points[-1]:
                track_points.append(track_points[0])

            # generate cones
            if hasattr(self.master, 'generate_cones_from_points'):
                self.master.generate_cones_from_points(track_points, track_width)

        except Exception as e:
            print(f"Error generating track: {e}")
            import traceback
            traceback.print_exc()


