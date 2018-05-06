from transitions import Machine
from Vision.Vision import Vision
from Vision.Target import Target
from Communication import SerialCommunication
from PositionDetermination import PosSensor
from MotorControl.MotorControl import MotorControl
from transitions.extensions import GraphMachine as Machine
import threading
import argparse

class Prachtstueck():
    def __init__(self, usePiCamera = 0):
        self.usePiCamera = usePiCamera

    def on_enter_init(self):
        print("Kommunikation Arduino Greifer, Whisker, Position, Batterie Raspi initialisieren")
        self.arduino = None #SerialCommunication('COM3', 9600)

        print("Arduino Motorensteuerung initialisieren und kalibrieren")
        self.motor_control = MotorControl(0, 0)

        print("Kamera auf 20 Grad setzen")
        self.motor_control.set_camera(20)

        print("Programm fuer Vision starten")
        # construct the argument parse and parse the arguments

        vision = Vision(self.usePiCamera > 0)

    def on_enter_to_load(self):
        print("Zum Wuerfel fahren")
        self.motor_control.drive_x(600, 100)

        print("Greifer nach unten")
        self.motor_control.drive_z(-100, 10)

    def on_enter_insert_load(self):
        print("Nach vorne fahren ca 2cm")
        self.motor_control.drive_x(20, 10)

    def on_enter_grab_load(self):
        print("Wuerfel greifen")
        self.arduino.setGrabber(SerialCommunication.GrabberState.CLOSE)
        print("Koordinatenanzeige starten")

    def on_enter_lift_load(self):
        print("Greifer nach oben")

    def on_enter_to_target(self):
        print("Fahren solange Zielplattform nicht in unterer Bildhaelfte")

    def on_enter_center_target(self):
        print("Kamera bewegen nach unten")
        print("Kamera in Ablademodus setzen")

        print("Fahren solange Zielplattform nicht mittig")

    def on_enter_set_load(self):
        print("Greifer nach unten")

    def on_enter_release_load(self):
        print("Wuerfel loslassen")

    def on_enter_lift_grabber(self):
        print("Greifer nach oben")

    def on_enter_fast_to_stop(self):
        print("Berechne restliche Fahrt")
        print("Berechnete Strecke fahren")

    def on_enter_slow_to_stop(self):
        print("Langsam fahren solange Stopp nicht erreicht")

    def on_enter_shutdown(self):
        print("Stop")

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("-p", "--picamera", type=int, default=-1,
                    help="whether or not the Raspberry Pi camera should be used")
    args = vars(ap.parse_args())

    # initiate state machine
    states = ['sleep', 'init', 'wait_for_start', 'to_load', 'insert_load', 'grab_load', 'lift_load', 'to_target',
              'center_target', 'set_load', 'release_load', 'lift_grabber', 'fast_to_stop', 'slow_to_stop', 'shutdown']
    transitions = [
        {'trigger': 'wake_up', 'source': 'sleep', 'dest': 'init'},
        {'trigger': 'init_finished', 'source': 'init', 'dest': 'wait_for_start'},
        {'trigger': 'start', 'source': 'wait_for_start', 'dest': 'to_load'},
        {'trigger': 'drive_finished', 'source': 'to_load', 'dest': 'insert_load'},
        {'trigger': 'drive_finished', 'source': 'insert_load', 'dest': 'grab_load'},
        {'trigger': 'load_grabbed', 'source': 'grab_load', 'dest': 'lift_load'},
        {'trigger': 'drive_finished', 'source': 'lift_load', 'dest': 'to_target'},
        {'trigger': 'target_is_close', 'source': 'to_target', 'dest': 'center_target'},
        {'trigger': 'target_is_centered', 'source': 'center_target', 'dest': 'set_load'},
        {'trigger': 'drive_finished', 'source': 'set_load', 'dest': 'release_load'},
        {'trigger': 'load_released', 'source': 'release_load', 'dest': 'lift_grabber'},
        {'trigger': 'drive_finished', 'source': 'lift_grabber', 'dest': 'fast_to_stop'},
        {'trigger': 'drive_finished', 'source': 'fast_to_stop', 'dest': 'slow_to_stop'},
        {'trigger': 'stop_btn_pushed', 'source': 'slow_to_stop', 'dest': 'shutdown'},
    ]

    prachtstueck = Prachtstueck(args["picamera"])
    machine = Machine(prachtstueck, states=states, transitions=transitions, initial='sleep')
    prachtstueck.wake_up()
    prachtstueck.init_finished()
    prachtstueck.start()
    print prachtstueck.state
    # create Graph -> graphviz needed!
    #prachtstueck.get_graph().draw('my_state_diagram.png', prog='dot')