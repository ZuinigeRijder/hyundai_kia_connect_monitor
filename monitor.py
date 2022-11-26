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
import sys
import configparser
import traceback
import time
from datetime import datetime
from pathlib import Path
from hyundai_kia_connect_api import VehicleManager


# == arg_has =================================================================
def arg_has(string):
    """ arguments has string """
    for i in range(1, len(sys.argv)):
        if sys.argv[i].lower() == string:
            return True

    return False


KEYWORD_LIST = ['forceupdate', 'cacheupdate', 'debug']
KEYWORD_ERROR = False
for kindex in range(1, len(sys.argv)):
    if not sys.argv[kindex].lower() in KEYWORD_LIST:
        print("Unknown keyword: " + sys.argv[kindex])
        KEYWORD_ERROR = True

if KEYWORD_ERROR or arg_has('help'):
    print('Usage: python monitor.py [forceupdate|cacheupdate]')
    exit()

DEBUG = arg_has('debug')
FORCEUPDATE = arg_has('forceupdate')
CACHEUPDATE = arg_has('cacheupdate')

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
FORCE_SECONDS = int(monitor_settings['force_update_seconds'])
USE_GEOCODE = monitor_settings['use_geocode'].lower() == 'true'
USE_GEOCODE_EMAIL = monitor_settings['use_geocode_email'].lower() == 'true'


# == subroutines =============================================================
def debug(line):
    """ print line if debugging """
    if DEBUG:
        print(datetime.now().strftime("%Y%m%d %H:%M:%S") + ': ' + line)


def log(msg):
    """log a message prefixed with a date/time format yyyymmdd hh:mm:ss"""
    print(datetime.now().strftime("%Y%m%d %H:%M:%S") + ': ' + msg)


def writeln(string):
    """ append line at monitor text file with end of line character """
    debug(string)
    with MFILE.open("a", encoding="utf-8") as file:
        file.write(string)
        file.write('\n')


def get_append_data():
    """ get_append_data """
    retries = 2
    while retries > 0:
        try:
            # get information and add to comma separated file
            manager = VehicleManager(
                region=int(REGION),
                brand=int(BRAND),
                username=USERNAME,
                password=PASSWORD,
                pin=PIN,
                geocode_api_enable=USE_GEOCODE,
                geocode_api_use_email=USE_GEOCODE_EMAIL
            )
            manager.check_and_refresh_token()
            if CACHEUPDATE:
                debug("CACHEUPDATE")
                manager.update_all_vehicles_with_cached_state()
            elif FORCEUPDATE:
                debug("FORCEUPDATE")
                manager.check_and_force_update_vehicles(600)
            else:
                debug(f"check_and_force_update_vehicles: {FORCE_SECONDS}")
                manager.check_and_force_update_vehicles(FORCE_SECONDS)

            for _, vehicle in manager.vehicles.items():
                geocode = ''
                if USE_GEOCODE:
                    if len(vehicle.geocode) > 0:
                        # replace comma by semicolon for easier splitting
                        geocode = ', ' + vehicle.geocode[0].replace(',', ';')

                writeln(
                    str(vehicle.last_updated_at) +
                    ', ' + str(vehicle.location_longitude) +
                    ', ' + str(vehicle.location_latitude) +
                    ', ' + str(vehicle.engine_is_running) +
                    ', ' + str(vehicle.car_battery_percentage) +
                    ', ' + str(vehicle.odometer) +
                    ', ' + str(vehicle.ev_battery_percentage) +
                    ', ' + str(vehicle.ev_battery_is_charging) +
                    ', ' + str(vehicle.ev_battery_is_plugged_in) +
                    geocode
                )
            retries = 0  # successfully end while loop
        except Exception as ex:  # pylint: disable=broad-except
            log('Exception: ' + str(ex))
            traceback.print_exc()
            retries -= 1
            log("Sleeping a minute")
            time.sleep(60)


# create header if file does not exists
if not MFILE.is_file():
    MFILE.touch()
    writeln(
        "datetime, longitude, latitude, engineOn" +
        ", 12V%, odometer, SOC%, charging, plugged, address"
    )
get_append_data()  # do the work
