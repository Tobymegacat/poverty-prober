from PySide6.QtWidgets import QWidget, QDialog,QHBoxLayout, QGraphicsTextItem, QFrame, QCheckBox, QPushButton, QVBoxLayout,QLabel,QLineEdit, QInputDialog, QListWidgetItem, QFileDialog, QToolTip, QMainWindow, QMessageBox, QGraphicsView, QGraphicsScene, QGraphicsRectItem 
from .probeGUI import Ui_MainWindow
from .probing_stuff import probe_handler
from .camera_stuff import camera_handler
from PySide6.QtGui import QBrush, QColor, QCursor, QPen
from PySide6.QtCore import QRectF, Qt
import numpy as np
import gdspy
import math
import keyboard
from .wafer_visualizer import WaferVisualizer

from pathlib import Path

import serial
import serial.tools.list_ports
import time
import pygame

import json

with open("config.json", "r") as f:
    config = json.load(f)





colornames =  [
            "green", "yellow", "cyan", "magenta", "gray", "lightgray", "darkgray",
            "orange", "pink", "purple", "brown", "navy", "teal",
            "lime", "olive", "maroon", "gold", "indigo", "turquoise",
            "skyblue", "deepskyblue", "lightblue", "dodgerblue",
            "orchid", "plum", "salmon", "coral", "tomato", "crimson"
        ]   

highest_id = 0

class ChipViewer(QDialog):
    def __init__(self, gds_path, chipname, rowcol, resistance_map=None):
        super().__init__()
        self.setWindowTitle(f"Chip Resistance Viewer: {chipname}, row: {rowcol[0,0]} col: {rowcol[1,0]}")
        self.gds_path = gds_path
        self.resistance_map = resistance_map
        
        # Main layout
        main_layout = QHBoxLayout(self)
        
        # Left panel for controls
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        control_panel.setFixedWidth(200)
        
        # Layer selection label
        layer_label = QLabel("Select Layers to Display:")
        control_layout.addWidget(layer_label)
        
        # Container for layer checkboxes
        self.checkbox_container = QWidget()
        self.checkbox_layout = QVBoxLayout(self.checkbox_container)
        control_layout.addWidget(self.checkbox_container)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Display")
        refresh_btn.clicked.connect(self.refresh_display)
        control_layout.addWidget(refresh_btn)
        
        # Add stretch to push everything to top
        control_layout.addStretch()
        
        main_layout.addWidget(control_panel)
        
        # Right panel for graphics view
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        main_layout.addWidget(self.view)
        
        # Store checkboxes
        self.layer_checkboxes = {}
        
        # Initialize
        self.discover_layers()
        self.load_gds()
        
        self.resize(1000, 600)
        self.show()

    def discover_layers(self):
        """Discover all layers 50 and above in the GDS file"""
        lib = gdspy.GdsLibrary(infile=self.gds_path)
        cell = lib.top_level()[0]
        
        # Get all layer specs
        poly_dict = cell.get_polygons(by_spec=True)
        
        # Find layers 50 and above
        available_layers = set()
        for (layer, datatype), polygons in poly_dict.items():
            if layer >= 50 and len(polygons) > 0:
                available_layers.add(layer)
        
        # Create checkboxes for each available layer
        for layer in sorted(available_layers):
            checkbox = QCheckBox(f"Junction Type {layer - 50}")
            checkbox.setChecked(True)  # All checked by default
            self.layer_checkboxes[layer] = checkbox
            self.checkbox_layout.addWidget(checkbox)

    def get_selected_layers(self):
        """Return set of currently selected layers"""
        return {layer for layer, checkbox in self.layer_checkboxes.items() 
                if checkbox.isChecked()}

    def refresh_display(self):
        """Refresh the display with currently selected layers"""
        self.scene.clear()
        self.load_gds()

    def load_gds(self):
        """Load and display GDS with selected layers only"""
        lib = gdspy.GdsLibrary(infile=self.gds_path)
        cell = lib.top_level()[0]
        
        # Get selected layers
        selected_layers = self.get_selected_layers()
        
        if not selected_layers:
            return  # Nothing to display
        
        # Group polygons by (layer, datatype)
        poly_dict = cell.get_polygons(by_spec=True)
        
        # Set background
        self.scene.setBackgroundBrush(QBrush(QColor(240, 240, 240)))
        
        # Color palette for different layers
        layer_colors = [
            QColor(180, 240, 200),  # Light green
            QColor(200, 180, 240),  # Light purple
            QColor(240, 200, 180),  # Light orange
            QColor(180, 200, 240),  # Light blue
            QColor(240, 240, 180),  # Light yellow
            QColor(240, 180, 200),  # Light pink
        ]
        
        for (layer, datatype), polygons in poly_dict.items():
            if layer not in selected_layers:
                continue  # Skip unselected layers
            
            # Choose color based on layer
            color_idx = (layer - 50) % len(layer_colors)
            layer_color = layer_colors[color_idx]
            
            for points in polygons:
                if len(points) != 4:
                    continue  # skip non-rectangles

                # Bounding box
                x_coords = points[:, 0]
                y_coords = points[:, 1]
                
                centroid = np.mean(points, axis=0) / 1000

                x = min(x_coords)
                y = min(y_coords)
                w = max(x_coords) - x
                h = max(y_coords) - y
                
                rect_item = QGraphicsRectItem(QRectF(x/7, (-y - h)/7, w/7, h/7))
                rect_item.setBrush(QBrush(layer_color))
                
                # Add border to distinguish layers
                pen = QPen(QColor(100, 100, 100))
                pen.setWidth(1)
                rect_item.setPen(pen)
                
                self.scene.addItem(rect_item)

                if self.resistance_map is not None and self.resistance_map.size > 0:
                    # Use tolerance-based matching instead of exact equality
                    tolerance = 1e-6  # Adjust this value as needed
                    
                    # Calculate distances to all points in resistance_map
                    distances = np.sqrt((self.resistance_map[0] - centroid[0])**2 + 
                                      (self.resistance_map[1] - centroid[1])**2)
                    
                    # Find the closest match
                    min_distance_idx = np.argmin(distances)
                    min_distance = distances[min_distance_idx]
                    
                    if min_distance < tolerance:
                        resistance = self.resistance_map[2, min_distance_idx]
                        
                        # Format resistance value
                        if resistance < 1000:
                            resistance_display = resistance
                            resistance_rounded = math.trunc(resistance_display * 100) / 100
                            text_item = QGraphicsTextItem(f"{resistance_rounded}Ω")
                        elif resistance < 1000000:
                            resistance_display = resistance / 1000
                            resistance_rounded = math.trunc(resistance_display * 100) / 100
                            text_item = QGraphicsTextItem(f"{resistance_rounded}kΩ")
                        else:
                            resistance_display = resistance / 1000000
                            resistance_rounded = math.trunc(resistance_display * 100) / 100
                            text_item = QGraphicsTextItem(f"{resistance_rounded}MΩ")
                        
                        text_item.setDefaultTextColor(QColor("black"))
                        text_item.setPos((x + w / 2)/7 - 18, (-y - h / 2)/7)
                        self.scene.addItem(text_item)
                    else:
                        # Optionally add a "No data" label
                        text_item = QGraphicsTextItem("No data")
                        text_item.setDefaultTextColor(QColor("red"))
                        text_item.setPos((x + w / 2 - 15)/7, (-y - h / 2)/7)
                        self.scene.addItem(text_item)

