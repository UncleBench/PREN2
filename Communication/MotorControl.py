import serial
import time


class MotorControl:
    def __init__(self, com, baud=115200):
        self.ser_com = None
        self.init_communication(com, baud)

    def init_communication(self, com, baud):
        self.ser_com = serial.Serial(com, baud)
        self.ser_com.timeout = 1
        line = ""
        # send soft-reset to initalize Grbl
        self.ser_com.write('\x18')
        while "Grbl 1.1f ['$' for help]" not in line:
            time.sleep(0.3)
            line = self.ser_com.readline()
            line.rstrip()

        if "[MSG:'$H'|'$X' to unlock]" in self.ser_com.readline():
            self.set_command("$X")
        self.ser_com.timeout = None

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

    def home(self):
        self.set_command("$H")
        
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
            if sub_str.split(":")[0] == "WPos":
                super_sub_str = sub_str.split(":")[1]
                m_pos['x'] = float(super_sub_str.split(",")[0])
                m_pos['y'] = float(super_sub_str.split(",")[1])
                m_pos['z'] = float(super_sub_str.split(",")[2])
        return state, m_pos

    def drive(self, x=None, z=None, speed=1000):
        """this method lets the motors drive with the given position and speed
            Args:
                x (float) : distance to drive in x-direction
                z (float) : distance to drive in z-direction
                speed (int) : speed of the driven motors

            Returns:
                -
        """
        command = "$J=G91 G21"
        if x is not None:
            command += " X" + str(x)
        if z is not None:
            command += " Z" + str(z)
        if speed is not None:
            command += "F" + str(speed)

        self.set_command(command)

    def stop(self):
        """stops the motors from moving
        """
        command = "\x85"
        self.ser_com.write(command)

    def drive_x(self, distance, speed):
        self.drive(x=distance, speed=speed)

    def drive_z(self, distance, speed):
        self.drive(z=distance, speed=speed)

    def drive_z_to_home(self, speed):
        command = "$J=G90G21 Z0 F" + str(speed)
        self.set_command(command)

    def get_distance_driven(self):
        distance = self.get_pos_decoded()[1]
        return distance

    def set_camera(self, deg):
        if 0 <= deg <= 135:
            command = '$J=G90G21Y' + str(deg) + 'F100000'
            self.set_command(command)
        else:
            raise ValueError('Valid camera angle range is 0 to 135 degrees')


if __name__ == '__main__':
    mc = MotorControl(com='/dev/Motor')
    mc.home()
    mc.drive(x=10, z=2.2, speed=10)
    print mc.get_pos_decoded()
