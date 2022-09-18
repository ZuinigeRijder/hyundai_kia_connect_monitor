# == monitor.py Author: Zuinige Rijder ==============================
"""
Simple Python3 script to monitor values of hyundai_kia_connect_api
https://github.com/Hyundai-Kia-Connect/hyundai_kia_connect_api

Following information is added to the monitor.csv file:
- datetime
- longitude
- latitude
- engineOn
- 12V%
- odometer
- SOC%
- charging
- plugged

Run this script e.g. once per hour (I use it on a Raspberry Pi)
and you can always check:
- odometer at specific day/hour
- where you have been at a specific day/hour
- when you have charged and how much
- see your 12 volt battery percentage fluctuation

Idea is that thereafter you can analyze the information over time,
e.g. with Excel:
- odometer over time
- average drive per day/week/month over time
- SOC over time
- 12V battery over time
- charging pattern over time
- visited places
"""
import configparser
import traceback
import time
from pathlib import Path
from hyundai_kia_connect_api import VehicleManager

MFILE = Path("monitor.csv")

# == read monitor in monitor.cfg ===========================
parser = configparser.ConfigParser()
parser.read('monitor.cfg')
monitor_settings = dict(parser.items('monitor'))

REGION = monitor_settings['region']
BRAND = monitor_settings['brand']
USERNAME = monitor_settings['username']
PASSWORD = monitor_settings['password']
PIN = monitor_settings['pin']


def writeln(string):
    """ append line at monitor text file with end of line character """
    with MFILE.open("a", encoding="utf-8") as file:
        file.write(string)
        file.write('\n')


def get_append_data():
    """ get_append_data """
    retries = 10
    while retries > 0:
        try:
            # get information and add to comma separated file
            manager = VehicleManager(
                region=int(REGION),
                brand=int(BRAND),
                username=USERNAME,
                password=PASSWORD,
                pin=PIN
            )
            manager.check_and_refresh_token()
            manager.check_and_force_update_vehicles(600)
            # vm.update_all_vehicles_with_cached_state()

            for _, vehicle in manager.vehicles.items():
                writeln(
                    str(vehicle.last_updated_at) +
                    ', ' + str(vehicle.location_longitude) +
                    ', ' + str(vehicle.location_latitude) +
                    ', ' + str(vehicle.engine_is_running) +
                    ', ' + str(vehicle.car_battery_percentage) +
                    ', ' + str(vehicle.odometer) +
                    ', ' + str(vehicle.ev_battery_percentage) +
                    ', ' + str(vehicle.ev_battery_is_charging) +
                    ', ' + str(vehicle.ev_battery_is_plugged_in)
                )
            retries = 0  # successfully end while loop
        except Exception:  # pylint: disable=broad-except
            traceback.print_exc()
            retries -= 1
            print("Sleeping a minute")
            time.sleep(60)


# create header if file does not exists
if not MFILE.is_file():
    MFILE.touch()
    writeln(
        "datetime, longitude, latitude, engineOn" +
        ", 12V%, odometer, SOC%, charging, plugged"
    )
get_append_data()  # do the work
