# == tripmaker.py Author: Zuinige Rijder ==============================
"""
Simple Python3 script to generate a trip report
https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor

Following information per row:
- Date
- Index (trip of the day)
- Trip (with start and end time)
- Odometer start -> from summary.trip.csv
- Odometer end
- Distance
- Start location -> from summary.trip.csv
- End location  -> from summary.trip.csv
- Location Time -> from summary.trip.csv

The trip information is determined from monitor.tripinfo.csv,
which has following fields (*=used):
- Date*, Start time*, Drive time*, Idle time, Distance*, Avg speed, Max speed

The odometer is NOT available in monitor.tripinfo.csv and monitor.dailystats.csv,
this will be retrieved from (filled by running summary.py):
- summary.trip.csv
  date*, odometer*, distance, -kWh, +kWh, SOC%, 12V%, address*
"""

from collections import deque
from datetime import datetime, timedelta
from io import TextIOWrapper
from os import path
from pathlib import Path
import logging
import sys
import traceback
from typing import Final
import typing

try:  # make gspread optional
    import gspread

    HAS_GSPREAD = True
except ImportError:
    HAS_GSPREAD = False

from monitor_utils import (
    arg_has,
    dbg,
    die,
    get_csv_path,
    get_translation,
    get_vin_arg,
    read_translations,
    set_dbg,
    sleep_a_minute,
    split_on_comma,
    split_output_to_sheet_list,
    to_float,
    to_int,
)

SCRIPT_DIRNAME: Final = path.abspath(path.dirname(__file__))
logging.config.fileConfig(f"{SCRIPT_DIRNAME}/logging_config.ini")
D: Final = arg_has("debug")
if D:
    set_dbg()

KEYWORD_LIST: Final = ["help", "sheetupdate", "debug"]
keyword_error = False
for kindex in range(1, len(sys.argv)):
    if sys.argv[kindex].lower() not in KEYWORD_LIST:
        arg = sys.argv[kindex]
        if "vin=" in arg.lower():
            _ = D and dbg("vin parameter: " + arg)
        else:
            print("Unknown keyword: " + arg)
            keyword_error = True

if keyword_error or arg_has("help"):
    die("Usage: python tripmaker.py [sheetupdate] [vin=VIN]")

VIN: Final[str] = get_vin_arg()

SHEETUPDATE: Final = arg_has("sheetupdate")
SHEET: typing.Any = None  # pylint: disable=invalid-name
OUTPUT_SPREADSHEET_NAME: Final[str] = (
    f"monitor.tripmaker.{VIN}" if VIN else "monitor.tripmaker"
)

# Initializing a queue for about 999 lines
MAX_QUEUE_LEN: Final = 999
PRINTED_OUTPUT_QUEUE: Final[deque[str]] = deque(maxlen=MAX_QUEUE_LEN)

TRIPINFO_CSV_FILE: Final[Path] = get_csv_path("monitor.tripinfo.csv", VIN)
SUMMARY_TRIP_CSV_FILE: Final[Path] = get_csv_path("summary.trip.csv", VIN)
TRIPMAKER_CSV_FILE: Final[Path] = get_csv_path("tripmaker.csv", VIN)

TRIPINFO_CSV_FILE_LINECOUNT = 0
SUMMARY_TRIP_CSV_FILE_LINECOUNT = 0
CURRENT_INDEX = 0
CURRENT_DATE = ""

TR_HELPER: Final[dict[str, str]] = read_translations()
COLUMN_WIDTHS: Final = [11, 6, 12, 18, 18, 12, 100, 100, 20]
HEADER = ""

SUMMARY_TRIP_CSV_INPUTFILE_EOL: bool = False
SUMMARY_TRIP_CSV_INPUTFILE_READ_AHEAD_LINE: str = ""
SUMMARY_TRIP_CSV_INPUTFILE_READ_DONE_ONCE: bool = False
SUMMARY_TRIP_CSV_INPUTFILE_CURR_SPLIT: list[str] = []
SUMMARY_TRIP_CSV_INPUTFILE_NEXT_SPLIT: list[str] = []
SUMMARY_TRIP_CSV_INPUTFILE_LINECOUNT: int = 0
PREV_END_TIME = ""
CURRENT_END_TIME = ""
PREV_LOCATION = ""
CURRENT_LOCATION = ""
PREV_ODOMETER = 0.0
CURRENT_ODOMETER = 0.0

