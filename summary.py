# == summary.py Author: Zuinige Rijder ========= pylint:disable=too-many-lines
"""
Simple Python3 script to make a summary of monitor.csv
"""
from io import TextIOWrapper
import sys
import configparser
import traceback
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from collections import deque
import gspread
from dateutil import parser
from monitor_utils import (
    log,
    arg_has,
    get_vin_arg,
    safe_divide,
    to_int,
    to_float,
    is_true,
    same_year,
    same_month,
    same_week,
    same_day,
    float_to_string,
    get_last_line,
    read_translations,
    get_translation,
    split_output_to_sheet_list,
)

D = arg_has("debug")


def dbg(line: str) -> bool:
    """print line if debugging"""
    if D:
        print(line)
    return D  # just to make a lazy evaluation expression possible


KEYWORD_LIST = [
    "trip",
    "day",
    "week",
    "month",
    "year",
    "sheetupdate",
    "-trip",
    "help",
    "debug",
]
KEYWORD_ERROR = False
for kindex in range(1, len(sys.argv)):
    if sys.argv[kindex].lower() not in KEYWORD_LIST:
        arg = sys.argv[kindex]
        if "vin=" in arg.lower():
            _ = D and dbg("vin parameter: " + arg)
        else:
            print("Unknown keyword: " + arg)
            KEYWORD_ERROR = True

if KEYWORD_ERROR or arg_has("help"):
    print(
        "Usage: python summary.py [trip] [day] [week] [month] [year] [sheetupdate] [vin=VIN]"  # noqa
    )
    exit()


CURRENT_DAY_STR = datetime.now().strftime("%Y-%m-%d")
MONITOR_CSV_FILENAME = Path("monitor.csv")
LASTRUN_FILENAME = Path("monitor.lastrun")
OUTPUT_SPREADSHEET_NAME = "hyundai-kia-connect-monitor"
CHARGE_CSV_FILENAME = Path("summary.charge.csv")
TRIP_CSV_FILENAME = Path("summary.trip.csv")
CHARGE_CSV_FILE: TextIOWrapper

LENCHECK = 1
VIN = get_vin_arg()
if VIN != "":
    MONITOR_CSV_FILENAME = Path(f"monitor.{VIN}.csv")
    LASTRUN_FILENAME = Path(f"monitor.{VIN}.lastrun")
    OUTPUT_SPREADSHEET_NAME = f"monitor.{VIN}"
    CHARGE_CSV_FILENAME = Path(f"summary.charge.{VIN}.csv")
    TRIP_CSV_FILENAME = Path("summary.trip.{VIN}.csv")
    LENCHECK = 2
_ = D and dbg(f"INPUT_CSV_FILE: {MONITOR_CSV_FILENAME.name}")

TRIP = len(sys.argv) == LENCHECK or arg_has("trip") and not arg_has("-trip")
DAY = len(sys.argv) == LENCHECK or arg_has("day") or arg_has("-trip")
WEEK = len(sys.argv) == LENCHECK or arg_has("week") or arg_has("-trip")
MONTH = len(sys.argv) == LENCHECK or arg_has("month") or arg_has("-trip")
YEAR = len(sys.argv) == LENCHECK or arg_has("year") or arg_has("-trip")
SHEETUPDATE = arg_has("sheetupdate")
if SHEETUPDATE:
    TRIP = True
    DAY = True
    WEEK = True
    MONTH = True
    YEAR = True

HIGHEST_ODO = 0.0

# == read monitor in monitor.cfg ===========================
config_parser = configparser.ConfigParser()
config_parser.read("summary.cfg")
monitor_settings = dict(config_parser.items("summary"))

ODO_METRIC = monitor_settings["odometer_metric"].lower()
NET_BATTERY_SIZE_KWH = to_float(monitor_settings["net_battery_size_kwh"])
AVERAGE_COST_PER_KWH = to_float(monitor_settings["average_cost_per_kwh"])
COST_CURRENCY = monitor_settings["cost_currency"]
MIN_CONSUMPTION_DISCHARGE_KWH = to_float(
    monitor_settings["min_consumption_discharge_kwh"]
)
SMALL_POSITIVE_DELTA = int(monitor_settings["ignore_small_positive_delta_soc"])
SMALL_NEGATIVE_DELTA = int(monitor_settings["ignore_small_negative_delta_soc"])
SHOW_ZERO_VALUES = is_true(monitor_settings["show_zero_values"])

