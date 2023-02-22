# == check_monitor.py Author: Zuinige Rijder =========
""" Simple Python3 script to check monitor.csv """
from datetime import datetime
from io import TextIOWrapper
from pathlib import Path

from monitor_utils import arg_has, split_on_comma

D = arg_has("debug")


def dbg(line: str) -> bool:
    """print line if debugging"""
    if D:
        print(line)
    return D  # just to make a lazy evaluation expression possible


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

MONITOR_CSV_FILENAME = Path("monitor.csv")

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
    Skips identical lines
    Skips identical lines, where only the datetime is different
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

        if line != MONITOR_CSV_READ_AHEAD_LINE:  # skip identical lines
            line = line.strip()
            # only lines with content and not header line
            if line != "" and not line.startswith("datetime"):
                index = line.find(",")
                next_line = MONITOR_CSV_READ_AHEAD_LINE.strip()
                read_ahead_index = next_line.find(",")
                # skip identical lines, when only first column (datetime) is the same
                if index >= 0 and (
                    read_ahead_index < 0 or next_line[read_ahead_index:] != line[index:]
                ):
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
            print(f"#### Skipping line {MONITOR_CSV_LINECOUNT}: [{line}]")
            continue

        _ = D and dbg(str(MONITOR_CSV_LINECOUNT) + ": LINE=[" + line + "]")
        next_line = MONITOR_CSV_READ_AHEAD_LINE.strip()
        next_split = MONITOR_CSV_NEXT_SPLIT
        if len(next_split) != 11:
            print(f"Next split skip: {MONITOR_CSV_LINECOUNT}: [{next_line}]")
            return line

        if split[ODO] == next_split[ODO] and split[SOC] > next_split[SOC]:
            print(f"#### Same odo and SOC smaller:\n{line}\n{next_line}\n")
            date_curr = datetime.strptime(split[DT][:19], "%Y-%m-%d %H:%M:%S")
            date_next = datetime.strptime(next_split[DT][:19], "%Y-%m-%d %H:%M:%S")
            delta_min = round((date_next - date_curr).total_seconds() / 60)
            print(f"delta minutes: {delta_min}")
            if delta_min < 20:
                # just use the next line
                continue

        return line


def check_monitor() -> None:
    """check_monitor"""
    while True:
        line = get_corrected_next_monitor_csv_line()
        if line == "":  # EOF
            break  # finish loop
        print(f"{MONITOR_CSV_LINECOUNT}: [{line}]")


check_monitor()  # do the work
