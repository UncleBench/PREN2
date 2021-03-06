#!/usr/bin/python
from Communication import SerialCommunication
from PositionDetermination import PosSensor
from numpy import median, mean
from time import sleep
import json
import argparse


def sensor_calibration(new_file, n_meas, meas_sens, z_pos, s_length):
    arduino = SerialCommunication.SerialCommunication('/dev/SensorActor')
    calibrated_val = {"raw_alpha_0": [], "raw_beta_0": [], "raw_alpha_0_avg": 0, "raw_beta_0_avg": 0, "sensitivity": [], "sensitivity_avg": 0}
    if not new_file or meas_sens:
        with open('sensor_cal_data.cal', 'r') as file:
            json_parsed = json.loads(file.read())
            if set(json_parsed.keys()) == set(calibrated_val.keys()):
                calibrated_val = json_parsed

    print "calibration starts in..."
    for j in range(0, 3, 1):
        print str(3-j) + "..."
        sleep(1)

    result = {'raw_alpha': [], 'raw_beta':[]}
    for i in range(0, n_meas, 1):
        sleep(0.5)
        raw_alpha = arduino.getRawAlpha()
        raw_beta = arduino.getRawBeta()
        result['raw_alpha'] += [raw_alpha]
        result['raw_beta'] += [raw_beta]
        print('ralpha:{:4d}; rbeta:{:4d}'.format(raw_alpha, raw_beta))

    if meas_sens is False:
        calibrated_val["raw_alpha_0"] += [int(median(result['raw_alpha']))]
        calibrated_val["raw_beta_0"] += [int(median(result['raw_beta']))]
        calibrated_val["raw_alpha_0_avg"] = int(mean(calibrated_val["raw_alpha_0"]) + 0.5)
        calibrated_val["raw_beta_0_avg"] = int(mean(calibrated_val["raw_beta_0"]) + 0.5)

        print('-----------------------')
        print('a_med: {:4d}; b_med {:4d}'.format(calibrated_val["raw_alpha_0"][-1], calibrated_val["raw_beta_0"][-1]))
        print('a_mean:{:4d}; b_mean{:4d}'.format(calibrated_val["raw_alpha_0_avg"], calibrated_val["raw_beta_0_avg"]))
        print('-----------------------')
    else:
        sensitivity = 0.002
        interval = sensitivity
        for k in range(0, 50, 1):
            alphaSensor = PosSensor.AngleSensor(calibrated_val["raw_alpha_0_avg"], sensitivity)
            betaSensor = PosSensor.AngleSensor(calibrated_val["raw_beta_0_avg"], -sensitivity)
            pos_sensor = PosSensor.PosSensor(alpha_sensor=alphaSensor, beta_sensor=betaSensor)
            pos = pos_sensor.get_pos_prachtstueck(int(median(result['raw_alpha'])), int(median(result['raw_beta'])), pos_sensor.prachtstueck_dim.offset_drive - s_length)

            # binary approximation of the sensitivity
            interval /= 2
            print 'pos.z', pos.z, 'z_pos', z_pos, 'sensitivity', sensitivity
            if pos.z > z_pos:
                sensitivity += interval
            elif pos.z < z_pos:
                sensitivity -= interval
            else:
                break;
        if new_file:
            calibrated_val["sensitivity"] = []
        calibrated_val["sensitivity"] += [sensitivity]
        calibrated_val["sensitivity_avg"] = mean(calibrated_val["sensitivity"])
        print('-----------------------')
        print('sensitivity: {:1.8f}'.format(calibrated_val["sensitivity"][-1]))
        print('mean_sens:   {:1.8f}'.format(calibrated_val["sensitivity_avg"]))
        print('-----------------------')

    with open('sensor_cal_data.cal', 'w') as file:
        file.write(json.dumps(calibrated_val))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('-n', action='store',
                        default=10,
                        dest='n_meas',
                        help='excecute n calibration measurements',
                        type=int)

    parser.add_argument('-new', action='store_true',
                        default=False,
                        dest='new_file',
                        help='create a new config file')

    parser.add_argument('-sensitivity', action='store_true',
                        default=False,
                        dest='meas_sens',
                        help='the sensitivity factor is measured')

    parser.add_argument('-z', action='store',
                        default=10.0,
                        dest='z_pos',
                        help='z-Pos in the sensitivity measurement',
                        type=float)

    parser.add_argument('-s', action='store',
                        default=10.0,
                        dest='s_length',
                        help='rope length in the sensitivity measurement (till the beta wheel)',
                        type=float)

    results = parser.parse_args()
    sensor_calibration(results.new_file, results.n_meas, results.meas_sens, results.z_pos, results.s_length)