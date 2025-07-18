import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget
from poverty_prober.gui_commands import MainWindow
from PySide6.QtCore import QTimer
from poverty_prober.camera_stuff import camera_handler
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import QRectF, QPointF
# {'X': 55.46, 'Y': 113.08, 'Z': 9.35}
# {'X': 120.48, 'Y': 112.78, 'Z': 8.95}

def main_loop():
    window.list_serial_ports()
    window.check_serial()
    window.game_pad_move()
    cam_num = window.ui.cam_input.text()
    try:
        cam_num = int(window.ui.cam_input.text())
    except ValueError:
        cam_num = None
        window.show_camera = False

    if window.show_camera and cam_num is not None:
        window.start_camera(cam_num)
        window.update_camera()

if __name__ == "__main__":

    app = QApplication(sys.argv)
    window = MainWindow()
    
    window.show()

    timer = QTimer()
    timer.timeout.connect(main_loop)
    timer.start(20)

    app.exec()

