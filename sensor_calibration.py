#!/usr/bin/python
import sys, argparse
from Communication import SerialCommunication
from numpy import median, mean
from time import sleep
import json

def arg_parser(argv):
    new_file = True
    n_meas = 10
    try:
        opts, args = getopt.getopt(argv,"hi:n:",["newfile=","nMeasurements="])
    except getopt.GetoptError:
        print 'sensor_calibration.py <-new/-add> -n <nMeasurements>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'sensor_calibration.py <-new/-add> -n <nMeasurements>'
            sys.exit()
        elif opt in ("-new", "-add"):
            if opt in "-new":
                new_file = True
            elif opt in "-add":
                new_file = False
            elif opt in "-n":
                n_meas = int(arg)
    return new_file, n_meas


def sensor_calibration(new_file, n_meas):
    print "test"
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
        result['raw_alpha'] += [arduino.getRawAlpha()]
        result['raw_beta'] += [arduino.getRawAlpha()]
        print(result['raw_alpha'], ";", result['raw_beta'])

    calibrated_val["raw_alpha_0"] += median(result['raw_alpha'])
    calibrated_val["raw_alpha_0"] += median(result['raw_alpha'])
    calibrated_val["raw_alpha_0_avg"] = int(mean(calibrated_val["raw_alpha_0"]) + 0.5)
    calibrated_val["raw_beta_0_avg"] = int(mean(calibrated_val["raw_beta_0"]) + 0.5)

    with open('sensor_cal_data.cal', 'w') as file:
        file.write(json.dumps(calibrated_val))


if __name__ == "__main__":
    #print sys.argv
    #parser = argparse.ArgumentParser(description='Process some integers.')
    #parser.add_argument('-a', action="store_true", default=False)
    #parser.add_argument('-b', action="store", dest="b")
    #parser.add_argument('-c', action="store", dest="c", type=int)
    #args =parser.parse_args([ '--noarg', '--witharg', 'val', '--witharg2=3' ])
    #print args
    #new_file, n_meas = arg_parser(sys.argv[1:])
    sensor_calibration(True, 10)