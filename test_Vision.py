import time
from MessageQueue.MessageQueue import MessageQueue, Message
from Vision.Vision import Vision


def interpret_command(msg):
    if msg['command'] == 'target_found':
        print "target found"
    if msg['command'] == 'target_centered':
        print "target centered @ %f" % msg['data']['y_ratio']

if __name__ == '__main__':
    main_queue = MessageQueue(callback=interpret_command, qname='ps_main')
    vision_queue = MessageQueue(qname='ps_vision')
    try:
        vision = Vision(usePiCamera=True, debug=False)
        time.sleep(2.0)
        vision_queue.send(Message('start'))
        time.sleep(15.0)
        vision_queue.send(Message('stop'))
        time.sleep(2.0)
        vision_queue.send(Message('start'))
        time.sleep(15.0)
        vision_queue.send(Message('shutdown'))
        vision.worker.join()
        main_queue.shutdown()
    except KeyboardInterrupt:
        vision_queue.send(Message('shutdown'))
        main_queue.shutdown()
        exit()
