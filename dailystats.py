# == dailystats.py Author: Zuinige Rijder =====================================
"""
Simple Python3 script to make a dailystats overview
"""
from dataclasses import dataclass
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path
from collections import deque
from dateutil.relativedelta import relativedelta
import gspread
from monitor_utils import (
    log,
    arg_has,
    get_vin_arg,
    safe_divide,
    sleep,
    split_on_comma,
    split_output_to_sheet_float_list,
    to_int,
    to_float,
    read_reverse_order,
    read_translations,
    get_translation,
    reverse_read_next_line,
    read_reverse_order_init,
    split_output_to_sheet_list,
)

# Initializing a queue for about 30 days
MAX_QUEUE_LEN = 122
PRINTED_OUTPUT_QUEUE: deque[str] = deque(maxlen=MAX_QUEUE_LEN)

D = arg_has("debug")


def dbg(line: str) -> bool:
    """print line if debugging"""
    if D:
        print(line)
    return D  # just to make a lazy evaluation expression possible


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
TRIPINFO_CSV_FILE = Path("monitor.tripinfo.csv")
CHARGE_CSV_FILE = Path("summary.charge.csv")
SUMMARY_TRIP_CSV_FILE = Path("summary.trip.csv")
LENCHECK = 1
VIN = get_vin_arg()
if VIN != "":
    DAILYSTATS_CSV_FILE = Path(f"monitor.dailystats.{VIN}.csv")
    TRIPINFO_CSV_FILE = Path(f"monitor.tripinfo.{VIN}.csv")
    CHARGE_CSV_FILE = Path(f"summary.charge.{VIN}.csv")
    SUMMARY_TRIP_CSV_FILE = Path(f"summary.trip.{VIN}.csv")
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

T_UNIT = "km"

TR_HELPER: dict[str, str] = read_translations()
COLUMN_WIDTHS = [11, 12, 14, 8, 9, 9, 8]


def update_width(text: str, index_column_widths: int) -> None:
    """update width"""
    if len(text) + 1 > COLUMN_WIDTHS[index_column_widths]:
        COLUMN_WIDTHS[index_column_widths] = len(text) + 1


def get_translation_and_update_width(text: str, index_column_widths: int) -> str:
    """get_translation_and_update_width"""
    translation = get_translation(TR_HELPER, text)
    update_width(translation, index_column_widths)
    return translation


@dataclass
class Translations:
    """Translations"""

    totals: str
    recuperation: str
    consumption: str
    engine: str
    climate: str
    electronic_devices: str
    battery_care: str

    trip: str
    distance: str
    average_speed: str
    max_speed: str
    idle_time: str

    per_hour: str


def fill_translations() -> Translations:
    """fill translations"""
    per_hour = get_translation_and_update_width("per hour", 5)
    avg_speed = get_translation(TR_HELPER, "Average speed") + f" {T_UNIT}/{per_hour}"
    max_speed = get_translation(TR_HELPER, "Max speed") + f" {T_UNIT}/{per_hour}"
    update_width(avg_speed, 4)
    update_width(max_speed, 5)

    translations = Translations(
        totals=get_translation_and_update_width("Totals", 0),
        recuperation=get_translation_and_update_width("Recuperation", 1),
        consumption=get_translation_and_update_width("Consumption", 2),
        engine=get_translation_and_update_width("Engine", 3),
        climate=get_translation_and_update_width("Climate", 4),
        electronic_devices=get_translation_and_update_width("Electronic devices", 5),
        battery_care=get_translation_and_update_width("Battery Care", 6),
        trip=get_translation_and_update_width("Trip", 1),
        distance=get_translation_and_update_width("Distance", 3),
        average_speed=avg_speed,
        max_speed=max_speed,
        idle_time=get_translation_and_update_width("Idle time", 6),
        per_hour=per_hour,
    )
    _ = D and dbg(f"Column widths: {COLUMN_WIDTHS}")
    return translations


TR = fill_translations()  # TR contains translations dataclass


def get_weekday_translation(weekday_string: str) -> str:
    """get weekday translation"""
    weekday = get_translation_and_update_width(weekday_string, 1)
    return weekday


(
    SUMMARY_TRIP_EOF,
    SUMMARY_TRIP_LAST_READ_LINE,
    SUMMARY_TRIP_READ_REVERSE_ORDER,
) = read_reverse_order_init(SUMMARY_TRIP_CSV_FILE)

