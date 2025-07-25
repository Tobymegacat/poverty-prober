# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'probeGUI.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QGraphicsView, QGridLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMainWindow, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget, QGroupBox, QHBoxLayout, QMessageBox, QScrollArea)


class ZoomableGraphicsView(QGraphicsView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.zoom_factor = 1.15
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            zoom_in = True
        else:
            zoom_in = False

        factor = self.zoom_factor if zoom_in else 1 / self.zoom_factor
        self.scale(factor, factor)


class HelpDialog(QMessageBox):
    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Help - {title}")
        self.setIcon(QMessageBox.Information)
        self.setText(f"<h3>{title}</h3>")
        self.setDetailedText(content)
        self.setStandardButtons(QMessageBox.Ok)
        self.setDefaultButton(QMessageBox.Ok)


class Ui_MainWindow(object):
    def __init__(self):
        self.help_contents = {
            "setup": """1. Select your COM port from the dropdown
2. Click 'Connect' to establish serial connection
3. Set camera number (usually 1) and click 'Start Cam Feed' to show the cam windows
4. Connect to the probe controller using 'Connect Controller'
5. Enter multimeter VISA address and connect
6. Use 'Enable Manual Drive' for manual probe control""",
            
            "alignment": """1. Use the manual control to drive to your first alignment mark. 

2. Click Set ALignment Mark 1. Click the top left and top right corners of the alignment square.

3. You will see an outline. If you are satisfied with it, hit enter to continue. Otherwise, hit esc to leave.

3. Do the same steps for the second alignment mark

4. Hit confirm alignment to lock in your settings

5. Manually drop your probes, and count the number of steps.

6. Hit the set Z-drop height button. In the prompt, enter the number of steps you counted """,
            
            "wafer_shape": """This visual grid represents your wafer layout:

- Use 'Build Wafer From Text' to import wafer layout

- Use 'Export Wafer to txt' to save current layout
""",
            
            "wafer_setup": """1. Click 'Add New Chip Type' to define chip specifications and GDS files

2. Use 'Edit Selected Chip Type' to modify existing chip definitions. click on a chip type in the scrolling list

3. Click 'Assign Chip To Wafer' to place chips on specific wafer positions. You can click a die in the wafer window to do so

4. Select chips from the list and hit edit to view their properties aswell""",
            
            "probing": """1. Use 'Probe Individual Die' for single chip measurements

2. Use 'Probe all chips of 1 type' for batch measurements

3. Click 'View Single Chip Resistance' to see measurement results

4. Use 'Visualize Entire Wafer' to see the complete wafer view with all chips"""
        }

    def create_help_button(self, section_key):
        help_btn = QPushButton("?")
        help_btn.setFixedSize(25, 25)
        help_btn.setToolTip(f"Help for {section_key}")
        help_btn.clicked.connect(lambda: self.show_help(section_key))
        return help_btn

    def show_help(self, section_key):
        if section_key in self.help_contents:
            title = section_key.replace("_", " ").title()
            content = self.help_contents[section_key]
            dialog = HelpDialog(title, content)
            dialog.exec()

    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(620, 700)  # Reduced height since we'll scroll
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        
        # Create scroll area
        scroll_area = QScrollArea(self.centralwidget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create scrollable content widget
        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)
        
        # Main layout for the central widget (just contains the scroll area)
        central_layout = QVBoxLayout(self.centralwidget)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.addWidget(scroll_area)
        
        # Main layout for scrollable content
        main_layout = QVBoxLayout(scroll_content)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Setup Section
        setup_group = QGroupBox("Setup")
        setup_group.setFont(QFont("Arial", 10, QFont.Bold))
        setup_layout = QGridLayout(setup_group)
        
        # Setup header with help button
        setup_header_layout = QHBoxLayout()
        setup_title = QLabel("SET UP")
        setup_title.setFont(QFont("Arial", 12, QFont.Bold))
        setup_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        setup_help_btn = self.create_help_button("setup")
        setup_header_layout.addWidget(setup_title)
        setup_header_layout.addStretch()
        setup_header_layout.addWidget(setup_help_btn)
        
        # COM Port section
        self.label = QLabel("COM PORTS:")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ser_dropdown = QComboBox()
        self.ser_connect = QPushButton("Connect")
        
        setup_layout.addLayout(setup_header_layout, 0, 0, 1, 3)
        setup_layout.addWidget(self.label, 1, 0, 1, 1)
        setup_layout.addWidget(self.ser_dropdown, 1, 1, 1, 1)
        setup_layout.addWidget(self.ser_connect, 1, 2, 1, 1)
        
        # Camera section
        self.label_3 = QLabel("Camera Num (use 1 usually)")
        self.label_3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cam_input = QLineEdit()
        self.cam_show = QPushButton("Start Cam Feed")
        
        setup_layout.addWidget(self.label_3, 2, 0, 1, 1)
        setup_layout.addWidget(self.cam_input, 2, 1, 1, 1)
        setup_layout.addWidget(self.cam_show, 2, 2, 1, 1)
        
        # Controller section
        self.controller_status = QLabel("No Controller Connected")
        self.controller_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.controller_status.setStyleSheet("QLabel { border: 2px solid gray; padding: 5px; }")
        self.controller_connect = QPushButton("Connect Controller")
        self.manual_drive = QPushButton("Enable Manual Drive")
        
        setup_layout.addWidget(self.controller_status, 3, 0, 1, 1)
        setup_layout.addWidget(self.controller_connect, 3, 1, 1, 1)
        setup_layout.addWidget(self.manual_drive, 3, 2, 1, 1)
        
        # Multimeter section
        self.label_5 = QLabel("Multimeter Visa Address:")
        self.label_5.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.MultimeterAddress = QLineEdit()
        self.pushButton_2 = QPushButton("Connect Multimeter")
        
        setup_layout.addWidget(self.label_5, 4, 0, 1, 1)
        setup_layout.addWidget(self.MultimeterAddress, 4, 1, 1, 1)
        setup_layout.addWidget(self.pushButton_2, 4, 2, 1, 1)
        
        main_layout.addWidget(setup_group)

        # Alignment Section
        alignment_group = QGroupBox("Alignment and Calibration")
        alignment_group.setFont(QFont("Arial", 10, QFont.Bold))
        alignment_layout = QGridLayout(alignment_group)
        
        # Alignment header with help button
        alignment_header_layout = QHBoxLayout()
        alignment_title = QLabel("Alignment and Calibration")
        alignment_title.setFont(QFont("Arial", 12, QFont.Bold))
        alignment_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        alignment_help_btn = self.create_help_button("alignment")
        alignment_header_layout.addWidget(alignment_title)
        alignment_header_layout.addStretch()
        alignment_header_layout.addWidget(alignment_help_btn)
        
        self.set_align_1 = QPushButton("Set Alignment Mark 1")
        self.set_align_2 = QPushButton("Set Alignment Mark 2")
        self.confirm_align = QPushButton("Confirm Alignment")
        self.Set_drop_height = QPushButton("Set Probe Drop Height")
        
        alignment_layout.addLayout(alignment_header_layout, 0, 0, 1, 3)
        alignment_layout.addWidget(self.set_align_1, 1, 0, 1, 1)
        alignment_layout.addWidget(self.set_align_2, 1, 1, 1, 1)
        alignment_layout.addWidget(self.confirm_align, 1, 2, 1, 1)
        alignment_layout.addWidget(self.Set_drop_height, 2, 0, 1, 3)
        
        main_layout.addWidget(alignment_group)

        # Wafer Shape Section
        wafer_shape_group = QGroupBox("Wafer Shape Setup")
        wafer_shape_group.setFont(QFont("Arial", 10, QFont.Bold))
        wafer_shape_layout = QVBoxLayout(wafer_shape_group)
        
        # Wafer shape header with help button
        wafer_shape_header_layout = QHBoxLayout()
        wafer_shape_title = QLabel("Wafer Shape Set Up")
        wafer_shape_title.setFont(QFont("Arial", 12, QFont.Bold))
        wafer_shape_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wafer_shape_help_btn = self.create_help_button("wafer_shape")
        wafer_shape_header_layout.addWidget(wafer_shape_title)
        wafer_shape_header_layout.addStretch()
        wafer_shape_header_layout.addWidget(wafer_shape_help_btn)
        
        # Graphics view and controls
        graphics_controls_layout = QHBoxLayout()
        self.graphicsView = ZoomableGraphicsView()
        self.graphicsView.setMinimumHeight(250)  # Reduced height
        self.graphicsView.setMaximumHeight(300)  # Added max height
        
        wafer_controls_layout = QVBoxLayout()
        self.wafer_create = QPushButton("Build Wafer From Text")
        self.export_2 = QPushButton("Export Wafer to txt")
        wafer_controls_layout.addWidget(self.wafer_create)
        wafer_controls_layout.addWidget(self.export_2)
        wafer_controls_layout.addStretch()
        
        graphics_controls_layout.addWidget(self.graphicsView, 3)
        graphics_controls_layout.addLayout(wafer_controls_layout, 1)
        
        wafer_shape_layout.addLayout(wafer_shape_header_layout)
        wafer_shape_layout.addLayout(graphics_controls_layout)
        
        main_layout.addWidget(wafer_shape_group)

        # Bottom section with two columns
        bottom_layout = QHBoxLayout()
        
        # Chips and Probing Section (Left)
        chips_probing_group = QGroupBox("Chips and Probing")
        chips_probing_group.setFont(QFont("Arial", 10, QFont.Bold))
        chips_probing_layout = QVBoxLayout(chips_probing_group)
        
        # Chips list
        self.listWidget = QListWidget()
        self.listWidget.setMaximumHeight(150)  # Reduced height
        chips_probing_layout.addWidget(self.listWidget)
        
        main_controls_layout = QVBoxLayout()
        
        # Wafer Setup subsection
        wafer_setup_header_layout = QHBoxLayout()
        wafer_setup_title = QLabel("Wafer Set Up")
        wafer_setup_title.setFont(QFont("Arial", 10, QFont.Bold))
        wafer_setup_help_btn = self.create_help_button("wafer_setup")
        wafer_setup_header_layout.addWidget(wafer_setup_title)
        wafer_setup_header_layout.addStretch()
        wafer_setup_header_layout.addWidget(wafer_setup_help_btn)
        
        self.edit_selected_chip_type = QPushButton("Edit Selected Chip Type")
        self.add_new_chip_type = QPushButton("Add New Chip Type")
        self.assign_chip_to_wafer = QPushButton("Assign Chip To Wafer")
        
        main_controls_layout.addLayout(wafer_setup_header_layout)
        main_controls_layout.addWidget(self.edit_selected_chip_type)
        main_controls_layout.addWidget(self.add_new_chip_type)
        main_controls_layout.addWidget(self.assign_chip_to_wafer)
        
        # Probing subsection
        probing_header_layout = QHBoxLayout()
        probing_title = QLabel("Probing Controls")
        probing_title.setFont(QFont("Arial", 10, QFont.Bold))
        probing_help_btn = self.create_help_button("probing")
        probing_header_layout.addWidget(probing_title)
        probing_header_layout.addStretch()
        probing_header_layout.addWidget(probing_help_btn)
        
        self.probe_individual = QPushButton("Probe Individual Chips")
        self.probe_all = QPushButton("Probe all chips of 1 type")
        self.see_resistance = QPushButton("View Single Chip Resistance")
        self.visualize_wafer = QPushButton("Visualize Entire Wafer")
        
        main_controls_layout.addLayout(probing_header_layout)
        main_controls_layout.addWidget(self.probe_individual)
        main_controls_layout.addWidget(self.probe_all)
        main_controls_layout.addWidget(self.see_resistance)
        main_controls_layout.addWidget(self.visualize_wafer)
        
        chips_probing_layout.addLayout(main_controls_layout)
        
        bottom_layout.addWidget(chips_probing_group)
        
        main_layout.addLayout(bottom_layout)
        
        # Add stretch to push everything up
        main_layout.addStretch()
        
        MainWindow.setCentralWidget(self.centralwidget)
        self.retranslateUi(MainWindow)
        QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Wafer Probe Control System", None))
        self.cam_input.setText("")
        self.MultimeterAddress.setText("24")