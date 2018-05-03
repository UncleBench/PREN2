from unittest import TestCase
from PosSensor import*


class TestPosSensor(TestCase):
    def setUp(self):
        platform = Platform(k=340.0, b=110.0, a=61.4)
        #self.prachtstueck = Prachtstueck(10.0, 10.0, r_1=1.0, r_2=1.0, d=21.5, u=10.75, v=2.7, ap=2.7, lp=10.0)
        self.prachtstueck = Prachtstueck(10.0, 10.0, d=30.0, u=13.93, v=6.9, ap=-2.725, lp=9.4)
        self.testee = PosSensor(platform=platform, prachtstueck=self.prachtstueck)

    def test_getPosPrachtstueck(self):
        alpha = 6.09
        beta = 22.359
        s = 166.771
        alpha_ = (alpha / (self.testee.alphaSensor.radPerValue)) * pi / 180 + self.testee.alphaSensor.offsetValue
        beta_ = (beta / (self.testee.betaSensor.radPerValue)) * pi / 180 + self.testee.betaSensor.offsetValue
        position = self.testee.getPosPrachtstueck(alpha_, beta_, s)
        self.assertAlmostEqual(position.x, 172.398, delta=0.01)
        self.assertAlmostEqual(position.z, 40.531, delta = 0.01)

    def test_getPosLoadRel(self):
        pos = Position(200, 200)
        result = self.testee.getPosLoadRel(pos, 20)
        self.assertAlmostEqual(result.z, 200.0-self.prachtstueck.offsetElevator, delta=0.01)
        self.assertAlmostEqual(result.x, 200.0, delta=0.01)

    def test_angleCorrection(self):
        self.assertAlmostEqual(self.testee.angleCorrection(11.732*pi/180)*180/pi, 11.489, delta=0.01)