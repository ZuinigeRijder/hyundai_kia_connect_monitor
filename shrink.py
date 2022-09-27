# == shrink_monitor_csv.py Author: Zuinige Rijder ===================
"""
Simple Python3 script to shrink monitor.csv
identical lines removed (first column excluded)
"""

from pathlib import Path


INPUT = Path("monitor.csv")
OUTPUT = Path("shrinked_monitor.csv")


def shrink():
    """ shrink csv file """
    with INPUT.open("r", encoding="utf-8") as inputfile:
        with OUTPUT.open("w", encoding="utf-8") as outputfile:
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