(
    TRIPINFO_EOF,
    TRIPINFO_LAST_READ_LINE,
    TRIPINFO_READ_REVERSE_ORDER,
) = read_reverse_order_init(TRIPINFO_CSV_FILE)

(
    CHARGE_EOF,
    CHARGE_LAST_READ_LINE,
    CHARGE_READ_REVERSE_ORDER,
) = read_reverse_order_init(CHARGE_CSV_FILE)


def reverse_read_next_summary_trip_line() -> None:
    """reverse_read_next_summary_trip_line"""
    global SUMMARY_TRIP_EOF, SUMMARY_TRIP_LAST_READ_LINE  # noqa pylint:disable=global-statement
    SUMMARY_TRIP_EOF, SUMMARY_TRIP_LAST_READ_LINE = reverse_read_next_line(
        SUMMARY_TRIP_READ_REVERSE_ORDER, SUMMARY_TRIP_EOF, SUMMARY_TRIP_LAST_READ_LINE
    )


def reverse_read_next_trip_info_line() -> None:
    """reverse_read_next_trip_info_line"""
    global TRIPINFO_EOF, TRIPINFO_LAST_READ_LINE  # noqa pylint:disable=global-statement
    TRIPINFO_EOF, TRIPINFO_LAST_READ_LINE = reverse_read_next_line(
        TRIPINFO_READ_REVERSE_ORDER, TRIPINFO_EOF, TRIPINFO_LAST_READ_LINE
    )


def reverse_read_next_charge_line() -> None:
    """reverse_read_next_charge_line"""
    global CHARGE_EOF, CHARGE_LAST_READ_LINE  # noqa pylint:disable=global-statement
    CHARGE_EOF, CHARGE_LAST_READ_LINE = reverse_read_next_line(
        CHARGE_READ_REVERSE_ORDER, CHARGE_EOF, CHARGE_LAST_READ_LINE
    )


T_DAYS = 0
T_DISTANCE = 0
T_CONSUMED = 0
T_REGENERATED = 0
T_ENGINE = 0
T_CLIMATE = 0
T_ELECTRONICS = 0
T_BATTERY_CARE = 0


def increment_dailystats_totals(split: list[str]) -> None:
    """increment_dailystats_totals"""
    _ = D and dbg(f"handle_line: {split}")
    global T_DAYS, T_UNIT, T_DISTANCE, T_CONSUMED, T_REGENERATED, T_ENGINE, T_CLIMATE, T_ELECTRONICS, T_BATTERY_CARE  # noqa pylint:disable=global-statement

    # date = split[DATE]
    distance = to_int(split[DISTANCE])
    unit = split[DISTANCE_UNIT]
    consumed = to_int(split[CONSUMED])
    regenerated = to_int(split[REGENERATED])
    engine = to_int(split[ENGINE])
    climate = to_int(split[CLIMATE])
    electronics = to_int(split[ELECTRONICS])
    battery_care = to_int(split[BATTERY_CARE])

    T_DAYS += 1
    T_UNIT = unit
    T_DISTANCE += distance
    T_CONSUMED += consumed
    T_REGENERATED += regenerated
    T_ENGINE += engine
    T_CLIMATE += climate
    T_ELECTRONICS += electronics
    T_BATTERY_CARE += battery_care


TOTAL_TRIPINFO_DRIVE_TIME = 0
TOTAL_TRIPINFO_IDLE_TIME = 0
TOTAL_TRIPINFO_DISTANCE = 0
TOTAL_TRIPINFO_AVERAGE_SPEED = 0
TOTAL_TRIPINFO_MAX_SPEED = 0


def increment_tripinfo_totals(line: str) -> None:
    """increment_tripinfo_totals"""
    _ = D and dbg(f"handle_line: {line}")
    global TOTAL_TRIPINFO_DRIVE_TIME, TOTAL_TRIPINFO_IDLE_TIME, TOTAL_TRIPINFO_DISTANCE, TOTAL_TRIPINFO_AVERAGE_SPEED, TOTAL_TRIPINFO_MAX_SPEED  # noqa pylint:disable=global-statement
    split = split_on_comma(line)
    drive_time = to_int(split[2])
    idle_time = to_int(split[3])
    distance = to_int(split[4])
    avg_speed = to_int(split[5])
    max_speed = to_int(split[6])

    TOTAL_TRIPINFO_DRIVE_TIME += drive_time
    TOTAL_TRIPINFO_IDLE_TIME += idle_time
    TOTAL_TRIPINFO_DISTANCE += distance
    TOTAL_TRIPINFO_AVERAGE_SPEED += drive_time * avg_speed
    TOTAL_TRIPINFO_MAX_SPEED = max(TOTAL_TRIPINFO_MAX_SPEED, max_speed)