if not TRIPINFO_CSV_FILE.is_file():
    die(f"{TRIPINFO_CSV_FILE} does not exist")
if not SUMMARY_TRIP_CSV_FILE.is_file():
    die(f"{SUMMARY_TRIP_CSV_FILE} does not exist")

TRIPINFO_CSV_INPUTFILE: TextIOWrapper = TRIPINFO_CSV_FILE.open("r", encoding="utf-8")
SUMMARY_TRIP_CSV_INPUTFILE: TextIOWrapper = SUMMARY_TRIP_CSV_FILE.open(
    "r", encoding="utf-8"
)
TRIPMAKER_CSV_OUTFILE: TextIOWrapper = TRIPMAKER_CSV_FILE.open("w", encoding="utf-8")


def update_width(text: str, index_column_widths: int) -> None:
    """update width"""
    if len(text) + 1 > COLUMN_WIDTHS[index_column_widths]:
        COLUMN_WIDTHS[index_column_widths] = len(text) + 1


def get_translation_and_update_width(text: str, index_column_widths: int) -> str:
    """get_translation_and_update_width"""
    translation = get_translation(TR_HELPER, text)
    update_width(translation, index_column_widths)
    return translation


def get_next_summary_trip_csv_line() -> str:
    """
    get_next_monitor_csv_line

    Returns empty string if EOF
    Can also be called when already EOF encountered (again empty line returned)
    Skips empty lines
    Skips header lines
    Skips lines without ,
    Does fill INPUT_CSV_READ_AHEAD_LINE (for external use)
    """
    global SUMMARY_TRIP_CSV_INPUTFILE_EOL, SUMMARY_TRIP_CSV_INPUTFILE_READ_AHEAD_LINE, SUMMARY_TRIP_CSV_INPUTFILE_READ_DONE_ONCE, SUMMARY_TRIP_CSV_INPUTFILE_CURR_SPLIT, SUMMARY_TRIP_CSV_INPUTFILE_NEXT_SPLIT, SUMMARY_TRIP_CSV_INPUTFILE_LINECOUNT, PREV_END_TIME, CURRENT_END_TIME, CURRENT_LOCATION, PREV_ODOMETER, CURRENT_ODOMETER  # noqa pylint:disable=global-statement

    while not SUMMARY_TRIP_CSV_INPUTFILE_EOL:
        if SUMMARY_TRIP_CSV_INPUTFILE_READ_DONE_ONCE:  # read 1 line
            line = SUMMARY_TRIP_CSV_INPUTFILE_READ_AHEAD_LINE
            SUMMARY_TRIP_CSV_INPUTFILE_CURR_SPLIT = (
                SUMMARY_TRIP_CSV_INPUTFILE_NEXT_SPLIT
            )
            PREV_END_TIME = CURRENT_END_TIME
            PREV_ODOMETER = CURRENT_ODOMETER
        else:  # read 2 lines
            SUMMARY_TRIP_CSV_INPUTFILE_READ_DONE_ONCE = True
            line = SUMMARY_TRIP_CSV_INPUTFILE.readline()
            SUMMARY_TRIP_CSV_INPUTFILE_CURR_SPLIT = split_on_comma(line)

        SUMMARY_TRIP_CSV_INPUTFILE_LINECOUNT += 1
        SUMMARY_TRIP_CSV_INPUTFILE_READ_AHEAD_LINE = (
            SUMMARY_TRIP_CSV_INPUTFILE.readline()
        )
        SUMMARY_TRIP_CSV_INPUTFILE_NEXT_SPLIT = split_on_comma(
            SUMMARY_TRIP_CSV_INPUTFILE_READ_AHEAD_LINE
        )
        if not line:
            SUMMARY_TRIP_CSV_INPUTFILE_EOL = True
            SUMMARY_TRIP_CSV_INPUTFILE_READ_AHEAD_LINE = line
            SUMMARY_TRIP_CSV_INPUTFILE_NEXT_SPLIT = []
            break  # finished

        line = line.strip()
        # only lines with content and not header line
        if line != "" and not line.startswith("date"):
            index = line.find(",")
            if index >= 0:
                _ = D and dbg(f"next=[{line}]")
                CURRENT_END_TIME = SUMMARY_TRIP_CSV_INPUTFILE_CURR_SPLIT[0]
                CURRENT_LOCATION = SUMMARY_TRIP_CSV_INPUTFILE_CURR_SPLIT[7]
                CURRENT_ODOMETER = to_float(SUMMARY_TRIP_CSV_INPUTFILE_CURR_SPLIT[1])
                return line

        _ = D and dbg(f"skip=[{line}]")

    _ = D and dbg("return=[]\n")
    return ""


