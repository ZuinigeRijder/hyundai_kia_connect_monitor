# == monitor_csv_to_kml.py Author: Zuinige Rijder ============================
"""
Simple Python3 script to convert monitor.csv to kml
identical (longitude, latitude) lines to previous line are removed

How to import kml in Google Maps:
https://www.spotzi.com/en/about/help-center/how-to-import-a-kml-into-google-maps/
"""
from pathlib import Path

# pylint: disable=line-too-long
INPUT = Path("monitor.csv")
OUTPUT = Path("monitor.kml")


def writeline(outputfile, line):
    """ writeline """
    outputfile.write(line)
    outputfile.write('\n')


def write_kml(outputfile, items):
    """ write kml """
    datetime = items[0]
    lon = items[1].strip()
    lat = items[2].strip()
    odometer = items[5].strip()
    soc = items[6].strip()

    writeline(outputfile, '  <Placemark>')
    writeline(outputfile, '    <name>' + datetime + '</name>')
    writeline(outputfile, '    <description>' + odometer + ' SOC:' + soc + '</description>') # noqa
    writeline(outputfile, '    <Point><coordinates>' + lon + ', ' + lat + '</coordinates></Point>') # noqa
    writeline(outputfile, '  </Placemark>')


def convert():
    """ convert csv file to kml """
    with OUTPUT.open("w", encoding="utf-8") as outputfile:
        count = 0
        writeline(outputfile, '<?xml version="1.0" encoding="UTF-8"?>')
        writeline(outputfile, '<kml xmlns="http://www.opengis.net/kml/2.2">')
        writeline(outputfile, '<Document>')
        writeline(outputfile, '<name>Locations</name>')

        with INPUT.open("r", encoding="utf-8") as inputfile:
            inputfile.readline()  # skip first line
            prev_location = ''
            for line in inputfile:
                location = ''
                items = line.split(',')
                if len(items) > 8:
                    location = items[1] + ", " + items[2]
                    if prev_location != location:
                        count += 1
                        write_kml(outputfile, items)
                    prev_location = location

        writeline(outputfile, '</Document>')
        writeline(outputfile, '</kml>')


convert()  # do the work
