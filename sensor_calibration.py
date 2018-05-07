#!/usr/bin/python
from Communication import SerialCommunication
from numpy import median, mean
from time import sleep
import json
import argparse


def sensor_calibration(new_file, n_meas):
    with open('sensor_cal_data.cal', 'r') as file:
        print 'parsed json', json.loads(file.read())
    arduino = SerialCommunication.SerialCommunication('/dev/SensorActor')
    calibrated_val = {"raw_alpha_0": [], "raw_beta_0": [], "raw_alpha_0_avg": 0, "raw_beta_0_avg": 0}
    if not new_file:
        with open('sensor_cal_data.cal', 'r') as file:
            json_parsed = json.loads(file.read())
            if set(json_parsed.keys()) == set(calibrated_val.keys()):
                calibrated_val = json_parsed

    result = {'raw_alpha': [], 'raw_beta':[]}
    for i in range(1, n_meas, 1):
        sleep(0.5)
        raw_alpha = arduino.getRawAlpha()
        raw_beta = arduino.getRawBeta()
        result['raw_alpha'] += [raw_alpha]
        result['raw_beta'] += [raw_beta]
        print('ralpha:{:4d}; rbeta:{:4d}'.format(raw_alpha, raw_beta))

    calibrated_val["raw_alpha_0"] += [int(median(result['raw_alpha']))]
    calibrated_val["raw_beta_0"] += [int(median(result['raw_beta']))]
    calibrated_val["raw_alpha_0_avg"] = int(mean(calibrated_val["raw_alpha_0"]) + 0.5)
    calibrated_val["raw_beta_0_avg"] = int(mean(calibrated_val["raw_beta_0"]) + 0.5)

    print('-----------------------')
    print('a_med: {:4d}; b_med {:4d}'.format(calibrated_val["raw_alpha_0"][-1], calibrated_val["raw_beta_0"][-1]))
    print('a_mean:{:4d}; b_mean{:4d}'.format(calibrated_val["raw_alpha_0_avg"], calibrated_val["raw_beta_0_avg"]))
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

    results = parser.parse_args()

    sensor_calibration(results.new_file, results.n_meas)