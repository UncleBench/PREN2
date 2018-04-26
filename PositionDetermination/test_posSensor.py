from unittest import TestCase
from PosSensor import*


class TestPosSensor(TestCase):
    def setUp(self):
        platform = Platform(k=340.0, b=110.0, a=61.4)
        self.prachtstueck = Prachtstueck(10.0, 10.0, r_1=1.0, r_2=1.0, d=21.5, u=10.75, v=2.7, ap=2.7, lp=10.0)
        alphaSensor = AngleSensor(2163.0, -0.00117507316)
        betaSensor = AngleSensor(2178.0, 0.00127890506)
        self.testee = PosSensor(platform=platform, prachtstueck=self.prachtstueck, alphaSensor=alphaSensor, betaSensor=betaSensor)

    def test_getPosPrachtstueck(self):
        posSensor = PosSensor()
        alpha = 20.691
        beta = 16.285
        s = 144.811
        alpha_ = (alpha / (-0.00117507316)) * pi / 180 + 2163.0
        beta_ = (beta / (0.00127890506)) * pi / 180 + 2178.0
        position = posSensor.getPosPrachtstueck(alpha_, beta_, s)
        self.assertAlmostEqual(position.x, 205.064, delta=0.01)
        self.assertAlmostEqual(position.z, 32.113, delta = 0.01)

    def test_getPosLoadRel(self):
        pos = Position(200, 200)
        result = self.testee.getPosLoadRel(pos, 20)
        self.assertAlmostEqual(result.z, 200.0-20*2.0*pi-self.prachtstueck.offsetElevator, delta=0.01)
        self.assertAlmostEqual(result.x, 200.0, delta=0.01)

    def test_angleCorrection(self):
        self.assertAlmostEqual(self.testee.angleCorrection(21.841*pi/180)*180/pi, 23.128, delta=0.01)
