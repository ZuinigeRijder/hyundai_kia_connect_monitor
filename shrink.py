# == shrink.py Author: Zuinige Rijder ========================================
"""
Simple Python3 script to shrink monitor.csv
identical lines removed (first column excluded)

INPUTFILE: monitor.csv or monitor.VIN.csv (latter if vin=VIN parameter)
OUTPUTFILE: shrinked_monitor.csv or shrinked_monitor.VIN.csv
            (latter if vin=VIN parameter)
standard output: summary per kml placemark

Usage:
python shrink.py [vin=VIN]

"""
import sys
from pathlib import Path


def get_vin_arg():
    """ get vin arg"""
    for i in range(1, len(sys.argv)):
        if "vin=" in sys.argv[i].lower():
            vin = sys.argv[i]
            vin = vin.replace("vin=", "")
            vin = vin.replace("VIN=", "")
            return vin

    return ''


INPUT_CSV_FILE = Path("monitor.csv")
OUTPUT_CSV_FILE = Path("shrinked_monitor.csv")
VIN = get_vin_arg()
if VIN != '':
    INPUT_CSV_FILE = Path(f"monitor.{VIN}.csv")
    OUTPUT_CSV_FILE = Path(f"shrinked_monitor.{VIN}.csv")


def shrink():
    """ shrink csv file """
    with INPUT_CSV_FILE.open("r", encoding="utf-8") as inputfile:
        with OUTPUT_CSV_FILE.open("w", encoding="utf-8") as outputfile:
            prevline = ''
            previndex = -1
            for line in inputfile:
                index = line.find(',')
                if index < 0 or previndex < 0 or index != previndex or \
                        prevline[previndex:] != line[index:]:
                    tmp = line.replace("False", "0").replace("True", "1")
                    outputfile.write(tmp)

                prevline = line
                previndex = index


shrink()  # do the work
