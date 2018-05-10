from kombu import Connection
from threading import Thread

class MessageQueue(object):
    def __init__(self, qname, callback=None):
        self.active = True
        self.qname = qname
        self.sender = Connection('amqp://').SimpleBuffer(self.qname)
        if not callback is None:
            self.receiver = Connection('amqp://').SimpleBuffer(self.qname)
            self.worker = Thread(target=self.receive, name='MQ'+self.qname,
                                 args=(callback,))
            self.worker.start()

    def receive(self, callback):
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