def print_output_queue() -> None:
    """print output queue"""
    array: list[dict] = []

    SHEET.batch_clear(["A:I"])

    row = 1
    values = split_output_to_sheet_list(HEADER)
    array.append({"range": f"A{row}:I{row}", "values": values})
    for queue_output in PRINTED_OUTPUT_QUEUE:
        row += 1
        _ = D and dbg(f"write row: {row} {queue_output}")
        values = split_output_to_sheet_list(queue_output)
        array.append({"range": f"A{row}:I{row}", "values": values})

    if len(array) > 0:
        SHEET.batch_update(array)


def print_output(output: str, sheetupdate: bool = True) -> None:
    """print output"""
    if SHEETUPDATE and sheetupdate:
        PRINTED_OUTPUT_QUEUE.append(output)

    split = split_on_comma(output)
    for i in range(len(split)):  # pylint:disable=consider-using-enumerate
        if i > 0:  # not first
            TRIPMAKER_CSV_OUTFILE.write(",")
        TRIPMAKER_CSV_OUTFILE.write(split[i])

        text = split[i].rjust(COLUMN_WIDTHS[i])
        print(text, end="")

    TRIPMAKER_CSV_OUTFILE.write("\n")
    print("")


def get_next_monitor_tripinfo() -> str:
    """get_next_monitor_tripinfo"""
    global TRIPINFO_CSV_FILE_LINECOUNT  # noqa pylint:disable=global-statement

    for line in TRIPINFO_CSV_INPUTFILE:
        line = line.strip()
        TRIPINFO_CSV_FILE_LINECOUNT += 1
        _ = D and dbg(str(TRIPINFO_CSV_FILE_LINECOUNT) + ": LINE=[" + line + "]")
        index = line.find(",")
        if index <= 0 or line.startswith("Date"):
            _ = D and dbg(f"Skipping line {TRIPINFO_CSV_FILE_LINECOUNT}:\n{line}")
        else:
            return line
    return ""


