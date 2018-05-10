from Vision.Vision import Vision
from Communication.SerialCommunication import StopState, GrabberState
from MessageQueue.MessageQueue import MessageQueue, Message
from Communication.Communication import Communication
from transitions.extensions import GraphMachine as Machine

class Prachtstueck():
    def __init__(self):
        self.communication_queue = MessageQueue(callback=None, qname='ps_communication')
        self.vision_queue = MessageQueue(callback=None, qname='ps_vision')
        self.gui_queue = MessageQueue(callback=None, qname='ps_gui')

    def on_enter_init(self):
        print("Kommunikation Arduino Greifer, Whisker, Position, Batterie Raspi initialisieren")

        print("Arduino Motorensteuerung initialisieren und kalibrieren")

        print("Kamera auf 20 Grad setzen")

        print("Programm fuer Vision starten")
        self.vision_queue(Message('start'))

    def on_enter_to_load(self):
        print("Zum Wuerfel fahren")
        self.communication_queue.send(Message('drive_x', [30, 10000]))

        print("Greifer nach unten")
        self.communication_queue.send(Message('drive_z', [-30, 10000]))

    def on_enter_insert_load(self):
        print("Nach vorne fahren ca 2cm")
        self.communication_queue.send(Message('drive_x', [20, 10000]))

    def on_enter_grab_load(self):
        print("Wuerfel greifen")
        self.communication_queue.send(Message('setGrabber', [GrabberState.CLOSE]))
        print("Koordinatenanzeige starten")
        self.gui_queue.send(Message('start_coord'))


    def on_enter_lift_load(self):
        print("Greifer nach oben")
        self.communication_queue.send(Message('drive_z', [-20, 10000]))

    def on_enter_to_target(self):
        print("Fahren solange Zielplattform nicht in unterer Bildhaelfte")
        self.communication_queue.send(Message('drive_x', [200, 30000]))

    def on_enter_center_target(self):
        print("Kamera bewegen nach unten")
        print("Kamera in Ablademodus setzen")

        self.communication_queue.send(Message('stop'))
        self.communication_queue.send(Message('drive_x', [30, 10000]))
        print("Fahren solange Zielplattform nicht mittig")

    def on_enter_set_load(self):
        print("Greifer nach unten")
        self.communication_queue.send(Message('stop'))
        self.communication_queue.send(Message('drive_z', [40, 10000]))

    def on_enter_release_load(self):
        print("Wuerfel loslassen")
        self.communication_queue.send(Message('setGrabber', [GrabberState.OPEN]))

    def on_enter_lift_grabber(self):
        print("Greifer nach oben")
        self.communication_queue.send(Message('drive_z', [20, 10000]))

    def on_enter_fast_to_stop(self):
        print("Berechne restliche Fahrt")
        print("Berechnete Strecke fahren")
        self.communication_queue.send(Message('drive_x', [50, 30000]))

    def on_enter_slow_to_stop(self):
        print("Langsam fahren solange Stopp nicht erreicht")
        self.communication_queue.send(Message('drive_x', [10, 30000]))

    def on_enter_shutdown(self):
        print("Stop")
        self.communication_queue.send(Message('stop'))
        #self.kill()

class Parser():
    def __init__(self, state_machine):
        self.state_machine = state_machine

    def interpret_command(self, msg):
        print "message received"

        if self.state_machine.is_init():
            if msg['command'] is 'init_finished':
                self.state_machine.init_finished()

        if self.state_machine.is_wait_for_start():
            if msg['command'] is 'start':
                self.state_machine.start()

        if self.state_machine.is_to_load():
            if msg['command'] is 'Position':
                print "Position:", msg['data']

        if self.state_machine.is_insert_load():
            if msg['command'] is 'Position':
                print "Position:", msg['data']

        if self.state_machine.is_to_target():
            if msg['command'] is 'target_found':
                print "target found"
                self.state_machine.target_is_close()

        if self.state_machine.is_center_target():
            if msg['command'] is 'target_centered':
                print "target centered"
                self.state_machine.target_is_centered()

        if self.state_machine.slow_to_stop():
            if msg['command'] is 'stop':
                self.state_machine.stop_btn_pushed()


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
    main_queue = MessageQueue(callback=parser.interpret_command(), qname='ps_main')

    # init Vision
    print "init Vision"
    vision = Vision(callback=parser.interpret_command, usePiCamera=True, debug=False)

    # init Communication
    print "init Communication"
    #communication = Communication(sens_act_com='/dev/SensorActor', motor_com='/dev/Motor')

    #prachtstueck = Prachtstueck(args["picamera"])
    #prachtstueck.wake_up()
    #prachtstueck.init_finished()
    #prachtstueck.start()
    #print prachtstueck.state
    # create Graph -> graphviz needed!
    #prachtstueck.get_graph().draw('my_state_diagram.png', prog='dot')