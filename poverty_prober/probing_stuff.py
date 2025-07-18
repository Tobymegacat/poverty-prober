import time
import numpy as np
import math

import json

with open("config.json", "r") as f:
    config = json.load(f)


class probe_handler():
    def __init__(self, ser):
        self.ser = ser
        
        # {x,y}

        # {x,y}

        self.microns_per_pixel = None

        self.scaling = None
        self.rotation = None
        self.displacement = None

        self.z1 = None
        self.z2 = None
        self.m = None
        self.b = None

        self.xyz = {'X':0, 'Y' :0, 'Z':0}
        self.x_direction = 'right'
        self.y_direction = 'up'
        self.x_backlash = 0.03
        self.y_backlash = 0.03



    def extract_xyz(self,line):
        xyz = {}
        for part in str(line).split():
            if part.startswith("X:") and "X" not in xyz:
                val = part[2:]
                if val:  # check it's not empty
                    xyz["X"] = float(val)
            elif part.startswith("Y:") and "Y" not in xyz:
                val = part[2:]
                if val:
                    xyz["Y"] = float(val)
            elif part.startswith("Z:") and "Z" not in xyz:
                val = part[2:]
                if val:
                    xyz["Z"] = float(val)
            if len(xyz) == 3:
                break
        return xyz

    def find_location(self):
        self.ser.flush()

        self.ser.write("M114\r\n")

        self.ser.flush()

        time.sleep(0.1)

        while True:
            line = self.ser.read()
            if line and 'X:' in line and 'Y:' in line and 'Z:' in line:
                print(line)
                self.xyz = self.extract_xyz(line)
                return self.xyz

    def pause(self):
        self.ser.flush()
        self.ser.write("M0\r\n")


    def homing(self):
        self.ser.flush()
        time.sleep(0.5)

        self.ser.write("G21\r\n")
        time.sleep(0.1)
        self.ser.write("G17\r\n")
        time.sleep(0.1)
        self.ser.write(f"{config["printer defaults"]["homing"]}\r\n")
        # self.gcode_waiting()
        time.sleep(0.1)
        self.ser.write("M302 S0 \r\n")
        time.sleep(0.1)
        self.ser.write("G0 E-10 \r\n")
        time.sleep(0.1)
        self.ser.write("M221 800 \r\n")

    def turn_off_measuring(self):
        self.ser.write("G1 E-15 F800\r\n")


    def turn_on_measuring(self):
        self.ser.write("G1 E15 F800\r\n")


    def rel_move(self, x, y, z = None, feed = None):

        self.ser.write("G91\r\n")
        cmd = "X" + str(x) + " " + "Y" + str(y)
        if z is not None:
            cmd = cmd + " Z" + str(z)
        if feed is None:
            cmd = cmd + " F" + str(200)
        else:
            cmd = cmd + " F" + str(feed)
        self.ser.write("G1 " + cmd + "\r\n")

    def abs_move(self, x, y, z = None, feed = None, level = False, wait = False):
        self.xyz = self.find_location()
        # print('jeebus')
        dx = x - self.xyz["X"]
        dy = y - self.xyz["Y"]
        if feed == None:
            feed = 200

        

        # Backlash correction: only apply if direction changed
        if dx < 0 and self.x_direction == 'right':
            dx -= self.x_backlash
            self.x_direction = 'left'
        elif dx > 0 and self.x_direction == 'left':
            dx += self.x_backlash
            self.x_direction = 'right'

        if dy < 0 and self.y_direction == 'up':
            dy -= self.y_backlash
            self.y_direction = 'down'
        elif dy > 0 and self.y_direction == 'down':
            dy += self.y_backlash
            self.y_direction = 'up'
            # print('up')

        # Move relative
        if z!= None:
            self.ser.write("G90\r\n")
            self.ser.write("G1 Z{z} F200\r\n")

        if level:
            self.ser.write("G90\r\n")
            self.ser.write(f"G1 Z{x*self.m + self.b} F200\r\n")
        self.rel_move(dx, dy, 0, feed)
        self.ser.flush()


        self.find_location()
        for i in range(int(-(-(x-self.xyz["X"])//0.06))):
            self.rel_move(0.06, 0, None, 200)
        for i in range(int(-(-(y-self.xyz["Y"])//0.06))):
            self.rel_move(0, 0.06, None, 200)    

        if wait:
            dist = np.hypot(dx,dy)
            # print("Frog")
            # print(f"wait {dist/feed}")
            time.sleep((dist/feed)*100)
            # print("Frogger")


            time.sleep(2)
            # print("Frosadfasg")


        # print('meep')

    def apply_transformation(self,align1_center, align2_center, align1_real, align2_real, z1, z2):
        
        temp = align2_center - align1_center
        temp1 = align2_real - align1_real
        theta_image = math.atan2(temp[1,0], temp[0,0])
        theta_real = math.atan2(temp1[1,0], temp1[0,0])
        self.rotation = theta_image - theta_real


        temp2 = align1_real - align2_real
        distance = np.hypot(temp[0,0], temp[1,0])
        ideal_distance = np.hypot(temp2[0,0], temp2[1,0])
        self.scaling = distance/ideal_distance

        rotation_matrix = np.array([[math.cos(self.rotation), -math.sin(self.rotation)],
                                    [math.sin(self.rotation), math.cos(self.rotation)]])

        self.displacement = align1_center - ((self.scaling * rotation_matrix) @ align1_real)

        self.displacement = (self.displacement +  align2_center - ((self.scaling * rotation_matrix) @ align2_real))/2.0


        self.m = float(z1 - z2) / float(align1_center[0,0] - align2_center[0,0])

        self.b = z1 - self.m*align1_center[0,0]

        # print(f"Displacement: {self.displacement}")
        # print(f"rotation: {self.rotation}")
        # print(f"scaling: {self.scaling}")

    def transformed_move(self,move, wait = False):
        transformed_point = move

        rotation_matrix = np.array([[math.cos(self.rotation), -math.sin(self.rotation)],
                                    [math.sin(self.rotation), math.cos(self.rotation)]])

        transformed_point = self.scaling * rotation_matrix @ transformed_point


        transformed_point = transformed_point + self.displacement

        # print('Kanye')

        self.abs_move(transformed_point[0,0],transformed_point[1,0],None,200,level=True, wait = wait)

    def gcode_waiting(self):
        
        time.sleep(0.1)
        self.ser.flush()
        timeout = 30
        start_time = time.time()
        
        self.ser.write("M302 S0 \r\n")
        response = ""
        
        while time.time() - start_time < timeout:
            if self.ser.in_waiting() > 0:
                char = self.ser.char_read()
                response += char
                
                if 'ok' in response.lower():
                    time.sleep(0.5)
                    return True
                elif 'error' in response.lower():
                    time.sleep(0.5)
                    return False






