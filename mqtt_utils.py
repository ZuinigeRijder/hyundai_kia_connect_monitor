# == mqtt_utils.py Author: Zuinige Rijder =========
"""mqtt utils"""
# pylint:disable=logging-fstring-interpolation, consider-using-enumerate

import configparser
import logging
import traceback
import time

try:  # make paho.mqtt optional
    from paho.mqtt import client as mqtt_client

    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False

from monitor_utils import (
    dbg,
    die,
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
    get_vin,
)

PARSER = configparser.ConfigParser()
PARSER.read(get_filepath("monitor.cfg"))

# == read [MQTT] settings in monitor.cfg ===========================
mqtt_settings = dict(PARSER.items("MQTT"))
SEND_TO_MQTT = get_bool(mqtt_settings, "send_to_mqtt", False)
MQTT_BROKER_HOSTNAME = get(mqtt_settings, "mqtt_broker_hostname", "localhost")
MQTT_BROKER_PORT = int(get(mqtt_settings, "mqtt_broker_port", "1883"))
MQTT_BROKER_USERNAME = get(mqtt_settings, "mqtt_broker_username", "")
MQTT_BROKER_PASSWORD = get(mqtt_settings, "mqtt_broker_password", "")
MQTT_BROKER_CABUNDLE = get(mqtt_settings, "mqtt_broker_cabundle", "")
MQTT_MAIN_TOPIC = get(mqtt_settings, "mqtt_main_topic", "hyundai_kia_connect_monitor")

MQTT_CLIENT = None  # will be filled at MQTT connect if configured

if SEND_TO_MQTT:
    ITEMS_MONITOR_CSV = get_items_monitor_csv()
    for IDX in range(len(ITEMS_MONITOR_CSV)):
        ITEMS_MONITOR_CSV[IDX] = f"monitor/monitor/{ITEMS_MONITOR_CSV[IDX]}"

    ITEMS_TRIPINFO_CSV = get_items_monitor_tripinfo_csv()
    for IDX in range(len(ITEMS_TRIPINFO_CSV)):
        ITEMS_TRIPINFO_CSV[IDX] = f"monitor/tripinfo/{ITEMS_TRIPINFO_CSV[IDX]}"

    ITEMS_DAILYSTATS_CSV = get_items_monitor_dailystats_csv()
    for IDX in range(len(ITEMS_DAILYSTATS_CSV)):
        ITEMS_DAILYSTATS_CSV[IDX] = f"monitor/dailystats/{ITEMS_DAILYSTATS_CSV[IDX]}"

    ITEMS_SUMMARY = get_items_summary()
    ITEMS_DAILYSTATS_DAY = get_items_dailystats_day()
    ITEMS_DAILYSTATS_TRIP = get_items_dailystat_trip()


# == connect MQTT ========================================================
def connect_mqtt():
    """connect_mqtt"""

    if not MQTT_AVAILABLE:
        die(
            "MQTT support not available, please install paho_mqtt, e.g."
            'pip install "paho_mqtt>=2.0"'
        )

    mqtt_first_reconnect_delay = 1
    mqtt_reconnect_rate = 2
    mqtt_max_reconnect_count = 12
    mqtt_max_reconnect_delay = 60

    def on_connect(client, userdata, flags, rc):  # pylint: disable=unused-argument
        if rc == 0:
            _ = d() and dbg("Connected to MQTT Broker!")
        else:
            logging.error("Failed to connect to MQTT Broker, return code %d\n", rc)

    def on_disconnect(client, userdata, rc):  # pylint: disable=unused-argument
        _ = d() and dbg(f"Disconnected with result code: {rc}")
        reconnect_count = 0
        reconnect_delay = mqtt_first_reconnect_delay
        while reconnect_count < mqtt_max_reconnect_count:
            _ = d() and dbg(f"Reconnecting in {reconnect_delay} seconds...")
            time.sleep(reconnect_delay)

            try:
                client.reconnect()
                _ = d() and dbg("Reconnected successfully!")
                return
            except Exception as reconnect_ex:  # pylint: disable=broad-except
                logging.error(f"{reconnect_ex}. Reconnect failed. Retrying...")

            reconnect_delay *= mqtt_reconnect_rate
            reconnect_delay = min(reconnect_delay, mqtt_max_reconnect_delay)
            reconnect_count += 1
        logging.info(f"Reconnect failed after {reconnect_count} attempts. Exiting...")

    mqtt_client_id = f"{MQTT_MAIN_TOPIC}-{get_vin()}"
    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1, mqtt_client_id)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    if MQTT_BROKER_USERNAME and MQTT_BROKER_PASSWORD:
        client.username_pw_set(MQTT_BROKER_USERNAME, MQTT_BROKER_PASSWORD)
    if MQTT_BROKER_CABUNDLE:
        client.tls_set(MQTT_BROKER_CABUNDLE)
    client.connect(MQTT_BROKER_HOSTNAME, MQTT_BROKER_PORT)
    return client