def print_output(output: str) -> None:
    """print output"""
    split = split_on_comma(output)
    for i in range(len(split)):  # pylint:disable=consider-using-enumerate
        text = split[i].rjust(COLUMN_WIDTHS[i])
        print(text, end="")
    print("")

    if SHEETUPDATE and len(PRINTED_OUTPUT_QUEUE) < MAX_QUEUE_LEN:
        PRINTED_OUTPUT_QUEUE.append(output)


def get_charge_for_date(date: str) -> str:
    """get_charge_for_date"""
    charge = ""
    while not CHARGE_EOF:
        line = CHARGE_LAST_READ_LINE
        splitted_line = split_on_comma(line)
        if len(splitted_line) > 3:
            charge_date = splitted_line[0]
            if charge_date == date:
                _ = D and dbg(f"charge match: {line}")
                charged = splitted_line[2]
                charge = f"(+{charged}kWh)"
                reverse_read_next_charge_line()
                break  # finished
            elif charge_date < date:
                _ = D and dbg(f"charge_date {charge_date} < {date}: {line}")
                break  # finished
            else:
                _ = D and dbg(f"charge skip: {line}")
        reverse_read_next_charge_line()
    _ = D and dbg(f"get_charge_for_date=({date})={charge}")
    return charge


def get_trip_for_datetime(
    date: str, trip_time_start_str: str, trip_time_end_str: str
) -> tuple[float, float]:
    """get_trip_for_datetime"""
    match = False
    matched_time = ""
    distance = 0.0
    kwh_consumed = 0.0
    kwh_charged = 0.0
    if D:
        print(f"get_trip_for_datetime: {date} {trip_time_start_str}{trip_time_end_str}")
    while not match and not SUMMARY_TRIP_EOF:
        line = SUMMARY_TRIP_LAST_READ_LINE
        splitted_line = split_on_comma(line)
        if len(splitted_line) > 3:
            trip_datetime = splitted_line[0]
            date_elements = trip_datetime.split(" ")
            if len(date_elements) < 2:
                log(f"Warning: skipping unexpected line: {line}")
                reverse_read_next_summary_trip_line()
                continue
            trip_date = date_elements[0]
            trip_time = date_elements[1]
            if trip_date == date:
                _ = D and dbg(f"trip date match: {line}")
                if trip_time > trip_time_start_str:
                    _ = D and dbg(
                        f"Match: {trip_time} > {trip_time_start_str}{trip_time_end_str}"
                    )
                    delta_seconds = (
                        datetime.strptime(trip_time, "%H:%M")
                        - datetime.strptime(trip_time_end_str, "-%H:%M")
                    ).total_seconds()
                    if abs(delta_seconds) < 3600:
                        matched_time = trip_time
                        distance = to_float(splitted_line[2])
                        kwh_consumed = to_float(splitted_line[3])
                        kwh_charged = to_float(splitted_line[4])
                        match = True
                    else:
                        if D:
                            print(
                                f"##### delta seconds: {delta_seconds} {date} {trip_time_start_str}{trip_time_end_str} {trip_time}"  # noqa
                            )

                else:
                    _ = D and dbg(
                        f"Skip : {trip_time} <= {trip_time_start_str}{trip_time_end_str}"  # noqa
                    )
                    break  # finished
            elif trip_date < date:
                _ = D and dbg(f"trip_date {trip_date} < {date}: {line}")
                break  # finished
            else:
                _ = D and dbg(f"trip_date skip: {line}")
        reverse_read_next_summary_trip_line()

    if D and matched_time != "":
        print(
            f"get_trip_for_datetime=({date} {trip_time_start_str}{trip_time_end_str})={matched_time}, {distance}, {kwh_consumed}, {kwh_charged}"  # noqa
        )
    return distance, kwh_consumed


