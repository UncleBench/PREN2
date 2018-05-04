from MotorControl import MotorControl
from Communication import SerialCommunication
from PositionDetermination import PosSensor
import time

if __name__ == '__main__':
    arduino = SerialCommunication.SerialCommunication('/dev/SensorActor', 9600)
    mc = MotorControl.MotorControl(0, 0, com='/dev/Motor')

    posSensor = PosSensor.PosSensor()

    alpha_ = 2000
    beta_ = 2000

    mc.drive_x(20, 10000)
    while 1:
        time.sleep(0.5)
        battery_v = arduino.getBatteryVoltage()
        try:
            alpha_ = arduino.getRawAlpha()
            beta_ = arduino.getRawBeta()
        except:
            pass
        dist = 40.0 + mc.get_distance_driven()
        pos = posSensor.get_pos_prachtstueck(alpha_, beta_, dist['x'])
        print('x:{:5.1f}  z:{:5.1f} | s:{:5.1f} | ralpha:{:4d} rbeta:{:4d} | battery:{:5.1f}'.format(pos.x, pos.z, dist['x'], alpha_, beta_, battery_v))