def start_mqtt_loop() -> None:
    """start_mqtt_loop"""
    global MQTT_CLIENT  # pylint: disable=global-statement
    if not MQTT_CLIENT and SEND_TO_MQTT:
        while True:
            try:
                _ = d() and dbg("Trying to connected to MQTT Broker")
                MQTT_CLIENT = connect_mqtt()
                MQTT_CLIENT.loop_start()
                break
            except Exception as connect_ex:  # pylint: disable=broad-except
                logging.error(  # pylint:disable=logging-fstring-interpolation
                    f"MQTT connect Exception: {connect_ex}, sleeping a minute"
                )
                traceback.print_exc()
                time.sleep(60)


def stop_mqtt() -> None:
    """stop_mqtt"""
    if MQTT_CLIENT and SEND_TO_MQTT:
        logging.debug("Stopping MQTT")
        MQTT_CLIENT.loop_stop()


# == send to MQTT ========================================================
def send_to_mqtt(subtopic: str, value: str) -> None:
    """send_to_mqtt"""
    start_mqtt_loop()

    msg_count = 1
    topic = f"{MQTT_MAIN_TOPIC}/{get_vin()}/{subtopic}"
    msg = f"{value}"
    logging.debug(  # pylint:disable=logging-fstring-interpolation
        f"send_to_mqtt: {topic} = {msg}"
    )
    while True:
        try:
            error = False
            if MQTT_CLIENT:
                result = MQTT_CLIENT.publish(topic, msg, qos=1, retain=True)
                status = result[0]
                if status == 0:
                    logging.debug(f"Send {msg} to topic {topic}")
                    msg_count = 6
                else:
                    error = True
        except Exception as publish_ex:  # pylint: disable=broad-except
            logging.error(  # pylint:disable=logging-fstring-interpolation
                f"MQTT publish Exception: {publish_ex}, sleeping a minute"
            )
            traceback.print_exc()
            time.sleep(60)

        if error:
            logging.error(  # pylint:disable=logging-fstring-interpolation
                f"Failed to send message {msg} to topic {topic}"
            )
            time.sleep(1)
            msg_count += 1

        if msg_count > 5:
            break


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
                send_to_mqtt(headers[i], value)
            else:
                skipped_first = True


def send_line(
    headers: list, line: str, replace_empty_by_0: bool = True, skip_first: bool = False
) -> None:
    """send_line"""
    splitted = line.split(",")
    send_splitted_line(headers, splitted, replace_empty_by_0, skip_first)


def send_monitor_csv_line_to_mqtt(line: str) -> None:
    """send_monitor_csv_line_to_mqtt"""
    if SEND_TO_MQTT:
        send_line(ITEMS_MONITOR_CSV, line)


def send_tripinfo_csv_line_to_mqtt(line: str) -> None:
    """send_tripinfo_csv_line_to_mqtt"""
    if SEND_TO_MQTT:
        send_line(ITEMS_TRIPINFO_CSV, line)


def send_dailystats_csv_line_to_mqtt(line: str) -> None:
    """send_dailystats_csv_line_to_mqtt"""
    if SEND_TO_MQTT:
        send_line(ITEMS_DAILYSTATS_CSV, line)


def get_items(subtopic: str, items: list[str]) -> list[str]:
    """get_items"""
    new_items: list[str] = []
    for item in items:
        new_items.append(f"{subtopic}/{item}")
    return new_items


def send_summary_line_to_mqtt(line: str) -> None:
    """send_summary_line_to_mqtt"""
    if SEND_TO_MQTT:
        splitted = [x.strip() for x in line.split(",")]
        period = splitted[0].replace(" ", "")
        summary_headers_dict = get_summary_headers()
        if period in summary_headers_dict:
            key = summary_headers_dict[period]
            send_splitted_line(
                get_items(f"summary/{key}", ITEMS_SUMMARY), splitted, True, True
            )
        else:
            _ = d() and dbg(
                f"Skipping: period={period}, headers={summary_headers_dict}"
            )


def send_dailystats_day_line_to_mqtt(postfix: str, line: str) -> None:
    """send_dailystats_day_line_to_mqtt"""
    if SEND_TO_MQTT:
        send_line(get_items(f"dailystats_day/{postfix}", ITEMS_DAILYSTATS_DAY), line)


def send_dailystats_trip_line_to_mqtt(
    postfix: str, line: str, skip_first_two: bool = False
) -> None:
    """send_dailystats_trip_line_to_mqtt"""
    if SEND_TO_MQTT:
        items = get_items(f"dailystats_trip/{postfix}", ITEMS_DAILYSTATS_TRIP)
        if skip_first_two:
            items = items[2:]
        send_line(items, line, replace_empty_by_0=False)
