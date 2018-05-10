from flask_socketio import SocketIO

class GUI():
    def __init__(self):
        self.socket = SocketIO(message_queue='amqp://')

    def update(self, x_pos, z_pos, voltage):
        self.socket.emit('gui_update', {'x_pos': x_pos, 'z_pos': z_pos, 
                                        'voltage': voltage})