def print_tripinfo(
    date_org: str,
    header: bool,
    charge: str,
    start_time: str,
    drive_time: str,
    idle_time: str,
    distance: str,
    avg_speed: str,
    max_speed: str,
) -> None:
    """print_tripinfo"""
    if header:
        print_output(
            f"{charge},{TR.trip},,{TR.distance},{TR.average_speed},{TR.max_speed},{TR.idle_time}"  # noqa
        )
    if start_time == "":  # totals line
        trip_time_str = f"{drive_time}min"
        distance_summary_trip = 0.0
        kwh_consumed = 0.0
    else:
        trip_time_start_str = start_time[0:2] + ":" + start_time[2:4]
        trip_time_date = datetime.strptime(trip_time_start_str, "%H:%M")
        trip_time_end = trip_time_date + relativedelta(minutes=to_int(drive_time))
        trip_time_end_str = trip_time_end.strftime("-%H:%M")
        trip_time_str = trip_time_start_str + trip_time_end_str

        # match with summary.tripinfo.csv and return kwh_consumed
        distance_summary_trip, kwh_consumed = get_trip_for_datetime(
            date_org, trip_time_start_str, trip_time_end_str
        )

    if kwh_consumed < 0.0:
        kwh_consumed = -kwh_consumed
    kwh = ""
    consumption = ""
    if distance_summary_trip == 0.0:  # just user other distance
        distance_summary_trip = to_int(distance)
    else:
        consumption = f"({distance_summary_trip:.1f}{T_UNIT})"

    if kwh_consumed > 0.0:
        kwh = f"({kwh_consumed:.1f}kWh)"
        km_mi_per_kwh = safe_divide(distance_summary_trip, kwh_consumed)
        consumption = f"({km_mi_per_kwh:.1f}{T_UNIT}/kWh)"

    print_output(
        f"{kwh},{trip_time_str},{consumption},{distance}{T_UNIT},{avg_speed}{T_UNIT}/{TR.per_hour},{max_speed}{T_UNIT}/{TR.per_hour},{idle_time}min"  # noqa
    )


def print_day_trip_info(date_org: str) -> None:
    """print stats"""
    charge = get_charge_for_date(date_org)
    date = date_org.replace("-", "")
    header = True
    while not TRIPINFO_EOF:
        line = TRIPINFO_LAST_READ_LINE
        splitted_line = split_on_comma(line)
        if len(splitted_line) > 5:
            tripinfo_date = splitted_line[0]
            if tripinfo_date == date:
                _ = D and (f"tripinfo match: {line}")
                print_tripinfo(
                    date_org,
                    header,
                    charge,
                    splitted_line[1],
                    splitted_line[2],
                    splitted_line[3],
                    splitted_line[4],
                    splitted_line[5],
                    splitted_line[6],
                )
                header = False
            elif tripinfo_date < date:
                _ = D and dbg(f"tripinfo_date {tripinfo_date} < {date}: {line}")
                break  # finished
            else:
                _ = D and dbg(f"tripinfo skip: {line}")
        reverse_read_next_trip_info_line()
    if header and charge != "":  # no trip info written, but charging session
        print_output(f"{charge},,,,,")  # still print charge


def print_dailystats(
    date: str,
    distance: int,
    consumed: int,
    regenerated: int,
    engine: int,
    climate: int,
    electronics: int,
    batterycare: int,
) -> None:
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

    totals = f"{date}"
    if date == "Totals":
        totals = TR.totals
        now = datetime.now()
        weekday_str = now.strftime("%a")
        tr_weekday = get_weekday_translation(weekday_str)
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M")
        tr_last_run = get_translation_and_update_width("Last run", 0)
        print_output(f"{tr_last_run},{date_str},{time_str},{tr_weekday},,,")
        print_output(",,,,,,")  # empty line/row

    print_output(
        f"{totals},{TR.recuperation},{TR.consumption},{TR.engine},{TR.climate},{TR.electronic_devices},{TR.battery_care}"  # noqa
    )
    print_output(
        f"{consumed_kwh:.1f}kWh,{regenerated_kwh:.1f}kWh,{km_mi_per_kwh:.1f}{T_UNIT}/kWh,{engine_kwh:.1f}kWh,{climate_kwh:.1f}kWh,{electronics_kwh:.1f}kWh,{battery_care_kwh:.1f}kWh"  # noqa
    )
    print_output(
        f"{distance}{T_UNIT},{regenerated_perc:.1f}%,{kwh_per_km_mi:.1f}kWh/100{T_UNIT},{engine_perc:.0f}%,{climate_perc:.1f}%,{electronics_perc:.1f}%,{battery_care_perc:.1f}%"  # noqa
    )


