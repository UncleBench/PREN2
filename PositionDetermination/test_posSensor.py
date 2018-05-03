from unittest import TestCase
from PosSensor import*


class TestPosSensor(TestCase):
    def setUp(self):
        platform = Platform(k=340.0, b=110.0, a=61.4)
        self.prachtstueck = PrachtstueckDimensions(10.0, 10.0, d=30.0, u=13.93, v=6.9, ap=-2.725, lp=8.3)
        self.testee = PosSensor(platform=platform, prachtstueck=self.prachtstueck)

    def test_get_pos_prachtstueck(self):
        alpha = 6.132
        beta = 22.896
        s = 166.771
        alpha_ = (alpha / self.testee.alpha_sensor.rad_per_value) * pi / 180 + self.testee.alpha_sensor.offset_value
        beta_ = (beta / self.testee.beta_sensor.rad_per_value) * pi / 180 + self.testee.beta_sensor.offset_value
        position = self.testee.get_pos_prachtstueck(alpha_, beta_, s)
        self.assertAlmostEqual(position.x, 172.398, delta=0.01)
        self.assertAlmostEqual(position.z, 40.531, delta=0.01)

    def test_get_pos_load_rel(self):
        pos = Position(200, 200)
        result = self.testee.get_pos_load_rel(pos, 20)
        self.assertAlmostEqual(result.z, 200.0 - self.prachtstueck.offset_elevator, delta=0.01)
        self.assertAlmostEqual(result.x, 200.0, delta=0.01)

    def test_angle_correction(self):
        self.assertAlmostEqual(self.testee.angle_correction(16.578*pi/180)*180/pi, 15.825, delta=0.01)
