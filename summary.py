# == summary.py Author: Zuinige Rijder =======================================
"""
Simple Python3 script to make a summary of monitor.csv
"""
import sys
import configparser
import traceback
import time
from datetime import datetime, timedelta
from pathlib import Path
from collections import deque
import gspread
from dateutil import parser


def log(msg):
    """log a message prefixed with a date/time format yyyymmdd hh:mm:ss"""
    print(datetime.now().strftime("%Y%m%d %H:%M:%S") + ': ' + msg)


def arg_has(string):
    """ arguments has string """
    for i in range(1, len(sys.argv)):
        if sys.argv[i].lower() == string:
            return True
    return False


DEBUG = arg_has('debug')


def debug(line):
    """ print line if debugging """
    if DEBUG:
        print(line)


def get_vin_arg():
    """ get vin argument"""
    for i in range(1, len(sys.argv)):
        if "vin=" in sys.argv[i].lower():
            vin = sys.argv[i]
            vin = vin.replace("vin=", "")
            vin = vin.replace("VIN=", "")
            debug(f"VIN = {vin}")
            return vin

    return ''


def to_int(string):
    """ convert to int """
    if "None" in string:
        return -1
    return int(string)


def to_float(string):
    """ convert to float """
    if "None" in string:
        return 0.0
    return float(string)


KEYWORD_LIST = ['trip', 'day', 'week', 'month', 'year', 'sheetupdate', '-trip', 'help', 'debug'] # noqa pylint:disable=line-too-long
KEYWORD_ERROR = False
for kindex in range(1, len(sys.argv)):
    if not sys.argv[kindex].lower() in KEYWORD_LIST:
        arg = sys.argv[kindex]
        if "vin=" in arg.tolower():
            debug("vin parameter: " + arg)
        else:
            print("Unknown keyword: " + arg)
            KEYWORD_ERROR = True

if KEYWORD_ERROR or arg_has('help'):
    print('Usage: python summary.py [trip] [day] [week] [month] [year] [sheetupdate] [vin=VIN]') # noqa pylint:disable=line-too-long
    exit()


INPUT_CSV_FILE = Path("monitor.csv")
OUTPUT_SPREADSHEET_NAME = "hyundai-kia-connect-monitor"
LENCHECK = 1
VIN = get_vin_arg()
if VIN != '':
    INPUT_CSV_FILE = Path(f"monitor.{VIN}.csv")
    OUTPUT_SPREADSHEET_NAME = f"monitor.{VIN}"
    LENCHECK = 2
debug(f"INPUT_CSV_FILE: {INPUT_CSV_FILE.name}")

TRIP = len(sys.argv) == LENCHECK or (arg_has('trip') and not arg_has('-trip'))
DAY = len(sys.argv) == LENCHECK or arg_has('day') or arg_has('-trip')
WEEK = len(sys.argv) == LENCHECK or arg_has('week') or arg_has('-trip')
MONTH = len(sys.argv) == LENCHECK or arg_has('month') or arg_has('-trip')
YEAR = len(sys.argv) == LENCHECK or arg_has('year') or arg_has('-trip')
SHEETUPDATE = arg_has('sheetupdate')
if SHEETUPDATE:
    DAY = True
    WEEK = True
    MONTH = True
    YEAR = True


# == read monitor in monitor.cfg ===========================
config_parser = configparser.ConfigParser()
config_parser.read('summary.cfg')
monitor_settings = dict(config_parser.items('summary'))

