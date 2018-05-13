import time
from MessageQueue.MessageQueue import MessageQueue, Message
from Communication.Communication import Communication


def interpret_command(msg):
    print msg

if __name__ == '__main__':
    main_queue = MessageQueue(callback=interpret_command, qname='ps_main')
    comm_queue = MessageQueue(qname='ps_communication')
    try:
        comm = Communication(sens_act_com='/dev/SensorActor', motor_com='/dev/Motor')
        time.sleep(15.0)
        comm.shutdown()
        comm.worker.join()
        main_queue.shutdown()
    except KeyboardInterrupt:
        comm.shutdown()
        main_queue.shutdown()
        exit()
