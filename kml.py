# == monitor_csv_to_kml.py Author: Zuinige Rijder ============================
"""
Simple Python3 script to convert monitor.csv to monitor.kml

INPUTFILE: monitor.csv
OUTPUTFILE: monitor.kml
standard output: summary per kml placemark

Usage:
python monitor_csv_to_kml.py

Lines are not written, when the following info is the same as previous line:
- longitude, latitude, engineOn, charging

The following information is written in the kml file:
- document name: monitor + now in format "yyyymmdd hh:mm"
- per placemark
-- name of place (index of Google Maps): datetime in format "yyyymmdd hh:mm"
   and optionally "C" when charging and "D" when in drive
-- description: SOC: nn% 12V: nn% ODO: odometer
   [(+distance since yyyymmdd hh:mm)] [drive] [charging] [plugged: n]
-- coordinate (longitude, latitude)

Note:
- the placemark lines are one-liners, so you can also search in monitor.kml

How to import kml in Google Maps:
https://www.spotzi.com/en/about/help-center/how-to-import-a-kml-into-google-maps/
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

INPUT = Path("monitor.csv")
OUTPUT = Path("monitor.kml")

# indexes to splitted monitor.csv items
DT = 0   # datetime
LON = 1  # longitude
LAT = 2  # latitude
ENGINEON = 3  # engineOn
V12 = 4  # 12V%
ODO = 5  # odometer
SOC = 6  # SOC%
CHARGING = 7  # charging
PLUGGED = 8  # plugged
LOCATION = 9  # location address (optional field)


def arg_has(string):
    """ arguments has string """
    for i in range(1, len(sys.argv)):
        if sys.argv[i].lower() == string:
            return True

    return False


def to_float(string):
    """ convert to float """
    if "None" in string:
        return 0.0
    return float(string)


def write(outputfile, line):
    """ write """
    outputfile.write(line)


def writeline(outputfile, line):
    """ writeline """
    outputfile.write(line)
    outputfile.write('\n')


def strip_datetime(string) -> str:
    """ strip datetime string to make it shorter """
    # get rid of timezone info part, so name is shorter
    string = string.strip()
    plus_index = string.find('+')
    if plus_index >= 0:
        string = string[:plus_index]

    # get rid of - in date so it is shorter
    string = string.replace('-', '')

    # get rid of seconds part
    last_double_point = string.rfind(':')
    if last_double_point >= 0:
        string = string[:last_double_point]

    return string


def get_address(split):
    """ get address """
    location_str = ''
    if len(split) > 9:
        location_str = split[LOCATION].strip()

    return location_str


def write_kml(outputfile, count, items, prev_items):
    """ write kml """
    name = strip_datetime(items[DT]) + ' '
    lon = items[LON].strip()
    lat = items[LAT].strip()
    driving = items[ENGINEON].strip() == 'True'
    voltage_12 = items[V12].strip()
    if voltage_12 == 'None':
        voltage_12 = '-1'
    odometer = to_float(items[ODO].strip())
    if odometer == 0.0:
        return  # bad line
    soc = items[SOC].strip()
    if soc == 'None':
        soc = '-1'
    charging = items[CHARGING].strip() == 'True'
    plugged = items[PLUGGED].strip()

    if charging:
        name += 'C'
    else:
        name += ' '
    if driving:
        name += 'D'
    else:
        name += ' '

    coordinates = f'<coordinates>{lon}, {lat}</coordinates>'
    address = get_address(items)
    if address == '':
        description = f'SOC:{soc:>3}% 12V:{voltage_12:>3}% ODO:{odometer:8.1f}'  # noqa pylint:disable=line-too-long
    else:
        description = f'SOC:{soc:>3}% 12V:{voltage_12:>3}% ODO:{odometer:8.1f} Address: {address}'  # noqa pylint:disable=line-too-long

    delta_odometer = 0
    if len(prev_items) > 8:
        delta_odometer = round(
            odometer - to_float(prev_items[ODO].strip()), 1)
        if delta_odometer != 0.0:
            if delta_odometer > 0.0:
                description += ' (+' + str(delta_odometer)
            else:
                description += ' (' + str(delta_odometer)
            description += ' since ' + strip_datetime(prev_items[DT]) + ')'

    if driving:
        description += ' drive'
    if charging:
        description += ' charging'

    if plugged != '0':
        description += ' plugged:' + plugged

    print(f"{count:3}: {name:17} ({lon:8},{lat:9}) {description}")

    write(outputfile, '<Placemark>')
    write(outputfile, '<name>' + name.strip() + '</name>')
    write(outputfile, '<description>' + description.strip() + '</description>')
    write(outputfile, '<Point>' + coordinates + '</Point>')
    writeline(outputfile, '</Placemark>')


def convert():
    """ convert csv file to kml """
    with OUTPUT.open("w", encoding="utf-8") as outputfile:
        count = 0
        writeline(outputfile, '<?xml version="1.0" encoding="UTF-8"?>')
        writeline(outputfile, '<kml xmlns="http://www.opengis.net/kml/2.2">')
        writeline(outputfile, '<Document>')
        writeline(
            outputfile,
            '<name>monitor ' +
            strip_datetime(format(datetime.now(timezone.utc).astimezone())) +
            '</name>'
        )

        with INPUT.open("r", encoding="utf-8") as inputfile:
            prev_location = ''
            prev_engine_on = ''
            prev_charging = ''
            prev_line = ''
            prev_items = []
            for line in inputfile:
                if line.find('datetime') == 0:
                    continue  # skip this header line
                location = ''
                items = line.split(',')
                if len(items) > 8 and line != prev_line:
                    location = items[1] + ", " + items[2]
                    engine_on = items[3].strip()
                    charging = items[7].strip()
                    if location != prev_location or \
                            engine_on != prev_engine_on or \
                            charging != prev_charging:
                        count += 1
                        write_kml(outputfile, count, items, prev_items)
                    prev_location = location
                    prev_engine_on = engine_on
                    prev_charging = charging
                    prev_line = line
                    prev_items = items

        writeline(outputfile, '</Document>')
        writeline(outputfile, '</kml>')


convert()  # do the work
