import serial
import time


class MotorControl:
    def __init__(self, x0, z0, com, baud=115200):
        self.x0 = x0
        self.z0 = z0
        self.ser_com = None
        self.init_communication(com, baud)

    def init_communication(self, com, baud):
        self.ser_com = serial.Serial(com, baud)
        self.ser_com.timeout = 5
        line = ""
        while "Grbl 1.1f ['$' for help]" not in line:
            time.sleep(0.3)
            line = self.ser_com.readline()
            line.rstrip()

        if "[MSG:'$H'|'$X' to unlock]" in self.ser_com.readline():
            self.set_command("$X\n")

    def set_command(self, command):
        self.ser_com.write(command + "\n")
        response_msg = self.ser_com.readline()
        if "ok" in response_msg:
            return
        if "[MSG:Caution: Unlocked]" in response_msg:
            self.ser_com.readline()
            return
        if "error" in response_msg:
            raise Exception("Grbl command" + command + " failed, " + response_msg)
        raise Exception("Grbl command" + command + "failed, received response msg:" + response_msg)

    def get_command(self, command):
        self.ser_com.write(command)
        return self.ser_com.readline().rstrip()

    def get_pos_decoded(self):
        """returns decoded states of the motors
        Args:
            -

        Returns:
            tuple: (String: state, Dictonary: Position ("x", "y", "z"))
        """
        response = self.get_command("?")
        start = response.index("<") + 1
        stop = response.index(">", start)
        state = response[start:stop].split("|")[0]
        m_pos = {}
        for sub_str in response[start:stop].split("|"):
            if sub_str.split(":")[0] == "MPos":
                super_sub_str = sub_str.split(":")[1]
                m_pos['x'] = float(super_sub_str.split(",")[0])
                m_pos['y'] = float(super_sub_str.split(",")[1])
                m_pos['z'] = float(super_sub_str.split(",")[2])

        return state, m_pos

    def drive(self, x=None, z=None, camera=None, speed=10000):
        """this method lets the motors drive with the given position and speed
            Args:
                x (float) : distance to drive in x-direction
                z (float) : distance to drive in z-direction
                camera (float) :  angle of how far to rotate the camera
                speed (int) : speed of the driven motors

            Returns:
                -
        """
        command = "$J=G91 G21"
        if x is not None:
            command += " X" + str(x)
        if z is not None:
            command += " Z" + str(z)
        if camera is not None:
            command += " Y" + str(camera)
        if speed is not None:
            command += "F" + str(speed)

        self.set_command(command)

    def stop(self):
        """stops the motors from moving
        """
        command = "~"
        self.set_command(command)

    def drive_x(self, distance, speed):
        self.drive(x=distance, speed=speed)

    def drive_z(self, distance, speed):
        self.drive(z=distance, speed=speed)

    def get_distance_driven(self):
        distance = self.get_pos_decoded()[1]
        return distance

    def move_camera(self, deg):
        self.drive(camera=deg, speed=100)


if __name__ == '__main__':
    mc = MotorControl(0, 0)
    mc.drive(x=10, z=2.2, camera=0.123, speed=10)
    print mc.get_pos_decoded()