# indexes to splitted monitor.csv items
DT = 0  # datetime
LON = 1  # longitude
LAT = 2  # latitude
ENGINEON = 3  # engineOn
V12 = 4  # 12V%
ODO = 5  # odometer
SOC = 6  # SOC%
CHARGING = 7  # charging
PLUGGED = 8  # plugged
LOCATION = 9  # location address (optional field)
EV_RANGE = 10  # EV range (optional field)

# number of days passed in this year
DAY_COUNTER = 0

# Initializing a queue with maximum size
LAST_OUTPUT_QUEUE_MAX_LEN = 122
LAST_OUTPUT_QUEUE: deque[str] = deque(maxlen=LAST_OUTPUT_QUEUE_MAX_LEN)


@dataclass
class Totals:
    """Totals"""

    current_day: datetime
    odo: float
    charged_perc: int
    discharged_perc: int
    charges: int
    trips: int
    elapsed_minutes: int
    soc_cur: int
    soc_avg: float
    soc_min: int
    soc_max: int
    volt12_cur: int
    volt12_avg: float
    volt12_min: int
    volt12_max: int
    soc_charged: int


@dataclass
class GrandTotals:
    """GrandTotals"""

    day: Totals
    week: Totals
    month: Totals
    year: Totals
    trip: Totals


@dataclass
class Translations:
    """Translations"""

    last_run: str
    period: str
    date: str
    info: str
    odometer: str
    delta: str
    cost: str
    soc_perc: str
    avg: str
    min: str
    max: str
    volt12_perc: str
    charges: str
    trips: str
    ev_range: str
    address: str
    vehicle_upd: str
    gps_update: str
    last_entry: str
    last_address: str
    driven: str


TR_HELPER: dict[str, str] = read_translations()


def fill_translations() -> Translations:
    """fill translations"""

    translations = Translations(
        last_run=get_translation(TR_HELPER, "Last run"),
        period=get_translation(TR_HELPER, "Period"),
        date=get_translation(TR_HELPER, "Date"),
        info=get_translation(TR_HELPER, "Info"),
        odometer=get_translation(TR_HELPER, "Odometer"),
        delta=get_translation(TR_HELPER, "Delta"),
        cost=get_translation(TR_HELPER, "Cost"),
        soc_perc=get_translation(TR_HELPER, "soc perc"),
        avg=get_translation(TR_HELPER, "AVG"),
        min=get_translation(TR_HELPER, "MIN"),
        max=get_translation(TR_HELPER, "MAX"),
        volt12_perc=get_translation(TR_HELPER, "12volt perc"),
        charges=get_translation(TR_HELPER, "#charges"),
        trips=get_translation(TR_HELPER, "#trips"),
        ev_range=get_translation(TR_HELPER, "EV range"),
        address=get_translation(TR_HELPER, "Address"),
        vehicle_upd=get_translation(TR_HELPER, "Vehicle upd"),
        gps_update=get_translation(TR_HELPER, "GPS update"),
        last_entry=get_translation(TR_HELPER, "Last entry"),
        last_address=get_translation(TR_HELPER, "Last address"),
        driven=get_translation(TR_HELPER, "Driven"),
    )
    return translations


TR = fill_translations()  # TR contains translations dataclass


def init(current_day: datetime, odo: float, soc: int, volt12: int) -> Totals:
    """init Totals with initial values"""
    # current_day, odo, charged_perc, discharged_perc, charges, trips,
    # elapsed_minutes,
    # soc_cur, soc_avg, soc_min, soc_max,
    # 12v_cur, 12v_avg, 12v_min, 12v_max
    _ = D and dbg(f"init({current_day})")
    totals = Totals(
        current_day,
        odo,
        0,
        0,
        0,
        0,
        0,
        soc,
        soc,
        soc,
        soc,  # SOC%
        volt12,
        volt12,
        volt12,
        volt12,  # 12V%
        0,  # soc_charged
    )
    return totals


COLUMN_WIDTHS = [13, 10, 5, 7, 8, 8, 8, 5, 5, 8, 3, 3, 3, 3, 3, 3, 3, 3, 6, 6, 4, 99]


def print_output_and_update_queue(output: str) -> None:
    """print output and update queue"""
    total_line = ""
    split = output.split(",")
    for i in range(len(split)):  # pylint:disable=consider-using-enumerate
        string = split[i].strip()
        if i == 0 and string != TR.period:
            string = get_translation(TR_HELPER, string)
        elif i == 2 and split[0].startswith("DAY "):
            string = get_translation(TR_HELPER, string)
        if len(string) > COLUMN_WIDTHS[i]:
            COLUMN_WIDTHS[i] = len(string)
        if i > 20:
            text = string.ljust(COLUMN_WIDTHS[i])
        else:
            text = string.rjust(COLUMN_WIDTHS[i])
        total_line += text
        total_line += ", "
    print(total_line)

    if SHEETUPDATE:
        LAST_OUTPUT_QUEUE.append(total_line)


