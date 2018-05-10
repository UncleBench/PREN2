import serial

ANGLE_ERROR_CODE = 65535	# -1 signed int

class CommException(Exception):
    pass

class GrabberState:
    CLOSE = 0
    OPEN = 1

class StopState:
    RUNNING = 0
    STOP = 1

class SerialCommunication:

    def __init__(self, com, baud=115200):
        """
        Args:
            com (String): Arduino Comport
            baud (int): Baudrate

        Returns:
            SerialCommunication: instance
        """
        self.ser = serial.Serial(com, baud)
        self.ser.timeout = 5    # first timeout 5s (due to startup time of the Arduino)
        if(self.ser.readline().rstrip() != "<Arduino is ready>"):
            raise CommException("Connection Failed")
        self.ser.timeout = 0.5  # then 0.5s


    def setCommand(self, command):
        """executes a setCommand on the serial interface
        Args:
            command (String): Command to send

        Returns:
            -

        Raises:
            CommException: ... when communication fails
        """
        self.ser.write(command + "\r")
        if(self.ser.readline().rstrip() != "AOK"):
            raise CommException("Sending the command '" + command + "' failed")

    def getCommand(self, command):
        """executes a getCommand on the serial interface
        Args:
            command (String): Command to send

        Returns:
            String: received answer

        Raises:
            CommException: ... when communication fails / ERR received / timeout exceeded
        """
        self.ser.write(command + "\r")
        result = self.ser.readline().rstrip()
        if result == "":
            raise CommException("Nothing received after command: "+command)
        if result == "ERR":
            raise CommException("Error occured after '"+command+"'")
        return result

    def getRawAlpha(self):
        """reads the raw alpha value from the Arduino
        Args:
            -

        Returns:
            int: raw alpha value

        Raises:
            CommException: ... when communication fails / ERR received / timeout exceeded
        """
        alpha_angle = int(self.getCommand("GA"))
        if alpha_angle == ANGLE_ERROR_CODE:
            raise CommException("Alpha Sensor failed")
        return alpha_angle

    def getRawBeta(self):
        """reads the raw beta value from the Arduino
        Args:
            -

        Returns:
            int: raw beta value

        Raises:
            CommException: ... when communication fails / ERR received / timeout exceeded
        """
        beta_angle = int(self.getCommand("GB"))
        if beta_angle == ANGLE_ERROR_CODE:
            raise CommException("Beta Sensor failed")
        return beta_angle

    def getStopState(self):
        """reads the stop state from the Arduino
        Args:
            -

        Returns:
            int: StopState.RUNNING / StopState.STOP

        Raises:
            CommException: ... when communication fails / ERR received / timeout exceeded
        """
        return int(self.getCommand("GS"))

    def getBatteryVoltage(self):
        """reads the stop state from the Arduino
        Args:
            -

        Returns:
            int: raw battery voltage

        Raises:
            CommException: ... when communication fails / ERR received / timeout exceeded
        """
        return float(self.getCommand("GV")) / 10

    def setGrabber(self, state):
        """sets the grabber state on the Arduino
        Args:
            state (int): GrabberState.OPEN, GrabberState.CLOSE

        Returns:
            -

        Raises:
            CommException: ... when communication fails / ERR received / timeout exceeded
        """
        self.setCommand("SG," + str(state))


if __name__ == '__main__':
    arduino = SerialCommunication('COM3', 9600)
    arduino.setGrabber(GrabberState.CLOSE)
    print arduino.getRawBeta(), arduino.getRawAlpha()