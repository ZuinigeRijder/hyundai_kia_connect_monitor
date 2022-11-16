# == summary.py Author: Zuinige Rijder ===================
"""
Simple Python3 script to make a summary of monitor.csv
"""
import sys
import configparser
from datetime import datetime, timedelta
from time import sleep
from pathlib import Path
from collections import deque
import gspread
from dateutil import parser
from geopy.distance import geodesic
from geopy.geocoders import Nominatim


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
MOVES = arg_has('move')
ADDRESS = arg_has('address')
if ADDRESS and not TRIP and not MOVES:
    TRIP = True
SHEETUPDATE = arg_has('sheetupdate')
if SHEETUPDATE:
    DAY = True
    WEEK = True
    MONTH = True
    YEAR = True

INPUT = Path("monitor.csv")

# == read monitor in monitor.cfg ===========================
config_parser = configparser.ConfigParser()
config_parser.read('summary.cfg')
monitor_settings = dict(config_parser.items('summary'))

ODO_METRIC = monitor_settings['odometer_metric'].lower()
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
T_TRIPS = 5
T_ELAPSED_MINUTES = 6
T_SOC_CUR = 7
T_SOC_AVG = 8
T_SOC_MIN = 9
T_SOC_MAX = 10
T_VOLT12_CUR = 11
T_VOLT12_AVG = 12
T_VOLT12_MIN = 13
T_VOLT12_MAX = 14
T_MOVES = 15

# indexes to totals tuples
T_DAY = 0
T_WEEK = 1
T_MONTH = 2
T_YEAR = 3
T_TRIP = 4

# number of days passed in this year
DAY_COUNTER = 0

# Initializing a queue with maximum size of 50
LAST_OUTPUT_QUEUE = deque(maxlen=50)


def debug(line):
    """ print line if debugging """
    if DEBUG:
        print(line)


def init(current_day, odo, soc, volt12):
    """ init tuple with initial values """
    # current_day, odo, charged_perc, discharged_perc, charges, trips,
    # elapsed_minutes,
    # soc_cur, soc_avg, soc_min, soc_max,
    # 12v_cur, 12v_avg, 12v_min, 12v_max,
    # moves
    debug(f"init({current_day})")
    return (
        current_day, odo, 0, 0, 0, 0, 0,
        soc, soc, soc, soc,  # SOC%
        volt12, volt12, volt12, volt12,  # 12V%
        0                     # moves
    )


def to_int(string):
    """ convert to int """
    if "None" in string:
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


def print_output_and_update_queue(output):
    """print output and update queue"""
    if SHEETUPDATE:
        LAST_OUTPUT_QUEUE.append(output)
    print(output)


def print_header_and_update_queue():
    """print header and update queue"""
    if ADDRESS:
        output=f"  Period, date      , info , odometer, delta {ODO_METRIC},    +kWh,     -kWh, {ODO_METRIC}/kWh, kWh/100{ODO_METRIC}, cost {COST_CURRENCY}, SOC%CUR,AVG,MIN,MAX, 12V%CUR,AVG,MIN,MAX, #charges,   #trips,   #moves, Address"  # noqa pylint:disable=line-too-long
    else:
        output=f"  Period, date      , info , odometer, delta {ODO_METRIC},    +kWh,     -kWh, {ODO_METRIC}/kWh, kWh/100{ODO_METRIC}, cost {COST_CURRENCY}, SOC%CUR,AVG,MIN,MAX, 12V%CUR,AVG,MIN,MAX, #charges,   #trips,   #moves"  # noqa pylint:disable=line-too-long
    print_output_and_update_queue(output)


def float_to_string(input_value):
    """ float to string without trailing zero """
    return (f"{input_value:9.1f}").rstrip('0').rstrip('.')


