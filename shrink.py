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
from pathlib import Path
from monitor_utils import get_vin_arg


INPUT_CSV_FILE = Path("monitor.csv")
OUTPUT_CSV_FILE = Path("shrinked_monitor.csv")
VIN = get_vin_arg()
if VIN != "":
    INPUT_CSV_FILE = Path(f"monitor.{VIN}.csv")
    OUTPUT_CSV_FILE = Path(f"shrinked_monitor.{VIN}.csv")


def shrink():
    """shrink csv file"""
    with INPUT_CSV_FILE.open("r", encoding="windows-1252") as inputfile:
        with OUTPUT_CSV_FILE.open("w", encoding="windows-1252") as outputfile:
            prevline = ""
            previndex = -1
            for line in inputfile:
                index = line.find(",")
                if (
                    index < 0
                    or previndex < 0
                    or index != previndex
                    or prevline[previndex:] != line[index:]
                ):
                    outputfile.write(line)

                prevline = line
                previndex = index


shrink()  # do the work