class wafer_chip_type(QListWidgetItem):
    def __init__(self, name, id, path):
        super().__init__(name)
        self.gds_path = path
        self.id = id
        
        self.points_to_probe = np.array([],[])
        if self.gds_path != None and self.gds_path != "None":
            self.generate_points_to_probe()


    def generate_points_to_probe(self):
        self.points_to_probe = []
        gdsii = gdspy.GdsLibrary(infile=self.gds_path)
        target_datatype = 0
        
        print(f"GDS file: {self.gds_path}")
        print(f"GDS units: {gdsii.unit}")  # Check the unit
        
        # Initialize empty array with proper shape
        self.points_to_probe = np.empty((3, 0))
        
        for cell_name in gdsii.cells:
            cell = gdsii.cells[cell_name]
            print(f"Processing cell: {cell_name}")
            
            # Start from layer 50 and go up until no polygons found
            layer = 50
            while True:
                layer_index = layer - 50
                polygons = cell.get_polygons(by_spec=(layer, target_datatype))
                
                if len(polygons) == 0:
                    break
                
                print(f"Layer {layer}: found {len(polygons)} polygons")
                
                for i, polygon in enumerate(polygons):
                    if len(polygon) == 4:
                        print(f"  Polygon {i}: {polygon}")
                        x_center = polygon[:, 0].mean()
                        y_center = polygon[:, 1].mean()
                        print(f"  Center: ({x_center}, {y_center})")
                        temp_center = np.array([[x_center], [y_center], [layer_index]])
                        self.points_to_probe = np.hstack((self.points_to_probe, temp_center))
                
                layer += 1
        
        print(f"Final points_to_probe: {self.points_to_probe}")
        return
        
