from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QGraphicsView, QGraphicsScene, QGraphicsTextItem, 
    QGraphicsPixmapItem, QGraphicsRectItem, QSlider, QFileDialog,
    QLabel, QLineEdit, QDialog, QFormLayout, QDialogButtonBox
)
from PySide6.QtGui import QPixmap, QWheelEvent, QBrush, QColor, QPainter, QLinearGradient
from PySide6.QtCore import Qt, QPointF, QRectF
import sys
import math
import numpy as np
import gdspy


class MinMaxDialog(QDialog):
    def __init__(self, current_min, current_max, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set Heat Map Range")
        self.setModal(True)
        
        layout = QFormLayout(self)
        
        self.min_edit = QLineEdit(str(current_min))
        self.max_edit = QLineEdit(str(current_max))
        
        layout.addRow("Minimum Value:", self.min_edit)
        layout.addRow("Maximum Value:", self.max_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                 QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        

    def get_values(self):
        try:
            min_val = float(self.min_edit.text())
            max_val = float(self.max_edit.text())
            return min_val, max_val
        except ValueError:
            return None, None


class ZoomableGraphicsView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)

        self.setRenderHint(self.renderHints() | 
                   QPainter.RenderHint.Antialiasing | 
                   QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.zoom_level = 0

    def wheelEvent(self, event: QWheelEvent):
        zoom_factor = 1.15
        if event.angleDelta().y() > 0:
            zoom = zoom_factor
            self.zoom_level += 1
        else:
            zoom = 1 / zoom_factor
            self.zoom_level -= 1

        self.scale(zoom, zoom)


class Junction(QGraphicsRectItem):
    def __init__(self, rectf, resistance, parent_chip, window, gds_coords):
        super().__init__(rectf)
        self.resistance = resistance
        self.window = window
        self.parent_chip = parent_chip
        self.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.gds_coords = gds_coords

    def mousePressEvent(self, event):
        # get reference to main app from scene or item

        if getattr(self.window, 'is_assigning_mode', False):
            self.window.selected_junction = self
            self.window.confirm_button.setEnabled(True)
        else:
            super().mousePressEvent(event)


class WaferVisualizer(QMainWindow):
    def __init__(self, chipscene, chip_list,camera):
        super().__init__()
        self.chip_list = chip_list
        self.chipscene = chipscene
        self.setWindowTitle("Wafer Chip Visualizer")
        self.setGeometry(100, 100, 1400, 800)  # Made wider for sidebar
        self.camera = camera
        # Heat map variables
        self.heatmap_enabled = False
        self.heatmap_min = 0
        self.heatmap_max = 100
        self.all_junctions = []  # Store all junctions for heat map updates

        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # QGraphicsScene and View
        self.scene = QGraphicsScene()
        self.view = ZoomableGraphicsView(self.scene)
        main_layout.addWidget(self.view, stretch=4)

        # Sidebar layout
        sidebar = QVBoxLayout()
        main_layout.addLayout(sidebar, stretch=1)

        # Heat map controls
        heatmap_label = QLabel("Heat Map Controls")
        heatmap_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        sidebar.addWidget(heatmap_label)

        # Toggle heat map button
        self.showheatmap = QPushButton("Show Heat Map")
        self.showheatmap.clicked.connect(self.toggle_heatmap)
        sidebar.addWidget(self.showheatmap)

        # Heat map adjustment buttons
        self.auto_scale_btn = QPushButton("Auto Scale")
        self.auto_scale_btn.clicked.connect(self.auto_scale_heatmap)
        sidebar.addWidget(self.auto_scale_btn)

        self.set_minmax_btn = QPushButton("Set Min/Max")
        self.set_minmax_btn.clicked.connect(self.set_minmax_dialog)
        sidebar.addWidget(self.set_minmax_btn)

        # Heat map legend
        legend_label = QLabel("Heat Map Legend")
        legend_label.setStyleSheet("font-weight: bold; margin-top: 20px;")
        sidebar.addWidget(legend_label)

        # Create heat map gradient view
        self.legend_scene = QGraphicsScene()
        self.legend_view = QGraphicsView(self.legend_scene)
        self.legend_view.setFixedHeight(100)
        self.legend_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.legend_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sidebar.addWidget(self.legend_view)

        # Min/Max value labels
        self.max_label = QLabel(f"Max: {self.heatmap_max}")
        self.min_label = QLabel(f"Min: {self.heatmap_min}")
        sidebar.addWidget(self.max_label)
        sidebar.addWidget(self.min_label)

        # Other controls
        controls_label = QLabel("Other Controls")
        controls_label.setStyleSheet("font-weight: bold; margin-top: 20px;")
        sidebar.addWidget(controls_label)

        # Reprobe button
        self.reprobe_btn = QPushButton("Reprobe Junction")
        sidebar.addWidget(self.reprobe_btn)

        # Add stretch to push everything to top
        sidebar.addStretch()

        # Initialize legend
        self.update_legend()
        
        self.wafer_populate()
        self.show()

    def resistance_to_color(self, resistance):
        """Convert resistance value to color based on heat map range"""
        if resistance is None or resistance < 0:
            return QColor(128, 128, 128)  # Gray for no data
        
        # Normalize resistance to 0-1 range
        if self.heatmap_max == self.heatmap_min:
            normalized = 0.5
        else:
            normalized = (resistance - self.heatmap_min) / (self.heatmap_max - self.heatmap_min)
            normalized = max(0, min(1, normalized))  # Clamp to 0-1
        
        # Create red-green gradient (red = high, green = low)
        red = int(255 * normalized)
        green = int(255 * (1 - normalized))
        blue = 0
        
        return QColor(red, green, blue)

    def get_heatmap_position(self, value):
        """
        Calculate where a value falls on the heatmap (0.0 to 1.0)
        Returns None if value is outside the range
        """
        if value is None:
            return None
        
        if self.heatmap_max == self.heatmap_min:
            return 0.5
        
        position = (value - self.heatmap_min) / (self.heatmap_max - self.heatmap_min)
        
        # Return position even if outside range, but you can clamp it if needed
        return position

    def update_legend(self):
        """Update the heat map legend gradient and labels"""
        self.legend_scene.clear()
        
        # Create gradient rectangle
        gradient_rect = QGraphicsRectItem(0, 0, 200, 30)
        
        # Create linear gradient from green to red
        gradient = QLinearGradient(0, 0, 200, 0)
        gradient.setColorAt(0, QColor(0, 255, 0))    # Green at start (low values)
        gradient.setColorAt(1, QColor(255, 0, 0))    # Red at end (high values)
        
        gradient_rect.setBrush(QBrush(gradient))
        self.legend_scene.addItem(gradient_rect)
        
        # Add value labels on the gradient
        min_text = QGraphicsTextItem(f"{self.heatmap_min:.1f}")
        min_text.setPos(-5, 35)
        min_text.setDefaultTextColor(QColor("black"))
        self.legend_scene.addItem(min_text)
        
        max_text = QGraphicsTextItem(f"{self.heatmap_max:.1f}")
        max_text.setPos(160, 35)
        max_text.setDefaultTextColor(QColor("black"))
        self.legend_scene.addItem(max_text)
        
        # Update labels
        self.max_label.setText(f"Max: {self.heatmap_max:.1f}")
        self.min_label.setText(f"Min: {self.heatmap_min:.1f}")
        
        # Fit the legend in view
        self.legend_view.fitInView(self.legend_scene.itemsBoundingRect(), Qt.AspectRatioMode.IgnoreAspectRatio)

    def toggle_heatmap(self):
        """Toggle heat map visualization on/off"""
        self.heatmap_enabled = not self.heatmap_enabled
        
        if self.heatmap_enabled:
            self.showheatmap.setText("Hide Heat Map")
            self.apply_heatmap_colors()
        else:
            self.showheatmap.setText("Show Heat Map")
            self.reset_junction_colors()

    def apply_heatmap_colors(self):
        """Apply heat map colors to all junctions"""
        for junction in self.all_junctions:
            color = self.resistance_to_color(junction.resistance)
            junction.setBrush(QBrush(color))

    def reset_junction_colors(self):
        """Reset all junctions to default color"""
        for junction in self.all_junctions:
            junction.setBrush(QBrush(QColor(180, 240, 200)))

    def auto_scale_heatmap(self):
        """Automatically scale heat map to min/max of all resistance values"""
        resistances = [j.resistance for j in self.all_junctions if j.resistance is not None]
        
        if resistances:
            self.heatmap_min = min(resistances)
            self.heatmap_max = max(resistances)
            self.update_legend()
            
            if self.heatmap_enabled:
                self.apply_heatmap_colors()

    def set_minmax_dialog(self):
        """Open dialog to manually set min/max values"""
        dialog = MinMaxDialog(self.heatmap_min, self.heatmap_max, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            min_val, max_val = dialog.get_values()
            
            if min_val is not None and max_val is not None and min_val < max_val:
                self.heatmap_min = min_val
                self.heatmap_max = max_val
                self.update_legend()
                
                if self.heatmap_enabled:
                    self.apply_heatmap_colors()

    def duplicate_and_scale_chip(self, chip_item, scale_factor):
        # Use the actual visual bounds
        scene_rect = chip_item.sceneBoundingRect()
        
        new_chip = QGraphicsRectItem(0, 0, 
                                    chip_item.rect().width() * scale_factor,
                                    chip_item.rect().height() * scale_factor)
        new_chip.setBrush(QColor(192,192,192))
        
        # Use the top-left of the scene bounding rect
        scaled_x = scene_rect.x() * scale_factor
        scaled_y = scene_rect.y() * scale_factor
        new_chip.setPos(scaled_x, scaled_y)
        
        return new_chip

    def wafer_populate(self):
        scene = self.chipscene
        for item in scene.items():
            new_chip = self.duplicate_and_scale_chip(item, 10)
            self.scene.addItem(new_chip)
            for index in range(self.chip_list.count()):
                category = self.chip_list.item(index)
                if category.id == item.chip_type:
                    if category.gds_path != None and category.gds_path != "None":
                        self.load_gds(category.gds_path, new_chip.pos(),item, item.probe_info)

    def load_gds(self, gds_path, center_offset,parent_chip, resistance_map=None, target_layer=50):
        lib = gdspy.GdsLibrary(infile=gds_path)
        cell = lib.top_level()[0]
        if isinstance(center_offset, QPointF):
            dx = center_offset.x() + 150
            dy = center_offset.y() + 150

        # Group polygons by (layer, datatype)
        poly_dict = cell.get_polygons(by_spec=True)

        for (layer, datatype), polygons in poly_dict.items():
            if layer != target_layer:
                continue  # skip other layers

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
                
                # Create junction with rectangle geometry only (no position in constructor)
                junction = Junction(QRectF(0, 0, w/10, h/10), None, parent_chip=parent_chip, window=self, gds_coords=centroid)
                junction.setBrush(QBrush(QColor(180, 240, 200)))
                
                # Set position using setPos for proper scene positioning
                junction_x = x/10 + dx
                junction_y = (-y - h)/10 + dy
                junction.setPos(junction_x, junction_y)
                
                self.scene.addItem(junction)
                self.all_junctions.append(junction)  # Store for heat map

                if resistance_map is not None and resistance_map.size > 0:
                    # Use tolerance-based matching instead of exact equality
                    tolerance = 1e-6  # Adjust this value as needed
                    
                    # Calculate distances to all points in resistance_map
                    distances = np.sqrt((resistance_map[0] - centroid[0])**2 + 
                                    (resistance_map[1] - centroid[1])**2)
                    
                    # Find the closest match
                    min_distance_idx = np.argmin(distances)
                    min_distance = distances[min_distance_idx]
                    
                    if min_distance < tolerance:
                        resistance = resistance_map[2, min_distance_idx]
                        junction.resistance = resistance
                        
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
                        
                        # Position text at junction center using setPos
                        # Get junction center position in scene coordinates
                        junction_center_x = junction_x + (w/10) / 2
                        junction_center_y = junction_y + (h/10) / 2
                        
                        # Offset text slightly (adjust these offsets as needed)
                        text_offset_x = -18  # Adjust for text centering
                        text_offset_y = -10  # Adjust for text centering
                        
                        text_item.setPos(junction_center_x + text_offset_x, 
                                    junction_center_y + text_offset_y)
                        
                        self.scene.addItem(text_item)
                    else:
                        # Optionally add a "No data" label
                        text_item = QGraphicsTextItem("No data")
                        text_item.setDefaultTextColor(QColor("red"))
                        
                        # Position "No data" text similarly
                        junction_center_x = junction_x + (w/10) / 2
                        junction_center_y = junction_y + (h/10) / 2
                        
                        text_item.setPos(junction_center_x - 15, junction_center_y - 10)
                        self.scene.addItem(text_item)

    def probe_single_junction(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Individual Junction Probe")
        layout = QVBoxLayout(dialog)
        
        info = QLabel("Click on Junction to reprobe")
        layout.addWidget(info)

        self.confirm_btn = QPushButton("Confirm")
        self.confirm_btn.setEnabled(False)  # only enable after selection
        layout.addWidget(self.confirm_btn)

        # Flag to enable chip selection mode
        self.is_assigning_mode = True
        self.selected_junction = None
        def confirm_selection():
            dialog.accept()

            self.is_assigning_mode = False
            die = self.selected_junction.parent_chip
            size = die.irl_size
            chip_type = die.chip_type
            probe_path = die.gds_coords

            center = die.irl_coordinates
            self.camera.plot_die(die_size_mm = size, 
                                 points_to_probe = probe_path, 
                                 die_center = center, 
                                 die_object = die)
        self.confirm_btn.clicked.connect(confirm_selection)
        dialog.show()




        self.confirm_btn.clicked.connect(confirm_selection)

        # Save reference so we can enable button when clicked
        self._probe_dialog = dialog
        

        dialog.show()