def sheet_append_first_rows(row_a: str, row_b: str) -> None:
    """sheet_append_first_rows"""
    row_a_values = row_a.split(",")
    row_b_values = row_b.split(",")
    len_a = len(row_a_values)
    len_b = len(row_b_values)
    if len_a != len_b:
        log(f"ERROR: sheet_append_first_rows, length A {len_a} != length B {len_b}")
        return  # nothing to do

    array = []
    for index, value in enumerate(row_a_values):
        row_a_value = value.strip()
        row_b_value = row_b_values[index].strip()
        row = index + 1
        if D:
            string_a = row_a_value.ljust(25)
            print(f"{string_a} {row_b_value}")
        array.append(
            {
                "range": f"A{row}:B{row}",
                "values": [[row_a_value, row_b_value]],
            }
        )
    SHEET.batch_update(array)

    formats = []
    formats.append(
        {
            "range": "A1:A23",
            "format": {
                "horizontalAlignment": "LEFT",
                "textFormat": {
                    "bold": True,
                    "underline": True,
                    "italic": True,
                },
            },
        }
    )
    SHEET.batch_format(formats)


def print_output_queue() -> None:
    """print output queue"""
    last_row = LAST_OUTPUT_QUEUE_MAX_LEN + 25  # start on row 25
    array = []
    formats = []
    qlen = len(LAST_OUTPUT_QUEUE)
    current_row = last_row - (LAST_OUTPUT_QUEUE_MAX_LEN - qlen)

    # print queue entries in reverse order, so in spreadsheet latest is first
    for queue_output in LAST_OUTPUT_QUEUE:
        current_row -= 1
        _ = D and dbg(f"write row: {current_row} {queue_output}")
        list_output = split_output_to_sheet_list(queue_output)
        array.append(
            {
                "range": f"A{current_row}:W{current_row}",
                "values": list_output,
            }
        )
        if TR.period in queue_output:
            textformat = {
                "bold": True,
                "underline": True,
                "italic": True,
            }
        else:
            textformat = {
                "bold": False,
                "underline": False,
                "italic": False,
            }

        formats.append(
            {
                "range": f"A{current_row}:U{current_row}",
                "format": {
                    "horizontalAlignment": "RIGHT",
                    "textFormat": textformat,
                },
            }
        )
        formats.append(
            {
                "range": f"V{current_row}:V{current_row}",
                "format": {
                    "horizontalAlignment": "LEFT",
                    "textFormat": textformat,
                },
            }
        )
    if len(array) > 0:
        SHEET.batch_update(array)
    if len(formats) > 0:
        SHEET.batch_format(formats)


def print_header_and_update_queue() -> None:
    """print header and update queue"""
    output = f"{TR.period},{TR.date},{TR.info},{TR.odometer},{TR.delta} {ODO_METRIC},+kWh,-kWh,{ODO_METRIC}/kWh,kWh/100{ODO_METRIC},{TR.cost} {COST_CURRENCY},{TR.soc_perc},{TR.avg},{TR.min},{TR.max},{TR.volt12_perc},{TR.avg},{TR.min},{TR.max},{TR.charges},{TR.trips},{TR.ev_range},{TR.address}"  # noqa
    print_output_and_update_queue(output)


def get_address(split: list[str]) -> str:
    """get address"""
    _ = D and dbg(f"get_address: str{split}")
    location_str = ""
    if len(split) > LOCATION:
        location_str = split[LOCATION].strip()
        if len(location_str) > 0:
            location_str = ' "' + location_str + '"'

    return location_str


def get_splitted_list_item(the_list: list[str], index: int) -> list[str]:
    """get splitted item from list"""
    if index < 0 or index >= len(the_list):
        return ["", ""]
    items = the_list[index].split(";")
    if len(items) != 2:
        return ["", ""]
    return [items[0].strip(), items[1].strip()]


if not MONITOR_CSV_FILENAME.is_file():
    log(f"ERROR: file does not exist: {MONITOR_CSV_FILENAME}")
    sys.exit(-1)

MONITOR_CSV_FILE: TextIOWrapper = MONITOR_CSV_FILENAME.open("r", encoding="utf-8")
MONITOR_CSV_FILE_EOL: bool = False
MONITOR_CSV_READ_AHEAD_LINE: str = ""
MONITOR_CSV_READ_DONE_ONCE: bool = False


