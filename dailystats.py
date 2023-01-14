# == dailystats.py Author: Zuinige Rijder =====================================
"""
Simple Python3 script to make a dailystats overview
"""
import sys
import os
import traceback
import time
from datetime import datetime
from pathlib import Path
from collections import deque
import gspread

# Initializing a queue for about 30 days
MAX_QUEUE_LEN = 122
PRINTED_OUTPUT_QUEUE = deque(maxlen=MAX_QUEUE_LEN)


def log(msg):
    """log a message prefixed with a date/time format yyyymmdd hh:mm:ss"""
    print(datetime.now().strftime("%Y%m%d %H:%M:%S") + ": " + msg)


def arg_has(string):
    """arguments has string"""
    for i in range(1, len(sys.argv)):
        if sys.argv[i].lower() == string:
            return True
    return False


D = arg_has("debug")


def dbg(line):
    """print line if debugging"""
    if D:
        print(line)
    return D  # just to make a lazy evaluation expression possible


def get_vin_arg():
    """get vin argument"""
    for i in range(1, len(sys.argv)):
        if "vin=" in sys.argv[i].lower():
            vin = sys.argv[i]
            vin = vin.replace("vin=", "")
            vin = vin.replace("VIN=", "")
            _ = D and dbg(f"VIN = {vin}")
            return vin

    return ""


def safe_divide(numerator, denumerator):
    """safe_divide"""
    if denumerator == 0.0:
        return 1.0
    return numerator / denumerator


def to_int(string):
    """convert to int"""
    if "None" in string:
        return -1
    split = string.split(".")  # get rid of decimal part
    return int(split[0].strip())


def to_float(string):
    """convert to float"""
    if "None" in string:
        return 0.0
    return float(string.strip())


KEYWORD_LIST = ["help", "sheetupdate", "debug"]
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
    print("Usage: python dailystats.py [sheetupdate] [vin=VIN]")
    exit()

SHEETUPDATE = arg_has("sheetupdate")
OUTPUT_SPREADSHEET_NAME = "monitor.dailystats"

DAILYSTATS_CSV_FILE = Path("monitor.dailystats.csv")
LASTRUN_FILE = Path("monitor.lastrun")
LENCHECK = 1
VIN = get_vin_arg()
if VIN != "":
    DAILYSTATS_CSV_FILE = Path(f"monitor.dailystats.{VIN}.csv")
    LASTRUN_FILE = Path(f"monitor.{VIN}.lastrun")
    OUTPUT_SPREADSHEET_NAME = f"monitor.dailystats.{VIN}"
    LENCHECK = 2
_ = D and dbg(f"DAILYSTATS_CSV_FILE: {DAILYSTATS_CSV_FILE.name}")


# indexes to splitted monitor.dailystats.csv items
DATE = 0
DISTANCE = 1
DISTANCE_UNIT = 2
CONSUMED = 3
REGENERATED = 4
ENGINE = 5
CLIMATE = 6
ELECTRONICS = 7
BATTERY_CARE = 8

TOTAL_DAYS = 0
TOTAL_UNIT = "km"
TOTAL_DISTANCE = 0
TOTAL_CONSUMED = 0
TOTAL_REGENERATED = 0
TOTAL_ENGINE = 0
TOTAL_CLIMATE = 0
TOTAL_ELECTRONICS = 0
TOTAL_BATTERY_CARE = 0


def float_to_string(input_value):
    """float to string without trailing zero"""
    return (f"{input_value:9.1f}").rstrip("0").rstrip(".")


def get_last_line(filename):
    """get last line of filename"""
    last_line = ""
    filename_file = Path(filename)
    if filename_file.is_file():
        with open(filename, "rb") as file:
            try:
                file.seek(-2, os.SEEK_END)
                while file.read(1) != b"\n":
                    file.seek(-2, os.SEEK_CUR)
            except OSError:
                file.seek(0)
            last_line = file.readline().decode()
            _ = D and dbg(f"{filename} last_line: [{last_line}]")
    return last_line


def get_last_date(filename):
    """get last date of filename"""
    last_date = "20000101"  # millenium
    last_line = get_last_line(filename)
    if last_line.startswith("20"):  # year starts with 20
        last_date = last_line.split(",")[0].strip()
    _ = D and dbg(f"{filename} last_date: [{last_date}]")
    return last_date


