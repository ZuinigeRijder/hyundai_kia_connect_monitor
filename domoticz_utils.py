# == domoticz_utils.py Author: Zuinige Rijder =========
""" domoticz utils """
# pylint:disable=logging-fstring-interpolation

import configparser
import logging
import logging.config

from monitor_utils import (
    execute_request,
    get,
    get_bool,
    get_filepath,
    get_items_monitor_csv,
    get_items_monitor_dailystats_csv,
    get_items_monitor_tripinfo_csv,
)

PARSER = configparser.ConfigParser()
PARSER.read(get_filepath("monitor.cfg"))

# == read [Domoticz] settings in monitor.cfg ===========================
domoticz_settings = dict(PARSER.items("Domoticz"))
SEND_TO_DOMOTICZ = get_bool(domoticz_settings, "send_to_domoticz", False)
DOMOTICZ_URL = get(domoticz_settings, "domot_url")

ITEMS_MONITOR_CSV = get_items_monitor_csv()
ITEMS_MONITOR_TRIPINFO_CSV = get_items_monitor_tripinfo_csv()
ITEMS_MONITOR_DAILYSTATS_CSV = get_items_monitor_dailystats_csv()


# == send to Domoticz ========================================================
def send_to_domoticz(header: str, value: str) -> None:
    """send_to_Domoticz"""
    idx = get(domoticz_settings, header, "0")
    if idx == "0":
        return  # nothing to do

    url = (
        DOMOTICZ_URL
        + "/json.htm?type=command&param=udevice&idx="
        + idx
        + "&svalue="
        + value
    )
    logging.debug(url)
    retry = 0
    while True:
        retry += 1
        content = execute_request(url, "", {})
        if content != "ERROR" or retry > 30:
            if content == "ERROR":
                logging.error(f"number of retries exceeded: {url}")
            return


def send_line(headers: list, line: str) -> None:
    """send_line"""
    splitted = line.split(",")
    if len(splitted) < len(headers):
        logging.info(f"line does not have all elements: {line}\n{headers}")
        return

    for i in range(len(splitted)):  # pylint:disable=consider-using-enumerate
        send_to_domoticz(headers[i], splitted[i].strip())


def send_monitor_csv_line_to_domoticz(line: str) -> None:
    """send_monitor_csv_line_to_domoticz"""
    if SEND_TO_DOMOTICZ:
        send_line(ITEMS_MONITOR_CSV, line)


def send_tripinfo_line_to_domoticz(line: str) -> None:
    """send_tripinfo_line_to_domoticz"""
    if SEND_TO_DOMOTICZ:
        send_line(ITEMS_MONITOR_TRIPINFO_CSV, line)


def send_dailystats_line_to_domoticz(line: str) -> None:
    """send_dailystats_line_to_domoticz"""
    if SEND_TO_DOMOTICZ:
        send_line(ITEMS_MONITOR_DAILYSTATS_CSV, line)