def get_next_monitor_csv_line() -> str:
    """
    get_next_monitor_csv_line

    Returns empty string if EOF
    Can also be called when already EOF encountered (again empty line returned)
    Skips empty lines
    Skips header lines
    Skips lines without ,
    Skips identical lines
    Skips identical lines, where only the datetime is different
    Does fill INPUT_CSV_READ_AHEAD_LINE (for external use)
    """
    global MONITOR_CSV_FILE_EOL, MONITOR_CSV_READ_AHEAD_LINE, MONITOR_CSV_READ_DONE_ONCE  # noqa pylint:disable=global-statement

    while not MONITOR_CSV_FILE_EOL:
        if MONITOR_CSV_READ_DONE_ONCE:  # read 1 line
            line = MONITOR_CSV_READ_AHEAD_LINE
            MONITOR_CSV_READ_AHEAD_LINE = MONITOR_CSV_FILE.readline()
        else:  # read 2 lines
            MONITOR_CSV_READ_DONE_ONCE = True
            line = MONITOR_CSV_FILE.readline()
            MONITOR_CSV_READ_AHEAD_LINE = MONITOR_CSV_FILE.readline()

        if not line:
            MONITOR_CSV_FILE_EOL = True
            MONITOR_CSV_READ_AHEAD_LINE = line
            break  # finished

        if line != MONITOR_CSV_READ_AHEAD_LINE:  # skip identical lines
            line = line.strip()
            # only lines with content and not header line
            if line != "" and not line.startswith("datetime"):
                index = line.find(",")
                next_line = MONITOR_CSV_READ_AHEAD_LINE.strip()
                read_ahead_index = next_line.find(",")
                # skip identical lines, when only first column is the same
                if index >= 0 and (
                    read_ahead_index < 0 or next_line[read_ahead_index:] != line[index:]
                ):
                    _ = D and dbg(f"next=[{line}]")
                    return line

        _ = D and dbg(f"skip=[{line}]")

    _ = D and dbg("return=[]\n")
    return ""


def write_charge_csv(line: str) -> None:
    """write charge csv"""
    _ = D and dbg(f"{CHARGE_CSV_FILENAME}:[{line}]")
    CHARGE_CSV_FILE.write(line)
    CHARGE_CSV_FILE.write("\n")


def write_trip_csv(line: str) -> None:
    """write trip csv"""
    _ = D and dbg(f"{TRIP_CSV_FILENAME}:[{line}]")
    TRIP_CSV_FILE.write(line)
    TRIP_CSV_FILE.write("\n")