def print_summary(prefix, current, values, location_str, factor):
    """ print_summary """
    debug("print_summary")
    debug("PREV  : " + str(values))
    debug("CURR  : " + str(current))
    debug("VALUES: " + str(values))
    odo = current[T_ODO]
    delta_odo = round(odo - values[T_ODO], 1) * factor
    odo_str = ''
    if odo != 0.0:
        odo_str = f"{odo:9.1f}"
    t_charged_perc = values[T_CHARGED_PERC] * factor
    if t_charged_perc < 0:
        t_charged_perc = 0
    t_discharged_perc = values[T_DISCHARGED_PERC] * factor
    if t_discharged_perc > 0:
        t_discharged_perc = 0
    t_charges = values[T_CHARGES] * factor
    t_trips = values[T_TRIPS] * factor
    t_moves = values[T_MOVES] * factor

    t_elapsed_minutes = max(values[T_ELAPSED_MINUTES], 1)
    t_soc_cur = values[T_SOC_CUR]
    t_soc_avg = round(values[T_SOC_AVG] / t_elapsed_minutes)
    t_soc_min = values[T_SOC_MIN]
    t_soc_max = values[T_SOC_MAX]

    t_volt12_cur = values[T_VOLT12_CUR]
    t_volt12_avg = round(values[T_VOLT12_AVG] / t_elapsed_minutes)
    t_volt12_min = values[T_VOLT12_MIN]
    t_volt12_max = values[T_VOLT12_MAX]

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
        t_charges_str = float_to_string(t_charges)
    t_trips_str = ""
    if SHOW_ZERO_VALUES or t_trips != 0:
        t_trips_str = float_to_string(t_trips)
    t_moves_str = ""
    if SHOW_ZERO_VALUES or t_moves != 0:
        t_moves_str = float_to_string(t_moves)

    if SHEETUPDATE and prefix.startswith('SHEET'):
        prefix = prefix.replace("SHEET ", "")
        SHEET.batch_update([{
            'range': 'A1:B1',
            'values': [["Last update", f"{prefix}"]],
        }, {
            'range': 'A2:B2',
            'values': [[f"Odometer {ODO_METRIC}", f"{odo:.1f}"]],
        }, {
            'range': 'A3:B3',
            'values': [[f"Driven {ODO_METRIC}", f"{delta_odo:.1f}"]],
        }, {
            'range': 'A4:B4',
            'values': [["+kWh", f"{charged_kwh:.1f}"]],
        }, {
            'range': 'A5:B5',
            'values': [["-kWh", f"{discharged_kwh:.1f}"]],
        }, {
            'range': 'A6:B6',
            'values': [[f"{ODO_METRIC}/kWh", f"{km_mi_per_kwh:.1f}"]],
        }, {
            'range': 'A7:B7',
            'values': [[f"kWh/100{ODO_METRIC}", f"{kwh_per_km_mi:.1f}"]],
        }, {
            'range': 'A8:B8',
            'values': [[f"Cost {COST_CURRENCY}", f"{cost:.2f}"]],
        }, {
            'range': 'A9:B9',
            'values': [["Current SOC%", f"{t_soc_cur}"]],
        }, {
            'range': 'A10:B10',
            'values': [["Average SOC%", f"{t_soc_avg}"]],
        }, {
            'range': 'A11:B11',
            'values': [["Min SOC%", f"{t_soc_min}"]],
        }, {
            'range': 'A12:B12',
            'values': [["Max SOC%", f"{t_soc_max}"]],
        }, {
            'range': 'A13:B13',
            'values': [["Current 12V%", f"{t_volt12_cur}"]],
        }, {
            'range': 'A14:B14',
            'values': [["Average 12V%", f"{t_volt12_avg}"]],
        }, {
            'range': 'A15:B15',
            'values': [["Min 12V%", f"{t_volt12_min}"]],
        }, {
            'range': 'A16:B16',
            'values': [["Max 12V%", f"{t_volt12_max}"]],
        }, {
            'range': 'A17:B17',
            'values': [["#Charges", f"{t_charges}"]],
        }, {
            'range': 'A18:B18',
            'values': [["#Trips", f"{t_trips}"]],
         }, {
            'range': 'A19:B19',
            'values': [["#Moves", f"{t_moves}"]],
        }])
    else:
        if ADDRESS:
            output=f"{prefix:18},{odo_str:9},{delta_odo_str:9},{charged_kwh_str:8},{discharged_kwh_str:9},{km_mi_per_kwh_str:7},{kwh_per_km_mi_str:10},{cost_str:10},{t_soc_cur:8},{t_soc_avg:3},{t_soc_min:3},{t_soc_max:3},{t_volt12_cur:8},{t_volt12_avg:3},{t_volt12_min:3},{t_volt12_max:3},{t_charges_str:9},{t_trips_str:9},{t_moves_str:9},{location_str}"  # noqa pylint:disable=line-too-long
        else:
            output=f"{prefix:18},{odo_str:9},{delta_odo_str:9},{charged_kwh_str:8},{discharged_kwh_str:9},{km_mi_per_kwh_str:7},{kwh_per_km_mi_str:10},{cost_str:10},{t_soc_cur:8},{t_soc_avg:3},{t_soc_min:3},{t_soc_max:3},{t_volt12_cur:8},{t_volt12_avg:3},{t_volt12_min:3},{t_volt12_max:3},{t_charges_str:9},{t_trips_str:9},{t_moves_str:9}"  # noqa pylint:disable=line-too-long
        print_output_and_update_queue(output)


def split_output_to_sheet_list(queue_output):
    """ split output to sheet list """
    split = queue_output.split(',')
    return [split]


def print_output_queue():
    """ print output queue """
    array = []
    current_row = 20
    for queue_output in LAST_OUTPUT_QUEUE:
        current_row += 1
        list_output = split_output_to_sheet_list(queue_output)
        array.append({
            'range': f"A{current_row}:U{current_row}",
            'values': list_output,
        })
    SHEET.batch_update(array)


