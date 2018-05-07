from numpy import *
import json


class Position:
    def __init__(self, x, z):
        """
        Args:
            x (float): [cm] x Position
            z (float): [cm] t Position

        Returns:
            Position: instance
        """
        self.x = x
        self.z = z


class Platform:
    def __init__(self, k=340.0, b=110.0, a=61.4):
        """
        Args:
            k (float): [cm] horizontal distance of the two poles
            a (float): [cm] height of the starting mast
            b (float): [cm] height of the ending mast

        Returns:
            Platform: instance
        """
        # dimensions of the platform
        self.k = k      # +-2 Distanz Startmast Endmast
        self.b = b      # +-2 hoehe Endmast
        self.a = a      # +-2 hoehe Startmast
        self.rope_length = sqrt(square(self.b - self.a) + square(self.k))       # Laenge Seil


class PrachtstueckDimensions:
    def __init__(self, offset_drive, offset_elevator, d=30.0, u=13.93, v=6.9, ap=-2.725, lp=8.3):
        """
        Args:
            offset_drive (float): [cm] offset of the drive distance (already driven distance on the rope)
            offset_elevator (float): [cm] offset of the elevation distance (already lowered distance of the "claw")
            d (float): [cm] distance between the two wheel shafts (front and back)
            u (float): [cm] horizontal distance between joint and front wheel shaft
            v (float): [cm] vertical distance between joint and bottom of rope
            ap (float): [cm] vertical distance between bottom of rope and angle sensor shaft
            lp (float): [cm] length of the angle sensor lever

        Returns:
            PrachtstueckDimensions: instance
        """
        # dimensions of the "Prachtstueck"
        self.d = d
        self.u = u
        self.v = v
        self.ap = ap
        self.lp = lp
        self.bp = sqrt(square(self.lp)-square(self.ap))     # initial hor. dist. between front shaft and lever cont.

        self.offset_drive = offset_drive
        self.offset_elevator = offset_elevator


class AngleSensor:
    def __init__(self, offset_value, rad_per_value):
        """
        Args:
            offset_value (float): [cm] AD-raw-value when angle-sensor lever is vertical
            rad_per_value (float): [cm] radiants per AD-raw-value -> Sensor: 5k, 340deg ; 3.3V, 12Bit ADC
                                 -> (340*pi/180)/(2^12) = 1448.75*10E-6

        Returns:
            AngleSensor: instance
        """
        # initial angle sensor data
        self.offset_value = offset_value
        self.rad_per_value = rad_per_value

    def get_radiants(self, raw_value):
        """converts a raw sensor value into an angle in radiants depending on the set offsetValue and radPerValue
        Args:
            raw_value (int): raw ADC value of the angle sensor

        Returns:
            float: measured angle in radiants
        """
        return (raw_value - self.offset_value) * self.rad_per_value


class PosSensor:
    def __init__(self, platform=None, prachtstueck=None, alpha_sensor=None, beta_sensor=None):
        self.platform = platform
        with open('sensor_cal_data.cal', 'r') as file:
            json_parsed = json.loads(file.read())
        if self.platform is None:
            self.platform = Platform()
        self.prachtstueck_dim = prachtstueck
        if self.prachtstueck_dim is None:
            self.prachtstueck_dim = PrachtstueckDimensions(10.0, 10.0)
        self.alpha_sensor = alpha_sensor
        if self.alpha_sensor is None:
            self.alpha_sensor = AngleSensor(json_parsed["raw_alpha_0_avg"], json_parsed["sensitivity_avg"])  #0.001091)
        self.beta_sensor = beta_sensor
        if self.beta_sensor is None:
            self.beta_sensor = AngleSensor(json_parsed["raw_beta_0_avg"], -json_parsed["sensitivity_avg"])   #-0.001091)

    def get_pos_prachtstueck(self, raw_alpha, raw_beta, driven_rope_distance):
        """calculates and returns the position of the "Prachtstueck" (shaft of the elevator motor; not the load!!!)
        Args:
            raw_alpha (int): raw ADC value of the alpha angle sensor
            raw_beta (int): raw ADC value of the beta angle sensor
            driven_rope_distance (float): driven distance on the rope in [cm]

        Returns:
            Position: x and z Position of the "Prachtstueck" (shaft of the elevator motor)
        """
        position = Position(0.0, 0.0)
        zeta = arctan2(self.platform.k, self.platform.b - self.platform.a)
        alpha = self.angle_correction(self.alpha_sensor.get_radiants(raw_alpha))
        beta = self.angle_correction(self.beta_sensor.get_radiants(raw_beta))

        gamma = pi - alpha - beta
        ds = self.prachtstueck_dim.d * sin(beta) / sin(gamma)
        s_tot = driven_rope_distance + ds
        delta = arcsin(sin(gamma) * s_tot/self.platform.rope_length)
        epsilon = pi - gamma - delta
        eta = zeta - epsilon
        p = driven_rope_distance * sin(eta)
        q = driven_rope_distance * cos(eta)
        theta = pi/2 - eta - alpha

        position.x = self.platform.k - p - (self.prachtstueck_dim.u * cos(theta) - self.prachtstueck_dim.v * sin(theta))
        position.z = self.platform.b - q - (self.prachtstueck_dim.u * sin(theta) + self.prachtstueck_dim.v * cos(theta))

        return position

    def get_pos_load_by_raw(self, raw_alpha, raw_beta, driven_rope_distance, elevator_distance):
        """returns position of the load
        Args:
            raw_alpha (int): raw ADC value of the alpha angle sensor
            raw_beta (int): raw ADC value of the beta angle sensor
            driven_rope_distance (float): driven distance on the rope in [cm]
            elevator_distance (float): driven distance on the z axis in [cm]

        Returns:
            Position: x and z Position of the "Load"
        """
        return self.get_pos_load_rel(self.get_pos_prachtstueck(raw_alpha, raw_beta, driven_rope_distance),
                                     elevator_distance)

    def get_pos_load_rel(self, pos_prachtstueck, elevator_distance):
        """returns position of the load
        Args:
            pos_prachtstueck (Position): Position of the "Prachtstueck"
            elevator_distance (float): driven distance on the z axis in [cm]

        Returns:
            Position: x and z Position of the "Load"
        """
        return Position(pos_prachtstueck.x, pos_prachtstueck.z - elevator_distance + self.prachtstueck_dim.offset_elevator)

    def angle_correction(self, angle):
        """corrects the measuread angle
        Args:
            angle (float): [rad] Uncorrected angle straight from the angle sensor

        Returns:
            float: [rad] corrected angle
        """
        if angle == 0.0:
            angle = 0.000001
        beta_0 = arccos(self.prachtstueck_dim.ap / self.prachtstueck_dim.lp) # angle between lever and horizon (at 0deg)
        beta = beta_0 - angle                                                # angle between lever and horizon (in use)
        # dist. joint to lever-rope contact point
        cp = sqrt(square(self.prachtstueck_dim.lp) + square(self.prachtstueck_dim.ap)
                  - 2 * self.prachtstueck_dim.lp * self.prachtstueck_dim.ap * cos(beta))
        corrected_angle = pi/2.0-arcsin(self.prachtstueck_dim.lp * sin(beta) / cp)   # angle of the rope
        return corrected_angle


if __name__ == '__main__':
    posSensor = PosSensor()
    alpha = 6.09
    beta = 22.359
    alpha_ = (alpha / (-0.00117507316)) * pi/180 + 2163.0
    beta_ = (beta / 0.00127890506) * pi/180 + 2178.0
    position = posSensor.get_pos_prachtstueck(alpha_, beta_, 166.771)
    print(position.x, position.z)
