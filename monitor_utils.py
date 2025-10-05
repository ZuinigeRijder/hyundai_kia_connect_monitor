# == monitor_utils.py Author: Zuinige Rijder =========
"""monitor utils"""
# pylint:disable=logging-fstring-interpolation

import configparser
import errno
import logging
import logging.config
import sys
import os
import socket
import traceback
from pathlib import Path
import time
from typing import Generator

from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import urlopen, Request


VIN = ""  # filled by set_vin() or determine_vin() method

D = False

TR_HELPER: dict[str, str] = {}
TR_SUMMARY_HEADERS_DICT: dict[str, str] = {}


def d() -> bool:
    """return D"""
    return D


def dbg(line: str) -> bool:
    """print line if debugging"""
    if D:
        logging.debug(line)
    return D  # just to make a lazy evaluation expression possible


def set_dbg() -> None:
    """set_dbg"""
    global D  # pylint:disable=global-statement
    D = True
    logging.getLogger().setLevel(logging.DEBUG)


def get_splitted_list_item(the_list: list[str], index: int) -> list[str]:
    """get splitted item from list"""
    if index < 0 or index >= len(the_list):
        return ["", ""]
    items = the_list[index].split(";")
    if len(items) != 2:
        return ["", ""]
    return [items[0].strip(), items[1].strip()]


def set_vin(vin: str) -> None:
    """set_vin"""
    global VIN  # pylint: disable=global-statement
    VIN = vin


def determine_vin(lastrun_filename: Path) -> None:
    """determine_vin"""
    # get vin information from monitor.lastrun
    with lastrun_filename.open("r", encoding="utf-8") as lastrun_file:
        lastrun_lines = lastrun_file.readlines()
    vin = get_splitted_list_item(lastrun_lines, 1)[1]
    set_vin(vin)


def get_vin() -> str:
    """get_vin"""
    return VIN


def get_items_monitor_csv() -> list:
    """get_items_monitor_csv"""
    items = "datetime, longitude, latitude, engineon, battery12v, odometer, soc, charging, plugged, address, evrange"  # noqa
    result = [x.strip().lower() for x in items.split(",")]
    return result


def get_items_monitor_tripinfo_csv() -> list:
    """get_items_monitor_tripinfo_csv"""
    items = "date, starttime, drivetime, idletime, distance, avgspeed, maxspeed"
    result = [x.strip().lower() for x in items.split(",")]
    return result


def get_items_monitor_dailystats_csv() -> list:
    """get_items_monitor_dailystats_csv"""
    items = "date, distance, distance_unit, total_consumed, regenerated_energy, engine_consumption, climate_consumption, onboard_electronics_consumption, battery_care_consumption"  # noqa
    result = [x.strip().lower() for x in items.split(",")]
    return result


def get_items_summary() -> list:
    """get_items_summary"""
    items = "period, date, info, odometer, delta_distance, kwh_charged, kwh_discharged, distance_unit_per_kwh, kwh_per_100_distance_unit, cost, soc, soc_avg, soc_min, soc_max, battery12v, battery12v_avg, battery12v_min, battery12v_max, charging_sessions, trip_count, range, address"  # noqa
    result = [x.strip().lower() for x in items.split(",")]
    return result


def get_items_dailystats_day() -> list:
    """get_items_dailystat_day"""
    items = "date, total_consumption, regenerated_energy, average_consumption, engine_consumption, climate_consumption, onboard_electronics_consumption, battery_care_consumption, driven, regenerated_energy_percentage, average_consumption_per_100, engine_consumption_percentage, climate_consumption_percentage, onboard_electronics_consumption_percentage, battery_care_consumption_percentage"  # noqa
    result = [x.strip().lower() for x in items.split(",")]
    return result


def get_items_dailystat_trip() -> list:
    """get_items_dailystat_trip"""
    items = "computed_kwh_charged, computed_day_consumption, computed_kwh_used, trip_time, computed_consumption_or_distance, distance, avg_speed, max_speed, idle_time"  # noqa
    result = [x.strip().lower() for x in items.split(",")]
    return result


def get_filepath(filename: str) -> str:
    """get_filepath"""
    if os.path.isfile(filename):  # current directory
        filepath = filename
    else:  # script directory
        script_dirname = os.path.abspath(os.path.dirname(__file__))
        filepath = f"{script_dirname}/{filename}"

    if not os.path.isfile(filepath):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filepath)
    return filepath