def print_summaries(current_day_values, totals):
    """ print_summaries """
    global DAY_COUNTER  # pylint:disable=global-statement
    debug(f"print_summaries: DAY_COUNTER: {DAY_COUNTER} {totals}")
    current_day = current_day_values[T_CURRENT_DAY]
    t_day = totals[T_DAY]
    t_week = totals[T_WEEK]
    t_month = totals[T_MONTH]
    t_year = totals[T_YEAR]
    t_trip = totals[T_TRIP]

    day_str = t_day[T_CURRENT_DAY].strftime("%Y-%m-%d")

    if not same_day(current_day, t_day[T_CURRENT_DAY]):
        DAY_COUNTER += 1
        debug(f"DAY_COUNTER increment: {DAY_COUNTER}")
        if DAY:
            day_info = t_day[T_CURRENT_DAY].strftime("%a")
            print_summary(
                f"DAY     , {day_str}, {day_info:5}",
                current_day_values,
                t_day,
                "",
                1.0
            )
        t_day = current_day_values
        t_trip = current_day_values

    if WEEK and not same_week(current_day, t_week[T_CURRENT_DAY]):
        weeknr = t_week[T_CURRENT_DAY].strftime("%W")
        print_summary(
            f"WEEK    , {day_str:10}, WK {weeknr:2}",
            current_day_values,
            t_week,
            "",
            1.0
        )
        t_week = current_day_values

    if MONTH and not same_month(current_day, t_month[T_CURRENT_DAY]):
        month_info = t_month[T_CURRENT_DAY].strftime("%b")
        print_summary(
            f"MONTH   , {day_str:10}, {month_info:5}",
            current_day_values,
            t_month,
            "",
            1.0
        )
        t_month = current_day_values
    if YEAR and not same_year(current_day, t_year[T_CURRENT_DAY]):
        year = t_year[T_CURRENT_DAY].strftime("%Y")
        print_summary(
            f"YEAR    , {day_str:10}, {year:5}",
            current_day_values,
            t_year,
            "",
            1.0
        )
        trips = t_year[T_TRIPS]
        print_summary(
            f"TRIPAVG , {day_str:10}, {trips:3}t ",
            current_day_values,
            t_year,
            "",
            1/trips
        )
        print_summary(
            f"DAYAVG  , {day_str:10}, {DAY_COUNTER:3}d ",
            current_day_values,
            t_year,
            "",
            1/DAY_COUNTER
        )
        print_summary(
            f"WEEKAVG , {day_str:10}, {DAY_COUNTER:3}d ",
            current_day_values,
            t_year,
            "",
            1/DAY_COUNTER*7
        )
        print_summary(
            f"MONTHAVG, {day_str:10}, {DAY_COUNTER:3}d ",
            current_day_values,
            t_year,
            "",
            365/DAY_COUNTER/12
        )
        print_summary(
            f"YEARLY  , {day_str:10}, {DAY_COUNTER:3}d ",
            current_day_values,
            t_year,
            "",
            365/DAY_COUNTER
        )
        if SHEETUPDATE and current_day.year == 2999:
            day_info = t_day[T_CURRENT_DAY].strftime("%a %H:%M")
            print_summary(
                f"SHEET {day_str:10} {day_info} {DAY_COUNTER:3}d",
                current_day_values,
                t_year,
                "",
                1.0
            )

        DAY_COUNTER = 0
        t_year = current_day_values

    totals = (t_day, t_week, t_month, t_year, t_trip)
    return totals


def keep_track_of_totals(values, split, prev_split, handle_moved):
    """ keep_track_of_totals """
    debug("keep track of totals")
    debug("prev_split: " + str(prev_split))
    debug("     split: " + str(split))

    t_odo = values[T_ODO]
    t_charged_perc = values[T_CHARGED_PERC]
    t_discharged_perc = values[T_DISCHARGED_PERC]
    t_charges = values[T_CHARGES]
    t_trips = values[T_TRIPS]
    t_elapsed_minutes = values[T_ELAPSED_MINUTES]
    t_soc_avg = values[T_SOC_AVG]
    t_soc_min = values[T_SOC_MIN]
    t_soc_max = values[T_SOC_MAX]
    t_volt12_avg = values[T_VOLT12_AVG]
    t_volt12_min = values[T_VOLT12_MIN]
    t_volt12_max = values[T_VOLT12_MAX]
    t_moves = values[T_MOVES]

    delta_odo = float(split[ODO].strip()) - float(prev_split[ODO].strip())
    coord_changed = (
        float(split[LAT].strip()) != float(prev_split[LAT].strip()) or
        float(split[LON].strip()) != float(prev_split[LON].strip())
    )
    moved = coord_changed or delta_odo
    if coord_changed:
        t_moves += 1
        if MOVES and handle_moved:
            debug("Coordinate changed")
            loc = (float(split[LAT].strip()), float(split[LON].strip()))
            prev_loc = (
                float(prev_split[LAT].strip()), float(prev_split[LON].strip()))
            t_odo = 0.0
            if ODO_METRIC == "km":
                t_odo = -geodesic(loc, prev_loc).kilometers
            elif ODO_METRIC == "mi":
                t_odo = -geodesic(loc, prev_loc).miles

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
        t_trips += 1
        debug(f"DELTA_ODO: {delta_odo:7.1f} {t_trips}")

    debug("    before: " + str(values))
    values = (
        values[T_CURRENT_DAY],
        t_odo,
        t_charged_perc,
        t_discharged_perc,
        t_charges,
        t_trips,
        t_elapsed_minutes,
        soc,
        t_soc_avg,
        t_soc_min,
        t_soc_max,
        volt12,
        t_volt12_avg,
        t_volt12_min,
        t_volt12_max,
        t_moves
    )
    debug("     after: " + str(values))
    return values