def compute_total_charge() -> float:
    """compute_total_charge"""
    total_charge = 0.0
    if CHARGE_CSV_FILE.is_file():
        with CHARGE_CSV_FILE.open("r", encoding="utf-8") as inputfile:
            linecount = 0
            for line in inputfile:
                line = line.strip()
                linecount += 1
                _ = D and dbg(str(linecount) + ": LINE=[" + line + "]")
                split = split_on_comma(line)
                if len(split) < 4 or line.startswith("date"):
                    _ = D and dbg(f"Skipping line:\n{line}")
                else:
                    charge = to_float(split[2])
                    total_charge += charge
    return total_charge


def summary_tripinfo() -> None:
    """summary_tripinfo"""
    if TRIPINFO_CSV_FILE.is_file():
        with TRIPINFO_CSV_FILE.open("r", encoding="utf-8") as inputfile:
            linecount = 0
            for line in inputfile:
                line = line.strip()
                linecount += 1
                _ = D and dbg(str(linecount) + ": LINE=[" + line + "]")
                index = line.find(",")
                if index <= 0 or line.startswith("Date"):
                    _ = D and dbg(f"Skipping line:\n{line}")
                else:
                    increment_tripinfo_totals(line)

    total_charge = compute_total_charge()
    average_speed = round(TOTAL_TRIPINFO_AVERAGE_SPEED / TOTAL_TRIPINFO_DRIVE_TIME)
    print_tripinfo(
        date_org="",
        header=True,
        charge=f"(+{total_charge:.1f}kWh)",
        start_time="",
        drive_time=f"{TOTAL_TRIPINFO_DRIVE_TIME}",
        idle_time=f"{TOTAL_TRIPINFO_IDLE_TIME}",
        distance=f"{TOTAL_TRIPINFO_DISTANCE}",
        avg_speed=f"{average_speed}",
        max_speed=f"{TOTAL_TRIPINFO_MAX_SPEED}",
    )
    print_output(",,,,,,")  # empty line/row


def reverse_print_dailystats_one_line(val: list[str]) -> None:
    """reverse print dailystats one line"""
    date = val[DATE].split(" ")[0]
    if len(date) == 8:
        date = date[0:4] + "-" + date[4:6] + "-" + date[6:]
    print_dailystats(
        date,
        to_int(val[DISTANCE]),
        to_int(val[CONSUMED]),
        to_int(val[REGENERATED]),
        to_int(val[ENGINE]),
        to_int(val[CLIMATE]),
        to_int(val[ELECTRONICS]),
        to_int(val[BATTERY_CARE]),
    )
    if date != "Totals":
        print_day_trip_info(date)
    print_output(",,,,,,")  # empty line/row


def reverse_print_dailystats(totals: bool) -> None:
    """reverse print dailystats"""
    if DAILYSTATS_CSV_FILE.is_file():
        prev_date_str = ""
        for line in read_reverse_order(DAILYSTATS_CSV_FILE.name):
            splitted = split_on_comma(line)
            if len(splitted) != 9 or splitted[0].startswith("date"):
                continue  # nothing to do
            date_str = splitted[0].split(" ")[0]
            if date_str != prev_date_str:  # skip identical dates
                if totals:
                    increment_dailystats_totals(splitted)
                else:
                    reverse_print_dailystats_one_line(splitted)
                prev_date_str = date_str
            else:
                _ = D and dbg(f"skipping: {splitted}")


def get_format(range_str: str, special: bool):
    """get_format"""
    result = {
        "range": range_str,
        "format": {
            "horizontalAlignment": "RIGHT",
            "textFormat": {
                "bold": special,
                "underline": special,
                "italic": special,
            },
        },
    }
    return result


def append(array: list[dict], formats: list[dict], row: int, values) -> int:
    """append"""
    row += 1
    array.append({"range": f"O{row}:U{row}", "values": values})
    formats.append(get_format(f"N{row}:U{row}", False))
    return row


