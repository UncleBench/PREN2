from numpy import *

class Position:
    def __init__(self, x, z):
        """
        Args:
            x (float): [cm] x Position
            y (float): [cm] t Position

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
        self.l = sqrt(square(self.b - self.a) + square(self.k)) # Laenge Seil

class Prachtstueck:
    def __init__(self, offsetDrive, offsetElevator, d=30.0, u=13.93, v=6.9, ap=-2.725, lp=8.3):
        """
        Args:
            offsetDrive (float): [cm] offset of the drive distance (already driven distance on the rope)
            offsetElevator (float): [cm] offset of the elevation distance (already lowered distance of the "claw")
            d (float): [cm] distance between the two wheel shafts (alpha and beta)
            u (float): [cm] horizontal distance between elevator wheel shaft and drive wheel shaft
            v (float): [cm] vertical distance between elevator wheel shaft and top of rope
            ap (float): [cm] vertical distance between top of rope and angle sensor shaft
            lp (float): [cm] length of the angle sensor lever

        Returns:
            Prachtstueck: instance
        """
        # dimensions of the "Prachtstueck"
        self.d = d                                  # Abstand zwischen Rollen
        self.u = u                                  # vertikale Distanz Seilwinde - obere Rolle
        self.v = v                                  # horizontale Distanz Seilwinde - obere Rolle
        self.ap = ap                                # vertikale Distanz Drehpunkt Winkelsensor zu unterer Seilflaeche
        self.lp = lp                                # Laenge des Hebels (Drehpunkt Poti bis Kontakt mit Seil)
        self.bp = sqrt(square(self.lp)-square(self.ap)) # Horizontale Distanz Drehpunkt Poti bis Kontakt Seil (Bei 0Grad Winkel)

        self.offsetDrive = offsetDrive
        self.offsetElevator = offsetElevator

class AngleSensor:
    def __init__(self, offsetValue, radPerValue):
        """
        Args:
            offsetValue (float): [cm] AD-raw-value when angle-sensor lever is vertical
            radPerValue (float): [cm] radiants per AD-raw-value -> Sensor: 5k, 340deg ; 3.3V, 12Bit ADC
                                 -> (340*pi/180)/(2^12) = 1448.75*10E-6

        Returns:
            AngleSensor: instance
        """
        # initial angle sensor data
        self.offsetValue = offsetValue
        self.radPerValue = radPerValue

    def getRadiants(self, rawValue):
        """converts a raw sensor value into an angle in radiants depending on the set offsetValue and radPerValue
        Args:
            rawValue (int): raw ADC value of the angle sensor

        Returns:
            float: measured angle in radiants
        """
        return (rawValue - self.offsetValue) * self.radPerValue

class PosSensor:
    def __init__(self, platform=None, prachtstueck=None, alphaSensor=None, betaSensor=None):
        self.platform = platform
        if self.platform is None:
            self.platform = Platform()
        self.prachtstueck = prachtstueck
        if self.prachtstueck is None:
            self.prachtstueck = Prachtstueck(10.0, 10.0)
        self.alphaSensor = alphaSensor
        if self.alphaSensor is None:
            self.alphaSensor = AngleSensor(2109.0, 0.001091)
        self.betaSensor = betaSensor
        if self.betaSensor is None:
            self.betaSensor = AngleSensor(2489.0, -0.001091)

    def getPosPrachtstueck(self, rawAlpha, rawBeta, drivenRopeDistance):
        """calculates and returns the position of the "Prachtstueck" (shaft of the elevator motor; not the load!!!)
        Args:
            rawAlpha (int): raw ADC value of the alpha angle sensor
            rawBeta (int): raw ADC value of the beta angle sensor
            drivenRopeDistance (float): driven distance on the rope in [cm]

        Returns:
            Position: x and z Position of the "Prachtstueck" (shaft of the elevator motor)
        """
        position = Position(0.0, 0.0)
        zeta = arctan2(self.platform.k, self.platform.b - self.platform.a)
        alpha = self.angleCorrection(self.alphaSensor.getRadiants(rawAlpha))
        beta = self.angleCorrection(self.betaSensor.getRadiants(rawBeta))

        gamma = pi - alpha - beta
        ds = self.prachtstueck.d * sin(beta) / sin(gamma)
        s_tot = drivenRopeDistance + ds
        delta = arcsin(sin(gamma) * s_tot/self.platform.l)
        epsilon = pi - gamma - delta
        eta = zeta - epsilon
        p = drivenRopeDistance * sin(eta)
        q = drivenRopeDistance * cos(eta)
        theta = pi/2 - eta - alpha

        position.x = self.platform.k - p - (self.prachtstueck.u * cos(theta) - self.prachtstueck.v * sin(theta))
        position.z = self.platform.b - q - (self.prachtstueck.u * sin(theta) + self.prachtstueck.v * cos(theta))

        return position

    def getPosLoadByRaw(self, rawAlpha, rawBeta, drivenRopeDistance, elevatorDistance):
        """returns position of the load
        Args:
            rawAlpha (int): raw ADC value of the alpha angle sensor
            rawBeta (int): raw ADC value of the beta angle sensor
            drivenRopeDistance (float): driven distance on the rope in [cm]
            elevatorDistance (float): driven distance on the z axis in [cm]

        Returns:
            Position: x and z Position of the "Load"
        """
        return self.getPosLoadRel(self.getPosPrachtstueck(rawAlpha, rawBeta, drivenRopeDistance), elevatorDistance)

    def getPosLoadRel(self, posPrachtstueck, elevatorDistance):
        """returns position of the load
        Args:
            posPrachtstueck (Position): Position of the "Prachtstueck"
            elevatorDistance (float): driven distance on the z axis in [cm]

        Returns:
            Position: x and z Position of the "Load"
        """
        return Position(posPrachtstueck.x, posPrachtstueck.z - elevatorDistance + self.prachtstueck.offsetElevator)

    def angleCorrection(self, angle):
        """corrects the measuread angle
        Args:
            angle (float): [rad] Uncorrected angle straight from the angle sensor

        Returns:
            float: [rad] corrected angle
        """
        if angle == 0.0:
            angle = 0.000001
        beta_0 = arccos(self.prachtstueck.ap/self.prachtstueck.lp)   # Winkel zwischen Hebel und Horizontale (Bei 0Grad)
        beta = beta_0 - angle                  # Winkel zwischen Hebel und Horizontale (Bei Auslenkung)
        cp = sqrt(square(self.prachtstueck.lp)+square(self.prachtstueck.ap)-2*self.prachtstueck.lp*self.prachtstueck.ap*cos(beta))     # Distanz Aufhaengung zu Kontaktpunkt Hebel - Seil

        correctedAngle = pi/2.0-arcsin(self.prachtstueck.lp*sin(beta)/cp)              # Winkel Drahtseil
        return correctedAngle


if __name__ == '__main__':
    posSensor = PosSensor()
    alpha = 6.09
    beta = 22.359
    alpha_ = (alpha / (-0.00117507316)) * pi/180 + 2163.0
    beta_ = (beta / (0.00127890506)) * pi/180 + 2178.0
    position = posSensor.getPosPrachtstueck(alpha_, beta_, 166.771)
    print(position.x, position.z)