def get_address(split):
    """ get address """
    location_str = ""
    if ADDRESS:
        sleep(1)  # do not abuse Nominatim, 1 request per second
        geolocator = \
            Nominatim(user_agent="hyundai_kia_connect_monitor")
        location = geolocator.reverse(
            split[LAT].strip() + ", " + split[LON].strip())
        location_str = ' "' + location.address + '"'
    return location_str


def handle_line(split, prev_split, totals):
    """ handle_line """
    debug(f"handle_line: {split}, {prev_split}")
    current_day = parser.parse(split[DT])
    current_day_values = init(
        current_day,
        float(split[ODO].strip()),
        to_int(split[SOC]),
        to_int(split[V12]))
    t_day = totals[T_DAY]
    if not t_day:  # first time, fill in with initial values
        debug(f"not TDAY: {t_day}")
        totals = (
            current_day_values,
            current_day_values,
            current_day_values,
            current_day_values,
            current_day_values
        )
        return totals

    t_trip = totals[T_TRIP]
    t_week = totals[T_WEEK]
    t_month = totals[T_MONTH]
    t_year = totals[T_YEAR]

    day_change = not same_day(current_day, t_day[T_CURRENT_DAY])
    if day_change:  # assume just before 24 hour
        current_day = \
            current_day.replace(hour=23, minute=59) - timedelta(days=1)

    # take into account totals per line
    if current_day.year != 2999:  # skip keep_track_of_totals for last entry
        if DAY:
            t_day = keep_track_of_totals(t_day, split, prev_split, False)
        if WEEK:
            t_week = keep_track_of_totals(t_week, split, prev_split, False)
        if MONTH:
            t_month = keep_track_of_totals(t_month, split, prev_split, False)
        if YEAR:
            t_year = keep_track_of_totals(t_year, split, prev_split, False)

        if MOVES:
            t_moves_init = init(
                current_day, 0.0,  to_int(split[SOC]), to_int(split[V12]))
            t_moves = keep_track_of_totals(
                t_moves_init, split, prev_split, True)
            if t_moves[T_MOVES] > 0:
                day_move_str = current_day.strftime("%Y-%m-%d")
                day_move_info = current_day.strftime("%H:%M")
                print_summary(
                    f"MOVE    , {day_move_str:10}, {day_move_info:5}",
                    t_moves_init,
                    t_moves,
                    get_address(split),
                    1.0
                )

        if TRIP:
            t_trip = keep_track_of_totals(t_trip, split, prev_split, False)
            if t_trip[T_TRIPS] > 0:
                day_trip_str = current_day.strftime("%Y-%m-%d")
                day_info = current_day.strftime("%H:%M")
                print_summary(
                    f"TRIP    , {day_trip_str:10}, {day_info:5}",
                    current_day_values,
                    t_trip,
                    get_address(split),
                    1.0
                )
                t_trip = current_day_values

    totals = (t_day, t_week, t_month, t_year, t_trip)

    if day_change:
        debug(f"DAY change: {t_day}")
        totals = print_summaries(current_day_values, totals)

    return totals


def summary():
    """ summary of monitor.csv file """
    with INPUT.open("r", encoding="utf-8") as inputfile:
        linecount = 0
        prev_index = -1
        prev_line = ''
        prev_split = ()
        totals = ((), (), (), (), ())
        print_header_and_update_queue()

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
        print_header_and_update_queue()


if SHEETUPDATE:
    gc = gspread.service_account()
    spreadsheet = gc.open("hyundai-kia-connect-monitor")
    SHEET = spreadsheet.sheet1

summary()  # do the work

if SHEETUPDATE:
    print_output_queue()
