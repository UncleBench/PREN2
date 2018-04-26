class MotorControl:
    def __init__(self, x0, z0):
        self.x = x0
        self.z = z0


    def drive_x(self, distance, speed):
        pass


    def drive_z(self, distance, speed):
        pass


    def get_distance_driven(self):
        return self.x, self.z


    def move_camera(self, deg):
        pass