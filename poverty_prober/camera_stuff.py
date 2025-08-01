import cv2
import numpy as np
from PySide6.QtWidgets import QInputDialog, QMessageBox
import time
import json
import importlib


from pymeasure.adapters import VISAAdapter

def import_from_path(dotted_path):
    module_path, class_name = dotted_path.rsplit('.', 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)

with open("config.json", "r") as f:
    config = json.load(f)

instrument_path = config['device']['instrument_type']
InstrumentClass = import_from_path(instrument_path)



class camera_handler():
    def __init__(self, prober, mainwindow):
        
        self.cam_connected = False

        self.instrument_connected = False

        self.multimeter = None
        self.mainwindow = mainwindow
        self.alignment_mode = False
        self.frozen_frame = None

        self.aligned = False
        
        self.z_drop = 0
        self.prober = prober

        self.cap = None
        self.running = False
        self.align1 = []
        self.align2 = []
        self.align1_center = None
        # {x,y}

        self.align2_center = None
        # {x,y}

        self.microns_per_pixel = None
        self.align1_real = None
        self.align2_real = None


    def connect_meter(self, address):
        try:
            adapter = VISAAdapter(f"GPIB::{address}::INSTR")
            self.multimeter = InstrumentClass(adapter)
            
            # Try a command to ensure it's responsive
            # print("ID:", instrument.id)
            msg = QMessageBox()
            msg.setWindowTitle("Success!")
            msg.setText("Instrument connection worked!")
            self.instrument_connected = True
            msg.exec()


        except Exception as e:
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText("Instrument connection failed")
            self.instrument_connected = False
            msg.exec()
            pass
            


    
    def start_camera(self, cam_number):
        if self.cap is None:
            self.cap = cv2.VideoCapture(cam_number)
            if not self.cap.isOpened():
                return False
            cv2.namedWindow("real camera", cv2.WINDOW_NORMAL)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            cv2.setMouseCallback("real camera", self.click_handler, param=1)
            self.cam_connected = True

            
        self.running = True

    def stop_camera(self):
        """Stop camera thread"""
        self.running = False
        if self.cap:
            self.cap.release()
            self.cap = None

    def update_camera(self):
        
        if self.alignment_mode:
            return


        ret, frame = self.cap.read()

        #region crosshair

        height, width = frame.shape[:2]
       
        center = (width // 2, height // 2)
        color = (0, 0, 255)  # red
        thickness = 1
        length = 10  # half-length of crosshair lines

        # Horizontal line
        cv2.line(frame, (center[0] - length, center[1]), (center[0] + length, center[1]), color, thickness)
        # Vertical line
        cv2.line(frame, (center[0], center[1] - length), (center[0], center[1] + length), color, thickness)
        #endregion

        cv2.imshow("real camera", frame)

        #region vid processing
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        focus_measure = cv2.Laplacian(gray, cv2.CV_64F).var()



        smoothed = cv2.GaussianBlur(gray, (3, 3), 1.2)
        clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
        enhanced = clahe.apply(smoothed)
        binary = cv2.adaptiveThreshold(enhanced, 255,
                               cv2.ADAPTIVE_THRESH_MEAN_C,
                               cv2.THRESH_BINARY, blockSize=51, C=-5)
        median = cv2.medianBlur(binary, 3)
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(median, connectivity=8)
        final = np.zeros_like(median)

        for i in range(1, num_labels):
            if stats[i, cv2.CC_STAT_AREA] > 100:  # Adjust if small features are being removed
                final[labels == i] = 255

        final = cv2.dilate(final, np.ones((3, 3), np.uint8), iterations=1)
        output = cv2.cvtColor(final, cv2.COLOR_GRAY2BGR)
        #endregion

        contours, _ = cv2.findContours(final, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        #region cross stuff
        cross_template = np.zeros((300, 300), dtype=np.uint8)

        # Define bar dimensions
        bar_width =40
        bar_length = 160
        center = (150, 150)  # center of the canvas

        # Draw vertical bar
        x1 = center[0] - bar_width // 2
        x2 = center[0] + bar_width // 2
        y1 = center[1] - bar_length // 2
        y2 = center[1] + bar_length // 2
        cv2.rectangle(cross_template, (x1, y1), (x2, y2), 255, -1)

        # Draw horizontal bar
        x1 = center[0] - bar_length // 2
        x2 = center[0] + bar_length // 2
        y1 = center[1] - bar_width // 2
        y2 = center[1] + bar_width // 2
        cv2.rectangle(cross_template, (x1, y1), (x2, y2), 255, -1)

        hole_size = 0
        cv2.rectangle(
            cross_template,
            (center[0] - hole_size // 2, center[1] - hole_size // 2),
            (center[0] + hole_size // 2, center[1] + hole_size // 2),
            0,
            -1
        )


        # Get contour of the template cross
        cross_contours, _ = cv2.findContours(cross_template, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cross_template_contour = cross_contours[0]

        #endregion

        #region contour detection
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 500:
                continue  # skip small stuff

            score = cv2.matchShapes(cross_template_contour, cnt, cv2.CONTOURS_MATCH_I1, 0.0)

            if score < 0.3:  # adjust threshold as needed
                cv2.drawContours(output, [cnt], -1, (0, 255, 255), 2)

                # Compute center of the shape
                M = cv2.moments(cnt)                                                                                                                                                                                                                                                   
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    
                    cv2.putText(output, "cross", (cx - 20, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 500:
                continue

            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)

            if len(approx) == 4 and cv2.isContourConvex(approx):
                cv2.drawContours(output, [approx], -1, (0, 255, 0), 2)
                M = cv2.moments(approx)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    cv2.putText(output, "Square", (cx - 20, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                    
        #endregion

        # self.hough_lines_corner_find(smoothed)


        cv2.imshow("processed image", output)

        key = cv2.waitKey(1) & 0xFF
        if key == 13:
             print(focus_measure)

        return [final, smoothed, focus_measure, frame]

    def generate_rotated_square(self, p1, p2):
        # Vector from p1 to p2
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        length = np.hypot(dx, dy)

        # Normalize and rotate 90 degrees
        dxn, dyn = dx / length, dy / length
        perp_dx, perp_dy = -dyn, dxn  # 90-degree rotation

        # Compute other two corners
        p3 = (int(p2[0] + perp_dx * length), int(p2[1] + perp_dy * length))
        p4 = (int(p1[0] + perp_dx * length), int(p1[1] + perp_dy * length))

        return [p1, p2, p3, p4]

    def click_handler(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if param==1:
                self.align1.append((x,y))
            else:
                self.align2.append((x,y))

    def align_1(self):
        # Enter alignment mode and freeze frame
        if self.alignment_mode == True:
            return

        self.alignment_mode = True
        self.align1 = []
        
        # Capture and freeze the current frame
        ret, self.frozen_frame = self.cap.read()
        if not ret:
            self.alignment_mode = False
            return

        cv2.setMouseCallback("real camera", self.click_handler, param=1)
        
        while True:
            key = cv2.waitKey(1) & 0xFF
            
            # Work with a copy of the frozen frame
            display_frame = self.frozen_frame
            
            if len(self.align1) == 2:
                square = self.generate_rotated_square(self.align1[0], self.align1[1])
                cv2.polylines(display_frame, [np.array(square)], isClosed=True, color=(0, 255, 0), thickness=2)
                
                height, width = display_frame.shape[:2]
                screen_center = np.array([[width//2],[height//2]])
                pixel_center = np.mean(np.array(square), axis=0).reshape(2, 1)
                
            cv2.imshow("real camera", display_frame)
            
            if key == 13 and len(self.align1) == 2:  # Enter key
                text, ok = QInputDialog.getText(None, "Input", "enter theoretical coords of this box in x,y format:")
                if ok:
                    wide, ok = QInputDialog.getText(None, "Input", "how many micron per side of square")
                    if ok:
                        wide = float(wide)
                        pixels = np.hypot(square[0][0]-square[1][0], square[0][1]-square[1][1])
                        self.microns_per_pixel = float(wide/pixels)

                        pixel_offset = pixel_center - screen_center
                        temp = 0.001*self.microns_per_pixel*(pixel_offset)

                        xyz = self.prober.find_location()
                        self.z1 = xyz['Z']
                        self.align1_center = np.array([[xyz['X']+temp[0,0]],[xyz['Y']-temp[1,0]]])
                        x, y = text.split(",")
                        self.align1_real = np.array([[float(x)],[float(y)]])
                        self.alignment_mode = False        

                        break
                    else:
                        self.align1 = []
                        self.alignment_mode = False        

                        break
                else:
                    self.align1 = []
                    self.alignment_mode = False        

                    break
            elif key == 27:  # Escape key
                self.alignment_mode = False        

                break
        # Exit alignment mode
        self.alignment_mode = False        

    def align_2(self):
        if self.alignment_mode == True:
            return
        # Enter alignment mode and freeze frame
        self.alignment_mode = True
        self.align2 = []
        
        # Capture and freeze the current frame
        ret, self.frozen_frame = self.cap.read()
        if not ret:
            self.alignment_mode = False
            return

        cv2.setMouseCallback("real camera", self.click_handler, param=2)
        
        while True:
            key = cv2.waitKey(1) & 0xFF

            # Work with a copy of the frozen frame
            display_frame = self.frozen_frame
            
            if len(self.align2) == 2:
                square = self.generate_rotated_square(self.align2[0], self.align2[1])
                cv2.polylines(display_frame, [np.array(square)], isClosed=True, color=(0, 255, 0), thickness=2)
                
                height, width = display_frame.shape[:2]
                screen_center = np.array([[width//2],[height//2]])
                pixel_center = np.mean(np.array(square), axis=0).reshape(2, 1)
                
            cv2.imshow("real camera", display_frame)
            key = cv2.waitKey(1) & 0xFF

            if key == 13 and len(self.align2) == 2:  # Enter key
                text, ok = QInputDialog.getText(None, "Input", "enter theoretical coords of this box in x,y format:")
                if ok:
                    wide, ok = QInputDialog.getText(None, "Input", "how many micron per side of square")
                    if ok:
                        wide = float(wide)
                        pixels = np.hypot(square[0][0]-square[1][0], square[0][1]-square[1][1])
                        self.microns_per_pixel = float(wide/pixels)

                        pixel_offset = pixel_center - screen_center
                        temp = 0.001*self.microns_per_pixel*(pixel_offset)

                        xyz = self.prober.find_location()
                        self.z2 = xyz['Z']
                        self.align2_center = np.array([[xyz['X']+temp[0,0]],[xyz['Y']-temp[1,0]]])
                        x, y = text.split(",")
                        self.align2_real = np.array([[float(x)],[float(y)]])
                        self.alignment_mode = False        

                        break
                    else:
                        self.align2 = []
                        self.alignment_mode = False        

                        break
                else:
                    self.align2 = []
                    self.alignment_mode = False        

                    break
            elif key == 27:  # Escape key
                self.alignment_mode = False        

                break
        # Exit alignment mode
        self.alignment_mode = False        


    
    def apply_transformation(self):
        if self.align1_center is not None and self.align2_center is not None:
            # Ask if user wants visual confirmation
            self.prober.apply_transformation(self.align1_center, self.align2_center, self.align1_real, self.align2_real, self.z1, self.z2)
            self.aligned = True

            visual_confirm_msg = QMessageBox()
            visual_confirm_msg.setWindowTitle("Visual Confirmation")
            visual_confirm_msg.setText("Do you want to visually confirm alignment by moving to both alignment marks?")
            visual_confirm_msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            visual_confirm_msg.setDefaultButton(QMessageBox.StandardButton.Yes)
            
            visual_response = visual_confirm_msg.exec()
            
            if visual_response == QMessageBox.StandardButton.Yes:
                # Move to first alignment mark
                # Add your actual movement code here, e.g.:
                # self.prober.move_to_position(self.align1_real[0], self.align1_real[1], self.z1)
                
                self.prober.transformed_move(self.align1_real, True)
                # Confirm first alignment mark
                self.update_camera()
                cv2.waitKey(1)
                confirm1_msg = QMessageBox()
                confirm1_msg.setWindowTitle("Confirm Alignment Mark 1")
                confirm1_msg.setText("The probe should now be at alignment mark 1. Does the position look correct?")
                confirm1_msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                confirm1_msg.setDefaultButton(QMessageBox.StandardButton.Yes)
                
                confirm1_response = confirm1_msg.exec()
                
                if confirm1_response == QMessageBox.StandardButton.No:
                    error_msg = QMessageBox()
                    error_msg.setWindowTitle("Alignment Error")
                    error_msg.setText("Alignment mark 1 position is incorrect. Please re-set alignment marks and try again.")
                    error_msg.exec()
                    return
                
                self.prober.transformed_move(self.align2_real, True)
                # Confirm first alignment mark
                self.update_camera()
                # Confirm second alignment mark
                confirm2_msg = QMessageBox()
                confirm2_msg.setWindowTitle("Confirm Alignment Mark 2")
                confirm2_msg.setText("The probe should now be at alignment mark 2. Does the position look correct?")
                confirm2_msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                confirm2_msg.setDefaultButton(QMessageBox.StandardButton.Yes)
                
                confirm2_response = confirm2_msg.exec()
                
                if confirm2_response == QMessageBox.StandardButton.No:
                    error_msg = QMessageBox()
                    error_msg.setWindowTitle("Alignment Error")
                    error_msg.setText("Alignment mark 2 position is incorrect. Please re-set alignment marks and try again.")
                    error_msg.exec()
                    return
                
                # Both confirmations passed
                success_msg = QMessageBox()
                success_msg.setWindowTitle("Visual Confirmation Complete")
                success_msg.setText("Both alignment marks confirmed. Proceeding with transformation.")
                success_msg.exec()
            
            # Proceed with original transformation
            
            final_msg = QMessageBox()
            final_msg.setWindowTitle("Alignment Complete")
            final_msg.setText("Transformation applied successfully. System is now aligned.")
            final_msg.exec()
            
        else:
            msg = QMessageBox()
            msg.setWindowTitle("Problem")

            if self.align1_center == None and self.align2_center is not None:
                msg.setText("you didnt assign alignment mark one. Please do so")
            elif self.align2_center == None and self.align1_center is not None:
                msg.setText("you didnt assign alignment mark two. Please do so")
            else:
                msg.setText("you didnt assign either alignment marks. Please do so")

            msg.exec()


    def plot_die(self, die_size_mm, points_to_probe, die_center, die_object):
        
        failed_probe = coords = np.empty((2, 0))

        sigma = False
        if not self.instrument_connected:
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText("Please connect your instrument")
            msg.exec()
            sigma = True

        if not self.cam_connected:
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText("Please connect your camera")
            msg.exec()
            sigma = True

        if not self.aligned:
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText("Please perform alignment")
            msg.exec()
            sigma = True

        if self.z_drop == None or 0:
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText("Please set drop height")
            msg.exec()
            sigma = True

        if sigma:
            return "bork"
            

        self.prober.transformed_move(die_center, True)
        # print('sigma')


        fuzziness = self.update_camera()[2]
        down = True
        while fuzziness < 0:
            prev = fuzziness
            if down:
                self.prober.rel_move(0,0,-0.04,200)
                time.sleep(1)
                fuzziness = self.update_camera()[2]
                if fuzziness < prev:
                    down = False
            else:
                self.prober.rel_move(0,0,0.04,200)
                time.sleep(1)
                fuzziness = self.update_camera()[2]




        for i in range(3):
            self.update_camera()
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC key
                # print("ESC pressed, exiting")
                return "bork"
        temp = np.array([[die_size_mm/2],[die_size_mm/2]])
        self.prober.transformed_move(die_center+temp, True)
        time.sleep(2)


        #region
        cross_template = np.zeros((300, 300), dtype=np.uint8)

        # Define bar dimensions
        bar_width = 40
        bar_length = 160
        center = (150, 150)  # center of the canvas

        # Draw vertical bar
        x1 = center[0] - bar_width // 2
        x2 = center[0] + bar_width // 2
        y1 = center[1] - bar_length // 2
        y2 = center[1] + bar_length // 2
        cv2.rectangle(cross_template, (x1, y1), (x2, y2), 255, -1)

        # Draw horizontal bar
        x1 = center[0] - bar_length // 2
        x2 = center[0] + bar_length // 2
        y1 = center[1] - bar_width // 2
        y2 = center[1] + bar_width // 2
        cv2.rectangle(cross_template, (x1, y1), (x2, y2), 255, -1)

        hole_size = 0
        cv2.rectangle(
            cross_template,
            (center[0] - hole_size // 2, center[1] - hole_size // 2),
            (center[0] + hole_size // 2, center[1] + hole_size // 2),
            0,
            -1
        )
        cross_contours, _ = cv2.findContours(cross_template, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cross_template_contour = cross_contours[0]

        #endregion

        closest_cross_center = None
        closest_distance = float('inf')


        for i in range(10):
            final = self.update_camera()[0]
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC key
                # print("ESC pressed, exiting")
                return "bork"

        time.sleep(5)

        contours, _ = cv2.findContours(final, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        height, width = final.shape[:2]
        img_center = np.array([[width // 2], [height // 2]])


        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 300:
                continue  # skip small stuff

            score = cv2.matchShapes(cross_template_contour, cnt, cv2.CONTOURS_MATCH_I1, 0.0)

            if score < 0.45:
                M = cv2.moments(cnt)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    distance = np.hypot(cx - img_center[0,0], cy - img_center[1,0])

                    if distance < closest_distance:
                        closest_distance = distance
                        closest_cross_center = np.array([[cx],[cy]])

        if closest_cross_center is None:
            pixel_offset = np.array([[0],[0]])

        pixel_offset = closest_cross_center - img_center
        pixel_offset[1,0] = pixel_offset[1,0] * -1  
        temp2 = 0.001*self.microns_per_pixel*(pixel_offset)
        # displacement += temp2  
        #endregion

        baseline = 0
        for y in range(10):
            baseline += self.multimeter.resistance

        baseline = baseline/10

        for i in range(points_to_probe.shape[1]):
            xy = np.array([[points_to_probe[0,i]],[points_to_probe[1,i]]])
            xy = xy + die_center

            self.prober.transformed_move(xy)
            
            time.sleep(2)

            final = self.update_camera()[1]
            
            key = cv2.waitKey(1) & 0xFF


            probe_center, boost = self.hough_lines_corner_find(final)
            pixel_offset = probe_center - img_center
            temp2 = 0.001*self.microns_per_pixel*(pixel_offset)

            if temp2[0,0] > 0.05:
                self.prober.rel_move(-0.06, 0, None, 200)
            if temp2[0,0] < -0.05:
                self.prober.rel_move(0.06, 0, None, 200)
            
            
            if boost != 0:
                self.prober.rel_move(0, boost*0.06, None, 200)
                print(f"boosted {boost}")
            if temp2[1,0] > 0.03:
                self.prober.rel_move(0, 0.06, None, 200)
            if temp2[1,0] < -0.03:
                self.prober.rel_move(0, -0.06, None, 200)
        
            final = self.update_camera()[1] 
            key = cv2.waitKey(1) & 0xFF



            if key == 27:  # ESC key
                # print("ESC pressed, exiting")
                return "bork"

            time.sleep(1)
            final = self.update_camera()[1] 
            key = cv2.waitKey(1) & 0xFF


            self.prober.rel_move(0,0,(-self.z_drop * 0.04),200)
            


            self.prober.turn_on_measuring()

            

            time.sleep(3)
            
            resistance = 0
            for x in range(10):
                resistance += self.multimeter.resistance

            resistance = resistance/10

            resistance = resistance - baseline

            if resistance > 1000000:
                failed_probe = np.hstack((failed_probe, xy))

            # print(resistance)

            totoro = np.array([[points_to_probe[0,i]],[points_to_probe[1,i]]])

            die_object.insert_probed_resistance(totoro, resistance)
            

            self.prober.turn_off_measuring()
            key = cv2.waitKey(1) & 0xFF

            final = self.update_camera()[1]
            if key == 27:  # ESC key
                # print("ESC pressed, exiting")
                return "bork"

            time.sleep(3)

            self.prober.rel_move(0,0,(self.z_drop * 0.04),200)

            final = self.update_camera()[1]
            key = cv2.waitKey(1) & 0xFF

            if key == 27:  # ESC key
                # print("ESC pressed , exiting")
                return "bork"

        #reprobe failed junctions

        for i in range(failed_probe.shape[1]):
            xy = np.array([[failed_probe[0,i]],[failed_probe[1,i]]])
            xy = xy + die_center

            self.prober.transformed_move(xy)
            
            time.sleep(2)

            final = self.update_camera()[1]
            
            key = cv2.waitKey(1) & 0xFF


            probe_center, boost = self.hough_lines_corner_find(final)
            pixel_offset = probe_center - img_center
            temp2 = 0.001*self.microns_per_pixel*(pixel_offset)

            if temp2[0,0] > 0.05:
                self.prober.rel_move(-0.06, 0, None, 200)
            if temp2[0,0] < -0.05:
                self.prober.rel_move(0.06, 0, None, 200)
            
            
            if boost != 0:
                self.prober.rel_move(0, boost*0.06, None, 200)
                print(f"boosted {boost}")
            if temp2[1,0] > 0.03:
                self.prober.rel_move(0, 0.06, None, 200)
            if temp2[1,0] < -0.03:
                self.prober.rel_move(0, -0.06, None, 200)
        
            final = self.update_camera()[1] 
            key = cv2.waitKey(1) & 0xFF



            if key == 27:  # ESC key
                # print("ESC pressed, exiting")
                return "bork"

            time.sleep(1)

            baseline = 0

            for y in range(10):
                baseline += self.multimeter.resistance

            baseline = baseline/10


            self.prober.rel_move(0,0,(-self.z_drop * 0.04),200)
            
            self.prober.turn_on_measuring()

            time.sleep(3)
            
            resistance = 0
            for x in range(10):
                resistance += self.multimeter.resistance

            resistance = resistance/10

            resistance = resistance - baseline

            # print(resistance)

            totoro = np.array([[points_to_probe[0,i]],[points_to_probe[1,i]]])

            die_object.insert_probed_resistance(totoro, resistance)
            
            self.prober.turn_off_measuring()
            key = cv2.waitKey(1) & 0xFF

            final = self.update_camera()[1]
            if key == 27:  # ESC key
                # print("ESC pressed, exiting")
                return "bork"

            time.sleep(3)

            self.prober.rel_move(0,0,(self.z_drop * 0.04),200)

            final = self.update_camera()[1]
            key = cv2.waitKey(1) & 0xFF

            if key == 27:  # ESC key
                # print("ESC pressed , exiting")
                return "bork"

    
    def hough_lines_corner_find(self, img):
        def line_angle(x1, y1, x2, y2):
            return np.arctan2(y2 - y1, x2 - x1)  # Radians
        
        def angle_diff(theta1, theta2):
            diff = np.abs(theta1 - theta2)
            return min(diff, np.pi - diff)  # Smallest angle between the lines

        def are_approximately_perpendicular(theta1, theta2, threshold_deg=10):
            diff_rad = np.deg2rad(threshold_deg)
            return np.abs(angle_diff(theta1, theta2) - np.pi / 2) < diff_rad
        
        def compute_intersection(line1, line2):
            x1, y1, x2, y2 = line1
            x3, y3, x4, y4 = line2

            A1, B1 = y2 - y1, x1 - x2
            C1 = A1 * x1 + B1 * y1
            A2, B2 = y4 - y3, x3 - x4
            C2 = A2 * x3 + B2 * y3

            det = A1 * B2 - A2 * B1
            if det == 0:
                return None  # parallel lines
            x = (B2 * C1 - B1 * C2) / det
            y = (A1 * C2 - A2 * C1) / det
            return int(x), int(y)

        closestpoints = np.empty((3, 0))

        edges = cv2.Canny(img, 50, 150, apertureSize=3)

        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=20, minLineLength=50, maxLineGap=10)



        height, width = img.shape[:2]
        screen_center = np.array([[width//2],[height//2]])

        
        if lines is None:
            # print("No lines detected by HoughLinesP")
            # Return screen center as fallback
            return screen_center, 0


        for i in range(len(lines)):
            for j in range(i + 1, len(lines)):
                l1, l2 = lines[i][0], lines[j][0]
                theta1 = line_angle(*l1)
                theta2 = line_angle(*l2)
                if are_approximately_perpendicular(theta1, theta2):
                    pt = compute_intersection(l1, l2)
                    if pt:
                        if closestpoints.shape[1] < 4:

                            distance = np.hypot(pt[0] - screen_center[0,0], pt[1] - screen_center[1,0])
                            new_point = np.array([[pt[0]], [pt[1]], [distance]])
                            closestpoints = np.hstack((closestpoints, new_point))
                            sorted_indices = np.argsort(closestpoints[2])  # Sort based on row index 2
                            closestpoints = closestpoints[:, sorted_indices]
                        else:
                            distance = np.hypot(pt[0] - screen_center[0,0], pt[1] - screen_center[1,0])
                            new_point = np.array([[pt[0]], [pt[1]], [distance]])
                            closestpoints = np.hstack((closestpoints, new_point))
                            sorted_indices = np.argsort(closestpoints[2])  # Sort based on row index 2
                            closestpoints = closestpoints[:, sorted_indices]
                            closestpoints = np.delete(closestpoints, -1, axis=1)
                        # cv2.circle(output, pt, 4, (0, 255, 0), -1)
        

        x = closestpoints[0]
        y = closestpoints[1]

        all_less = np.all(closestpoints[1, :] < screen_center[1,0])

        all_more = np.all(closestpoints[1, :] > screen_center[1,0])

        if all_less:
            boost = 1
        elif all_more:
            boost = -1
        else:
            boost = 0

        centroid_x = np.mean(x)
        centroid_y = np.mean(y)
        centroid = np.array([[centroid_x],[centroid_y]])

        return centroid, boost

    def set_drop_dist(self):
        text, ok = QInputDialog.getText(None, "Z drop dist", "enter number of steps to drop to probe Z:")
        if ok:
            try:
                steps = int(text)
            except ValueError:
                steps = None
            finally:
                self.z_drop = steps