def get(dictionary: dict, key: str, default: str = "") -> str:
    """get key from dictionary"""
    if key in dictionary:
        return dictionary[key].strip()
    return default


def get_bool(dictionary: dict, key: str, default: bool = True) -> bool:
    """get boolean value from dictionary key"""
    value = get(dictionary, key)
    if value == "":
        return default
    return value.lower() == "true"


def arg_has(string: str) -> bool:
    """arguments has string"""
    for i in range(1, len(sys.argv)):
        if sys.argv[i].lower() == string:
            return True
    return False


def get_vin_arg() -> str:
    """get vin argument"""
    for i in range(1, len(sys.argv)):
        if "vin=" in sys.argv[i].lower():
            vin = sys.argv[i]
            vin = vin.replace("vin=", "")
            vin = vin.replace("VIN=", "")
            return vin

    return ""


def sleep_seconds(seconds: int) -> None:
    """sleep seconds"""
    _ = D and dbg(f"Sleeping {seconds} seconds")
    time.sleep(seconds)


def sleep_a_minute(retries: int) -> int:
    """sleep a minute when retries > 0"""
    if retries > 0:
        retries -= 1
        if retries > 0:
            logging.info("Sleeping a minute")
            time.sleep(60)
    return retries


def km_to_mile(kilometer: float) -> float:
    """Convert km to mile"""
    mile = kilometer * 0.6213711922
    return mile


def safe_divide(numerator: float, denumerator: float) -> float:
    """safe_divide"""
    if denumerator == 0.0:
        return 0.0
    return numerator / denumerator


def to_int(string: str) -> int:
    """convert to int"""
    if "None" in string:
        return -1
    return round(to_float(string))


def to_float(string: str) -> float:
    """convert to float"""
    if "None" in string:
        return 0.0
    return float(string.strip())


def get_safe_float(number: float) -> float:
    """get safe float"""
    if number is None:
        return 0.0
    return number


def float_to_string_no_trailing_zero(input_value: float) -> str:
    """float to string without trailing zero"""
    return (f"{input_value:.1f}").rstrip("0").rstrip(".")


def get_safe_bool(value: bool) -> bool:
    """get safe bool"""
    if value is None:
        return False
    return value


def is_true(string: str) -> bool:
    """return if string is true (True or not 0 digit)"""
    if "None" in string:
        return False
    tmp = string.strip().lower()
    if tmp == "true":
        return True
    elif tmp == "false":
        return False
    else:
        return tmp.isdigit() and tmp != "0"


def same_year(d_1: datetime, d_2: datetime) -> bool:
    """return if same year"""
    return d_1.year == d_2.year


def same_month(d_1: datetime, d_2: datetime) -> bool:
    """return if same month"""
    if d_1.month != d_2.month:
        return False
    return d_1.year == d_2.year


def same_week(d_1: datetime, d_2: datetime) -> bool:
    """return if same week"""
    if d_1.isocalendar().week != d_2.isocalendar().week:
        return False
    return d_1.year == d_2.year


def same_day(d_1: datetime, d_2: datetime) -> bool:
    """return if same day"""
    if d_1.day != d_2.day:
        return False
    if d_1.month != d_2.month:
        return False
    return d_1.year == d_2.year


def split_on_comma(text: str) -> list[str]:
    """split string on comma and strip spaces around strings"""
    result = [x.strip() for x in text.split(",")]
    return result


def split_output_to_sheet_list(text: str) -> list[list[str]]:
    """split output to sheet list"""
    return [split_on_comma(text)]


def split_output_to_sheet_float_list(text: str) -> list[list[float]]:
    """split output to sheet float list"""
    result = [float(x.strip()) for x in text.split(",")]
    return [result]


def get_last_line(filename: Path) -> str:
    """get last line of filename"""
    last_line = ""
    if filename.is_file():
        with open(filename.name, "rb") as file:
            try:
                file.seek(-2, os.SEEK_END)
                while file.read(1) != b"\n":
                    file.seek(-2, os.SEEK_CUR)
            except OSError:
                file.seek(0)
            last_line = file.readline().decode().strip()
    return last_line


def get_safe_datetime(date: datetime, tzinfo: timezone) -> datetime:
    """get safe datetime"""
    if date is None:
        return datetime(2000, 1, 1, tzinfo=tzinfo)
    return date


def get_last_date(filename: str) -> str:
    """get last date of filename"""
    last_date = "20000101"  # millenium
    last_line = get_last_line(Path(filename))
    if last_line.startswith("20"):  # year starts with 20
        last_date = last_line.split(",")[0].strip()
    return last_date


