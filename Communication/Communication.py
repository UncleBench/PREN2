from MessageQueue.MessageQueue import MessageQueue, Message
from SerialCommunication import SerialCommunication
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

    def initiate_communication(self):
        print "start Communication Process"
        setproctitle("Communication")
        #self.main_queue = MessageQueue(callback=self.command_interpreter, qname='main')
        self.main_queue = MessageQueue(callback=None, qname='main')
        #self.receiver_queue = MessageQueue(qname='')
        self.position_thread = Thread(target=self.update_position)
        self.pos_sensor = PosSensor()
        self.sens_act = SerialCommunication(com=self.sens_act_com)
        self.motor = MotorControl(com=self.motor_com)
        self.position_thread.start()

    def update_position(self):
        print "start position update thread"
        while True:
            sleep(1)
            self.sens_act_lock.aquire()
            raw_alpha = self.sens_act.getRawAlpa()
            raw_beta = self.sens_act.getRawBeta()
            battery_voltage = self.sens_act.getBatteryVoltage()
            self.sens_act_lock.release()

            self.motor_lock.aquire()
            #driven_dist = self.motor.get_distance_driven()
            driven_dist = {'x': 20.0, 'z': 20.0}
            self.motor_lock.release()

            pos = self.pos_sensor.get_pos_load_by_raw(raw_alpha, raw_beta, driven_dist['x'], driven_dist['z'])

            msg = Message("Position", [pos.x, pos.z, battery_voltage])
            #self.receiver_queue.send(msg)
            self.position_thread.send(msg)


    def command_interpreter(self, command):
        meth = getattr(self, command['cmd'])
        meth(*command['data'])