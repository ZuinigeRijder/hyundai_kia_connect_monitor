# == summary.py Author: Zuinige Rijder ===================
"""
Simple Python3 script to make a summary of monitor.csv
"""
import sys
import configparser
from datetime import datetime
from pathlib import Path
from dateutil import parser


def arg_has(string):
    """ arguments has string """
    for i in range(1, len(sys.argv)):
        if sys.argv[i].lower() == string:
            return True

    return False


DEBUG = arg_has('debug')
TRIP = len(sys.argv) == 1 or (arg_has('trip') and not arg_has('-trip'))
DAY = len(sys.argv) == 1 or arg_has('day') or arg_has('-trip')
WEEK = len(sys.argv) == 1 or arg_has('week') or arg_has('-trip')
MONTH = len(sys.argv) == 1 or arg_has('month') or arg_has('-trip')
YEAR = len(sys.argv) == 1 or arg_has('year') or arg_has('-trip')

INPUT = Path("monitor.csv")

# == read monitor in monitor.cfg ===========================
config_parser = configparser.ConfigParser()
config_parser.read('summary.cfg')
monitor_settings = dict(config_parser.items('summary'))

ODO_METRIC = monitor_settings['odometer_metric']
NET_BATTERY_SIZE_KWH = float(monitor_settings['net_battery_size_kwh'])
AVERAGE_COST_PER_KWH = float(monitor_settings['average_cost_per_kwh'])
COST_CURRENCY = monitor_settings['cost_currency']
MIN_CONSUMPTION_DISCHARGE_KWH = float(
    monitor_settings['min_consumption_discharge_kwh'])
SMALL_POSITIVE_DELTA = int(
    monitor_settings['ignore_small_positive_delta_soc'])
SMALL_NEGATIVE_DELTA = int(
    monitor_settings['ignore_small_negative_delta_soc'])
SHOW_ZERO_VALUES = monitor_settings['show_zero_values'].lower() == 'true'

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

# indexes to total tuples
T_CURRENT_DAY = 0
T_ODO = 1
T_CHARGED_PERC = 2
T_DISCHARGED_PERC = 3
T_CHARGES = 4
T_DRIVES = 5
T_ELAPSED_MINUTES = 6
T_SOC_AVG = 7
T_SOC_MIN = 8
T_SOC_MAX = 9
T_VOLT12_AVG = 10
T_VOLT12_MIN = 11
T_VOLT12_MAX = 12

# indexes to totals tuples
T_DAY = 0
T_WEEK = 1
T_MONTH = 2
T_YEAR = 3
T_TRIP = 4


def debug(line):
    """ print line if debugging """
    if DEBUG:
        print(line)


def init(current_day, odo):
    """ init tuple with initial values """
    # current_day, odo, charged_perc, discharged_perc, charges, drives,
    # elapsed_minutes, soc_avg, soc_min, soc_max
    debug(f"init({current_day})")
    return (current_day, odo, 0, 0, 0, 0, 0, -1.0, 999, -1, -1.0, 999, -1)


def to_int(string):
    """ convert to int """
    if string == "None":
        return -1
    return int(string)


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


print(f"Period, date      , info , delta {ODO_METRIC},    +kWh,     -kWh, {ODO_METRIC}/kWh, kWh/100{ODO_METRIC}, cost {COST_CURRENCY}, SOC%AVG,MIN,MAX, 12V%AVG,MIN,MAX, #charges, #drives")  # noqa pylint:disable=line-too-long