def print_summary(
    prefix: str, current: Totals, values: Totals, split: list[str], factor: float
) -> None:
    """print_summary"""
    if D:
        dbg("print_summary")
        dbg("PREV  : " + str(values))
        dbg("CURR  : " + str(current))
        dbg("VALUES: " + str(values))
    odo = current.odo
    if odo == 0.0:
        return  # bad line

    delta_odo = round(odo - values.odo, 1) * factor
    odo_str = ""
    if odo != 0.0:
        odo_str = f"{odo:9.1f}"
    t_charged_perc = values.charged_perc * factor
    if t_charged_perc < 0:
        t_charged_perc = 0
    t_discharged_perc = values.discharged_perc * factor
    if t_discharged_perc > 0:
        t_discharged_perc = 0
    t_charges = values.charges * factor
    t_trips = values.trips * factor

    t_elapsed_minutes = max(values.elapsed_minutes, 1)
    t_soc_cur = values.soc_cur
    t_soc_avg = round(safe_divide(values.soc_avg, t_elapsed_minutes))
    t_soc_min = values.soc_min
    t_soc_max = values.soc_max

    t_volt12_cur = values.volt12_cur
    t_volt12_avg = round(safe_divide(values.volt12_avg, t_elapsed_minutes))
    t_volt12_min = values.volt12_min
    t_volt12_max = values.volt12_max
    t_soc_charged = values.soc_charged

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
        if TRIP or discharged_kwh < -MIN_CONSUMPTION_DISCHARGE_KWH:  # skip inaccurate
            cost = discharged_kwh * -AVERAGE_COST_PER_KWH
            cost_str = f"{cost:10.2f}"
            km_mi_per_kwh = safe_divide(delta_odo, -discharged_kwh)
            km_mi_per_kwh_str = f"{km_mi_per_kwh:7.1f}"
            if km_mi_per_kwh > 0.0:
                kwh_per_km_mi = safe_divide(100, km_mi_per_kwh)
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

    ev_range = -1
    if len(split) > EV_RANGE:
        ev_range = to_int(split[EV_RANGE])

    if DAY and charged_kwh > 3.0 and prefix.startswith("DAY "):
        splitted = prefix.split(",")
        if len(splitted) > 2:
            date = splitted[1].strip()
            write_charge_csv(f"{date}, {odo:.1f}, {charged_kwh:.1f}, {t_soc_charged}")

    if TRIP and prefix.startswith("TRIP "):
        splitted = prefix.split(",")
        if len(splitted) > 2:
            date = splitted[1].strip()
            time_str = splitted[2].strip()
            write_trip_csv(
                f"{date} {time_str}, {odo:.1f}, {delta_odo:.1f}, {discharged_kwh:.1f}, {charged_kwh:.1f}"  # noqa
            )

    if SHEETUPDATE and prefix.startswith("SHEET "):
        km_mi_per_kwh_str = km_mi_per_kwh_str.strip()
        kwh_per_km_mi_str = kwh_per_km_mi_str.strip()
        cost_str = cost_str.strip()
        prefix = prefix.replace("SHEET ", "")
        last_line = get_last_line(MONITOR_CSV_FILENAME).replace(",", ";")
        last_run_datetime = datetime.fromtimestamp(LASTRUN_FILENAME.stat().st_mtime)
        last_run_dt = last_run_datetime.strftime("%Y-%m-%d %H:%M ") + get_translation(
            TR_HELPER, last_run_datetime.strftime("%a")
        )

        lastrun_lines = []
        if LASTRUN_FILENAME.is_file():
            with LASTRUN_FILENAME.open("r", encoding="utf-8") as lastrun_file:
                lastrun_lines = lastrun_file.readlines()

        last_updated_at = get_splitted_list_item(lastrun_lines, 2)
        location_last_updated_at = get_splitted_list_item(lastrun_lines, 3)
        last_upd_dt = last_updated_at[1]
        location_last_upd_dt = location_last_updated_at[1]

        row_a = f"{TR.last_run},{TR.vehicle_upd},{TR.gps_update},{TR.last_entry},{TR.last_address},{TR.odometer} {ODO_METRIC},{TR.driven} {ODO_METRIC},+kWh,-kWh,{ODO_METRIC}/kWh,kWh/100{ODO_METRIC},{TR.cost} {COST_CURRENCY},{TR.soc_perc},{TR.avg} {TR.soc_perc},{TR.min} {TR.soc_perc},{TR.max} {TR.soc_perc},{TR.volt12_perc},{TR.avg} {TR.volt12_perc},{TR.min} {TR.volt12_perc},{TR.max} {TR.volt12_perc},{TR.charges},{TR.trips},{TR.ev_range}"  # noqa
        row_b = f"{last_run_dt},{last_upd_dt},{location_last_upd_dt},{last_line},{location_str},{odo:.1f},{delta_odo:.1f},{charged_kwh:.1f},{discharged_kwh:.1f},{km_mi_per_kwh_str},{kwh_per_km_mi_str},{cost_str},{t_soc_cur},{t_soc_avg},{t_soc_min},{t_soc_max},{t_volt12_cur},{t_volt12_avg},{t_volt12_min},{t_volt12_max},{t_charges},{t_trips},{ev_range}"  # noqa
        sheet_append_first_rows(row_a, row_b)

    else:
        output = f"{prefix:18},{odo_str:9},{delta_odo_str:9},{charged_kwh_str:8},{discharged_kwh_str:9},{km_mi_per_kwh_str:7},{kwh_per_km_mi_str:10},{cost_str:10},{t_soc_cur:8},{t_soc_avg:3},{t_soc_min:3},{t_soc_max:3},{t_volt12_cur:8},{t_volt12_avg:3},{t_volt12_min:3},{t_volt12_max:3},{t_charges_str:9},{t_trips_str:9},{ev_range},{location_str}"  # noqa
        print_output_and_update_queue(output)


