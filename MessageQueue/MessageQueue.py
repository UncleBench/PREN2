from kombu import Connection
from contextlib import closing
from multiprocessing import Process
from setproctitle import setproctitle

class MessageQueue(object):
    def __init__(self, callback):
        self.active = True
        self.sender = Connection('amqp://').SimpleBuffer('psMQ')
        self.receiver = Connection('amqp://').SimpleBuffer('psMQ')
        self.worker = Process(target=self.receive, name='MessageQueue',
                        args=(callback,))
        self.worker.start()

    def receive(self, callback):
        setproctitle('MessageQueue')
        while self.active:
            message = self.receiver.get(block=True, timeout=None)
            if message:
                if message.payload == '__QX':
                    self.active = False
                else:
                    callback(message.payload)
        self.receiver.close()

    def send(self, message):
        self.sender.put(message, serializer='json', compression=None)
        
    def shutdown(self):
        self.send('__QX')
        self.sender.close()

class Message():
    def __init__(self, command, data):
        self.command = command
        self.data = data