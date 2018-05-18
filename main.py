from Vision.Vision import Vision
from PositionDetermination.PosSensor import Position
from MessageQueue.MessageQueue import MessageQueue, Message
from GUI import GUI
from Communication.Communication import Communication
from transitions.extensions import GraphMachine as Machine
from transitions import MachineError
from time import sleep

import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('transitions').setLevel(logging.INFO)
logging.getLogger('socketio').setLevel(logging.ERROR)

class Prachtstueck():
    def __init__(self):
        self.communication_queue = MessageQueue(qname='ps_communication')
        self.vision_queue = MessageQueue(qname='ps_vision')
        self.gui_queue = GUI()
        print "init Message Queue"
        self.main_queue = MessageQueue(callback=self.interpret_command, qname='ps_main')

        self.position = Position(0, 0, 0)
        self.batteryVoltage = 0.0

    def on_enter_init(self):
        print("Kommunikation Arduino Greifer, Whisker, Position, Batterie Raspi initialisieren")
        self.communication_queue.send(Message('setGrabber', [100]))

        print("Arduino Motorensteuerung initialisieren und kalibrieren")
        self.communication_queue.send(Message('home'))

        print("Kamera auf 20 Grad setzen")
        self.communication_queue.send(Message('set_camera', [72]))

        print("Programm fuer Vision starten")

        self.init_finished()

    def on_enter_to_load(self):
        print("Zum Wuerfel fahren and Greifer nach unten")
        self.communication_queue.send(Message('drive', [300, -300, 3500])) #- (self.position.z-20)

    def on_enter_insert_load(self):
        print("Nach vorne fahren ca 2cm")
        self.communication_queue.send(Message('drive_x', [20, 3500]))

    def on_enter_grab_load(self):
        print("Wuerfel greifen")
        self.communication_queue.send(Message('setGrabber', [9]))
        print("Koordinatenanzeige starten")
        self.gui_queue.send(Message('show_coord', True))
        sleep(1)
        self.load_grabbed()


    def on_enter_lift_load(self):
        print("Greifer nach oben")
        self.communication_queue.send(Message('drive_z_to_home', [10000]))

    def on_enter_to_target(self):
        print("Fahren solange Zielplattform nicht in unterer Bildhaelfte")
        self.vision_queue.send(Message('start'))
        self.communication_queue.send(Message('drive_x', [(300-self.position.x)*10, 8000]))

    def on_enter_center_target(self):
        print("Kamera bewegen nach unten")
        print("Kamera in Ablademodus setzen")

        self.communication_queue.send(Message('stop'))
        self.communication_queue.send(Message('set_camera', [90]))
        self.communication_queue.send(Message('drive_x', [400, 2000]))
        print("Fahren solange Zielplattform nicht mittig")

    def on_enter_set_load(self):
        print("Greifer nach unten")
        self.vision_queue.send(Message('stop'))
        self.communication_queue.send(Message('stop'))
        self.communication_queue.send(Message('drive', [30, -(self.position.z*10-20), 3500])) #-

    def on_enter_release_load(self):
        print("Wuerfel loslassen")
        self.communication_queue.send(Message('setGrabber', [100]))
        sleep(2)
        self.gui_queue.send(Message('show_coord', False))
        self.load_released()

    def on_enter_lift_grabber(self):
        print("Greifer nach oben")
        self.communication_queue.send(Message('drive_z_to_home', [10000]))

    def on_enter_fast_to_stop(self):
        print("Berechne restliche Fahrt")
        print("Berechnete Strecke fahren")
        self.communication_queue.send(Message('drive_x', [(300-self.position.x)*10, 10000])) #self.position.x-20

    def on_enter_slow_to_stop(self):
        print("Langsam fahren solange Stopp nicht erreicht")
        self.communication_queue.send(Message('drive_x', [1000, 1000]))

    def on_enter_shutdown(self):
        print("Stop")
        self.communication_queue.send(Message('stop'))
        self.vision_queue.send(Message('shutdown'))
        self.communication_queue.send(Message('shutdown'))
        self.main_queue.shutdown()

    def interpret_command(self, msg):
        if self.is_sleep():
            if msg['command'] == 'home':
                self.wake_up()

        if self.is_init():
            if msg['command'] == 'init_finished':
                self.init_finished()

        if self.is_wait_for_start():
            if msg['command'] == 'start':
                self.start()

        if self.is_to_target():
            if msg['command'] == 'target_found':
                print "target found"
                self.target_is_close()

        if self.is_center_target():
            if msg['command'] == 'target_centered':
                print "target centered"
                self.target_is_centered()

        if msg['command'] == 'stop':
            self.to_shutdown()

        if msg['command'] == 'motor_state':
            if msg['data'] == 'Idle':
                try:
                    self.drive_finished()
                except MachineError:
                    print "drive_finished() not valid in this state"

        if msg['command'] == 'Position':
            self.position.x = msg['data'][0]
            self.position.z = msg['data'][1]
            self.batteryVoltage = msg['data'][2]

        if msg['command'] == 'goto':
            print "goto command is not implemented yet"

        if (msg['command'] == 'drive') or (msg['command'] == 'set_camera'):
            self.communication_queue.send(msg)

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

    # init Communication
    print "init Communication"
    communication = Communication(sens_act_com='/dev/SensorActor', motor_com='/dev/Motor')

    # init Vision
    print "init Vision"
    vision = Vision(usePiCamera=True, debug=False)

    #prachtstueck = Prachtstueck(args["picamera"])
    #prachtstueck.wake_up()
    #prachtstueck.init_finished()
    #prachtstueck.start()
    #print prachtstueck.state
    # create Graph -> graphviz needed!
    #prachtstueck.get_graph().draw('my_state_diagram.png', prog='dot')