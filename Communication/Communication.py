from MessageQueue.MessageQueue import MessageQueue, Message
from GUI import GUI
from SerialCommunication import SerialCommunication, StopState
from MotorControl import MotorControl
from PositionDetermination.PosSensor import PosSensor
from multiprocessing import Process
from threading import Thread, RLock
from time import sleep
from setproctitle import setproctitle

class Communication():
    def __init__(self, sens_act_com, motor_com):
        self.sens_act_com = sens_act_com
        self.motor_com = motor_com

        self.worker = Process(target=self.initiate_communication, name='Communication')
        self.sens_act_lock = RLock()
        self.motor_lock = RLock()
        self.worker.start()

        self.last_state = None

    def initiate_communication(self):
        print "start Communication Process"
        setproctitle("Communication")

        self.main_queue = MessageQueue(qname='ps_main')
        self.gui_queue = GUI()
        self.communication_queue = MessageQueue(callback=self.command_interpreter, qname='ps_communication')

        self.position_thread = Thread(target=self.update_position, name="Position Update")
        self.pos_sensor = PosSensor()
        self.sens_act = SerialCommunication(com=self.sens_act_com)
        self.motor = MotorControl(com=self.motor_com)
        self.position_thread.start()
        self.position_thread.join()

    def update_position(self):
        print "start position update thread"
        while True:
            sleep(1)
            self.sens_act_lock.acquire()
            raw_alpha = self.sens_act.getRawAlpha()
            raw_beta = self.sens_act.getRawBeta()
            battery_voltage = self.sens_act.getBatteryVoltage()
            stop_state = self.sens_act.getStopState()
            self.sens_act_lock.release()

            self.motor_lock.acquire()
            #driven_dist = self.motor.get_pos_decoded()
            driven_dist = ("Idle", {'x': 20.0, 'z': 20.0})
            self.motor_lock.release()

            if stop_state is StopState.STOP:
                self.gui_queue.send(Message('stop', []))
                self.main_queue.send(Message('stop', []))

            state = driven_dist[0]
            pos = self.pos_sensor.get_pos_load_by_raw(raw_alpha, raw_beta, 343.46-driven_dist[1]['x']/10, driven_dist[1]['z']/10)

            if self.last_state != state:
                self.gui_queue.send(Message('motor_state', [state]))

            data = [pos.x, pos.z, battery_voltage]
            self.gui_queue.update(*data)
            data.append(pos.s)
            self.main_queue.send(Message("Position", data))

            self.last_state = state

    def command_interpreter(self, command):
        if hasattr(self.motor, command['cmd']):
            meth = getattr(self.motor, command['cmd'])
        else:
            meth = getattr(self.sens_act, command['cmd'])
        meth(*command['data'])