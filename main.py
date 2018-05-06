from Vision import Vision, Target
from Communication import SerialCommunication
from PositionDetermination import PosSensor
from MotorControl import MotorControl
import threading
import argparse


if __name__ == '__main__':
    # arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-p", "--picamera", type=int, default=-1,
                    help="whether or not the Raspberry Pi camera should be used")
    args = vars(ap.parse_args())


    print("Webserver starten")
    print("Kommunikation Arduino Greifer, Whisker, Position, Batterie Raspi initialisieren")
    arduino = SerialCommunication('COM3', 9600)

    print("Arduino Motorensteuerung initialisieren und kalibrieren")
    motor_control = MotorControl(0,0)

    print("Kamera auf 20 Grad setzen")
    motor_control.set_camera(20)

    print("Programm für Vision starten")
    # construct the argument parse and parse the arguments

    vision = Vision(usePiCamera=args["picamera"] > 0)

    print("Warten auf Startsignal")

    print("Zum Würfel fahren")
    motor_control.drive_x(600, 100)

    print("Greifer nach unten")
    motor_control.drive_z(-100, 10)

    print("Nach vorne fahren ca 2cm")
    motor_control.drive_x(20, 10)

    print("Würfel greifen")
    arduino.setGrabber(SerialCommunication.GrabberState.CLOSE)

    print("Koordinatenanzeige starten")

    print("Greifer nach oben")
    print("Fahren solange Zielplattform nicht in unterer Bildhälfte")
    print("Kamera bewegen nach unten")
    print("Kamera in Ablademodus setzen")

    print("Fahren solange Zielplattform nicht mittig")
    print("Greifer nach unten")
    print("Würfel loslassen")
    print("Greifer nach oben")
    print("Berechne restliche Fahrt")
    print("Berechnete Strecke fahren")
    print("Langsam fahren solange Stopp nicht erreicht")
    print("Stop")