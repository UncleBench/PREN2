import time
from MessageQueue.MessageQueue import MessageQueue, Message
from Vision.Vision import Vision


def interpret_command(msg):
    if msg['command'] is 'target_found':
        print "target found"
    if msg['command'] is 'target_centered':
        print "target centered"

if __name__ == '__main__':
    main_queue = MessageQueue(callback=interpret_command, qname='ps_main')
    vision_queue = MessageQueue(qname='ps_vision')
    vision = Vision(usePiCamera=True, debug=False)
    time.sleep(2.0)
    vision_queue.send(Message('start'))