from Vision.Vision import Vision
from MessageQueue.MessageQueue import MessageQueue
from Communication.Communication import Communication
from transitions.extensions import GraphMachine as Machine
import argparse

class Prachtstueck():
    def __init__(self):
        pass
        #self.main_queue = MessageQueue(callback=parser.interpret_command, )

    def on_enter_init(self):
        print("Kommunikation Arduino Greifer, Whisker, Position, Batterie Raspi initialisieren")

        print("Arduino Motorensteuerung initialisieren und kalibrieren")

        print("Kamera auf 20 Grad setzen")

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
        #self.arduino.setGrabber(SerialCommunication.GrabberState.CLOSE)
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


class Parser():
    def __init__(self, state_machine):
        self.state_machine = state_machine

    def interpret_command(self, msg):
        if msg['command'] is 'Position':
            print "Position:", msg['data']
        elif msg['command'] is 'target_found':
            print "target found"
        elif msg['command'] is 'target_centered':
            print "target centered"
        #if command is "wake_up":
        #    self.state_machine.wake_up()
        #elif command is "init_finished":
        #    self.state_machine.init_finished()
        #elif command is "start":
        #    self.state_machine.start()
        #else:
        #    print "Can't parse command: ", command

if __name__ == '__main__':

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
    print "init state machine"
    prachtstueck = Prachtstueck()
    machine = Machine(prachtstueck, states=states, transitions=transitions, initial='sleep')

    # init Parser
    print "init Parser"
    parser = Parser(prachtstueck)

    print "init Message Queue"
    #msg_queue = MessageQueue(callback=parser.interpret_command)
    main_queue = MessageQueue(qname='main', callback=parser.interpret_command)

    # init Vision
    print "init Vision"
    vision = Vision(callback=parser.interpret_command, usePiCamera=True, debug=False)

    # init Communication
    print "init Communication"
    communication = Communication(sens_act_com='/dev/SensorActor', motor_com='/dev/Motor')

    #prachtstueck = Prachtstueck(args["picamera"])
    #prachtstueck.wake_up()
    #prachtstueck.init_finished()
    #prachtstueck.start()
    #print prachtstueck.state
    # create Graph -> graphviz needed!
    #prachtstueck.get_graph().draw('my_state_diagram.png', prog='dot')