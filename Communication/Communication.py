from MessageQueue.MessageQueue import MessageQueue, Message
from GUI import GUI
from SerialCommunication import SerialCommunication, StopState
from MotorControl import MotorControl
from PositionDetermination.PosSensor import PosSensor
from multiprocessing import Process, Event
from threading import Thread, Lock
from time import sleep
from setproctitle import setproctitle

class Communication():
    def __init__(self, sens_act_com, motor_com):
        self.sens_act_com = sens_act_com
        self.motor_com = motor_com
        self.shutdown_flag = Event()

        self.worker = Process(target=self.initiate_communication, name='Communication')
        self.worker.start()

    def shutdown(self):
        self.shutdown_flag.set()

    def initiate_communication(self):
        print "start Communication Process"
        setproctitle("Communication")

        self.last_state = None
        self.main_queue = MessageQueue(qname='ps_main')
        self.gui_queue = GUI()

        self.pos_sensor = PosSensor()
        self.sens_act = SerialCommunication(com=self.sens_act_com)
        self.motor = MotorControl(com=self.motor_com)

        self.communication_queue = MessageQueue(callback=self.command_interpreter, qname='ps_communication')

        self.sens_act_lock = Lock()
        self.motor_lock = Lock()
        self.position_thread = Thread(target=self.update_position, name="Position Update",
                                        args=(self.sens_act_lock, self.motor_lock))
        self.position_thread.start()
        self.position_thread.join()

    def update_position(self, sens_act_lock, motor_lock):
        print "start position update thread"
        while not self.shutdown_flag.is_set():
            sleep(0.2)
            sens_act_lock.acquire()
            raw_alpha = self.sens_act.getRawAlpha()
            raw_beta = self.sens_act.getRawBeta()
            battery_voltage = self.sens_act.getBatteryVoltage()
            stop_state = self.sens_act.getStopState()
            sens_act_lock.release()

            motor_lock.acquire()
            driven_dist = self.motor.get_pos_decoded()
            #driven_dist = ("Idle", {'x': 20.0, 'z': 20.0})
            motor_lock.release()

            if stop_state is StopState.STOP:    # TODO maybe bugix needed (gui_queue is from different class now) -> update -> might be ok
                self.gui_queue.send(Message('stop'))
                self.main_queue.send(Message('stop'))

            state = driven_dist[0]
            # TODO outsource 343.46 to PosSensor class (as offset value), change value to actual value
            pos = self.pos_sensor.get_pos_load_by_raw(raw_alpha, raw_beta, driven_dist[1]['x']/10, driven_dist[1]['z']/10)
            print raw_alpha, raw_beta, driven_dist[1]['x']/10, driven_dist[1]['z']/10

            if self.last_state != state:
                self.main_queue.send(Message('motor_state', state))

            data = [pos.x, pos.z, battery_voltage]
            self.gui_queue.update(*data)
            data.append(pos.s)
            self.main_queue.send(Message("Position", data))

            self.last_state = state

        self.communication_queue.shutdown()

    def command_interpreter(self, command):
        if hasattr(self.motor, command['command']):
            meth = getattr(self.motor, command['command'])
            self.motor_lock.acquire()
            if 'data' in command:
                meth(*command['data'])
            else:
                meth()
            self.motor_lock.release()
        elif hasattr(self.sens_act, command['command']):
            meth = getattr(self.sens_act, command['command'])
            self.sens_act_lock.acquire()
            if 'data' in command:
                meth(*command['data'])
            else:
                meth()
            self.sens_act_lock.release()
        elif hasattr(self, command['command']):
            meth = getattr(self, command['command'])
            if 'data' in command:
                meth(*command['data'])
            else:
                meth()
        else:
            raise ValueError('Unknown command')
