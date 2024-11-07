# == mqtt_utils.py Author: Zuinige Rijder =========
""" mqtt utils """
# pylint:disable=logging-fstring-interpolation

import configparser
import logging
import logging.config
import traceback
import time

from paho.mqtt import client as mqtt_client

from monitor_utils import (
    get,
    get_bool,
    get_filepath,
    get_items_monitor_csv,
    get_items_monitor_dailystats_csv,
    get_items_monitor_tripinfo_csv,
)

ITEMS_MONITOR_CSV = get_items_monitor_csv()
ITEMS_MONITOR_TRIPINFO_CSV = get_items_monitor_tripinfo_csv()
ITEMS_MONITOR_DAILYSTATS_CSV = get_items_monitor_dailystats_csv()


PARSER = configparser.ConfigParser()
PARSER.read(get_filepath("monitor.cfg"))

# == read [MQTT] settings in monitor.cfg ===========================
mqtt_settings = dict(PARSER.items("MQTT"))
SEND_TO_MQTT = get_bool(mqtt_settings, "send_to_mqtt", False)
MQTT_BROKER_HOSTNAME = get(mqtt_settings, "mqtt_broker_hostname", "localhost")
MQTT_BROKER_PORT = int(get(mqtt_settings, "mqtt_broker_port", "1883"))
MQTT_BROKER_USERNAME = get(mqtt_settings, "mqtt_broker_username", "")
MQTT_BROKER_PASSWORD = get(mqtt_settings, "mqtt_broker_password", "")
MQTT_MAIN_TOPIC = get(mqtt_settings, "mqtt_main_topic", "hyundai_kia_connect_monitor")

MQTT_CLIENT = None  # will be filled at MQTT connect if configured
VIN = None  # filled by set_vin() method


def set_vin(vin: str) -> None:
    """set_vin"""
    global VIN  # pylint: disable=global-statement
    VIN = vin


# == connect MQTT ========================================================
def connect_mqtt() -> mqtt_client.Client:
    """connect_mqtt"""

    mqtt_first_reconnect_delay = 1
    mqtt_reconnect_rate = 2
    mqtt_max_reconnect_count = 12
    mqtt_max_reconnect_delay = 60

    def on_connect(client, userdata, flags, rc):  # pylint: disable=unused-argument
        if rc == 0:
            logging.debug("Connected to MQTT Broker!")
        else:
            logging.error("Failed to connect to MQTT Broker, return code %d\n", rc)

    def on_disconnect(client, userdata, rc):  # pylint: disable=unused-argument
        logging.debug("Disconnected with result code: %s", rc)
        reconnect_count = 0
        reconnect_delay = mqtt_first_reconnect_delay
        while reconnect_count < mqtt_max_reconnect_count:
            logging.debug("Reconnecting in %d seconds...", reconnect_delay)
            time.sleep(reconnect_delay)

            try:
                client.reconnect()
                logging.debug("Reconnected successfully!")
                return
            except Exception as reconnect_ex:  # pylint: disable=broad-except
                logging.error("%s. Reconnect failed. Retrying...", reconnect_ex)

            reconnect_delay *= mqtt_reconnect_rate
            reconnect_delay = min(reconnect_delay, mqtt_max_reconnect_delay)
            reconnect_count += 1
        logging.info("Reconnect failed after %s attempts. Exiting...", reconnect_count)

    mqtt_client_id = f"{MQTT_MAIN_TOPIC}-{VIN}"
    client = mqtt_client.Client(mqtt_client_id)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    if MQTT_BROKER_USERNAME and MQTT_BROKER_PASSWORD:
        client.username_pw_set(MQTT_BROKER_USERNAME, MQTT_BROKER_PASSWORD)
    client.connect(MQTT_BROKER_HOSTNAME, MQTT_BROKER_PORT)
    return client


def start_mqtt_loop() -> None:
    """start_mqtt_loop"""
    global MQTT_CLIENT  # pylint: disable=global-statement
    if not MQTT_CLIENT:
        while True:
            try:
                logging.debug("Trying to connected to MQTT Broker")
                MQTT_CLIENT = connect_mqtt()
                MQTT_CLIENT.loop_start()
                break
            except Exception as connect_ex:  # pylint: disable=broad-except
                logging.error(  # pylint:disable=logging-fstring-interpolation
                    f"MQTT connect Exception: {connect_ex}, sleeping a minute"
                )
                traceback.print_exc()
                time.sleep(60)


def stop_mqtt_loop() -> None:
    """stop_mqtt_loop"""
    if MQTT_CLIENT:
        logging.debug("Trying stop MQTT Broker loop")
        MQTT_CLIENT.loop_stop()


# == send to MQTT ========================================================
def send_to_mqtt(subtopic: str, value: str) -> None:
    """send_to_mqtt"""
    start_mqtt_loop()

    msg_count = 1
    topic = f"{MQTT_MAIN_TOPIC}/{VIN}/{subtopic}"
    msg = f"{value}"
    logging.debug(  # pylint:disable=logging-fstring-interpolation
        f"topic: {topic}, msg: {msg}"
    )
    while True:
        try:
            error = False
            if MQTT_CLIENT:
                result = MQTT_CLIENT.publish(topic, msg, qos=1, retain=True)
                status = result[0]
                if status == 0:
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


def send_line(headers: list, line: str) -> None:
    """send_line"""
    splitted = line.split(",")
    if len(splitted) < len(headers):
        logging.info(f"line does not have all elements: {line}\n{headers}")
        return

    for i in range(len(splitted)):  # pylint:disable=consider-using-enumerate
        send_to_mqtt(headers[i], splitted[i].strip())


def send_monitor_csv_line_to_mqtt(line: str) -> None:
    """send_monitor_csv_line_to_mqtt"""
    if SEND_TO_MQTT:
        send_line(ITEMS_MONITOR_CSV, line)


def send_tripinfo_line_to_mqtt(line: str) -> None:
    """send_tripinfo_line_to_mqtt"""
    if SEND_TO_MQTT:
        send_line(ITEMS_MONITOR_TRIPINFO_CSV, line)


def send_dailystats_line_to_mqtt(line: str) -> None:
    """send_dailystats_line_to_mqtt"""
    if SEND_TO_MQTT:
        send_line(ITEMS_MONITOR_DAILYSTATS_CSV, line)
