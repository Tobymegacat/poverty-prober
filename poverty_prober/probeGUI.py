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
    QVBoxLayout, QWidget)


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



class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(577, 932)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayoutWidget_3 = QWidget(self.centralwidget)
        self.gridLayoutWidget_3.setObjectName(u"gridLayoutWidget_3")
        self.gridLayoutWidget_3.setGeometry(QRect(0, 10, 581, 911))
        self.gridLayout_3 = QGridLayout(self.gridLayoutWidget_3)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(self.gridLayoutWidget_3)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_3.addWidget(self.label, 1, 0, 1, 1)

        self.label_10 = QLabel(self.gridLayoutWidget_3)
        self.label_10.setObjectName(u"label_10")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.label_10.setFont(font)
        self.label_10.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_10.setMargin(0)

        self.gridLayout_3.addWidget(self.label_10, 11, 0, 1, 3)

        self.cam_input = QLineEdit(self.gridLayoutWidget_3)
        self.cam_input.setObjectName(u"cam_input")

        self.gridLayout_3.addWidget(self.cam_input, 3, 1, 1, 1)

        self.label_9 = QLabel(self.gridLayoutWidget_3)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setFont(font)
        self.label_9.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_9.setMargin(0)

        self.gridLayout_3.addWidget(self.label_9, 6, 0, 1, 3)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_4 = QLabel(self.gridLayoutWidget_3)
        self.label_4.setObjectName(u"label_4")
        font1 = QFont()
        font1.setBold(True)
        self.label_4.setFont(font1)
        self.label_4.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.label_4)

        self.edit_selected_chip_type = QPushButton(self.gridLayoutWidget_3)
        self.edit_selected_chip_type.setObjectName(u"edit_selected_chip_type")

        self.verticalLayout.addWidget(self.edit_selected_chip_type)

        self.add_new_chip_type = QPushButton(self.gridLayoutWidget_3)
        self.add_new_chip_type.setObjectName(u"add_new_chip_type")

        self.verticalLayout.addWidget(self.add_new_chip_type)

        self.assign_chip_to_wafer = QPushButton(self.gridLayoutWidget_3)
        self.assign_chip_to_wafer.setObjectName(u"assign_chip_to_wafer")

        self.verticalLayout.addWidget(self.assign_chip_to_wafer)

        self.label_2 = QLabel(self.gridLayoutWidget_3)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setFont(font1)
        self.label_2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.label_2)

        self.probe_individual = QPushButton(self.gridLayoutWidget_3)
        self.probe_individual.setObjectName(u"probe_individual")

        self.verticalLayout.addWidget(self.probe_individual)

        self.probe_all = QPushButton(self.gridLayoutWidget_3)
        self.probe_all.setObjectName(u"probe_all")

        self.verticalLayout.addWidget(self.probe_all)

        # self.transformed_move = QPushButton(self.gridLayoutWidget_3)
        # self.transformed_move.setObjectName(u"transformed_move")

        # self.verticalLayout.addWidget(self.transformed_move)

        self.see_resistance = QPushButton(self.gridLayoutWidget_3)
        self.see_resistance.setObjectName(u"see_resistance")

        self.verticalLayout.addWidget(self.see_resistance)

        self.visualize_wafer = QPushButton(self.gridLayoutWidget_3)
        self.visualize_wafer.setObjectName(u"visualize_wafer")
        self.visualize_wafer.setText("Visualize Entire Wafer")
        self.verticalLayout.addWidget(self.visualize_wafer)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_2)


        self.gridLayout_3.addLayout(self.verticalLayout, 22, 1, 1, 2)

        self.cam_show = QPushButton(self.gridLayoutWidget_3)
        self.cam_show.setObjectName(u"cam_show")

        self.gridLayout_3.addWidget(self.cam_show, 3, 2, 1, 1)

        self.confirm_align = QPushButton(self.gridLayoutWidget_3)
        self.confirm_align.setObjectName(u"confirm_align")

        self.gridLayout_3.addWidget(self.confirm_align, 7, 2, 1, 1)

        self.graphicsView = ZoomableGraphicsView(self.gridLayoutWidget_3)
        self.graphicsView.setObjectName(u"graphicsView")

        self.gridLayout_3.addWidget(self.graphicsView, 14, 0, 1, 2)

        self.label_8 = QLabel(self.gridLayoutWidget_3)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setFont(font)
        self.label_8.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_8.setMargin(0)

        self.gridLayout_3.addWidget(self.label_8, 0, 0, 1, 3)

        self.listWidget = QListWidget(self.gridLayoutWidget_3)
        self.listWidget.setObjectName(u"listWidget")

        self.gridLayout_3.addWidget(self.listWidget, 22, 0, 1, 1)

        self.controller_status = QLabel(self.gridLayoutWidget_3)
        self.controller_status.setObjectName(u"controller_status")
        self.controller_status.setLineWidth(2)
        self.controller_status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_3.addWidget(self.controller_status, 4, 0, 1, 1)

        self.ser_dropdown = QComboBox(self.gridLayoutWidget_3)
        self.ser_dropdown.setObjectName(u"ser_dropdown")

        self.gridLayout_3.addWidget(self.ser_dropdown, 1, 1, 1, 1)

        self.manual_drive = QPushButton(self.gridLayoutWidget_3)
        self.manual_drive.setObjectName(u"manual_drive")

        self.gridLayout_3.addWidget(self.manual_drive, 4, 2, 1, 1)

        self.set_align_1 = QPushButton(self.gridLayoutWidget_3)
        self.set_align_1.setObjectName(u"set_align_1")

        self.gridLayout_3.addWidget(self.set_align_1, 7, 0, 1, 1)

        self.controller_connect = QPushButton(self.gridLayoutWidget_3)
        self.controller_connect.setObjectName(u"controller_connect")

        self.gridLayout_3.addWidget(self.controller_connect, 4, 1, 1, 1)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.wafer_create = QPushButton(self.gridLayoutWidget_3)
        self.wafer_create.setObjectName(u"wafer_create")

        self.verticalLayout_2.addWidget(self.wafer_create)

        self.export_2 = QPushButton(self.gridLayoutWidget_3)
        self.export_2.setObjectName(u"export_2")

        self.verticalLayout_2.addWidget(self.export_2)


        self.gridLayout_3.addLayout(self.verticalLayout_2, 14, 2, 1, 1)

        self.ser_connect = QPushButton(self.gridLayoutWidget_3)
        self.ser_connect.setObjectName(u"ser_connect")

        self.gridLayout_3.addWidget(self.ser_connect, 1, 2, 1, 1)

        self.label_11 = QLabel(self.gridLayoutWidget_3)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setFont(font)
        self.label_11.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_11.setMargin(0)

        self.gridLayout_3.addWidget(self.label_11, 21, 0, 1, 3)

        self.Set_drop_height = QPushButton(self.gridLayoutWidget_3)
        self.Set_drop_height.setObjectName(u"Set_drop_height")

        self.gridLayout_3.addWidget(self.Set_drop_height, 9, 0, 1, 3)

        self.label_3 = QLabel(self.gridLayoutWidget_3)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_3.addWidget(self.label_3, 3, 0, 1, 1)

        self.set_align_2 = QPushButton(self.gridLayoutWidget_3)
        self.set_align_2.setObjectName(u"set_align_2")

        self.gridLayout_3.addWidget(self.set_align_2, 7, 1, 1, 1)

        self.pushButton_2 = QPushButton(self.gridLayoutWidget_3)
        self.pushButton_2.setObjectName(u"pushButton_2")

        self.gridLayout_3.addWidget(self.pushButton_2, 5, 2, 1, 1)

        self.label_5 = QLabel(self.gridLayoutWidget_3)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_5.setMargin(4)

        self.gridLayout_3.addWidget(self.label_5, 5, 0, 1, 1)

        self.MultimeterAddress = QLineEdit(self.gridLayoutWidget_3)
        self.MultimeterAddress.setObjectName(u"MultimeterAddress")

        self.gridLayout_3.addWidget(self.MultimeterAddress, 5, 1, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"COM PORTS: ", None))
        self.label_10.setText(QCoreApplication.translate("MainWindow", u"Wafer Shape Set Up", None))
        self.cam_input.setText("")
        self.label_9.setText(QCoreApplication.translate("MainWindow", u"Alignment and Calibration", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Wafer Set Up", None))
        self.edit_selected_chip_type.setText(QCoreApplication.translate("MainWindow", u"Edit Selected Chip Type", None))
        self.add_new_chip_type.setText(QCoreApplication.translate("MainWindow", u"Add New Chip Type", None))
        self.assign_chip_to_wafer.setText(QCoreApplication.translate("MainWindow", u"Assign Chip To Wafer", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Probing stuff", None))
        self.probe_individual.setText(QCoreApplication.translate("MainWindow", u"Probe Individual Chips", None))
        self.probe_all.setText(QCoreApplication.translate("MainWindow", u"Probe all chips of 1 type", None))
        # self.transformed_move.setText(QCoreApplication.translate("MainWindow", u"Move to wafer coordinates", None))
        self.see_resistance.setText(QCoreApplication.translate("MainWindow", u"View Single Chip Resistance", None))
        self.cam_show.setText(QCoreApplication.translate("MainWindow", u"Start Cam Feed", None))
        self.confirm_align.setText(QCoreApplication.translate("MainWindow", u"Confirm Alignment", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"SET UP", None))
        self.controller_status.setText(QCoreApplication.translate("MainWindow", u"No Controller Connected", None))
        self.manual_drive.setText(QCoreApplication.translate("MainWindow", u"Enable Manual Drive", None))
        self.set_align_1.setText(QCoreApplication.translate("MainWindow", u"Set Alignment Mark 1", None))
        self.controller_connect.setText(QCoreApplication.translate("MainWindow", u"Connect Controller", None))
        self.wafer_create.setText(QCoreApplication.translate("MainWindow", u"Build Wafer From Text", None))
        self.export_2.setText(QCoreApplication.translate("MainWindow", u"Export Wafer to txt", None))
        self.ser_connect.setText(QCoreApplication.translate("MainWindow", u"Connect", None))
        self.label_11.setText(QCoreApplication.translate("MainWindow", u"Chips and probing!", None))
        self.Set_drop_height.setText(QCoreApplication.translate("MainWindow", u"Set Probe Drop Height", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Camera Num (use 1 usually)", None))
        self.set_align_2.setText(QCoreApplication.translate("MainWindow", u"Set Alignment Mark 2", None))
        self.pushButton_2.setText(QCoreApplication.translate("MainWindow", u"Connect Multimeter", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"Multimeter Visa Address:", None))
    # retranslateUi