def print_summary(prefix, current, values):
    """ print_summary """
    debug("print_summary")
    debug("PREV  : " + str(values))
    debug("CURR  : " + str(current))
    debug("VALUES: " + str(values))
    delta_odo = round(current[T_ODO] - values[T_ODO], 1)

    t_charged_perc = values[T_CHARGED_PERC]
    if t_charged_perc < 0:
        t_charged_perc = 0
    t_discharged_perc = values[T_DISCHARGED_PERC]
    if t_discharged_perc > 0:
        t_discharged_perc = 0
    t_charges = values[T_CHARGES]
    t_drives = values[T_DRIVES]

    t_elapsed_minutes = values[T_ELAPSED_MINUTES]
    t_soc_avg = values[T_SOC_AVG]
    t_soc_min = values[T_SOC_MIN]
    t_soc_max = values[T_SOC_MAX]
    soc_average = 0
    if t_elapsed_minutes != 0:
        soc_average = round(t_soc_avg / t_elapsed_minutes)

    t_volt12_avg = values[T_VOLT12_AVG]
    t_volt12_min = values[T_VOLT12_MIN]
    t_volt12_max = values[T_VOLT12_MAX]
    volt12_average = 0
    if t_elapsed_minutes != 0:
        volt12_average = round(t_volt12_avg / t_elapsed_minutes)

    charged_kwh = NET_BATTERY_SIZE_KWH / 100 * t_charged_perc
    discharged_kwh = NET_BATTERY_SIZE_KWH / 100 * t_discharged_perc
    km_mi_per_kwh_str = ""
    kwh_per_km_mi_str = ""
    cost_str = ""
    if SHOW_ZERO_VALUES:
        km_mi_per_kwh_str = "    0.0"
        kwh_per_km_mi_str = "       0.0"
        cost_str = "      0.00"
    if t_discharged_perc < 0:
        if discharged_kwh < -MIN_CONSUMPTION_DISCHARGE_KWH:  # skip inaccurate
            cost = discharged_kwh * -AVERAGE_COST_PER_KWH
            cost_str = f"{cost:10.2f}"
            km_mi_per_kwh = delta_odo / -discharged_kwh
            km_mi_per_kwh_str = f"{km_mi_per_kwh:7.1f}"
            if km_mi_per_kwh > 0.0:
                kwh_per_km_mi = 100 / km_mi_per_kwh
                kwh_per_km_mi_str = f"{kwh_per_km_mi:10.1f}"

    else:
        # do not show positive discharges
        t_discharged_perc = 0

    delta_odo_str = ""
    if SHOW_ZERO_VALUES or delta_odo != 0.0:
        delta_odo_str = f"{delta_odo:9.1f}"
    charged_kwh_str = ""
    if SHOW_ZERO_VALUES or charged_kwh != 0.0:
        charged_kwh_str = f"{charged_kwh:8.1f}"
    discharged_kwh_str = ""
    if SHOW_ZERO_VALUES or discharged_kwh != 0.0:
        discharged_kwh_str = f"{discharged_kwh:9.1f}"
    t_charges_str = ""
    if SHOW_ZERO_VALUES or t_charges != 0:
        t_charges_str = f"{t_charges:9}"
    t_drives_str = ""
    if SHOW_ZERO_VALUES or t_drives != 0:
        t_drives_str = f"{t_drives:8}"
    print(f"{prefix:18},{delta_odo_str:9},{charged_kwh_str:8},{discharged_kwh_str:9},{km_mi_per_kwh_str:7},{kwh_per_km_mi_str:10},{cost_str:10},{soc_average:8},{t_soc_min:3},{t_soc_max:3},{volt12_average:8},{t_volt12_min:3},{t_volt12_max:3},{t_charges_str:9},{t_drives_str:8}")  # noqa pylint:disable=line-too-long


def print_summaries(current_day_values, totals):
    """ print_summaries """
    debug(f"print_summaries: {totals}")
    current_day = current_day_values[T_CURRENT_DAY]
    t_day = totals[T_DAY]
    t_week = totals[T_WEEK]
    t_month = totals[T_MONTH]
    t_year = totals[T_YEAR]
    t_trip = totals[T_TRIP]

    day_str = t_day[T_CURRENT_DAY].strftime("%Y-%m-%d")

    if not same_day(current_day, t_day[T_CURRENT_DAY]):
        if DAY:
            day_info = t_day[T_CURRENT_DAY].strftime("%a")
            print_summary(
                f"DAY   , {day_str}, {day_info:5}",
                current_day_values,
                t_day
            )
        t_day = current_day_values
        t_trip = current_day_values

    if WEEK and not same_week(current_day, t_week[T_CURRENT_DAY]):
        weeknr = t_week[T_CURRENT_DAY].strftime("%W")
        print_summary(
            f"WEEK  , {day_str:10}, WK {weeknr:2}",
            current_day_values,
            t_week
        )
        t_week = current_day_values

    if MONTH and not same_month(current_day, t_month[T_CURRENT_DAY]):
        month_info = t_month[T_CURRENT_DAY].strftime("%b")
        print_summary(
            f"MONTH , {day_str:10}, {month_info:5}",
            current_day_values,
            t_month
        )
        t_month = current_day_values
    if YEAR and not same_year(current_day, t_year[T_CURRENT_DAY]):
        year = t_year[T_CURRENT_DAY].strftime("%Y")
        print_summary(
            f"YEAR  , {day_str:10}, {year:5}",
            current_day_values,
            t_year
        )
        t_year = current_day_values

    totals = (t_day, t_week, t_month, t_year, t_trip)
    return totals


