# == summary.py Author: Zuinige Rijder ===================
"""
Simple Python3 script to make a summary of monitor.csv
"""
from datetime import datetime
from pathlib import Path
from dateutil import parser

DEBUG = False

INPUT = Path("monitor.csv")

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


def debug(line):
    """ print line if debugging """
    if DEBUG:
        print(line)


def same_year(d_1: datetime, d_2: datetime):
    """ return if same year """
    return d_1.year == d_2.year


def same_month(d_1: datetime, d_2: datetime):
    """ return if same month """
    if d_1.month != d_2.month:
        return False
    if d_1.year != d_2.year:
        return False
    return True


def same_week(d_1: datetime, d_2: datetime):
    """ return if same week """
    if d_1.isocalendar().week != d_2.isocalendar().week:
        return False
    if d_1.year != d_2.year:
        return False
    return True


def same_day(d_1: datetime, d_2: datetime):
    """ return if same day """
    if d_1.day != d_2.day:
        return False
    if d_1.month != d_2.month:
        return False
    if d_1.year != d_2.year:
        return False
    return True


def compute_deltas(prefix, current, first):
    """ compute_deltas """
    debug("compute_deltas")
    debug("PREV: " + str(first))
    debug("CURR: " + str(current))
    delta_odo = round(current[1] - first[1], 1)
    delta_soc = current[2] - first[2]
    if delta_soc > 3 or delta_soc < -3 or delta_odo > 1.0:
        print(
            f"{prefix:17} driven: {delta_odo:5.1f} delta SOC: {delta_soc:+3}%"
        )


def handle_line(line, first_day, first_week, first_month, first_year):
    """ handle_line """
    split = line.split(',')
    current_day = parser.parse(split[DT])
    odo = float(split[ODO].strip())
    soc = int(split[SOC].strip())

    current_day_values = (current_day, odo, soc)
    if not first_day:
        return (
            current_day_values,
            current_day_values,
            current_day_values,
            current_day_values
        )
    else:
        if not same_day(current_day, first_day[0]):
            compute_deltas(
                "DAY   " + first_day[0].strftime("%Y-%m-%d"),
                current_day_values,
                first_day
            )
            first_day = current_day_values
        if not same_week(current_day, first_week[0]):
            compute_deltas(
                "WEEK  " + str(first_year[0].year) + " W" +
                str(first_week[0].isocalendar().week),
                current_day_values,
                first_week
            )
            first_week = current_day_values
        if not same_month(current_day, first_month[0]):
            compute_deltas(
                "MONTH " + first_month[0].strftime("%Y-%m"),
                current_day_values,
                first_month
            )
            first_month = current_day_values
        if not same_year(current_day, first_year[0]):
            compute_deltas(
                "YEAR  " + str(first_year[0].year),
                current_day_values,
                first_year
            )
            first_year = current_day_values

    return (first_day, first_week, first_month, first_year)


def summary():
    """ summary of monitor.csv file """

    with INPUT.open("r", encoding="utf-8") as inputfile:
        linecount = 0
        prev_index = -1
        prev_line = ''
        first_day = ()
        first_week = ()
        first_month = ()
        first_year = ()
        for line in inputfile:
            line = line.strip()
            linecount += 1
            debug(str(linecount) + ': LINE=[' + line + ']')
            index = line.find(',')
            if index < 0 or prev_index < 0 or index != prev_index or \
                    prev_line[prev_index:] != line[index:]:
                if prev_index >= 0:
                    (first_day, first_week, first_month, first_year) = \
                        handle_line(
                        line,
                        first_day,
                        first_week,
                        first_month,
                        first_year
                    )

            prev_index = index
            prev_line = line

        # also compute last last day/week/month
        prev_line = "2999" + prev_line[4:]
        debug("Handling last values")
        handle_line(prev_line, first_day, first_week, first_month, first_year)


summary()  # do the work
