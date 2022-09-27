# == summary.py Author: Zuinige Rijder ===================
"""
Simple Python3 script to make a summary of monitor.csv
"""
import sys
import configparser
from datetime import datetime
from pathlib import Path
from dateutil import parser

DEBUG = len(sys.argv) == 2 and sys.argv[1].lower() == 'debug'

INPUT = Path("monitor.csv")

# == read monitor in monitor.cfg ===========================
config_parser = configparser.ConfigParser()
config_parser.read('summary.cfg')
monitor_settings = dict(config_parser.items('summary'))

ODO_METRIC = monitor_settings['odometer_metric']
NET_BATTERY_SIZE_KWH = float(monitor_settings['net_battery_size_kwh'])
AVERAGE_COST_PER_KWH = float(monitor_settings['average_cost_per_kwh'])
COST_CURRENCY = monitor_settings['cost_currency']

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
    return d_1.year == d_2.year


def same_week(d_1: datetime, d_2: datetime):
    """ return if same week """
    if d_1.isocalendar().week != d_2.isocalendar().week:
        return False
    return d_1.year == d_2.year


def same_day(d_1: datetime, d_2: datetime):
    """ return if same day """
    if d_1.day != d_2.day:
        return False
    if d_1.month != d_2.month:
        return False
    return d_1.year == d_2.year


print(f"Label, date      , driven {ODO_METRIC}, charged%, discharged%, charges, drives, {ODO_METRIC}/kWh, kWh/100{ODO_METRIC}, cost {COST_CURRENCY}")  # noqa pylint:disable=line-too-long


def compute_deltas(prefix, current, values):
    """ compute_deltas """
    debug("compute_deltas")
    debug("PREV: " + str(values))
    debug("CURR: " + str(current))
    delta_odo = round(current[1] - values[1], 1)
    charged = values[2]
    discharged = values[3]
    charges = values[4]
    drives = values[5]
    km_mi_per_kwh = 0.0
    kwh_per_km_mi = 0.0
    cost = 0.00
    if discharged < -2:
        cost = NET_BATTERY_SIZE_KWH / 100 * -discharged * AVERAGE_COST_PER_KWH
        km_mi_per_kwh = delta_odo / (NET_BATTERY_SIZE_KWH / 100 * -discharged)
        if km_mi_per_kwh > 0.0:
            kwh_per_km_mi = 100 / km_mi_per_kwh
    else:
        # do not show small discharges
        discharged = 0
    if charged > 0 or discharged < 0 or delta_odo > 1.0 or drives > 0:
        print(f"{prefix:17}, {delta_odo:9.1f}, {charged:+7}%, {discharged:11}, {charges:7}, {drives:6}, {km_mi_per_kwh:6.1f}, {kwh_per_km_mi:9.1f}, {cost:9.2f}")  # noqa pylint:disable=line-too-long


def init(current_day, odo):
    """ init tuple with initial charging and discharging """
    return (current_day, odo, 0, 0, 0, 0)


def keep_track_of_totals(values, split, prev_split):
    """ add """
    charged = values[2]
    discharged = values[3]
    charges = values[4]
    drives = values[5]

    odo = float(split[ODO].strip())
    prev_odo = float(prev_split[ODO].strip())

    soc = int(split[SOC].strip())
    prev_soc = int(prev_split[SOC].strip())
    delta_soc = soc - prev_soc

    charging = split[CHARGING].strip() == "True"
    prev_charging = prev_split[CHARGING].strip() == "True"

    if delta_soc != 0:
        debug("Delta SOC: " + str(delta_soc))
        if delta_soc > 0:
            if delta_soc == 1:
                # small SOC difference can occur due to
                # temperature difference (morning/evening),
                # so correct discharged for delta_soc of 1
                discharged += delta_soc
            else:
                charged += delta_soc
        else:
            discharged += delta_soc

    debug(f"CHARGES: {charging} {prev_charging}")
    if charging and not prev_charging:
        charges += 1
        debug("CHARGES: " + str(charges))
    if delta_soc > 1 and not charging and not prev_charging:
        charges += 1
        debug("charges: DELTA_SOC > 1: " + str(charges))

    engine_on = split[ENGINEON].strip() == "True"
    engine_on_2 = prev_split[ENGINEON].strip() == "True"
    if engine_on and not engine_on_2:
        drives += 1
        debug("ENGINE_ON: " + str(drives))
    if odo != prev_odo and not engine_on and not engine_on_2:
        drives += 1
        debug("ODO: " + str(drives))

    return (values[0], values[1], charged, discharged, charges, drives)


def handle_line(  # pylint: disable=too-many-arguments
    line, prev_line, first_d, first_w, first_m, first_y
):
    """ handle_line """
    split = line.split(',')
    current_day = parser.parse(split[DT])
    odo = float(split[ODO].strip())

    current_day_values = init(current_day, odo)
    if not first_d:
        return (
            current_day_values,
            current_day_values,
            current_day_values,
            current_day_values
        )

    # take into account totals per line
    prev_split = prev_line.split(',')
    first_d = keep_track_of_totals(first_d, split, prev_split)
    first_w = keep_track_of_totals(first_w, split, prev_split)
    first_m = keep_track_of_totals(first_m, split, prev_split)
    first_y = keep_track_of_totals(first_y, split, prev_split)

    if not same_day(current_day, first_d[0]):
        compute_deltas(
            "DAY  , " + first_d[0].strftime("%Y-%m-%d"),
            current_day_values,
            first_d
        )
        first_d = current_day_values
        if not same_week(current_day, first_w[0]):
            compute_deltas(
                "WEEK , " + str(first_y[0].year) + " W" +
                str(first_w[0].isocalendar().week),
                current_day_values,
                first_w
            )
            first_w = current_day_values
        if not same_month(current_day, first_m[0]):
            compute_deltas(
                "MONTH, " + first_m[0].strftime("%Y-%m"),
                current_day_values,
                first_m
            )
            first_m = current_day_values
        if not same_year(current_day, first_y[0]):
            compute_deltas(
                "YEAR , " + str(first_y[0].year),
                current_day_values,
                first_y
            )
            first_y = current_day_values

    return (first_d, first_w, first_m, first_y)


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
                        prev_line,
                        first_day,
                        first_week,
                        first_month,
                        first_year
                    )

            prev_index = index
            prev_line = line

        # also compute last last day/week/month
        temp_line = "2999" + prev_line[4:]
        debug("Handling last values")
        handle_line(
            temp_line,
            prev_line,
            first_day,
            first_week,
            first_month,
            first_year
        )


summary()  # do the work