def keep_track_of_totals(values, split, prev_split):
    """ keep_track_of_totals """
    debug("keep track of totals")
    debug("prev_split: " + str(prev_split))
    debug("     split: " + str(split))

    t_charged_perc = values[T_CHARGED_PERC]
    t_discharged_perc = values[T_DISCHARGED_PERC]
    t_charges = values[T_CHARGES]
    t_drives = values[T_DRIVES]
    t_elapsed_minutes = values[T_ELAPSED_MINUTES]
    t_soc_avg = values[T_SOC_AVG]
    t_soc_min = values[T_SOC_MIN]
    t_soc_max = values[T_SOC_MAX]
    t_volt12_avg = values[T_VOLT12_AVG]
    t_volt12_min = values[T_VOLT12_MIN]
    t_volt12_max = values[T_VOLT12_MAX]

    delta_odo = float(split[ODO].strip()) - float(prev_split[ODO].strip())
    moved = (
        delta_odo != 0.0 or
        float(split[LAT].strip()) != float(prev_split[LAT].strip()) or
        float(split[LON].strip()) != float(prev_split[LON].strip())
    )

    soc = to_int(split[SOC].strip())
    prev_soc = to_int(prev_split[SOC].strip())
    delta_soc = soc - prev_soc
    if (soc == 0 or prev_soc == 0) and abs(delta_soc) > 5:
        # possibly wrong readout, take largest
        soc = max(soc, prev_soc)
        prev_soc = soc
        delta_soc = 0

    # keep track of elapsed minutes
    current_day = parser.parse(split[DT])
    prev_day = parser.parse(prev_split[DT])
    elapsed_minutes = round((current_day - prev_day).total_seconds() / 60)
    t_elapsed_minutes += elapsed_minutes

    # keep track of average SOC over time
    average_soc = (soc + prev_soc) / 2
    t_soc_avg += (average_soc * elapsed_minutes)
    t_soc_min = min(soc, t_soc_min)
    t_soc_max = max(soc, t_soc_max)

    # keep track of average 12V over time
    volt12 = to_int(split[V12].strip())
    prev_volt12 = to_int(prev_split[V12].strip())
    average_volt12 = (volt12 + prev_volt12) / 2
    t_volt12_avg += (average_volt12 * elapsed_minutes)
    t_volt12_min = min(volt12, t_volt12_min)
    t_volt12_max = max(volt12, t_volt12_max)

    charging = split[CHARGING].strip() == "True"
    prev_charging = prev_split[CHARGING].strip() == "True"
    no_charging = not charging and not prev_charging

    if delta_soc != 0:
        debug(f"Delta SOC: {delta_soc}, no_charging: {no_charging}, moved: {moved}, elapsed_minutes: {elapsed_minutes}")  # noqa pylint:disable=line-too-long
        if delta_soc > 0:  # charge +kWh
            if delta_soc <= SMALL_POSITIVE_DELTA and no_charging and not moved:
                # small SOC difference can occur due to
                # temperature difference (e.g. morning/evening)
                debug(f"skipping positive delta\n{prev_split}\n{split}")
                t_discharged_perc += delta_soc
            else:
                if no_charging and not moved and elapsed_minutes < 120:
                    debug(f"Unexpected positive delta?\n{prev_split}\n{split}")
                t_charged_perc += delta_soc
        else:
            if delta_soc >= SMALL_NEGATIVE_DELTA and no_charging and not moved:
                # small SOC difference can occur due to
                # temperature difference (e.g. morning/evening)
                debug(f"skipping negative delta\n{prev_split}\n{split}")
                t_charged_perc += delta_soc
            else:
                t_discharged_perc += delta_soc

    if charging and not prev_charging:
        t_charges += 1
        debug("CHARGES: " + str(t_charges))
    elif delta_soc > 1 and no_charging:
        t_charges += 1
        debug("charges: DELTA_SOC > 1: " + str(t_charges))

    if delta_odo != 0.0:
        t_drives += 1
        debug(f"DELTA_ODO: {delta_odo:7.1f} {t_drives}")

    debug("    before: " + str(values))
    values = (
        values[T_CURRENT_DAY],
        values[T_ODO],
        t_charged_perc,
        t_discharged_perc,
        t_charges,
        t_drives,
        t_elapsed_minutes,
        t_soc_avg,
        t_soc_min,
        t_soc_max,
        t_volt12_avg,
        t_volt12_min,
        t_volt12_max
    )
    debug("     after: " + str(values))
    return values