def read_reverse_order(
    file_name: str, encoding: str = "utf-8"
) -> Generator[str, None, None]:
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
                yield buffer.decode(encoding=encoding)[::-1]
                # Reinitialize the byte array to save next line
                buffer = bytearray()
            else:
                # If last read character is not eol then add it in buffer
                buffer.extend(new_byte)
        # If there is still data in buffer, then it is first line.
        if len(buffer) > 0:
            # Yield the first line too
            yield buffer.decode()[::-1]


def read_reverse_order_init(
    path: Path, encoding: str = "utf-8"
) -> tuple[bool, str, Generator[str, None, None]]:
    """ "read_reverse_order_init"""
    eof = False
    last_read_line = ""
    if path.is_file():
        reverse_order_iterator = read_reverse_order(path.name, encoding)
        return eof, last_read_line, reverse_order_iterator
    else:
        eof = True
        # avoid mypy type error
        empty_list: list[str] = []
        return eof, last_read_line, (item for item in empty_list)


def reverse_read_next_line(
    reverse_order_generator: Generator[str, None, None],
    eof: bool,
    last_read_line: str,
) -> tuple[bool, str]:
    """reverse_read_next_line"""
    stop_value = None
    while not eof:
        line = next(reverse_order_generator, stop_value)
        if line is stop_value:
            eof = True
            last_read_line = ""
        else:
            line = line.strip()
            if (
                line != "" and "Date" not in line and "date" not in line
            ):  # skip header/empty lines
                last_read_line = line
                return eof, last_read_line
    return eof, last_read_line


def read_translations() -> dict:
    """read translations"""
    if len(TR_HELPER) == 0:
        parser = configparser.ConfigParser()
        parser.read(get_filepath("monitor.cfg"))
        monitor_settings = dict(parser.items("monitor", raw=True))
        language = get(monitor_settings, "language", "en").lower().strip()
        translations_csv_file = Path(get_filepath("monitor.translations.csv"))
        with translations_csv_file.open("r", encoding="utf-8") as inputfile:
            linecount = 0
            column = 1
            for line in inputfile:
                linecount += 1
                split = split_on_comma(line)
                if len(split) < 15:
                    logging.error(
                        f"Error: unexpected translation csvline {linecount}: {line}"
                    )
                    continue
                key = split[0]
                translation = split[1]
                if linecount == 1:
                    continue  # skip first line
                elif linecount == 2:
                    # determine column index
                    for index, value in enumerate(split):
                        if value.lower() == language:
                            column = index
                            break
                else:
                    current = split[column]
                    if current != "":
                        translation = current

                TR_HELPER[key] = translation
    return TR_HELPER


def get_summary_headers() -> dict:
    """get summary headers"""
    _ = read_translations()
    if len(TR_SUMMARY_HEADERS_DICT) == 0:
        keys = [
            "TRIP",
            "DAY",
            "WEEK",
            "MONTH",
            "YEAR",
            "TRIPAVG",
            "DAYAVG",
            "WEEKAVG",
            "MONTHAVG",
            "YEARLY",
        ]
        for key in keys:
            TR_SUMMARY_HEADERS_DICT[TR_HELPER[key].replace(" ", "")] = key
    return TR_SUMMARY_HEADERS_DICT


def get_translation(translations: dict[str, str], text: str) -> str:
    """get translation"""
    if text in translations:
        translation = translations[text]
        # print(f"found translation: {translation}")
    else:
        print(f"fallback translation: {text}")
        translation = text

    return translation


# == execute_request ==========================================================
def execute_request(url: str, data: str, headers: dict) -> str:
    """execute request and handle errors"""
    if data != "":
        post_data = data.encode("utf-8")
        request = Request(url, data=post_data, headers=headers)
    else:
        request = Request(url)
    errorstring = ""
    try:
        with urlopen(request, timeout=30) as response:
            body = response.read()
            content = body.decode("utf-8")
            _ = D and dbg(content)
            return content
    except HTTPError as error:
        errorstring = str(error.status) + ": " + error.reason
    except URLError as error:
        errorstring = str(error.reason)
    except TimeoutError:
        errorstring = "Request timed out"
    except socket.timeout:
        errorstring = "Socket timed out"
    except Exception as ex:  # pylint: disable=broad-except
        errorstring = "urlopen exception: " + str(ex)
        traceback.print_exc()

    logging.error(url + " -> " + errorstring)
    time.sleep(60)  # retry after 1 minute
    return "ERROR"
