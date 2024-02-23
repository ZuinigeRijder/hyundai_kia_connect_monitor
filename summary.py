# == summary.py Author: Zuinige Rijder ========= pylint:disable=too-many-lines
"""
Simple Python3 script to make a summary of monitor.csv
"""
from copy import deepcopy
from io import TextIOWrapper
import sys
import configparser
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from collections import deque
import gspread
from dateutil import parser
from monitor_utils import (
    get_filepath,
    log,
    arg_has,
    get,
    get_vin_arg,
    safe_divide,
    sleep,
    split_on_comma,
    to_int,
    to_float,
    is_true,
    same_year,
    same_month,
    same_week,
    same_day,
    get_last_line,
    read_translations,
    get_translation,
    split_output_to_sheet_list,
    float_to_string_no_trailing_zero,
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
DAY_CSV_FILENAME = Path("summary.day.csv")
CHARGE_CSV_FILE: TextIOWrapper

LENCHECK = 1
VIN = get_vin_arg()
if VIN != "":
    MONITOR_CSV_FILENAME = Path(f"monitor.{VIN}.csv")
    LASTRUN_FILENAME = Path(f"monitor.{VIN}.lastrun")
    OUTPUT_SPREADSHEET_NAME = f"monitor.{VIN}"
    CHARGE_CSV_FILENAME = Path(f"summary.charge.{VIN}.csv")
    TRIP_CSV_FILENAME = Path("summary.trip.{VIN}.csv")
    DAY_CSV_FILENAME = Path("summary.day.{VIN}.csv")
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
config_parser.read(get_filepath("monitor.cfg"))
monitor_settings = dict(config_parser.items("monitor"))
ODO_METRIC = get(monitor_settings, "odometer_metric", "km").lower()

config_parser.read(get_filepath("summary.cfg"))
summary_settings = dict(config_parser.items("summary"))

NET_BATTERY_SIZE_KWH = to_float(summary_settings["net_battery_size_kwh"])
AVERAGE_COST_PER_KWH = to_float(summary_settings["average_cost_per_kwh"])
COST_CURRENCY = summary_settings["cost_currency"]
MIN_CONSUMPTION_DISCHARGE_KWH = to_float(
    summary_settings["min_consumption_discharge_kwh"]
)
SMALL_POSITIVE_DELTA = int(summary_settings["ignore_small_positive_delta_soc"])
SMALL_NEGATIVE_DELTA = int(summary_settings["ignore_small_negative_delta_soc"])
SHOW_ZERO_VALUES = is_true(summary_settings["show_zero_values"])

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

SHEET_ROW_A = ""
SHEET_ROW_B = ""


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
    split = split_on_comma(output)
    for i in range(len(split)):  # pylint:disable=consider-using-enumerate
        string = split[i]
        if i == 0 and string != TR.period:
            string = get_translation(TR_HELPER, string)
        elif i == 2 and split[0] == "DAY":
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
    row_a_values = split_on_comma(row_a)
    row_b_values = split_on_comma(row_b)
    len_a = len(row_a_values)
    len_b = len(row_b_values)
    if len_a != len_b:
        log(f"ERROR: sheet_append_first_rows, length A {len_a} != length B {len_b}")
        return  # nothing to do

    array = []
    for index, value in enumerate(row_a_values):
        row_a_value = value
        row_b_value = row_b_values[index]
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

    array.append({"range": "C6", "values": [[""]]})  # go to beginning of spreadsheet
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
        location_str = split[LOCATION]
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
MONITOR_CSV_CURR_SPLIT: list[str] = []
MONITOR_CSV_NEXT_SPLIT: list[str] = []
MONITOR_CSV_LINECOUNT: int = 0


def get_next_monitor_csv_line() -> str:
    """
    get_next_monitor_csv_line

    Returns empty string if EOF
    Can also be called when already EOF encountered (again empty line returned)
    Skips empty lines
    Skips header lines
    Skips lines without ,
    Does fill INPUT_CSV_READ_AHEAD_LINE (for external use)
    """
    global MONITOR_CSV_FILE_EOL, MONITOR_CSV_READ_AHEAD_LINE, MONITOR_CSV_READ_DONE_ONCE, MONITOR_CSV_CURR_SPLIT, MONITOR_CSV_NEXT_SPLIT, MONITOR_CSV_LINECOUNT  # noqa pylint:disable=global-statement

    while not MONITOR_CSV_FILE_EOL:
        if MONITOR_CSV_READ_DONE_ONCE:  # read 1 line
            line = MONITOR_CSV_READ_AHEAD_LINE
            MONITOR_CSV_CURR_SPLIT = MONITOR_CSV_NEXT_SPLIT
        else:  # read 2 lines
            MONITOR_CSV_READ_DONE_ONCE = True
            line = MONITOR_CSV_FILE.readline()
            MONITOR_CSV_CURR_SPLIT = split_on_comma(line)

        MONITOR_CSV_LINECOUNT += 1
        MONITOR_CSV_READ_AHEAD_LINE = MONITOR_CSV_FILE.readline()
        MONITOR_CSV_NEXT_SPLIT = split_on_comma(MONITOR_CSV_READ_AHEAD_LINE)
        if not line:
            MONITOR_CSV_FILE_EOL = True
            MONITOR_CSV_READ_AHEAD_LINE = line
            MONITOR_CSV_NEXT_SPLIT = []
            break  # finished

        line = line.strip()
        # only lines with content and not header line
        if line != "" and not line.startswith("datetime"):
            index = line.find(",")
            if index >= 0:
                _ = D and dbg(f"next=[{line}]")
                return line

        _ = D and dbg(f"skip=[{line}]")

    _ = D and dbg("return=[]\n")
    return ""


def get_corrected_next_monitor_csv_line() -> str:
    """get_corrected_next_monitor_csv_line"""
    while True:
        line = get_next_monitor_csv_line()
        if line == "":  # EOF
            return ""  # finished

        split = MONITOR_CSV_CURR_SPLIT
        if len(split) != 11:
            _ = D and dbg(f"#### Skipping line {MONITOR_CSV_LINECOUNT}: [{line}]")
            continue

        _ = D and dbg(str(MONITOR_CSV_LINECOUNT) + ": LINE=[" + line + "]")
        next_line = MONITOR_CSV_READ_AHEAD_LINE.strip()
        next_split = MONITOR_CSV_NEXT_SPLIT
        if len(next_split) != 11:
            _ = D and dbg(f"Next split skip: {MONITOR_CSV_LINECOUNT}: [{next_line}]")
            return line

        if split[ODO] == next_split[ODO] and split[SOC] > next_split[SOC]:
            _ = D and dbg(f"#### Same odo and SOC smaller:\n{line}\n{next_line}\n")
            date_curr = datetime.strptime(split[DT][:19], "%Y-%m-%d %H:%M:%S")
            date_next = datetime.strptime(next_split[DT][:19], "%Y-%m-%d %H:%M:%S")
            delta_min = round((date_next - date_curr).total_seconds() / 60)
            _ = D and dbg(f"delta minutes: {delta_min}")
            if delta_min < 20:
                # just use the next line
                continue

        return line


def write_charge_csv(line: str) -> None:
    """write charge csv"""
    _ = D and dbg(f"{CHARGE_CSV_FILENAME}:[{line}]")
    CHARGE_CSV_FILE.write(line)
    CHARGE_CSV_FILE.write("\n")


def write_day_csv(line: str) -> None:
    """write day csv"""
    _ = D and dbg(f"{DAY_CSV_FILENAME}:[{line}]")
    DAY_CSV_FILE.write(line)
    DAY_CSV_FILE.write("\n")


def write_trip_csv(line: str) -> None:
    """write trip csv"""
    _ = D and dbg(f"{TRIP_CSV_FILENAME}:[{line}]")
    TRIP_CSV_FILE.write(line)
    TRIP_CSV_FILE.write("\n")


def show_zero_values_float(value: float) -> str:
    """show_zero_values_float"""
    string = ""
    if SHOW_ZERO_VALUES or value != 0.0:
        string = f"{value:.1f}"
    return string


def show_zero_values_float_no_trailing_zero(value: float) -> str:
    """show_zero_values_float_no_trailing_zero"""
    string = ""
    if SHOW_ZERO_VALUES or value != 0.0:
        string = float_to_string_no_trailing_zero(value)
    return string


def print_summary(
    prefix: str, current: Totals, values: Totals, split: list[str], factor: float
) -> None:
    """print_summary"""
    global SHEET_ROW_A, SHEET_ROW_B  # pylint:disable=global-statement
    if D:
        dbg("print_summary")
        dbg("PREV  : " + str(values))
        dbg("CURR  : " + str(current))
        dbg("VALUES: " + str(values))
    odo = current.odo
    if odo == 0.0:
        return  # bad line

    delta_odo = round(odo - values.odo, 1) * factor
    odo_str = show_zero_values_float(odo)
    t_charged_perc = max(0.0, values.charged_perc * factor)
    t_discharged_perc = min(0.0, values.discharged_perc * factor)
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
        km_mi_per_kwh_str = "0.0"
        kwh_per_km_mi_str = "0.0"
        cost_str = "0.00"
    if t_discharged_perc < 0:
        if TRIP or discharged_kwh < -MIN_CONSUMPTION_DISCHARGE_KWH:  # skip inaccurate
            cost = discharged_kwh * -AVERAGE_COST_PER_KWH
            cost_str = f"{cost:.2f}"
            km_mi_per_kwh = safe_divide(delta_odo, -discharged_kwh)
            km_mi_per_kwh_str = f"{km_mi_per_kwh:.1f}"
            if km_mi_per_kwh > 0.0:
                kwh_per_km_mi = safe_divide(100, km_mi_per_kwh)
                kwh_per_km_mi_str = f"{kwh_per_km_mi:.1f}"
    else:
        # do not show positive discharges
        t_discharged_perc = 0

    delta_odo_str = show_zero_values_float(delta_odo)
    charged_kwh_str = show_zero_values_float(charged_kwh)
    discharged_kwh_str = show_zero_values_float(discharged_kwh)
    t_charges_str = show_zero_values_float_no_trailing_zero(t_charges)
    t_trips_str = show_zero_values_float_no_trailing_zero(t_trips)
    location_str = get_address(split)

    ev_range = -1
    if len(split) > EV_RANGE:
        ev_range = to_int(split[EV_RANGE])

    if DAY and prefix.startswith("DAY "):
        splitted = split_on_comma(prefix)
        if len(splitted) > 2:
            date = splitted[1]
            write_day_csv(
                f"{date}, {odo:.1f}, {float_to_string_no_trailing_zero(delta_odo)}, {float_to_string_no_trailing_zero(discharged_kwh)}, {float_to_string_no_trailing_zero(charged_kwh)}"  # noqa
            )
            if charged_kwh > 3.0:
                write_charge_csv(
                    f"{date}, {odo:.1f}, {float_to_string_no_trailing_zero(charged_kwh)}, {t_soc_charged}"  # noqa
                )

    if TRIP and prefix.startswith("TRIP "):
        splitted = split_on_comma(prefix)
        if len(splitted) > 2:
            date = splitted[1]
            time_str = splitted[2]
            write_trip_csv(
                f"{date} {time_str}, {odo:.1f}, {float_to_string_no_trailing_zero(delta_odo)}, {float_to_string_no_trailing_zero(discharged_kwh)}, {float_to_string_no_trailing_zero(charged_kwh)}"  # noqa
            )

    if SHEETUPDATE and prefix.startswith("SHEET "):
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
        SHEET_ROW_A = f"{TR.last_run},{TR.vehicle_upd},{TR.gps_update},{TR.last_entry},{TR.last_address},{TR.odometer} {ODO_METRIC},{TR.driven} {ODO_METRIC},+kWh,-kWh,{ODO_METRIC}/kWh,kWh/100{ODO_METRIC},{TR.cost} {COST_CURRENCY},{TR.soc_perc},{TR.avg} {TR.soc_perc},{TR.min} {TR.soc_perc},{TR.max} {TR.soc_perc},{TR.volt12_perc},{TR.avg} {TR.volt12_perc},{TR.min} {TR.volt12_perc},{TR.max} {TR.volt12_perc},{TR.charges},{TR.trips},{TR.ev_range}"  # noqa
        SHEET_ROW_B = f"{last_run_dt},{last_upd_dt},{location_last_upd_dt},{last_line},{location_str},{odo:.1f},{float_to_string_no_trailing_zero(delta_odo)},{float_to_string_no_trailing_zero(charged_kwh)},{float_to_string_no_trailing_zero(discharged_kwh)},{km_mi_per_kwh_str},{kwh_per_km_mi_str},{cost_str},{t_soc_cur},{t_soc_avg},{t_soc_min},{t_soc_max},{t_volt12_cur},{t_volt12_avg},{t_volt12_min},{t_volt12_max},{t_charges},{t_trips},{ev_range}"  # noqa
    else:
        output = f"{prefix},{odo_str},{delta_odo_str},{charged_kwh_str},{discharged_kwh_str},{km_mi_per_kwh_str},{kwh_per_km_mi_str},{cost_str},{t_soc_cur},{t_soc_avg},{t_soc_min},{t_soc_max},{t_volt12_cur},{t_volt12_avg},{t_volt12_min},{t_volt12_max},{t_charges_str},{t_trips_str},{ev_range},{location_str}"  # noqa
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
        elapsed = current_day - t_day.current_day
        DAY_COUNTER += elapsed.days
        if DAY:
            day_info = t_day.current_day.strftime("%a")
            print_summary(
                f"DAY     , {day_str}, {day_info}",
                current_day_values,
                t_day,
                split,
                1.0,
            )
        t_day = deepcopy(current_day_values)
        t_trip = deepcopy(current_day_values)

    if WEEK and (not same_week(current_day, t_week.current_day) or last):
        weeknr = t_week.current_day.strftime("%W")
        print_summary(
            f"WEEK    , {day_str}, WK {weeknr}",
            current_day_values,
            t_week,
            split,
            1.0,
        )
        t_week = deepcopy(current_day_values)

    if MONTH and (not same_month(current_day, t_month.current_day) or last):
        month_info = t_month.current_day.strftime("%b")
        print_summary(
            f"MONTH   , {day_str}, {month_info}",
            current_day_values,
            t_month,
            split,
            1.0,
        )
        t_month = deepcopy(current_day_values)
    if YEAR and (not same_year(current_day, t_year.current_day) or last):
        year = t_year.current_day.strftime("%Y")
        print_summary(
            f"YEAR    , {day_str}, {year}",
            current_day_values,
            t_year,
            split,
            1.0,
        )
        trips = t_year.trips
        print_summary(
            f"TRIPAVG , {day_str}, {trips}t ",
            current_day_values,
            t_year,
            split,
            safe_divide(1, trips),
        )
        print_summary(
            f"DAYAVG  , {day_str}, {DAY_COUNTER}d ",
            current_day_values,
            t_year,
            split,
            safe_divide(1, DAY_COUNTER),
        )
        print_summary(
            f"WEEKAVG , {day_str}, {DAY_COUNTER}d ",
            current_day_values,
            t_year,
            split,
            safe_divide(7, DAY_COUNTER),
        )
        print_summary(
            f"MONTHAVG, {day_str}, {DAY_COUNTER}d ",
            current_day_values,
            t_year,
            split,
            safe_divide(365 / 12, DAY_COUNTER),
        )
        print_summary(
            f"YEARLY  , {day_str}, {DAY_COUNTER}d ",
            current_day_values,
            t_year,
            split,
            safe_divide(365, DAY_COUNTER),
        )
        if SHEETUPDATE and last:
            day_info = current_day.strftime("%a %H:%M")
            print_summary(
                f"SHEET {day_str} {day_info} {DAY_COUNTER}d",
                current_day_values,
                t_year,
                split,
                1.0,
            )

        DAY_COUNTER = 0
        t_year = deepcopy(current_day_values)

    totals = GrandTotals(t_day, t_week, t_month, t_year, t_trip)
    return totals


def keep_track_of_totals(
    values: Totals, split: list[str], prev_split: list[str]
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

    delta_odo = max(0.0, odo - prev_odo)
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
        _ = D and dbg(
            f"DELTA_ODO: {float_to_string_no_trailing_zero(delta_odo)} {t_trips}"
        )

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
            deepcopy(current_day_values),
            deepcopy(current_day_values),
            deepcopy(current_day_values),
            deepcopy(current_day_values),
            deepcopy(current_day_values),
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
            t_trip = keep_track_of_totals(t_trip, split, prev_split)
            if t_trip.trips > 0:
                day_trip_str = current_day.strftime("%Y-%m-%d")
                day_info = current_day.strftime("%H:%M")
                print_summary(
                    f"TRIP    , {day_trip_str}, {day_info}",
                    current_day_values,
                    t_trip,
                    split,
                    1.0,
                )
                t_trip = deepcopy(current_day_values)

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

    prev_line = ""
    prev_split = ()
    totals: GrandTotals = GrandTotals(None, None, None, None, None)

    print_header_and_update_queue()

    while True:
        line = get_corrected_next_monitor_csv_line()
        if line == "":  # EOF
            break  # finish loop
        _ = D and dbg(str(MONITOR_CSV_LINECOUNT) + ": LINE=[" + line + "]")
        split = MONITOR_CSV_CURR_SPLIT
        if totals.day and not same_day(
            parser.parse(split[DT]), parser.parse(prev_split[DT])
        ):
            # handle end of day previous day
            eod_line = line[0:11] + "00:00:00" + prev_line[19:]
            if D:
                dbg(f"prev_line: {prev_line}\n eod_line: {eod_line}")
            last_split = split_on_comma(eod_line)
            totals = handle_line(
                MONITOR_CSV_LINECOUNT, last_split, prev_split, totals, False
            )
        totals = handle_line(MONITOR_CSV_LINECOUNT, split, prev_split, totals, False)

        prev_line = line
        prev_split = split

    # also compute last last day/week/month
    _ = D and dbg("Handling last values")
    # handle end of day for last value
    eod_line = prev_line[0:11] + "23:59:59" + prev_line[19:]
    last_split = split_on_comma(eod_line)
    _ = D and dbg(f"prev_line: {prev_line}\n eod_line: {eod_line}")
    totals = handle_line(MONITOR_CSV_LINECOUNT, last_split, prev_split, totals, False)
    # and show summaries
    handle_line(MONITOR_CSV_LINECOUNT, last_split, last_split, totals, True)
    print_header_and_update_queue()


# always rewrite charge file, because input might be changed
CHARGE_CSV_FILE = CHARGE_CSV_FILENAME.open("w", encoding="utf-8")
write_charge_csv("date, odometer, +kWh, end charged SOC%")


# always rewrite day and tripfile, because input might be changed
DAY_CSV_FILE = DAY_CSV_FILENAME.open("w", encoding="utf-8")
write_day_csv("date, odometer, distance, -kWh, +kWh")

TRIP_CSV_FILE = TRIP_CSV_FILENAME.open("w", encoding="utf-8")
write_trip_csv("date, odometer, distance, -kWh, +kWh")

summary()  # do the work
MONITOR_CSV_FILE.close()
CHARGE_CSV_FILE.close()
DAY_CSV_FILE.close()
TRIP_CSV_FILE.close()

if SHEETUPDATE:
    RETRIES = 2
    while RETRIES > 0:
        try:
            gc = gspread.service_account()
            spreadsheet = gc.open(OUTPUT_SPREADSHEET_NAME)
            SHEET = spreadsheet.sheet1
            SHEET.clear()
            sheet_append_first_rows(SHEET_ROW_A, SHEET_ROW_B)
            print_output_queue()
            RETRIES = 0
        except Exception as ex:  # pylint: disable=broad-except
            log("Exception: " + str(ex))
            traceback.print_exc()
            RETRIES = sleep(RETRIES)
