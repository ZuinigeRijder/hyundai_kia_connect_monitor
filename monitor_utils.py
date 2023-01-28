# == monitor_utils.py Author: Zuinige Rijder =========
"""
monitor utils
"""
import configparser
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Generator


def log(msg: str) -> None:
    """log a message prefixed with a date/time format yyyymmdd hh:mm:ss"""
    print(datetime.now().strftime("%Y%m%d %H:%M:%S") + ": " + msg)


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


def safe_divide(numerator: float, denumerator: float) -> float:
    """safe_divide"""
    if denumerator == 0.0:
        return 1.0
    return numerator / denumerator


def to_int(string: str) -> int:
    """convert to int"""
    if "None" in string:
        return -1
    split = string.split(".")  # get rid of decimal part
    return int(split[0].strip())


def to_float(string: str) -> float:
    """convert to float"""
    if "None" in string:
        return 0.0
    return float(string.strip())


def float_to_string(input_value: float) -> str:
    """float to string without trailing zero"""
    return (f"{input_value:9.1f}").rstrip("0").rstrip(".")


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


def get_last_date(filename: str) -> str:
    """get last date of filename"""
    last_date = "20000101"  # millenium
    last_line = get_last_line(Path(filename))
    if last_line.startswith("20"):  # year starts with 20
        last_date = last_line.split(",")[0].strip()
    return last_date


def read_reverse_order(file_name: str) -> Generator[str, None, None]:
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


def read_reverse_order_init(path: Path) -> tuple[bool, str, Generator[str, None, None]]:
    """ "read_reverse_order_init"""
    eof = False
    last_read_line = ""
    if path.is_file():
        reverse_order_iterator = read_reverse_order(path.name)
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
    translations: dict = {}
    parser = configparser.ConfigParser()
    parser.read("monitor.cfg")
    monitor_settings = dict(parser.items("monitor"))
    language = monitor_settings["language"].lower().strip()
    translations_csv_file = Path("monitor.translations.csv")
    with translations_csv_file.open("r", encoding="utf-8") as inputfile:
        linecount = 0
        column = 1
        for line in inputfile:
            linecount += 1
            split = line.split(",")
            if len(split) < 15:
                log(f"Error: unexpected translation csvline {linecount}: {line}")
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
                current = split[column].strip()
                if current != "":
                    translation = current

            translations[key] = translation
    return translations


def get_translation(translations: dict[str, str], text: str) -> str:
    """get translation"""
    if text in translations:
        translation = translations[text]
        # print(f"found translation: {translation}")
    else:
        print(f"fallback translation: {text}")
        translation = text

    return translation
