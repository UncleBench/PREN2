import serial
import time

class MotorControl:
    def __init__(self):
        self.serCom = serial.Serial("COM3", 115200)
        self.serCom.timeout = 5
        line = ""
        while "Grbl 1.1f ['$' for help]" not in line:
            time.sleep(0.3)
            line = self.serCom.readline()
            line.rstrip()

    def get_pos(self):
        time.sleep(0.3)
        self.serCom.write("?")
        line = self.serCom.readline()
        line.rstrip()
        return line

    def get_pos_encoded(self):
        result = self.getPos()

        mPos = result[11:28].split(',')
        for i, val in enumerate(mPos):
            mPos[i] = float(mPos[i])

        fs = result[32:35].split(',')
        for i, val in enumerate(fs):
            fs[i] = int(fs[i])

        wco = result[40:57].split(',')
        for i, val in enumerate(wco):
            wco[i] = float(wco[i])

        return (mPos, fs, wco)

    def drive_x(self, distance, speed):
        pass


    def drive_z(self, distance, speed):
        pass


    def get_distance_driven(self):
        pos = self.get_pos_encoded()
        return pos(0)[0], pos(0)[1]


    def move_camera(self, deg):
        pass