def handle_line(split, prev_split, totals):
    """ handle_line """
    debug(f"handle_line: {split}, {prev_split}")
    current_day = parser.parse(split[DT])

    t_day = totals[T_DAY]
    t_week = totals[T_WEEK]
    t_month = totals[T_MONTH]
    t_year = totals[T_YEAR]
    t_trip = totals[T_TRIP]

    if not t_day:  # first time, fill in with initial values
        debug(f"not TDAY: {t_day}")
        current_day_values = init(current_day, float(split[ODO].strip()))
        totals = (
            current_day_values,
            current_day_values,
            current_day_values,
            current_day_values,
            current_day_values
        )
        return totals

    day_change = not same_day(current_day, t_day[T_CURRENT_DAY])
    if day_change:
        debug(f"DAY change: {t_day}")
        current_day_values = init(current_day, float(split[ODO].strip()))
        totals = print_summaries(current_day_values, totals)

    t_day = totals[T_DAY]
    t_week = totals[T_WEEK]
    t_month = totals[T_MONTH]
    t_year = totals[T_YEAR]
    t_trip = totals[T_TRIP]

    # take into account totals per line
    if DAY:
        t_day = keep_track_of_totals(t_day, split, prev_split)
    if WEEK:
        t_week = keep_track_of_totals(t_week, split, prev_split)
    if MONTH:
        t_month = keep_track_of_totals(t_month, split, prev_split)
    if YEAR:
        t_year = keep_track_of_totals(t_year, split, prev_split)

    if TRIP:
        t_trip = keep_track_of_totals(t_trip, split, prev_split)
        if t_trip[T_DRIVES] > 0:
            current_day_values = init(current_day, float(split[ODO].strip()))
            day_trip_str = current_day.strftime("%Y-%m-%d")
            day_info = current_day.strftime("%H:%M")
            print_summary(
                f"TRIP  , {day_trip_str:10}, {day_info:5}",
                current_day_values,
                t_trip
            )
            t_trip = current_day_values

    totals = (t_day, t_week, t_month, t_year, t_trip)

    return totals


def summary():
    """ summary of monitor.csv file """

    with INPUT.open("r", encoding="utf-8") as inputfile:
        linecount = 0
        prev_index = -1
        prev_line = ''
        prev_split = ()
        totals = ((), (), (), (), ())

        for line in inputfile:
            line = line.strip()
            linecount += 1
            debug(str(linecount) + ': LINE=[' + line + ']')
            index = line.find(',')
            if index <= 0 or line.startswith("datetime"):
                debug("Skipping line")
                continue  # skip headers and lines starting or without ,
            split = line.split(',')
            if not totals[T_DAY] or not same_day(parser.parse(split[DT]), parser.parse(prev_split[DT])) or prev_line[prev_index:] != line[index:]:    # noqa pylint:disable=line-too-long
                totals = handle_line(
                    split,
                    prev_split,
                    totals
                )

            prev_index = index
            prev_line = line
            prev_split = split

        # also compute last last day/week/month
        debug("Handling last values")
        handle_line(
            ("2999" + prev_line[4:]).split(","),
            prev_split,
            totals
        )


summary()  # do the work