def print_summaries(
    current_day_values: Totals, totals: GrandTotals, split: list[str], last: bool
) -> GrandTotals:
    """print_summaries"""
    global DAY_COUNTER  # pylint:disable=global-statement
    current_day = current_day_values.current_day
    t_day = totals.day
    t_week = totals.week
    t_month = totals.month
    t_year = totals.year
    t_trip = totals.trip

    day_str = t_day.current_day.strftime("%Y-%m-%d")

    if not same_day(current_day, t_day.current_day) or last:
        DAY_COUNTER += 1
        if DAY:
            day_info = t_day.current_day.strftime("%a")
            print_summary(
                f"DAY     , {day_str}, {day_info:5}",
                current_day_values,
                t_day,
                split,
                1.0,
            )
        t_day = current_day_values
        t_trip = current_day_values

    if WEEK and (not same_week(current_day, t_week.current_day) or last):
        weeknr = t_week.current_day.strftime("%W")
        print_summary(
            f"WEEK    , {day_str:10}, WK {weeknr:2}",
            current_day_values,
            t_week,
            split,
            1.0,
        )
        t_week = current_day_values

    if MONTH and (not same_month(current_day, t_month.current_day) or last):
        month_info = t_month.current_day.strftime("%b")
        print_summary(
            f"MONTH   , {day_str:10}, {month_info:5}",
            current_day_values,
            t_month,
            split,
            1.0,
        )
        t_month = current_day_values
    if YEAR and (not same_year(current_day, t_year.current_day) or last):
        year = t_year.current_day.strftime("%Y")
        print_summary(
            f"YEAR    , {day_str:10}, {year:5}",
            current_day_values,
            t_year,
            split,
            1.0,
        )
        trips = t_year.trips
        print_summary(
            f"TRIPAVG , {day_str:10}, {trips:3}t ",
            current_day_values,
            t_year,
            split,
            safe_divide(1, trips),
        )
        print_summary(
            f"DAYAVG  , {day_str:10}, {DAY_COUNTER:3}d ",
            current_day_values,
            t_year,
            split,
            safe_divide(1, DAY_COUNTER),
        )
        print_summary(
            f"WEEKAVG , {day_str:10}, {DAY_COUNTER:3}d ",
            current_day_values,
            t_year,
            split,
            safe_divide(7, DAY_COUNTER),
        )
        print_summary(
            f"MONTHAVG, {day_str:10}, {DAY_COUNTER:3}d ",
            current_day_values,
            t_year,
            split,
            safe_divide(365 / 12, DAY_COUNTER),
        )
        print_summary(
            f"YEARLY  , {day_str:10}, {DAY_COUNTER:3}d ",
            current_day_values,
            t_year,
            split,
            safe_divide(365, DAY_COUNTER),
        )
        if SHEETUPDATE and last:
            day_info = current_day.strftime("%a %H:%M")
            print_summary(
                f"SHEET {day_str:10} {day_info} {DAY_COUNTER:3}d",
                current_day_values,
                t_year,
                split,
                1.0,
            )

        DAY_COUNTER = 0
        t_year = current_day_values

    totals = GrandTotals(t_day, t_week, t_month, t_year, t_trip)
    return totals