def handle_monitor_tripinfo(line: str):
    """handle_monitor_tripinfo"""
    global CURRENT_INDEX, CURRENT_DATE, PREV_LOCATION  # noqa pylint:disable=global-statement

    split = split_on_comma(line)
    date_str = split[0]
    start_time = split[1]
    drive_time = to_int(split[2])
    distance = to_float(split[4])

    if CURRENT_INDEX == 0:  # first time called
        get_next_summary_trip_csv_line()

    if CURRENT_DATE != date_str:
        CURRENT_INDEX = 1
    else:
        CURRENT_INDEX += 1

    date = datetime.strptime(date_str, "%Y%m%d")

    trip_time_start_str = start_time[0:2] + ":" + start_time[2:4]
    trip_time_start = datetime.strptime(trip_time_start_str, "%H:%M")
    trip_time_end = trip_time_start + timedelta(minutes=drive_time)
    trip_time_end_str = trip_time_end.strftime("-%H:%M")
    trip_time_str = trip_time_start_str + trip_time_end_str

    # find the last summary.tripinfo.csv line just before monitor.tripinfo.csv date
    trip_date_time_start = datetime.combine(date.date(), trip_time_start.time())
    trip_date_time_end_exact = trip_date_time_start + timedelta(minutes=drive_time)
    trip_date_time_end = trip_date_time_end_exact + timedelta(minutes=10)

    current_location = PREV_LOCATION
    current_odometer = CURRENT_ODOMETER
    summary_trip_fields: Final = 8
    while len(SUMMARY_TRIP_CSV_INPUTFILE_CURR_SPLIT) >= summary_trip_fields:
        if len(SUMMARY_TRIP_CSV_INPUTFILE_NEXT_SPLIT) >= summary_trip_fields:
            # print(f"{SUMMARY_TRIP_CSV_INPUTFILE_NEXT_SPLIT}")
            summary_trip_date_time = datetime.strptime(
                SUMMARY_TRIP_CSV_INPUTFILE_NEXT_SPLIT[0], "%Y-%m-%d %H:%M"
            )
            if summary_trip_date_time < trip_date_time_start:
                # next line still before start time
                line = get_next_summary_trip_csv_line()
            else:
                summary_trip_current_date_time = datetime.strptime(
                    SUMMARY_TRIP_CSV_INPUTFILE_CURR_SPLIT[0], "%Y-%m-%d %H:%M"
                )
                if summary_trip_current_date_time < trip_date_time_start:
                    # print(f"PREV_LOCATION = CURRENT_LOCATION: {CURRENT_LOCATION}")
                    PREV_LOCATION = CURRENT_LOCATION
                if summary_trip_date_time <= trip_date_time_end:
                    # next line still in time range
                    line = get_next_summary_trip_csv_line()
                else:
                    break  # out of while loop
        else:
            break  # out of while loop

    if len(SUMMARY_TRIP_CSV_INPUTFILE_CURR_SPLIT) >= summary_trip_fields:
        summary_trip_date_time = datetime.strptime(
            SUMMARY_TRIP_CSV_INPUTFILE_CURR_SPLIT[0], "%Y-%m-%d %H:%M"
        )
        if summary_trip_date_time < trip_date_time_start:
            PREV_LOCATION = CURRENT_LOCATION

        if trip_date_time_start <= summary_trip_date_time <= trip_date_time_end:
            current_location = CURRENT_LOCATION
            current_odometer = CURRENT_ODOMETER

    print_output(
        f"{date.date()}, {CURRENT_INDEX}, {trip_time_str}, {current_odometer-distance:.1f}, {current_odometer:.1f}, {distance:.1f}, {PREV_LOCATION}, {current_location}, {CURRENT_END_TIME}"  # noqa
    )
    CURRENT_DATE = date_str
    PREV_LOCATION = CURRENT_LOCATION
    return


def fill_translated_header():
    """fill_translated_header"""
    global HEADER  # pylint:disable=global-statement
    header = ""
    split = split_on_comma(
        "Date, Index, Trip, Odometer start, Odometer end, Distance, Start address, End address, Time"  # noqa
    )
    index = 0
    for item in split:
        if len(header) > 0:
            header += ", "
        translation = get_translation_and_update_width(item.strip(), index)
        header += translation
    HEADER = header


def tripmaker():
    """tripmaker"""
    fill_translated_header()
    print_output(HEADER, False)

    finished = False
    while not finished:
        line = get_next_monitor_tripinfo()
        if line == "":
            finished = True
        else:
            _ = D and dbg(f"line: {line}")
            handle_monitor_tripinfo(line)


# Main program
RETRIES = -1
if SHEETUPDATE:
    if not HAS_GSPREAD:
        die(
            "Google spreadsheet support not available, please install gspread, e.g."
            'pip install "gspread>=5.6.2"'
        )

    RETRIES = 2
    while RETRIES > 0:
        try:
            gc = gspread.service_account()
            spreadsheet = gc.open(OUTPUT_SPREADSHEET_NAME)
            SHEET = spreadsheet.sheet1  # pylint: disable=invalid-name
            RETRIES = -1
        except Exception as ex:  # pylint: disable=broad-except
            logging.error("Exception: " + str(ex))  # pylint:disable=logging-not-lazy
            traceback.print_exc()
            RETRIES = sleep_a_minute(RETRIES)

if RETRIES != -1:
    exit(-1)

tripmaker()

RETRIES = -1
if SHEETUPDATE:
    RETRIES = 2
    while RETRIES > 0:
        try:
            print_output_queue()
            RETRIES = -1
        except Exception as ex:  # pylint: disable=broad-except
            logging.error("Exception: " + str(ex))  # pylint:disable=logging-not-lazy
            traceback.print_exc()
            RETRIES = sleep_a_minute(RETRIES)

if RETRIES == -1:
    sys.exit(0)
sys.exit(-1)
