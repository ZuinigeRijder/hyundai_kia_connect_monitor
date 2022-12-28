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
import os
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
    if sys.argv[kindex].lower() not in KEYWORD_LIST:
        print("Unknown keyword: " + sys.argv[kindex])
        KEYWORD_ERROR = True

if KEYWORD_ERROR or arg_has('help'):
    print('Usage: python monitor.py [forceupdate|cacheupdate]')
    exit()

DEBUG = arg_has('debug')
FORCEUPDATE = arg_has('forceupdate')
CACHEUPDATE = arg_has('cacheupdate')


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
LANGUAGE = monitor_settings['language']


# == subroutines =============================================================
def debug(line):
    """ print line if debugging """
    if DEBUG:
        print(datetime.now().strftime("%Y%m%d %H:%M:%S") + ': ' + line)


def log(msg):
    """log a message prefixed with a date/time format yyyymmdd hh:mm:ss"""
    print(datetime.now().strftime("%Y%m%d %H:%M:%S") + ': ' + msg)


def writeln(filename, string):
    """ append line at monitor text file with end of line character """
    debug(string)
    monitor_csv_file = Path(filename)
    write_header = False
    # create header if file does not exists
    if not monitor_csv_file.is_file():
        monitor_csv_file.touch()
        write_header = True
    with monitor_csv_file.open("a", encoding="utf-8") as file:
        if write_header:
            file.write("datetime, longitude, latitude, engineOn, 12V%, odometer, SOC%, charging, plugged, address, EV range\n")  # noqa pylint:disable=line-too-long
        file.write(string)
        file.write('\n')


def get_last_line(filename):
    """ get last line of filename """
    with open(filename, "rb") as file:
        try:
            file.seek(-2, os.SEEK_END)
            while file.read(1) != b'\n':
                file.seek(-2, os.SEEK_CUR)
        except OSError:
            file.seek(0)
        last_line = file.readline().decode().strip()
        debug(f"{filename} last_line: [{last_line}]")
        return last_line


def get_last_date(last_line):
    """ get last date of last_line """
    last_date = '20000101'  # millenium
    if last_line.startswith("20"):  # year starts with 20
        last_date = last_line.split(',')[0].strip()
    debug(f"{last_line} last_date: [{last_date}]")
    return last_date


def handle_daily_stats(vehicle, number_of_vehicles):
    """ handle daily stats """
    daily_stats = vehicle.daily_stats
    if len(daily_stats) == 0:
        debug("No daily stats")
        return

    filename = "monitor.dailystats.csv"
    if number_of_vehicles > 1:
        filename = "monitor.dailystats." + vehicle.VIN + ".csv"
    dailystats_file = Path(filename)
    write_header = False
    # create header if file does not exists
    if not dailystats_file.is_file():
        dailystats_file.touch()
        write_header = True
    with dailystats_file.open("a", encoding="utf-8") as file:
        if write_header:
            file.write("date, distance, distance_unit, total_consumed, regenerated_energy, engine_consumption, climate_consumption, onboard_electronics_consumption, battery_care_consumption\n")  # noqa pylint:disable=line-too-long
        today = datetime.now().strftime("%Y%m%d")
        last_line = get_last_line(filename)
        last_date = get_last_date(last_line)
        i = len(daily_stats)
        while i > 0:
            i = i - 1
            stat = daily_stats[i]
            dailystats_date = stat.date.strftime("%Y%m%d")
            if today != dailystats_date and dailystats_date >= last_date:
                # only append not already written daily stats and not today
                line = f"{dailystats_date}, {stat.distance}, {stat.distance_unit}, {stat.total_consumed}, {stat.regenerated_energy},  {stat.engine_consumption}, {stat.climate_consumption}, {stat.onboard_electronics_consumption}, {stat.battery_care_consumption}"  # noqa pylint:disable=line-too-long
                if last_line != line:
                    debug(f"Writing dailystats:\nline=[{line}]\nlast=[{last_line}]")  # noqa pylint:disable=line-too-long
                    file.write(line)
                    file.write("\n")
                else:
                    debug(f"Skipping dailystats: date=[{dailystats_date}]\nlast=[{last_line}]\nline=[{line}]")  # noqa pylint:disable=line-too-long
            else:
                debug(f"Skipping dailystats: [{dailystats_date}] [{last_line}]")  # noqa pylint:disable=line-too-long


def write_last_run():
    """ write last run """
    filename = "monitor.lastrun"
    lastrun_file = Path(filename)
    with lastrun_file.open("w", encoding="utf-8") as file:
        file.write(datetime.now().strftime("%Y%m%d %H:%M:%S\n"))


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
                geocode_api_use_email=USE_GEOCODE_EMAIL,
                language=LANGUAGE
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

            line = ''
            number_of_vehicles = len(manager.vehicles)
            for _, vehicle in manager.vehicles.items():
                geocode = ''
                if USE_GEOCODE:
                    if len(vehicle.geocode) > 0:
                        # replace comma by semicolon for easier splitting
                        geocode_name = vehicle.geocode[0]
                        if geocode_name != '':
                            geocode = geocode_name.replace(',', ';')

                line = f"{vehicle.last_updated_at}, {vehicle.location_longitude}, {vehicle.location_latitude}, {vehicle.engine_is_running}, {vehicle.car_battery_percentage}, {vehicle.odometer}, {vehicle.ev_battery_percentage}, {vehicle.ev_battery_is_charging}, {vehicle.ev_battery_is_plugged_in}, {geocode}, {vehicle.ev_driving_range}"   # noqa pylint:disable=line-too-long
                if 'None, None' in line:  # something gone wrong, retry
                    log(f"Skipping Unexpected line: {line}")
                else:
                    filename = "monitor.csv"
                    if number_of_vehicles > 1:
                        filename = "monitor." + vehicle.VIN + ".csv"
                    last_line = get_last_line(filename)
                    last_date = get_last_date(last_line)
                    current_date = line.split(",")[0].strip()
                    debug(f"Current date:          [{current_date}]")
                    if current_date == last_date:
                        if line != last_line:
                            debug(f"Writing1:\nline=[{line}]\nlast=[{last_line}]\ncurrent=[{current_date}]\nlast   =[{last_date}]")  # noqa pylint:disable=line-too-long
                            writeln(filename, line)
                        else:
                            debug(f"Skipping1:\nline=[{line}]\nlast=[{last_line}]")  # noqa pylint:disable=line-too-long
                    else:
                        debug(f"Writing2:\nline=[{line}]\ncurrent=[{current_date}]\nlast   =[{last_date}]")   # noqa pylint:disable=line-too-long
                        writeln(filename, line)
                    handle_daily_stats(vehicle, number_of_vehicles)

            if 'None, None' in line:  # something gone wrong, retry
                retries -= 1
                log("Sleeping a minute")
                time.sleep(60)
            else:
                retries = 0  # successfully end while loop
                write_last_run()
        except Exception as ex:  # pylint: disable=broad-except
            log('Exception: ' + str(ex))
            traceback.print_exc()
            retries -= 1
            log("Sleeping a minute")
            time.sleep(60)


get_append_data()  # do the work