ODO_METRIC = monitor_settings['odometer_metric'].lower()
NET_BATTERY_SIZE_KWH = to_float(monitor_settings['net_battery_size_kwh'])
AVERAGE_COST_PER_KWH = to_float(monitor_settings['average_cost_per_kwh'])
COST_CURRENCY = monitor_settings['cost_currency']
MIN_CONSUMPTION_DISCHARGE_KWH = to_float(
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
LOCATION = 9  # location address (optional field)

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


def init(current_day, odo, soc, volt12):
    """ init tuple with initial values """
    # current_day, odo, charged_perc, discharged_perc, charges, trips,
    # elapsed_minutes,
    # soc_cur, soc_avg, soc_min, soc_max,
    # 12v_cur, 12v_avg, 12v_min, 12v_max
    debug(f"init({current_day})")
    return (
        current_day, odo, 0, 0, 0, 0, 0,
        soc, soc, soc, soc,  # SOC%
        volt12, volt12, volt12, volt12  # 12V%
    )


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


def split_output_to_sheet_list(queue_output):
    """ split output to sheet list """
    split = queue_output.split(',')
    return [split]


def print_output_queue():
    """ print output queue """
    first_row = 21
    last_row = 73
    array = []

    # clean rows first
    list_output = split_output_to_sheet_list(",,,,,,,,,,,,,,,,,,,,,,")
    qlen = len(LAST_OUTPUT_QUEUE)
    current_row = first_row
    debug(f"current_row={current_row} last_row={last_row} queue_len={qlen}")
    for _ in range(current_row, last_row):
        debug(f"clear row: {current_row}")
        array.append({
                'range': f"A{current_row}:W{current_row}",
                'values': list_output,
            })
        current_row += 1

    # print queue entries in reverse order, so in spreadsheet latest is first
    current_row = last_row - (50 - qlen)
    for queue_output in LAST_OUTPUT_QUEUE:
        current_row -= 1
        debug(f"write row: {current_row} {queue_output}")
        list_output = split_output_to_sheet_list(queue_output)
        array.append({
            'range': f"A{current_row}:V{current_row}",
            'values': list_output,
        })
    SHEET.batch_update(array)


def print_header_and_update_queue():
    """print header and update queue"""
    output=f"  Period, date      , info , odometer, delta {ODO_METRIC},    +kWh,     -kWh, {ODO_METRIC}/kWh, kWh/100{ODO_METRIC}, cost {COST_CURRENCY}, SOC%CUR,AVG,MIN,MAX, 12V%CUR,AVG,MIN,MAX, #charges,   #trips, Address"  # noqa pylint:disable=line-too-long
    print_output_and_update_queue(output)


def float_to_string(input_value):
    """ float to string without trailing zero """
    return (f"{input_value:9.1f}").rstrip('0').rstrip('.')


def get_address(split):
    """ get address """
    debug(f"get_address: str{split}")
    location_str = ""
    if len(split) > 9:
        location_str = split[LOCATION].strip()
        if len(location_str) > 0:
            location_str = ' "' + location_str + '"'

    return location_str


def print_summary(prefix, current, values, split, factor):
    """ print_summary """
    debug("print_summary")
    debug("PREV  : " + str(values))
    debug("CURR  : " + str(current))
    debug("VALUES: " + str(values))
    odo = current[T_ODO]
    if odo == 0.0:
        return  # bad line

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

    location_str = get_address(split)

    if SHEETUPDATE and prefix.startswith('SHEET'):
        km_mi_per_kwh_str = km_mi_per_kwh_str.strip()
        kwh_per_km_mi_str = kwh_per_km_mi_str.strip()
        cost_str = cost_str.strip()
        prefix = prefix.replace("SHEET ", "")
        last_update_datetime = datetime.fromtimestamp(
            INPUT_CSV_FILE.stat().st_mtime)
        day_info = last_update_datetime.strftime("%Y-%m-%d %H:%M %a")
        SHEET.batch_update([{
            'range': 'A1:B1',
            'values': [["Last update", f"{day_info}"]],
        }, {
            'range': 'A2:B2',
            'values': [["Last entry", f"{prefix}"]],
        }, {
            'range': 'A3:B3',
            'values': [["Last address", f"{location_str}"]],
        }, {
            'range': 'A4:B4',
            'values': [[f"Odometer {ODO_METRIC}", f"{odo:.1f}"]],
        }, {
            'range': 'A5:B5',
            'values': [[f"Driven {ODO_METRIC}", f"{delta_odo:.1f}"]],
        }, {
            'range': 'A6:B6',
            'values': [["+kWh", f"{charged_kwh:.1f}"]],
        }, {
            'range': 'A7:B7',
            'values': [["-kWh", f"{discharged_kwh:.1f}"]],
        }, {
            'range': 'A8:B8',
            'values': [[f"{ODO_METRIC}/kWh", f"{km_mi_per_kwh_str}"]],
        }, {
            'range': 'A9:B9',
            'values': [[f"kWh/100{ODO_METRIC}", f"{kwh_per_km_mi_str}"]],
        }, {
            'range': 'A10:B10',
            'values': [[f"Cost {COST_CURRENCY}", f"{cost_str}"]],
        }, {
            'range': 'A11:B11',
            'values': [["Current SOC%", f"{t_soc_cur}"]],
        }, {
            'range': 'A12:B12',
            'values': [["Average SOC%", f"{t_soc_avg}"]],
        }, {
            'range': 'A13:B13',
            'values': [["Min SOC%", f"{t_soc_min}"]],
        }, {
            'range': 'A14:B14',
            'values': [["Max SOC%", f"{t_soc_max}"]],
        }, {
            'range': 'A15:B15',
            'values': [["Current 12V%", f"{t_volt12_cur}"]],
        }, {
            'range': 'A16:B16',
            'values': [["Average 12V%", f"{t_volt12_avg}"]],
        }, {
            'range': 'A17:B17',
            'values': [["Min 12V%", f"{t_volt12_min}"]],
        }, {
            'range': 'A18:B18',
            'values': [["Max 12V%", f"{t_volt12_max}"]],
        }, {
            'range': 'A19:B19',
            'values': [["#Charges", f"{t_charges}"]],
        }, {
            'range': 'A20:B20',
            'values': [["#Trips", f"{t_trips}"]],
        }])
    else:
        output=f"{prefix:18},{odo_str:9},{delta_odo_str:9},{charged_kwh_str:8},{discharged_kwh_str:9},{km_mi_per_kwh_str:7},{kwh_per_km_mi_str:10},{cost_str:10},{t_soc_cur:8},{t_soc_avg:3},{t_soc_min:3},{t_soc_max:3},{t_volt12_cur:8},{t_volt12_avg:3},{t_volt12_min:3},{t_volt12_max:3},{t_charges_str:9},{t_trips_str:9},{location_str}"  # noqa pylint:disable=line-too-long
        print_output_and_update_queue(output)


def print_summaries(current_day_values, totals, split, last):
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

    if not same_day(current_day, t_day[T_CURRENT_DAY]) or last:
        DAY_COUNTER += 1
        debug(f"DAY_COUNTER increment: {DAY_COUNTER}")
        if DAY:
            day_info = t_day[T_CURRENT_DAY].strftime("%a")
            print_summary(
                f"DAY     , {day_str}, {day_info:5}",
                current_day_values,
                t_day,
                split,
                1.0
            )
        t_day = current_day_values
        t_trip = current_day_values

    if WEEK and (not same_week(current_day, t_week[T_CURRENT_DAY]) or last):
        weeknr = t_week[T_CURRENT_DAY].strftime("%W")
        print_summary(
            f"WEEK    , {day_str:10}, WK {weeknr:2}",
            current_day_values,
            t_week,
            split,
            1.0
        )
        t_week = current_day_values

    if MONTH and (not same_month(current_day, t_month[T_CURRENT_DAY]) or last):
        month_info = t_month[T_CURRENT_DAY].strftime("%b")
        print_summary(
            f"MONTH   , {day_str:10}, {month_info:5}",
            current_day_values,
            t_month,
            split,
            1.0
        )
        t_month = current_day_values
    if YEAR and (not same_year(current_day, t_year[T_CURRENT_DAY]) or last):
        year = t_year[T_CURRENT_DAY].strftime("%Y")
        print_summary(
            f"YEAR    , {day_str:10}, {year:5}",
            current_day_values,
            t_year,
            split,
            1.0
        )
        trips = t_year[T_TRIPS]
        print_summary(
            f"TRIPAVG , {day_str:10}, {trips:3}t ",
            current_day_values,
            t_year,
            split,
            1/trips
        )
        print_summary(
            f"DAYAVG  , {day_str:10}, {DAY_COUNTER:3}d ",
            current_day_values,
            t_year,
            split,
            1/DAY_COUNTER
        )
        print_summary(
            f"WEEKAVG , {day_str:10}, {DAY_COUNTER:3}d ",
            current_day_values,
            t_year,
            split,
            1/DAY_COUNTER*7
        )
        print_summary(
            f"MONTHAVG, {day_str:10}, {DAY_COUNTER:3}d ",
            current_day_values,
            t_year,
            split,
            365/DAY_COUNTER/12
        )
        print_summary(
            f"YEARLY  , {day_str:10}, {DAY_COUNTER:3}d ",
            current_day_values,
            t_year,
            split,
            365/DAY_COUNTER
        )
        if SHEETUPDATE and last:
            day_info = current_day.strftime("%a %H:%M")
            debug('SHEETUPDATE: ' + day_info)
            print_summary(
                f"SHEET {day_str:10} {day_info} {DAY_COUNTER:3}d",
                current_day_values,
                t_year,
                split,
                1.0
            )

        DAY_COUNTER = 0
        t_year = current_day_values

    totals = (t_day, t_week, t_month, t_year, t_trip)
    return totals


def keep_track_of_totals(values, split, prev_split):
    """ keep_track_of_totals """
    debug("keep track of totals")
    debug("prev_split: " + str(prev_split))
    debug("     split: " + str(split))

    odo = to_float(split[ODO].strip())
    if odo == 0.0:
        return values  # bad line
    prev_odo = to_float(prev_split[ODO].strip())
    if prev_odo == 0.0:
        return values  # bad line

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

    delta_odo = odo - prev_odo
    if delta_odo < 0.0:
        debug(f"negative odometer:\n{prev_split}\n{split}")
        delta_odo = 0.0

    coord_changed = (
        to_float(split[LAT].strip()) != to_float(prev_split[LAT].strip()) or
        to_float(split[LON].strip()) != to_float(prev_split[LON].strip())
    )
    moved = coord_changed or delta_odo != 0.0

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
        t_volt12_max
    )
    debug("     after: " + str(values))
    return values