def keep_track_of_totals(
    values: Totals, split: list[str], prev_split: list[str], trip=False
) -> Totals:
    """keep_track_of_totals"""
    if D:
        dbg("keep track of totals")
        dbg("prev_split: " + str(prev_split))
        dbg("     split: " + str(split))

    odo = to_float(split[ODO])
    if odo == 0.0:
        return values  # bad line
    prev_odo = to_float(prev_split[ODO])
    if prev_odo == 0.0:
        return values  # bad line

    t_odo = values.odo
    t_charged_perc = values.charged_perc
    t_discharged_perc = values.discharged_perc
    t_charges = values.charges
    t_trips = values.trips
    t_elapsed_minutes = values.elapsed_minutes
    t_soc_avg = values.soc_avg
    t_soc_min = values.soc_min
    t_soc_max = values.soc_max
    t_volt12_avg = values.volt12_avg
    t_volt12_min = values.volt12_min
    t_volt12_max = values.volt12_max
    t_soc_charged = values.soc_charged

    delta_odo = odo - prev_odo
    if delta_odo < 0.0:
        _ = D and dbg(f"negative odometer:\n{prev_split}\n{split}")
        delta_odo = 0.0

    coord_changed = to_float(split[LAT]) != to_float(prev_split[LAT]) or to_float(
        split[LON]
    ) != to_float(prev_split[LON])
    moved = coord_changed or delta_odo != 0.0

    soc = to_int(split[SOC])
    prev_soc = to_int(prev_split[SOC])
    delta_soc = soc - prev_soc
    if (soc == 0 or prev_soc == 0) and abs(delta_soc) > 5:
        # possibly wrong readout, take largest
        soc = max(soc, prev_soc)
        prev_soc = soc
        delta_soc = 0

    if delta_odo > 0.0:
        t_trips += 1
        _ = D and dbg(f"DELTA_ODO: {delta_odo:7.1f} {t_trips}")
        if trip:
            # workaround that sometimes SOC is decreased in next line
            # so the trip information shows not the correct used kWh
            next_line = MONITOR_CSV_READ_AHEAD_LINE.strip()
            if next_line != "":
                next_split = next_line.split(",")
                if len(next_split) > 8:
                    next_date = next_split[0].split(" ")[0]
                    next_soc = to_int(next_split[SOC])
                    split_date = split[0].split(" ")[0]
                    if D:
                        print(
                            f"split_date: {split_date}\nnext_date : {next_date}\nsplit: {split}\nnext : {next_split}\n"  # noqa
                        )
                    if (
                        next_date == split_date
                        and next_split[ODO] == split[ODO]
                        and next_soc < soc
                    ):
                        # date and ODO the same, but SOC is lower, fix it
                        _ = D and dbg(f"before soc: {soc}, delta_soc: {delta_soc}")
                        delta_soc = next_soc - prev_soc
                        soc = next_soc
                        _ = D and dbg(f"after  soc: {soc}, delta_soc: {delta_soc}\n")

    # keep track of elapsed minutes
    current_day = parser.parse(split[DT])
    prev_day = parser.parse(prev_split[DT])
    elapsed_minutes = round((current_day - prev_day).total_seconds() / 60)
    t_elapsed_minutes += elapsed_minutes

    # keep track of average SOC over time
    average_soc = (soc + prev_soc) / 2
    t_soc_avg += average_soc * elapsed_minutes
    t_soc_min = min(soc, t_soc_min)
    t_soc_max = max(soc, t_soc_max)

    # keep track of average 12V over time
    volt12 = to_int(split[V12])
    prev_volt12 = to_int(prev_split[V12])
    average_volt12 = (volt12 + prev_volt12) / 2
    t_volt12_avg += average_volt12 * elapsed_minutes
    t_volt12_min = min(volt12, t_volt12_min)
    t_volt12_max = max(volt12, t_volt12_max)

    charging = is_true(split[CHARGING])
    prev_charging = is_true(prev_split[CHARGING])
    no_charging = not charging and not prev_charging

    if delta_soc != 0:
        if D:
            dbg(
                f"Delta SOC: {delta_soc}, no_charging: {no_charging}, moved: {moved}, elapsed_minutes: {elapsed_minutes}"  # noqa
            )
        if delta_soc > 0:  # charge +kWh
            if delta_soc <= SMALL_POSITIVE_DELTA and no_charging and not moved:
                # small SOC difference can occur due to
                # temperature difference (e.g. morning/evening)
                if D:
                    dbg(f"skipping positive delta\n{prev_split}\n{split}")
                t_discharged_perc += delta_soc
            else:
                if no_charging and not moved and elapsed_minutes < 120:
                    if D:
                        dbg(
                            f"Unexpected positive delta?\n{prev_split}\n{split}"  # noqa
                        )
                t_charged_perc += delta_soc
                t_soc_charged = soc  # remember latest soc for when charged
        else:
            if delta_soc >= SMALL_NEGATIVE_DELTA and no_charging and not moved:
                # small SOC difference can occur due to
                # temperature difference (e.g. morning/evening)
                if D:
                    dbg(f"skipping negative delta\n{prev_split}\n{split}")
                t_charged_perc += delta_soc
            else:
                t_discharged_perc += delta_soc

    if charging and not prev_charging:
        t_charges += 1
        _ = D and dbg("CHARGES: " + str(t_charges))
    elif delta_soc > 1 and no_charging:
        t_charges += 1
        _ = D and dbg("charges: DELTA_SOC > 1: " + str(t_charges))

    _ = D and dbg("    before: " + str(values))
    values = Totals(
        values.current_day,
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
        t_soc_charged,
    )
    _ = dbg("     after: " + str(values)) if D else 0
    return values