class wafer_chip(QGraphicsRectItem):
    def __init__(self, x, y, size, chip_type, irl_size, main_window, rowcol):
        super().__init__(x, y, size, size)
        self.irl_coordinates = np.array([[],[]])
        self.main_window = main_window
        self.irl_size = irl_size
        self.chip_type = int(chip_type)
        
        self.rowcol = rowcol

        self.setBrush(QBrush(QColor(colornames[self.chip_type])))
        self.setPen(QColor("black"))
        self.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.LeftButton)

        self.probe_info = None
        self.update_probe_points()

    def update_probe_points(self):
        for index in range(self.main_window.ui.listWidget.count()):
            category = self.main_window.ui.listWidget.item(index)
            if category.id == self.chip_type:
                if category.points_to_probe.size >0:
                    probe_path = category.points_to_probe.copy()
                    probe_path[:2,:] = probe_path[:2,:]/1000
                    self.probe_info = np.zeros((4, probe_path.shape[1]))
                    self.probe_info[:2,:] = probe_path[:2,:]
                    self.probe_info[2,:] = -1
                    self.probe_info[3,:] = probe_path[2,:]

    def insert_probed_resistance(self, coord, resistance):
        
        # Use tolerance for floating point comparison
        tolerance = 1e-6
        mask = (np.abs(self.probe_info[0] - coord[0,0]) < tolerance) & \
            (np.abs(self.probe_info[1] - coord[1,0]) < tolerance)
        indices = np.where(mask)[0]
        
        if len(indices) > 0:
            self.probe_info[2, indices[0]] = resistance



    def mousePressEvent(self, event):
        # get reference to main app from scene or item

        if getattr(self.main_window, 'is_assigning_mode', False):
            new_id = self.main_window.active_chip_type
            self.chip_type = new_id

            self.setBrush(QColor(colornames[self.chip_type]))  # optional visual feedback
            self.update_probe_points()

        elif getattr(self.main_window, 'is_probing_mode', False):
            self.main_window.selected_chip = self
            self.main_window._on_chip_selected()
            self.main_window.confirm_btn.setEnabled(True)


        else:
            super().mousePressEvent(event)
    
    def set_irl_coords(self, x, y):
        self.irl_coordinates = np.array([[x],[y]])

