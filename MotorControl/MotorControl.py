import serial
import time

class MotorControl:
    def __init__(self, x0, z0):
        self.x0 = x0
        self.z0 = z0
        self.init_communication("COM5")

    def init_communication(self, com):
        self.serCom = serial.Serial(com, 115200)
        self.serCom.timeout = 5
        line = ""
        while "Grbl 1.1f ['$' for help]" not in line:
            time.sleep(0.3)
            line = self.serCom.readline()
            line.rstrip()

    def set_command(self, str):
        self.serCom.write(str + "\n")
        responseMsg = self.serCom.readline()
        print "response Msg:" + responseMsg
        if "ok" in responseMsg:
            return
        if "error" in responseMsg:
            raise Exception("Grbl command" + str +"failed, " + responseMsg)
        raise Exception("Grbl command" + str + "failed, received response msg:" + responseMsg)

    def get_command(self, str):
        self.serCom.write(str + "\n")
        return self.serCom.readline().rstrip()

    def get_pos_decoded(self):
        """returns decoded states of the motors
        Args:
            -

        Returns:
            tuple: (String: state, Dictonary: Position ("x", "y", "z"))
        """
        str = self.get_command("?")
        start = str.index("<") + 1
        stop = str.index(">", start)
        state = str[start:stop].split("|")[0]
        mPos = {}
        for sub_str in str[start:stop].split("|"):
            if sub_str.split(":")[0] == "MPos":
                super_sub_str = sub_str.split(":")[1]
                mPos['x'] = float(super_sub_str.split(",")[0])
                mPos['y'] = float(super_sub_str.split(",")[1])
                mPos['z'] = float(super_sub_str.split(",")[2])

        return state, mPos

    def drive(self, x = None, xSpeed=30000, z = None, zSpeed=10000, camera = None, cameraSpeed = 1):
        """this method lets the motors drive with the given position and speed
            Args:
                x (float) : distance to drive in x-direction
                xSpeed (int) : speed in x-direction
                z (float) : distance to drive in z-direction
                zSpeed (int) : speed in z-direction
                camera (float) :  angle of how far to rotate the camera
                cameraSpeed (int) : rotating speed

            Returns:
                -
        """
        command = "$J=G91 G21"
        if x != None:
            command += " X" + str(x)
            if xSpeed != None:
                command += "F" + str(xSpeed)
        if z != None:
            command += " Z" + str(z)
            if zSpeed != None:
                command += "F" + str(zSpeed)
        if camera != None:
            command += " Y" + str(camera)
            if cameraSpeed != None:
                command += "F" + str(cameraSpeed)

        print command
        self.set_command(command)

    def stop(self):
        """stops the motors from moving
        """
        command = "~"
        self.set_command(command)

    def drive_x(self, distance, speed):
        self.drive(x = distance, xSpeed=speed)


    def drive_z(self, distance, speed):
        self.drive(z=distance, zSpeed=speed)


    def get_distance_driven(self):
        pos = self.get_pos_encoded()
        return pos(0)[0], pos(0)[1]


    def move_camera(self, deg):
        self.drive(camera=deg)

if __name__ == '__main__':
    mc = MotorControl(0,0)
    mc.drive(x=10, z=2.2, zSpeed=None, camera=0.123, cameraSpeed=None)
    print mc.get_pos_decoded()
