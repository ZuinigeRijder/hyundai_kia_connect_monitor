# == domoticz_utils.py Author: Zuinige Rijder =========
""" domoticz utils """
# pylint:disable=logging-fstring-interpolation, consider-using-enumerate

import configparser
import logging
import logging.config

from monitor_utils import (
    dbg,
    execute_request,
    get,
    d,
    get_bool,
    get_filepath,
    get_items_dailystat_trip,
    get_items_dailystats_day,
    get_items_monitor_csv,
    get_items_monitor_dailystats_csv,
    get_items_monitor_tripinfo_csv,
    get_items_summary,
    get_summary_headers,
)

PARSER = configparser.ConfigParser()
PARSER.read(get_filepath("monitor.cfg"))

# == read [Domoticz] settings in monitor.cfg ===========================
domoticz_settings = dict(PARSER.items("Domoticz"))
SEND_TO_DOMOTICZ = get_bool(domoticz_settings, "send_to_domoticz", False)
DOMOTICZ_URL = get(domoticz_settings, "domot_url")

if SEND_TO_DOMOTICZ:
    ITEMS_MONITOR_CSV = get_items_monitor_csv()
    for IDX in range(len(ITEMS_MONITOR_CSV)):
        ITEMS_MONITOR_CSV[IDX] = f"monitor_monitor_{ITEMS_MONITOR_CSV[IDX]}"

    ITEMS_TRIPINFO_CSV = get_items_monitor_tripinfo_csv()
    for IDX in range(len(ITEMS_TRIPINFO_CSV)):
        ITEMS_TRIPINFO_CSV[IDX] = f"monitor_tripinfo_{ITEMS_TRIPINFO_CSV[IDX]}"

    ITEMS_DAILYSTATS_CSV = get_items_monitor_dailystats_csv()
    for IDX in range(len(ITEMS_DAILYSTATS_CSV)):
        ITEMS_DAILYSTATS_CSV[IDX] = f"monitor_dailystats_{ITEMS_DAILYSTATS_CSV[IDX]}"

    ITEMS_SUMMARY = get_items_summary()
    ITEMS_DAILYSTATS_DAY = get_items_dailystats_day()
    ITEMS_DAILYSTATS_TRIP = get_items_dailystat_trip()


# == send to Domoticz ========================================================
def send_to_domoticz(header: str, value: str) -> None:
    """send_to_Domoticz"""
    reference_test = DOMOTICZ_URL == "domoticz_reference_test"
    idx = get(domoticz_settings, header.lower(), "0")
    _ = d() and dbg(f"send_to_domoticz: idx = {idx}, {header} = {value}")
    if idx == "0":
        return  # nothing to do

    url = (
        DOMOTICZ_URL
        + "/json.htm?type=command&param=udevice&idx="
        + idx
        + "&svalue="
        + value
    )
    _ = d() and dbg(f"send_to_domoticz: {url}")
    retry = 0
    while not reference_test:
        retry += 1
        content = execute_request(url, "", {})
        if content != "ERROR" or retry > 30:
            if content == "ERROR":
                logging.error(f"number of retries exceeded: {url}")
            return


def send_splitted_line(
    headers: list, splitted: list, replace_empty_by_0: bool, skip_first: bool
) -> None:
    """send_splitted_line"""
    if len(splitted) < len(headers):
        logging.warning(
            f"line does not have all elements: {splitted}\nHEADERS={headers}"
        )
        return

    skipped_first = not skip_first
    for i in range(len(splitted)):  # pylint:disable=consider-using-enumerate
        if i < len(headers):
            if skipped_first:
                value = splitted[i].strip()
                if replace_empty_by_0 and value == "":
                    value = "0"
                send_to_domoticz(headers[i], value)
            else:
                skipped_first = True


def send_line(
    headers: list, line: str, replace_empty_by_0: bool = True, skip_first: bool = False
) -> None:
    """send_line"""
    splitted = line.split(",")
    send_splitted_line(headers, splitted, replace_empty_by_0, skip_first)


def send_monitor_csv_line_to_domoticz(line: str) -> None:
    """send_monitor_csv_line_to_domoticz"""
    if SEND_TO_DOMOTICZ:
        send_line(ITEMS_MONITOR_CSV, line)


def send_tripinfo_csv_line_to_domoticz(line: str) -> None:
    """send_tripinfo_csv_line_to_domoticz"""
    if SEND_TO_DOMOTICZ:
        send_line(ITEMS_TRIPINFO_CSV, line)


def send_dailystats_csv_line_to_domoticz(line: str) -> None:
    """send_dailystats_csv_line_to_domoticz"""
    if SEND_TO_DOMOTICZ:
        send_line(ITEMS_DAILYSTATS_CSV, line)


def get_items(subtopic: str, items: list[str]) -> list[str]:
    """get_items"""
    new_items: list[str] = []
    for item in items:
        new_items.append(f"{subtopic}_{item}")
    return new_items


def send_summary_line_to_domoticz(line: str) -> None:
    """send_summary_line_to_domoticz"""
    if SEND_TO_DOMOTICZ:
        splitted = [x.strip() for x in line.split(",")]
        period = splitted[0].replace(" ", "")
        summary_headers_dict = get_summary_headers()
        if period in summary_headers_dict:
            key = summary_headers_dict[period]
            send_splitted_line(
                get_items(f"summary_{key}", ITEMS_SUMMARY), splitted, True, True
            )
        else:
            _ = d() and dbg(
                f"Skipping: period={period}, headers={summary_headers_dict}"
            )


def send_dailystats_day_line_to_domoticz(postfix: str, line: str) -> None:
    """send_dailystats_day_line_to_domoticz"""
    if SEND_TO_DOMOTICZ:
        send_line(get_items(f"dailystats_day_{postfix}", ITEMS_DAILYSTATS_DAY), line)


def send_dailystats_trip_line_to_domoticz(
    postfix: str, line: str, skip_first_two: bool = False
) -> None:
    """send_dailystats_trip_line_to_domoticz"""
    if SEND_TO_DOMOTICZ:
        items = get_items(f"dailystats_trip_{postfix}", ITEMS_DAILYSTATS_TRIP)
        if skip_first_two:
            items = items[2:]
        send_line(items, line, replace_empty_by_0=False)