def handle_line(split, prev_split, totals, last):
    """ handle_line """
    debug(f"handle_line: {split}, {prev_split}")
    odo = to_float(split[ODO].strip())
    if odo == 0.0:
        return totals  # bad line
    current_day = parser.parse(split[DT])
    current_day_values = init(
        current_day,
        odo,
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

    # take into account totals per line
    if not last:  # skip keep_track_of_totals for last entry
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
            if t_trip[T_TRIPS] > 0:
                day_trip_str = current_day.strftime("%Y-%m-%d")
                day_info = current_day.strftime("%H:%M")
                print_summary(
                    f"TRIP    , {day_trip_str:10}, {day_info:5}",
                    current_day_values,
                    t_trip,
                    split,
                    1.0
                )
                t_trip = current_day_values

    totals = (t_day, t_week, t_month, t_year, t_trip)

    if last or not same_day(current_day, t_day[T_CURRENT_DAY]):
        debug(f"DAY change: {t_day}")
        totals = print_summaries(current_day_values, totals, split, last)

    return totals


def summary():
    """ summary of monitor.csv file """
    with INPUT_CSV_FILE.open("r", encoding="utf-8") as inputfile:
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
            if index <= 0 or line.startswith("datetime") or prev_line == line:
                debug(f"Skipping line:\n{line}\n{prev_line}")
                continue  # skip headers and lines starting or without ,
            split = line.split(',')
            if not totals[T_DAY] or not same_day(parser.parse(split[DT]), parser.parse(prev_split[DT])) or prev_line[prev_index:] != line[index:]:  # noqa pylint:disable=line-too-long
                if totals[T_DAY] and not same_day(parser.parse(split[DT]), parser.parse(prev_split[DT])):  # noqa pylint:disable=line-too-long
                    # handle end of day previous day
                    eod_line = line[0:11] + "00:00:00" + prev_line[19:]
                    debug(f"prev_line: {prev_line}\n eod_line: {eod_line}")
                    last_split = eod_line.split(',')
                    totals = handle_line(last_split, prev_split, totals, False)
                totals = handle_line(
                    split,
                    prev_split,
                    totals,
                    False
                )

            prev_index = index
            prev_line = line
            prev_split = split

        # also compute last last day/week/month
        debug("Handling last values")
        # handle end of day for last value
        date_string = prev_line[0:10]
        date_date = datetime.strptime(date_string, "%Y-%m-%d")
        eod_date = date_date + timedelta(days=1)
        eod_line = eod_date.strftime("%Y-%m-%d ") + \
            "00:00:00" + prev_line[19:]
        last_split = eod_line.split(',')
        debug(f"prev_line: {prev_line}\n eod_line: {eod_line}")
        totals = handle_line(last_split, prev_split, totals, False)
        # and show summaries
        handle_line(
            last_split,
            last_split,
            totals,
            True
        )
        print_header_and_update_queue()


if SHEETUPDATE:
    RETRIES = 2
    while RETRIES > 0:
        try:
            gc = gspread.service_account()
            spreadsheet = gc.open(OUTPUT_SPREADSHEET_NAME)
            SHEET = spreadsheet.sheet1
            RETRIES = 0
        except Exception as ex:  # pylint: disable=broad-except
            log('Exception: ' + str(ex))
            traceback.print_exc()
            RETRIES -= 1
            log("Sleeping a minute")
            time.sleep(60)

summary()  # do the work

if SHEETUPDATE:
    RETRIES = 2
    while RETRIES > 0:
        try:
            print_output_queue()
            RETRIES = 0
        except Exception as ex:  # pylint: disable=broad-except
            log('Exception: ' + str(ex))
            traceback.print_exc()
            RETRIES -= 1
            log("Sleeping a minute")
            time.sleep(60)