def read_reverse_order(file_name):
    """read in reverse order"""
    # Open file for reading in binary mode
    with open(file_name, "rb") as read_obj:
        # Move the cursor to the end of the file
        read_obj.seek(0, os.SEEK_END)
        # Get the current position of pointer i.e eof
        pointer_location = read_obj.tell()
        # Create a buffer to keep the last read line
        buffer = bytearray()
        # Loop till pointer reaches the top of the file
        while pointer_location >= 0:
            # Move the file pointer to the location pointed by pointer_location
            read_obj.seek(pointer_location)
            # Shift pointer location by -1
            pointer_location = pointer_location - 1
            # read that byte / character
            new_byte = read_obj.read(1)
            # If the read byte is newline character then one line is read
            if new_byte == b"\n":
                # Fetch the line from buffer and yield it
                yield buffer.decode()[::-1]
                # Reinitialize the byte array to save next line
                buffer = bytearray()
            else:
                # If last read character is not eol then add it in buffer
                buffer.extend(new_byte)
        # If there is still data in buffer, then it is first line.
        if len(buffer) > 0:
            # Yield the first line too
            yield buffer.decode()[::-1]


def split_output_to_sheet_list(text):
    """split output to sheet list"""
    result = [x.strip() for x in text.split(",") if x != ""]
    return [result]


def increment_totals(line):
    """handle line"""
    _ = D and dbg(f"handle_line: {line}")
    global TOTAL_DAYS, TOTAL_UNIT, TOTAL_DISTANCE, TOTAL_CONSUMED, TOTAL_REGENERATED, TOTAL_ENGINE, TOTAL_CLIMATE, TOTAL_ELECTRONICS, TOTAL_BATTERY_CARE  # noqa pylint:disable=line-too-long,disable=global-statement
    split = line.split(",")
    # date = split[DATE].strip()
    distance = to_int(split[DISTANCE])
    unit = split[DISTANCE_UNIT].strip()
    consumed = to_int(split[CONSUMED])
    regenerated = to_int(split[REGENERATED])
    engine = to_int(split[ENGINE])
    climate = to_int(split[CLIMATE])
    electronics = to_int(split[ELECTRONICS])
    battery_care = to_int(split[BATTERY_CARE])

    TOTAL_DAYS += 1
    TOTAL_UNIT = unit
    TOTAL_DISTANCE += distance
    TOTAL_CONSUMED += consumed
    TOTAL_REGENERATED += regenerated
    TOTAL_ENGINE += engine
    TOTAL_CLIMATE += climate
    TOTAL_ELECTRONICS += electronics
    TOTAL_BATTERY_CARE += battery_care


COLUMN_WIDTHS = [11, 10, 15, 10, 10, 10, 11]


def print_output(output):
    """print output"""
    split = output.split(",")
    for i in range(len(split)):  # pylint:disable=consider-using-enumerate
        text = split[i].center(COLUMN_WIDTHS[i])
        print(text, end="")
    print("")

    if SHEETUPDATE and len(PRINTED_OUTPUT_QUEUE) < MAX_QUEUE_LEN:
        PRINTED_OUTPUT_QUEUE.append(output)


def print_stats(
    date,
    distance,
    consumed,
    regenerated,
    engine,
    climate,
    electronics,
    batterycare,
):
    """print stats"""
    regenerated_perc = safe_divide(regenerated * 100, consumed)
    engine_perc = safe_divide(engine * 100, consumed)
    climate_perc = safe_divide(climate * 100, consumed)
    electronics_perc = safe_divide(electronics * 100, consumed)
    battery_care_perc = safe_divide(batterycare * 100, consumed)
    km_mi_per_kwh = safe_divide(distance, consumed / 1000)
    kwh_per_km_mi = safe_divide(100, km_mi_per_kwh)

    consumed_kwh = consumed / 1000
    regenerated_kwh = regenerated / 1000
    engine_kwh = engine / 1000
    climate_kwh = climate / 1000
    electronics_kwh = electronics / 1000
    battery_care_kwh = batterycare / 1000

    if date == "Totals":
        lastrun = datetime.now().strftime("%Y-%m-%d %H:%M %a")
        print_output(f"Last run,{lastrun},,,,,")
        print_output(",,,,,,")  # empty line/row

    print_output(
        f"{date},Regen,Consumption,Engine,Climate,Electr.,BatteryCare"
    )
    print_output(
        f"{consumed_kwh:.1f}kWh,{regenerated_kwh:.1f}kWh,{km_mi_per_kwh:.1f}{TOTAL_UNIT}/kWh,{engine_kwh:.1f}kWh,{climate_kwh:.1f}kWh,{electronics_kwh:.1f}kWh,{battery_care_kwh:.1f}kWh"  # noqa pylint:disable=line-too-long
    )
    print_output(
        f"{distance}{TOTAL_UNIT},{regenerated_perc:.1f}%,{kwh_per_km_mi:.1f}kWh/100{TOTAL_UNIT},{engine_perc:.0f}%,{climate_perc:.1f}%,{electronics_perc:.1f}%,{battery_care_perc:.1f}%"  # noqa pylint:disable=line-too-long
    )
    print_output(",,,,,,")  # empty line/row