def handle_line(
    linecount: int,
    split: list[str],
    prev_split: list[str],
    totals: GrandTotals,
    last: bool,
) -> GrandTotals:
    """handle_line"""
    _ = D and dbg(f"handle_line: {split}, {prev_split}")
    global HIGHEST_ODO  # pylint:disable=global-statement
    odo = to_float(split[ODO])
    if odo == 0.0:
        _ = D and dbg(f"bad odo: {odo}")
        return totals  # bad line
    if odo < HIGHEST_ODO:
        if D:
            dbg(f"taking over highest ODO: {HIGHEST_ODO} odo={odo}")
        odo = HIGHEST_ODO
    else:
        HIGHEST_ODO = odo

    current_day = parser.parse(split[DT])
    current_day_values = init(current_day, odo, to_int(split[SOC]), to_int(split[V12]))
    t_day = totals.day
    if not t_day:
        _ = D and dbg(f"not TDAY: {t_day} first time, fill in with initial values")
        totals = GrandTotals(
            current_day_values,
            current_day_values,
            current_day_values,
            current_day_values,
            current_day_values,
        )
        return totals

    if (split[DT] == prev_split[DT]) and (
        (split[LAT] != prev_split[LAT]) or (split[LON] != prev_split[LON])
    ):
        print(
            f"Warning: timestamp wrong line {linecount}\nSPLIT: {split}\nPREV : {prev_split}"  # noqa
        )

    t_trip = totals.trip
    t_week = totals.week
    t_month = totals.month
    t_year = totals.year

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
            t_trip = keep_track_of_totals(t_trip, split, prev_split, trip=True)
            if t_trip.trips > 0:
                day_trip_str = current_day.strftime("%Y-%m-%d")
                day_info = current_day.strftime("%H:%M")
                print_summary(
                    f"TRIP    , {day_trip_str:10}, {day_info:5}",
                    current_day_values,
                    t_trip,
                    split,
                    1.0,
                )
                t_trip = current_day_values

    totals = GrandTotals(t_day, t_week, t_month, t_year, t_trip)

    if last or not same_day(current_day, t_day.current_day):
        _ = D and dbg(f"DAY change: {t_day}")
        totals = print_summaries(current_day_values, totals, split, last)

    return totals


def summary():
    """summary of monitor.csv file"""
    if not MONITOR_CSV_FILENAME.is_file():
        log(f"ERROR: file does not exist: {MONITOR_CSV_FILENAME}")
        return

    linecount = 0
    prev_line = ""
    prev_split = ()
    totals: GrandTotals = GrandTotals(None, None, None, None, None)

    print_header_and_update_queue()

    while True:
        line = get_next_monitor_csv_line()
        if line == "":  # EOF
            break  # finish loop
        linecount += 1
        _ = D and dbg(str(linecount) + ": LINE=[" + line + "]")
        split = line.split(",")
        if totals.day and not same_day(
            parser.parse(split[DT]), parser.parse(prev_split[DT])
        ):
            # handle end of day previous day
            eod_line = line[0:11] + "00:00:00" + prev_line[19:]
            if D:
                dbg(f"prev_line: {prev_line}\n eod_line: {eod_line}")
            last_split = eod_line.split(",")
            totals = handle_line(linecount, last_split, prev_split, totals, False)
        totals = handle_line(linecount, split, prev_split, totals, False)

        prev_line = line
        prev_split = split

    # also compute last last day/week/month
    _ = D and dbg("Handling last values")
    # handle end of day for last value
    eod_line = prev_line[0:11] + "23:59:59" + prev_line[19:]
    last_split = eod_line.split(",")
    _ = D and dbg(f"prev_line: {prev_line}\n eod_line: {eod_line}")
    totals = handle_line(linecount, last_split, prev_split, totals, False)
    # and show summaries
    handle_line(linecount, last_split, last_split, totals, True)
    print_header_and_update_queue()


if SHEETUPDATE:
    RETRIES = 2
    while RETRIES > 0:
        try:
            gc = gspread.service_account()
            spreadsheet = gc.open(OUTPUT_SPREADSHEET_NAME)
            SHEET = spreadsheet.sheet1
            SHEET.clear()
            RETRIES = 0
        except Exception as ex:  # pylint: disable=broad-except
            log("Exception: " + str(ex))
            traceback.print_exc()
            RETRIES -= 1
            log("Sleeping a minute")
            time.sleep(60)


# always rewrite charge file, because input might be changed
CHARGE_CSV_FILE = CHARGE_CSV_FILENAME.open("w", encoding="utf-8")
write_charge_csv("date, odometer, +kWh, end charged SOC%")


# always rewrite trip file, because input might be changed
TRIP_CSV_FILE = TRIP_CSV_FILENAME.open("w", encoding="utf-8")
write_trip_csv("date, odometer, distance, -kWh, +kWh")

summary()  # do the work
MONITOR_CSV_FILE.close()
CHARGE_CSV_FILE.close()
TRIP_CSV_FILE.close()

if SHEETUPDATE:
    RETRIES = 2
    while RETRIES > 0:
        try:
            print_output_queue()
            RETRIES = 0
        except Exception as ex:  # pylint: disable=broad-except
            log("Exception: " + str(ex))
            traceback.print_exc()
            RETRIES -= 1
            log("Sleeping a minute")
            time.sleep(60)