def print_output_queue() -> None:
    """print output queue"""
    array: list[dict] = []
    formats: list[dict] = []
    row = 0
    # copy daily
    cd_row = 2
    cd_header = False
    cd_date = ""
    # copy trip
    ct_row = 25
    ct_header = False
    ct_header_printed = False
    ct_day_change = True
    ct_date = ""
    array.append({"range": "N1", "values": [[f"{T_UNIT}/kWh"]]})
    for queue_output in PRINTED_OUTPUT_QUEUE:
        row += 1
        _ = D and dbg(f"write row: {row} {queue_output}")
        values = split_output_to_sheet_list(queue_output)
        array.append({"range": f"A{row}:G{row}", "values": values})
        if (
            TR.recuperation in queue_output
            or TR.totals in queue_output
            or TR.trip in queue_output
        ):
            formats.append(get_format(f"A{row}:G{row}", True))
            if TR.recuperation in queue_output:
                ct_header = False
                ct_day_change = True
                cd_date = split_on_comma(queue_output)[0]
                ct_date = cd_date
                if not cd_header:
                    cd_row = append(array, formats, cd_row, values)
                    cd_header = True

            if TR.trip in queue_output:
                if not ct_header and not ct_header_printed:
                    ct_header_printed = True
                    copy = split_output_to_sheet_list(queue_output)
                    copy[0][0] = ""  # clear consumption
                    ct_row = append(array, formats, ct_row, copy)
                ct_header = True

        else:
            formats.append(get_format(f"A{row}:G{row}", False))
            if cd_date != "":
                # dailystats
                tmp = re.sub(r"[^0-9.,]", "", queue_output)
                floats = split_output_to_sheet_float_list(tmp)
                cd_row = append(array, formats, cd_row, floats)
                array.append({"range": f"N{cd_row}", "values": [[cd_date]]})
                cd_date = ""
            else:
                if ct_header and queue_output != ",,,,,,":
                    # tripinfo
                    trip = [ct_date, 0, "", 0, 0, 0, 0]  # clear consumption
                    tmp = re.sub(r"[^0-9.,:-]", "", queue_output)
                    entry = split_output_to_sheet_list(tmp)[0]
                    trip_time = entry[1]
                    if ":" in trip_time:
                        # only the first entry of a day should contain date
                        if not ct_day_change:
                            trip[0] = trip_time.split("-")[0]  # only start time
                        else:
                            trip[0] = ct_date + " " + trip_time.split("-")[0]
                        ct_day_change = False
                        # replace time range with elapsed minutes
                        strip = trip_time.split("-")
                        delta_min = round(
                            (
                                datetime.strptime(strip[1], "%H:%M")
                                - datetime.strptime(strip[0], "%H:%M")
                            ).total_seconds()
                            / 60
                        )
                        if delta_min < 0:
                            delta_min += 24 * 60
                        trip[1] = delta_min
                    elif trip_time.isdigit():
                        trip[1] = int(entry[1])  # convert to int

                    for i in range(3, 7):
                        trip[i] = int(entry[i])
                    ct_row = append(array, formats, ct_row, [trip])

    if len(array) > 0:
        SHEET.batch_update(array)
    if len(formats) > 0:
        SHEET.batch_format(formats)


# main program
if SHEETUPDATE:
    RETRIES = 2
    while RETRIES > 0:
        try:
            gc = gspread.service_account()
            spreadsheet = gc.open(OUTPUT_SPREADSHEET_NAME)
            SHEET = spreadsheet.sheet1
            SHEET.batch_clear(["A:G", "N:V"])
            RETRIES = 0
        except Exception as ex:  # pylint: disable=broad-except
            log("Exception: " + str(ex))
            traceback.print_exc()
            RETRIES = sleep(RETRIES)


reverse_print_dailystats(totals=True)  # do the total dailystats summary first
print_dailystats(
    "Totals",
    T_DISTANCE,
    T_CONSUMED,
    T_REGENERATED,
    T_ENGINE,
    T_CLIMATE,
    T_ELECTRONICS,
    T_BATTERY_CARE,
)

summary_tripinfo()  # then the total tripinfo
reverse_print_dailystats(totals=False)  # and then dailystats

if SHEETUPDATE:
    RETRIES = 2
    while RETRIES > 0:
        try:
            print_output_queue()
            RETRIES = 0
        except Exception as ex:  # pylint: disable=broad-except
            log("Exception: " + str(ex))
            traceback.print_exc()
            RETRIES = sleep(RETRIES)
