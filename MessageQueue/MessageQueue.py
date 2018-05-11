from kombu import Connection
from threading import Thread
import json

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

class Message(object):
    def __new__(cls, *args, **kwargs):
        msg = super(Message, cls).__new__(cls)
        msg.__init__(*args, **kwargs)
        return msg.__dict__
        
    def __init__(self, command, data=None):
        self.command = command
        if not data is None:
            try:
                json.dumps(data)
                self.data = data
            except TypeError:
                self.data = data.__dict__