class serial_handler():
    def __init__(self):
        self.ser = None
        self.ser_name = None


    def list_serial_ports(self):
        ports = list(serial.tools.list_ports.comports())
        ports = [port for port in ports if "Bluetooth" not in str(port)]
        return [str(port.device) for port in ports]
    
    def connect_serial_port(self, port):
        try:
            if self.ser!=None:
                self.ser.close()
            self.ser = serial.Serial(port, 115200, timeout=1)
            time.sleep(2)


        except serial.SerialException as e:
            return False

        finally:
            if self.ser!=None and self.ser.is_open:
                self.ser_name = port
                return True
            
    def check_serial(self):
        if self.ser is not None:
      
            ports = self.list_serial_ports()
            yeet = False
            for port in ports:
                if self.ser_name == port:
                    yeet = True
            
            if yeet is False:
                self.ser.close()

            return yeet
        
    def write(self, message):
        self.ser.write(message.encode())
        self.ser.flush()

    def flush(self):
        self.ser.flush()
        self.ser.reset_input_buffer()

    def read(self):
        return self.ser.readline().decode().strip()

    def char_read(self):
        return self.ser.read(1).decode()

    def in_waiting(self):
        return self.ser.in_waiting

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        pygame.init()
        pygame.joystick.init()

        self.list = [3.04, 2, 4, 6, 8, 6, 4, 2]

        # Set up UI

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.ser = serial_handler()

        self.probe_handler = probe_handler(self.ser)

        self.camera = camera_handler(self.probe_handler, self)

       

        self.drop_dist = 0

        self.connected = False
        self.ser_name = None
        self.gamepad_connected = False
        self.joystick = None

        self.manual = False

        self.show_camera = False


        self.active_chip_type = None
        self.is_assigning_mode = False

        # Attach functions to buttons

        self.ui.ser_connect.clicked.connect(self.connect_serial_port)
        self.ui.controller_connect.clicked.connect(self.find_gamepads)
        self.ui.manual_drive.clicked.connect(self.manual_set)
        self.ui.cam_show.clicked.connect(self.camera_set)

        self.ui.set_align_1.clicked.connect(self.align_1)
        self.ui.set_align_2.clicked.connect(self.align_2)
        self.ui.confirm_align.clicked.connect(self.apply_transformation)

        self.ui.wafer_create.clicked.connect(self.create_wafer)
        self.ui.add_new_chip_type.clicked.connect(self.create_chip_type)
        self.ui.edit_selected_chip_type.clicked.connect(self.edit_chip_type)

        self.ui.assign_chip_to_wafer.clicked.connect(self.assign_chip_type)
        
        self.ui.probe_individual.clicked.connect(self.probe_single_chip)
        self.ui.Set_drop_height.clicked.connect(self.drop_test)
        self.ui.export_2.clicked.connect(self.export)
        
        self.ui.see_resistance.clicked.connect(self.check_single_chip)
        self.ui.pushButton_2.clicked.connect(self.connect_meter)
        self.ui.MultimeterAddress.setText(f"{config["device"]["address"]}")
        self.ui.cam_input.setText(f"{config["camera"]["default_cam"]}")
        self.ui.probe_all.clicked.connect(self.probe_all)
        # self.ui.transformed_move.clicked.connect(self.manual_move)
        self.ui.visualize_wafer.clicked.connect(self.visualize_all)


    def connect_meter(self):
        if self.ui.MultimeterAddress.text() != None:
            self.camera.connect_meter(self.ui.MultimeterAddress.text())
        else:
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText("Please enter a VISA Address for your device")
            msg.exec()


    def gotomark1(self):
        pass

    def gotomark2(self):
        pass
    
    def printloc(self):
        print(self.probe_handler.find_location())

    def start_camera(self, cam_num):
        self.camera.start_camera(cam_num)

    def update_camera(self):
        self.camera.update_camera()

    def manual_set(self):
        if self.connected:
            self.manual = not self.manual

        if self.manual:
            self.ui.manual_drive.setText("Disable Manual Drive")
        else:
            self.ui.manual_drive.setText("Enable Manual Drive")
    
    def camera_set(self):
        self.show_camera = not self.show_camera

    def list_serial_ports(self):
        self.ui.ser_dropdown.clear()
        self.ui.ser_dropdown.addItems(self.ser.list_serial_ports())

    def connect_serial_port(self):
        selected_text = str(self.ui.ser_dropdown.currentText())

        if self.ser.connect_serial_port(selected_text):
            msg = QMessageBox()
            msg.setWindowTitle("Connected")
            msg.setText("COM connection work :]")
            self.ui.label.setText("Connected:")
            msg.exec()
            self.connected = True
            self.homing()

        else:
            msg = QMessageBox()
            msg.setWindowTitle("Failed to Connect")
            msg.setText("COM connection didn't work :[")
            self.ui.label.setText("COM PORTS: ")
            msg.exec()

    def check_serial(self):
        if self.ser.check_serial() is False:
            self.connected = False
            self.ui.label.setText("COM PORT: ")  

    def homing(self):
        if self.connected:     
            self.probe_handler.homing()

    def find_gamepads(self):
        if pygame.joystick.get_count() == 0:
            self.joystick = None
            self.ui.controller_status.setText("No controller connected")
            self.gamepad_connected = False
        else:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            self.ui.controller_status.setText(self.joystick.get_name())
            self.ui.gamepad_connected = True

    def game_pad_move(self):
        mult = 0.06
        if self.manual:
            
            zboost = 1
            pushed = False
            if self.joystick != None:
                pygame.event.pump()
                
                if self.joystick.get_button(int(config["keybinds"]["z-boost"])):
                    zboost = 10

                if self.joystick.get_button(int(config["keybinds"]["speed-mode-1"])):
                    mult = 0.5
                    pushed = True
                elif self.joystick.get_button(int(config["keybinds"]["speed-mode-2"])):
                    mult = 3
                    pushed = True
                else:
                    mult = 0.06 
            if not pushed:
                if keyboard.is_pressed("shift"):
                    mult = 0.5
                elif keyboard.is_pressed("ctrl"):
                    mult = 3
                else:
                    mult = 0.06
            
            y_axis = 0
            x_axis = 0

            if self.joystick!= None:
                y_axis = -self.joystick.get_axis(int((config["keybinds"]["y-axis"])))
                x_axis = self.joystick.get_axis(int(config["keybinds"]["x-axis"]))
            
                if abs(x_axis) < 0.05:
                    x_axis = 0
                if abs(y_axis) < 0.05:
                    y_axis = 0

            if keyboard.is_pressed('w'):
                y_axis = 1
            elif keyboard.is_pressed('s'):
                y_axis = -1

            if keyboard.is_pressed('a'):
                x_axis = -1
            elif keyboard.is_pressed('d'):
                x_axis = 1

            if abs(x_axis) > 0.1 or abs(y_axis) > 0.1:
                self.probe_handler.rel_move(x=x_axis * mult, y=y_axis * mult, z=0, feed=500)
                time.sleep(0.2)  # prevent spamming

                   
            if self.joystick != None:
                

                if self.joystick.get_button(int(config["keybinds"]["z-down-button"])):
                    self.probe_handler.rel_move(0,0,-0.04 * zboost, 500)
                    time.sleep(0.25)

                if self.joystick.get_button(int(config["keybinds"]["z-up-button"])):
                    self.probe_handler.rel_move(0,0,0.04 * zboost, 500)
                    time.sleep(0.25)

                

            if keyboard.is_pressed("e"):
                self.probe_handler.rel_move(0,0,-0.04 * mult, 500)
                time.sleep(0.25)
            if keyboard.is_pressed("q"):
                    self.probe_handler.rel_move(0,0,0.04 * mult, 500)
                    time.sleep(0.25)
            

    def align_1(self):
        self.camera.align_1()
    
    def align_2(self):
        self.camera.align_2()

    def apply_transformation(self):
        self.camera.apply_transformation()

    def wafer_populate(self, list, irlsize):
        scene = QGraphicsScene()
        width = max(len(row) for row in list)
        rowcenter = width-1 * 16

        for row in range(len(list)):
            
            if len(list[row])%2==1:
                offset = rowcenter - (len(list[row])//2) * 32
            else:
                offset = rowcenter - ((len(list[row])/2) - 0.5) * 32
            
            y = row * 32

            for col in range(len(list[row])):
                rowcol = np.array([[row],[col]])
                chip = wafer_chip(offset, y, 30, list[row][col], irlsize, self, rowcol)

                chip.set_irl_coords((offset - rowcenter)/32 * irlsize, ((len(list)-1)/2.0 - row) * irlsize)
                scene.addItem(chip)

                # print(chip.pos())
                offset = offset + 32

        self.ui.graphicsView.setScene(scene)

    def create_wafer(self):
        global highest_id
        array = []
        file_path, _ = QFileDialog.getOpenFileName(
        parent=None,
        caption="Open Wafer txt file",
        filter="txt files (*.txt);;All Files (*)"
        )
        
        self.ui.listWidget.clear()

        Hannah = False
        chip_id = None
        path = None
        preset_paths = {}

        with open(file_path, 'r') as file:
            for line in file:
                if line.strip() == 'preset paths':
                    Hannah = True
                elif line.strip() and Hannah == False:  # Skip empty lines:
                    numbers = [int(num.strip()) for num in line.strip().split(',') if num.strip()]
                    array.append(numbers)
                elif Hannah == True:
                    if ',' not in line:
                        continue

                    chip_id_str, path_str, name = line.split(',', 2)
                    chip_id = int(chip_id_str.strip())
                    path = path_str.strip()
                    name = name.strip()
                    preset_paths[chip_id] = [path,name]

        
        size, ok = QInputDialog.getText(None, "Input", "How many mm is one side of wafer?:")
            
        if ok:
            try:
                size = float(size)
            except ValueError:
                return 
            
            finally:
                unique_types = set()

                for row in array:
                    for num in row:
                        unique_types.add(num)
                for chip_type in unique_types:
                    if chip_type in preset_paths:
                        if preset_paths[chip_type][0] != "None":
                            item = wafer_chip_type(preset_paths[chip_type][1], chip_type, Path(preset_paths[chip_type][0]))
                        else:
                            item = wafer_chip_type(preset_paths[chip_type][1], chip_type, None)

                        item.setForeground(QBrush(QColor(colornames[chip_type])))

                    else:
                        item = wafer_chip_type(f"Chip {chip_type}", chip_type)
                        item.setForeground(QBrush(QColor(colornames[chip_type])))

                    self.ui.listWidget.addItem(item)
                    highest_id+=1

                    self.wafer_populate(array, size)


    def edit_chip_type(self):
        window = QDialog(self)
        window.setWindowTitle(f"Edit {self.ui.listWidget.currentItem().text()}")
        layout = QVBoxLayout(window)

        # Name input
        layout.addWidget(QLabel("Chip Name:"))
        name_input = QLineEdit()
        name_input.setText(self.ui.listWidget.currentItem().text())
        layout.addWidget(name_input)

        # GDS file selector
        gds_path = None
        gds_label = QLabel(f"{self.ui.listWidget.currentItem().gds_path}")
        layout.addWidget(gds_label)

        def getfile():
            nonlocal gds_path
            file_path, _ = QFileDialog.getOpenFileName(window, "Select GDS File", "", "GDS Files (*.gds);;All Files (*)")
            if file_path:
                gds_path = file_path
                gds_label.setText(file_path)

        gds_button = QPushButton("Select GDS File")
        gds_button.clicked.connect(getfile)
        layout.addWidget(gds_button)

        # Confirm button
        def accept():
            item = self.ui.listWidget.currentItem()
            item.setText(name_input.text())
            item.gds_path = gds_path  # you may want to store this elsewhere
            if gds_path is not None:
                item.generate_points_to_probe()
            window.accept()

        confirm_button = QPushButton("Save")
        confirm_button.clicked.connect(accept)
        layout.addWidget(confirm_button)

        window.setLayout(layout)
        window.exec()

    def create_chip_type(self):
        global highest_id
        window = QDialog(self)
        window.setWindowTitle("create a new chip type :D")
        layout = QVBoxLayout(window)

        # Name input
        layout.addWidget(QLabel("Chip Name:"))
        name_input = QLineEdit()
        name_input.setText("choose a funny name for your new chip type!")
        layout.addWidget(name_input)

        # GDS file selector
        gds_path = None
        gds_label = QLabel("No file selected.")
        layout.addWidget(gds_label)

        def getfile():
            nonlocal gds_path
            file_path, _ = QFileDialog.getOpenFileName(window, "Select GDS File", "", "GDS Files (*.gds);;All Files (*)")
            if file_path:
                gds_path = file_path
                gds_label.setText(file_path)

        gds_button = QPushButton("Select GDS File")
        gds_button.clicked.connect(getfile)
        layout.addWidget(gds_button)

        # Confirm button
        def accept():
            global highest_id
            item = wafer_chip_type(name_input.text(), highest_id+1)
            highest_id += 1
            item.gds_path = gds_path
            if gds_path is not None:
                item.generate_points_to_probe()
            self.ui.listWidget.addItem(item)
            window.accept()
            

        confirm_button = QPushButton("Save")
        confirm_button.clicked.connect(accept)
        layout.addWidget(confirm_button)

        window.setLayout(layout)
        window.exec()

    def assign_chip_type(self):
        dialog = QDialog()
        dialog.setWindowTitle("Assign type to die on wafer")

        layout = QVBoxLayout(dialog)


        if self.ui.listWidget.currentItem() is not None:
            end = QPushButton("end assigning")
            layout.addWidget(end)

            layout.addWidget(QLabel(f"Currently assigning {self.ui.listWidget.currentItem().text()}"))
            self.active_chip_type = self.ui.listWidget.currentItem().id
            self.is_assigning_mode = True  # flag for later


            def end_assignment():
                self.active_chip_type = None
                self.is_assigning_mode = False
                dialog.accept()

            end.clicked.connect(end_assignment)
            dialog.show()

        
        else:
            layout.addWidget(QLabel("don't be indecisive! choose a chip type first :]"))
            dialog.exec()

    def probe_single_chip(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Select a Chip to Probe")
        layout = QVBoxLayout(dialog)
        
        info = QLabel("Click a chip on the wafer to probe.")
        layout.addWidget(info)

        # Container for checkboxes (will be populated after chip selection)
        checkbox_frame = QFrame()
        checkbox_layout = QVBoxLayout(checkbox_frame)
        checkbox_label = QLabel("Select layers to probe:")
        checkbox_layout.addWidget(checkbox_label)
        layout.addWidget(checkbox_frame)
        
        # Initially hide the checkbox frame
        checkbox_frame.hide()

        self.confirm_btn = QPushButton("Confirm")
        self.confirm_btn.setEnabled(False)  # only enable after selection
        layout.addWidget(self.confirm_btn)

        # Flag to enable chip selection mode
        self.is_probing_mode = True
        self.selected_chip = None
        self.layer_checkboxes = {}  # Store checkboxes by layer index
        
        def populate_layer_checkboxes():
            """Populate checkboxes based on available layers in selected chip type"""
            if self.selected_chip is None:
                return
                
            chip_type = self.selected_chip.chip_type
            
            # Find the matching category and get probe_path
            probe_path = None
            for index in range(self.ui.listWidget.count()):
                category = self.ui.listWidget.item(index)
                if category.id == chip_type:
                    probe_path = category.points_to_probe
                    print(f"raw probe path{probe_path}")
                    break
            
            if probe_path is None or probe_path.shape[0] < 3:
                return
                
            # Get unique layer indices from row 2 (0-indexed)
            unique_layers = np.unique(probe_path[2, :]).astype(int)
            
            # Clear existing checkboxes
            for checkbox in self.layer_checkboxes.values():
                checkbox.deleteLater()
            self.layer_checkboxes.clear()
            
            # Create checkboxes for each layer
            for layer_idx in sorted(unique_layers):
                layer_num = layer_idx + 50  # Convert back to actual layer number
                checkbox = QCheckBox(f"Layer {layer_num} (Index {layer_idx})")
                checkbox.setChecked(True)  # All checked by default
                self.layer_checkboxes[layer_idx] = checkbox
                checkbox_layout.addWidget(checkbox)
            
            # Show the checkbox frame
            checkbox_frame.show()
            dialog.adjustSize()  # Resize dialog to fit new content

        def confirm_selection():
            dialog.accept()
            self.is_probing_mode = False

            chip_type = self.selected_chip.chip_type

            # Get the full probe_path
            probe_path = None
            for index in range(self.ui.listWidget.count()):
                category = self.ui.listWidget.item(index)
                if category.id == chip_type:
                    probe_path = category.points_to_probe
                    print(f"Raw probe_path from category: {probe_path}")
                    break
            
            if probe_path is not None:
                # Filter probe_path based on selected checkboxes
                selected_layers = {layer_idx for layer_idx, checkbox in self.layer_checkboxes.items() 
                                if checkbox.isChecked()}
                
                if selected_layers:
                    # Create mask for selected layers
                    layer_mask = np.isin(probe_path[2, :], list(selected_layers))
                    filtered_probe_path = probe_path[:, layer_mask]
                    print(f"After filtering: {filtered_probe_path}")
                else:
                    # If no layers selected, use empty array
                    filtered_probe_path = np.empty((probe_path.shape[0], 0))
                
                sorted_path = self.sort_probe_path(filtered_probe_path)
                print(f"After sorting: {sorted_path}")
                sorted_path = sorted_path/1000
                size = self.selected_chip.irl_size
                center = self.selected_chip.irl_coordinates
                self.camera.plot_die(die_size_mm=size, 
                                    points_to_probe=sorted_path,
                                    die_center=center,
                                    die_object=self.selected_chip)
        # Override the chip selection to populate checkboxes
        original_chip_selected = getattr(self, '_on_chip_selected', None)
        
        def on_chip_selected():
            if original_chip_selected:
                original_chip_selected()
            populate_layer_checkboxes()
            self.confirm_btn.setEnabled(True)
        
        self._on_chip_selected = on_chip_selected

        self.confirm_btn.clicked.connect(confirm_selection)

        # Save reference so we can enable button when clicked
        self._probe_dialog = dialog
        dialog.show()

    def probe_all(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Select a Chip type to probe")
        layout = QVBoxLayout(dialog)
        self.selected_type = None
        
        info = QLabel("Click a chip type to probe.")
        layout.addWidget(info)

        # Container for checkboxes (will be populated after chip type selection)
        checkbox_frame = QFrame()
        checkbox_layout = QVBoxLayout(checkbox_frame)
        checkbox_label = QLabel("Select types to probe:")
        checkbox_layout.addWidget(checkbox_label)
        layout.addWidget(checkbox_frame)
        
        # Initially hide the checkbox frame
        checkbox_frame.hide()

        confirm_btn = QPushButton("Confirm")
        confirm_btn.setEnabled(False)  # only enable after selection
        layout.addWidget(confirm_btn)

        self.type_checkboxes = {}  # Store checkboxes by type index

        def populate_type_checkboxes():
            """Populate checkboxes based on available types in selected chip category"""
            if self.selected_type is None:
                return
                
            probe_path = self.selected_type.points_to_probe
            print(f"raw probe path: {probe_path}")
            
            if probe_path is None or probe_path.shape[0] < 3:
                return
                
            # Get unique type indices from row 3 (0-indexed)
            unique_types = np.unique(probe_path[2, :]).astype(int)
            
            # Clear existing checkboxes
            for checkbox in self.type_checkboxes.values():
                checkbox.deleteLater()
            self.type_checkboxes.clear()
            
            # Create checkboxes for each type
            for type_idx in sorted(unique_types):
                checkbox = QCheckBox(f"Type {type_idx}")
                checkbox.setChecked(True)  # All checked by default
                self.type_checkboxes[type_idx] = checkbox
                checkbox_layout.addWidget(checkbox)
            
            # Show the checkbox frame
            checkbox_frame.show()
            dialog.adjustSize()  # Resize dialog to fit new content

        def on_chip_selected(item):
            self.selected_type = item  # Assume `item` is a custom QListWidgetItem with `chip_type`, etc.
            populate_type_checkboxes()
            confirm_btn.setEnabled(True)

        def confirm_selection():
            dialog.accept()
            
            # Get the full probe_path
            probe_path = self.selected_type.points_to_probe
            
            if probe_path is not None:
                # Filter probe_path based on selected checkboxes
                selected_types = {type_idx for type_idx, checkbox in self.type_checkboxes.items() 
                                if checkbox.isChecked()}
                
                if selected_types:
                    # Create mask for selected types
                    type_mask = np.isin(probe_path[2, :], list(selected_types))
                    filtered_probe_path = probe_path[:, type_mask]
                    print(f"After filtering: {filtered_probe_path}")
                else:
                    # If no types selected, use empty array
                    filtered_probe_path = np.empty((probe_path.shape[0], 0))
                
                # Scale the coordinates
                filtered_probe_path[:2,:] = filtered_probe_path[:2,:] / 1000

                for item in self.ui.graphicsView.scene().items():
                    if isinstance(item, wafer_chip):
                        if item.chip_type == self.selected_type.id:
                            size = item.irl_size
                            center = item.irl_coordinates
                            tylerthecreator = self.camera.plot_die(
                                die_size_mm=size,
                                points_to_probe=self.sort_probe_path(filtered_probe_path),
                                die_center=center,
                                die_object=item
                            )

                            if tylerthecreator == 'bork':
                                break

        # Connect the list widget click
        self.ui.listWidget.itemClicked.connect(on_chip_selected)
        confirm_btn.clicked.connect(confirm_selection)

        self._probe_dialog = dialog
        self._probe_confirm_btn = confirm_btn

        dialog.show()  # Use exec_() instead of show() to block until closed


    def sort_probe_path(self, array):
        sorted = array[:, np.argsort(array[1])[::-1]]  # sort Y descending
        row_start = 0
        currently_right = True

        for i in range(1, sorted.shape[1]):
            y = sorted[1, i]
            if abs(y - sorted[1, row_start]) > 0.02:
                row_end = i
                sub = sorted[:, row_start:row_end]
                if currently_right:
                    sorted_sub = sub[:, np.argsort(sub[0])]  # sort by X ascending
                else:
                    sorted_sub = sub[:, np.argsort(sub[0])[::-1]]  # sort by X descending
                
                sorted[:, row_start:row_end] = sorted_sub
                row_start = row_end
                currently_right = not currently_right

        # Final group (end of array)
        sub = sorted[:, row_start:]
        if currently_right:
            sorted_sub = sub[:, np.argsort(sub[0])]
        else:
            sorted_sub = sub[:, np.argsort(sub[0])[::-1]]
        sorted[:, row_start:] = sorted_sub

        return sorted

    def drop_test(self):
        self.camera.set_drop_dist()

    def export(self):
        
        if self.ui.graphicsView.scene().items() == None:
            msg = QMessageBox()
            msg.setWindowTitle("Hold Up")
            msg.setText("You haven't made a wafer to export yet")
            msg.exec()

        else:
            file_path, _ = QFileDialog.getSaveFileName(None, "Save File", "new_wafer.txt", "Text Files (*.txt)")

            if file_path:
                with open(file_path, "w") as f:
                    current_row = self.ui.graphicsView.scene().items()[0].irl_coordinates[1,0]
                    for chip in self.ui.graphicsView.scene().items():
                        if chip.irl_coordinates[1,0] == current_row:
                            f.write(f"{chip.chip_type},")
                        if chip.irl_coordinates[1,0] != current_row:
                            f.write("\n")
                            f.write(f"{chip.chip_type},")
                            current_row = chip.irl_coordinates[1,0]

                    f.write("\n")
                    f.write("preset paths")
                    f.write("\n")


                    for i in range(self.ui.listWidget.count()):
                        type = self.ui.listWidget.item(i)
                        f.write(f"{type.id},{type.gds_path},{type.text()}")
                        f.write("\n")                    

    def check_single_chip(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Select a Chip to view info for")
        layout = QVBoxLayout(dialog)
        
        info = QLabel("click on a chip to see its deepest secrets.")
        layout.addWidget(info)

        confirm_btn = QPushButton("Confirm")
        confirm_btn.setEnabled(False)  # only enable after selection
        layout.addWidget(confirm_btn)

        # Flag to enable chip selection mode
        self.is_probing_mode = True
        self.selected_chip = None
        
        def on_chip_selected():
            confirm_btn.setEnabled(True)

        self._on_chip_selected = on_chip_selected

        def confirm_selection():
            dialog.accept()

            self.is_probing_mode = False

            chip_type = self.selected_chip.chip_type

            for index in range(self.ui.listWidget.count()):
                category = self.ui.listWidget.item(index)
                if category.id == chip_type:
                    break

            self.viewer = ChipViewer(category.gds_path, category.text(), self.selected_chip.rowcol, self.selected_chip.probe_info)

        confirm_btn.clicked.connect(confirm_selection)

        self.confirm_btn = confirm_btn
        # Save reference so we can enable button when clicked
        self._probe_dialog = dialog
        self.confirm_btn = confirm_btn

        dialog.show()


    def visualize_all(self):
        self.viewer = WaferVisualizer(self.ui.graphicsView.scene(), self.ui.listWidget, self.camera)


    def manual_move(self):
        text, ok = QInputDialog.getText(None, "Input", "enter theoretical coords of this box in x,y format:")
        if ok:
            x,y = text.split(",")
            try:
                x = int(x)
                y = int(y)
            except ValueError:
                return
            
            xy = np.array([[x],[y]])
            self.probe_handler.transfomred_move(xy)
    # def probe_all