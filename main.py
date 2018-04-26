import Vision
from Communication import SerialCommunication as communication
from PositionDetermination import PosSensor as position
import MotorControl
import threading


if __name__ == '__main__':

    print("Webserver starten")
    print("Kommunikation Arduino Greifer, Whisker, Position, Batterie Raspi initialisieren")

    print("Arduino Motorensteuerung initialisieren und kalibrieren")
    motor_control = MotorControl(0,0)

    print("Kamera auf 20 Grad setzen")
    motor_control.move_camera(20)

    print("Programm für Vision starten")
    vision = Vision()
    camera_thread = threading.Thread(target=vision.show_webcam(mirror=True))
    camera_thread.start()

    print("Warten auf Startsignal")

    print("Zum Würfel fahren")
    print("Greifer nach unten")
    print("Nach vorne fahren ca 2cm")
    print("Würfel greifen")
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