def summary(today_daily_stats_line):
    """summary of monitor.dailystats.csv file"""
    if today_daily_stats_line != "":
        increment_totals(today_daily_stats_line)
    with DAILYSTATS_CSV_FILE.open("r", encoding="utf-8") as inputfile:
        linecount = 0
        for line in inputfile:
            line = line.strip()
            linecount += 1
            _ = D and dbg(str(linecount) + ": LINE=[" + line + "]")
            index = line.find(",")
            if index <= 0 or line.startswith("date"):
                _ = D and dbg(f"Skipping line:\n{line}")
            else:
                increment_totals(line)

    print_stats(
        "Totals",
        TOTAL_DISTANCE,
        TOTAL_CONSUMED,
        TOTAL_REGENERATED,
        TOTAL_ENGINE,
        TOTAL_CLIMATE,
        TOTAL_ELECTRONICS,
        TOTAL_BATTERY_CARE,
    )


def reverse_print_dailystats_one_line(line):
    """reverse print dailystats one line"""
    line = line.strip()
    _ = D and dbg(f"line={line}")
    val = line.split(",")
    if len(val) != 9 or line.startswith("date"):
        return  # nothing to do

    date = val[DATE].strip()
    if len(date) == 8:
        date = date[0:4] + "-" + date[4:6] + "-" + date[6:]
    print_stats(
        date,
        to_int(val[DISTANCE]),
        to_int(val[CONSUMED]),
        to_int(val[REGENERATED]),
        to_int(val[ENGINE]),
        to_int(val[CLIMATE]),
        to_int(val[ELECTRONICS]),
        to_int(val[BATTERY_CARE]),
    )


def reverse_print_dailystats(today_daily_stats_line):
    """reverse print dailystats"""
    if today_daily_stats_line != "":
        reverse_print_dailystats_one_line(today_daily_stats_line)
    for line in read_reverse_order(DAILYSTATS_CSV_FILE.name):
        reverse_print_dailystats_one_line(line)


def print_output_queue():
    """print output queue"""
    array = []
    formats = []
    current_row = 0
    for queue_output in PRINTED_OUTPUT_QUEUE:
        current_row += 1
        _ = D and dbg(f"write row: {current_row} {queue_output}")
        list_output = split_output_to_sheet_list(queue_output)
        array.append(
            {"range": f"A{current_row}:G{current_row}", "values": list_output}
        )
        if "Regen" in queue_output:
            formats.append(
                {
                    "range": f"A{current_row}:G{current_row}",
                    "format": {
                        "horizontalAlignment": "CENTER",
                        "textFormat": {
                            "bold": True,
                            "underline": True,
                            "italic": True,
                        },
                    },
                }
            )
        else:
            formats.append(
                {
                    "range": f"A{current_row}:G{current_row}",
                    "format": {
                        "horizontalAlignment": "CENTER",
                        "textFormat": {
                            "bold": False,
                            "underline": False,
                            "italic": False,
                        },
                    },
                }
            )

    if len(array) > 0:
        SHEET.batch_update(array)
    if len(formats) > 0:
        SHEET.batch_format(formats)


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


TODAY_DAILY_STATS_LINE = ""
with LASTRUN_FILE.open("r", encoding="utf-8") as lastrun_file:
    lastrun_lines = lastrun_file.readlines()
    if len(lastrun_lines) > 5:
        TODAY_DAILY_STATS_LINE = lastrun_lines[5].strip()

summary(TODAY_DAILY_STATS_LINE)  # do the total summary first
reverse_print_dailystats(TODAY_DAILY_STATS_LINE)  # and then dailystats

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
