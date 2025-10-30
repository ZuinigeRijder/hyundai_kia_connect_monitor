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
# pylint:disable=logging-fstring-interpolation,logging-not-lazy
from os import path
import re
import subprocess
import sys
import io
import configparser
import traceback
import logging
import logging.config
from pathlib import Path
from datetime import datetime, timedelta
import typing
from hyundai_kia_connect_api import VehicleManager, Vehicle, exceptions
from monitor_utils import (
    add_months,
    arg_has,
    dbg,
    die,
    float_to_string_no_trailing_zero,
    get,
    get_bool,
    get_filepath,
    get_last_line,
    get_safe_bool,
    get_safe_datetime,
    get_safe_float,
    km_to_mile,
    same_day,
    set_dbg,
    set_vin,
    sleep_a_minute,
    sleep_seconds,
    to_int,
)

from mqtt_utils import (
    send_dailystats_csv_line_to_mqtt,
    send_monitor_csv_line_to_mqtt,
    send_tripinfo_csv_line_to_mqtt,
    stop_mqtt,
)
from domoticz_utils import (
    send_dailystats_csv_line_to_domoticz,
    send_monitor_csv_line_to_domoticz,
    send_tripinfo_csv_line_to_domoticz,
)

SCRIPT_DIRNAME = path.abspath(path.dirname(__file__))
logging.config.fileConfig(f"{SCRIPT_DIRNAME}/logging_config.ini")
D = arg_has("debug")
if D:
    set_dbg()

# keep forceupdate and cacheupdate as keyword, but do nothing with them
KEYWORD_LIST = ["forceupdate", "cacheupdate", "debug", "test"]
KEYWORD_ERROR = False
for kindex in range(1, len(sys.argv)):
    if sys.argv[kindex].lower() not in KEYWORD_LIST:
        print("Unknown keyword: " + sys.argv[kindex])
        KEYWORD_ERROR = True

if KEYWORD_ERROR or arg_has("help"):
    die("Usage: python monitor.py")

TEST = arg_has("test")
# == read monitor in monitor.cfg ===========================
parser = configparser.ConfigParser()
parser.read(get_filepath("monitor.cfg"))
monitor_settings = dict(parser.items("monitor", raw=True))

REGION = monitor_settings["region"]
BRAND = monitor_settings["brand"]
USERNAME = monitor_settings["username"]
PASSWORD = monitor_settings["password"]
PIN = monitor_settings["pin"]
USE_GEOCODE = get_bool(monitor_settings, "use_geocode", False)
USE_GEOCODE_EMAIL = get_bool(monitor_settings, "use_geocode_email", False)
GEOCODE_PROVIDER = to_int(
    get(monitor_settings, "geocode_provider", "1")
)  # 1=OPENSTREETMAP 2=GOOGLE
if GEOCODE_PROVIDER < 1 or GEOCODE_PROVIDER > 2:
    die("Invalid GEOCODE_PROVIDER in monitor.cfg, expected 1 or 2")

GOOGLE_API_KEY = get(monitor_settings, "google_api_key", "")
if len(GOOGLE_API_KEY) == 0:
    GOOGLE_API_KEY = None  # default no API key needed for OPENSTREETMAP

if GEOCODE_PROVIDER == 2 and GOOGLE_API_KEY is None:
    die("Missing GOOGLE_API_KEY in monitor.cfg")

LANGUAGE = monitor_settings["language"]
ODO_METRIC = get(monitor_settings, "odometer_metric", "km").lower()
MONITOR_INFINITE = get_bool(monitor_settings, "monitor_infinite", False)
MONITOR_INFINITE_INTERVAL_MINUTES = to_int(
    get(monitor_settings, "monitor_infinite_interval_minutes", "60")
)
MONITOR_EXECUTE_COMMANDS_WHEN_SOMETHING_WRITTEN_OR_ERROR = get(
    monitor_settings, "monitor_execute_commands_when_something_written_or_error", ""
)

MONITOR_FORCE_SYNC_WHEN_ODOMETER_DIFFERENT_LOCATION_WORKAROUND = get_bool(
    monitor_settings,
    "monitor_force_sync_when_odometer_different_location_workaround",
    False,
)
MONITOR_FORCE_SYNC_MAX_COUNT = to_int(
    get(
        monitor_settings,
        "monitor_force_sync_max_count",
        "10",
    )
)
MONITOR_FORCE_SYNC_COUNT = 0


MONITOR_SOMETHING_WRITTEN_OR_ERROR = False


def writeln(filename: str, string: str) -> None:
    """append line at monitor text file with end of line character"""
    global MONITOR_SOMETHING_WRITTEN_OR_ERROR  # pylint:disable=global-statement
    _ = D and dbg(string)
    monitor_csv_file = Path(filename)
    write_header = False
    # create header if file does not exists
    if not monitor_csv_file.is_file():
        monitor_csv_file.touch()
        write_header = True
    with monitor_csv_file.open("a", encoding="utf-8") as file:
        if write_header:
            file.write(
                "datetime, longitude, latitude, engineOn, 12V%, odometer, SOC%, charging, plugged, address, EV range\n"  # noqa
            )
        file.write(string)
        file.write("\n")
        MONITOR_SOMETHING_WRITTEN_OR_ERROR = True


def to_miles_needed(vehicle: Vehicle) -> bool:
    """to_miles_needed"""
    return ODO_METRIC == "mi" and vehicle.odometer_unit == "km"


def handle_daily_stats(vehicle: Vehicle, number_of_vehicles: int) -> None:
    """handle daily stats"""
    global MONITOR_SOMETHING_WRITTEN_OR_ERROR  # pylint:disable=global-statement
    daily_stats = vehicle.daily_stats
    if len(daily_stats) == 0:
        _ = D and dbg("No daily stats")
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
            file.write(
                "date, distance, distance_unit, total_consumed, regenerated_energy, engine_consumption, climate_consumption, onboard_electronics_consumption, battery_care_consumption\n"  # noqa
            )
        usa = int(REGION) == 3
        today_time_str = datetime.now().strftime("%H:%M")
        last_line = get_last_line(Path(filename))
        last_line_file = last_line
        last_date = last_line.split(",")[0].strip()  # get yyymmdd hh:mm
        if not usa:
            # get rid of timestamp, always write new cumulative data from today
            last_date = last_date.split(" ")[0].strip()
        last_line = re.sub("^[^,]*,", "", last_line).strip()  # get rid of first column
        _ = D and dbg(f"daily_stats: {daily_stats}")
        i = len(daily_stats)
        while i > 0:
            i = i - 1
            stat = daily_stats[i]
            if usa:
                # write new (non-cumulative) data from today
                dailystats_date = stat.date.strftime("%Y%m%d %H:%M")
            else:
                # always write new cumulative data from today
                dailystats_date = stat.date.strftime("%Y%m%d")
            if D:
                print(
                    f"{i} dailystats_date:[{dailystats_date}] [{last_date}] {stat}"  # noqa
                )
            if dailystats_date >= last_date:
                # only append not already written daily stats
                distance = float(stat.distance)
                distance_unit = vehicle.odometer_unit
                if to_miles_needed(vehicle):
                    distance = km_to_mile(distance)
                    distance_unit = ODO_METRIC
                line = f"{float_to_string_no_trailing_zero(distance)}, {distance_unit}, {stat.total_consumed}, {stat.regenerated_energy},  {stat.engine_consumption}, {stat.climate_consumption}, {stat.onboard_electronics_consumption}, {stat.battery_care_consumption}"  # noqa
                if dailystats_date > last_date or last_line != line:
                    if not usa:
                        # use request time to keep track of updates
                        dailystats_date = f"{dailystats_date} {today_time_str}"

                    full_line = f"{dailystats_date}, {line}"
                    if D:
                        print(
                            f"Writing dailystats {dailystats_date} {last_date}\nflin=[{full_line}]\nline=[{line}]\nlast=[{last_line}]"  # noqa
                        )

                    MONITOR_SOMETHING_WRITTEN_OR_ERROR = True
                    if TEST:
                        send_dailystats_csv_line_to_mqtt(last_line_file)
                        send_dailystats_csv_line_to_domoticz(last_line_file)
                    else:
                        file.write(full_line)
                        file.write("\n")
                        send_dailystats_csv_line_to_mqtt(full_line)
                        send_dailystats_csv_line_to_domoticz(full_line)

                    last_line = line

                else:
                    if D:
                        print(
                            f"Skipping dailystats: date=[{dailystats_date}]\nlast=[{last_line}]\nline=[{line}]"  # noqa
                        )
            else:
                if D:
                    print(
                        f"Skipping dailystats: [{dailystats_date}] [{last_line}]"
                    )  # noqa


def write_last_run(
    vehicle: Vehicle, number_of_vehicles: int, vehicle_stats: list[str]
) -> None:
    """write last run"""
    if TEST:  # do not write last run
        return
    filename = "monitor.lastrun"
    vin = vehicle.VIN
    if number_of_vehicles > 1:
        filename = "monitor." + vin + ".lastrun"
    lastrun_file = Path(filename)
    with lastrun_file.open("w", encoding="utf-8") as file:
        now_string = datetime.now().strftime("%Y-%m-%d %H:%M %a")
        last_updated_at = vehicle_stats[0].split("+")[0]
        location_last_updated_at = vehicle_stats[1].split("+")[0]
        last_line = vehicle_stats[2]
        today_daily_stats_line = vehicle_stats[3]

        file.write(f"last run      ; {now_string}\n")
        file.write(f"vin           ; {vin}\n")
        file.write(f"vehicle update; {last_updated_at}\n")
        file.write(f"gps update    ; {location_last_updated_at}\n")
        file.write(f"{last_line}\n")
        file.write(f"{today_daily_stats_line}\n")


def append_error_to_last_run(error_string: str) -> None:
    """append error to last run"""
    filename = "monitor.lastrun"
    if MANAGER and MANAGER.vehicles and len(MANAGER.vehicles) > 1:
        filename = "monitor." + MANAGER.vehicles[0].VIN + ".lastrun"
    lastrun_file = Path(filename)
    with lastrun_file.open("a", encoding="utf-8") as file:
        file.write(f"{error_string}\n")


def handle_day_trip_info(
    manager: VehicleManager,
    vehicle: Vehicle,
    file: io.TextIOWrapper,
    month_trip_info,
    last_date: str,
    last_hhmmss: str,
    last_line: str,
) -> tuple[str, str]:
    """handle_day_trip_info"""
    global MONITOR_SOMETHING_WRITTEN_OR_ERROR  # pylint:disable=global-statement
    for day in month_trip_info.day_list:
        yyyymmdd = day.yyyymmdd
        if yyyymmdd >= last_date:
            _ = D and dbg(f"update_day_trip_info: {yyyymmdd}")
            manager.update_day_trip_info(vehicle.id, yyyymmdd)
            day_trip_info = vehicle.day_trip_info
            if day_trip_info is not None:
                _ = D and dbg(f"day_trip_info: {day_trip_info}")
                for trip in reversed(day_trip_info.trip_list):
                    if D:
                        print(
                            f"{yyyymmdd},{trip.hhmmss},{trip.drive_time},{trip.idle_time},{trip.distance},{trip.avg_speed},{trip.max_speed}"  # noqa
                        )
                    hhmmss = trip.hhmmss
                    if yyyymmdd > last_date or hhmmss > last_hhmmss:
                        distance = float(trip.distance)
                        avg_speed = float(trip.avg_speed)
                        max_speed = float(trip.max_speed)
                        if to_miles_needed(vehicle):
                            distance = km_to_mile(distance)
                            avg_speed = km_to_mile(avg_speed)
                            max_speed = km_to_mile(max_speed)
                        line = f"{yyyymmdd},{hhmmss},{trip.drive_time},{trip.idle_time},{float_to_string_no_trailing_zero(distance)},{avg_speed:.0f},{max_speed:.0f}"  # noqa
                        _ = D and dbg(f"Writing tripinfo line:[{line}]")
                        MONITOR_SOMETHING_WRITTEN_OR_ERROR = True
                        if TEST:
                            send_tripinfo_csv_line_to_mqtt(last_line)
                            send_tripinfo_csv_line_to_domoticz(last_line)
                        else:
                            file.write(line)
                            file.write("\n")
                            send_tripinfo_csv_line_to_mqtt(line)
                            send_tripinfo_csv_line_to_domoticz(line)

                        last_date = yyyymmdd
                        last_hhmmss = hhmmss
                    else:
                        _ = D and dbg(f"Skipping trip: {yyyymmdd},{hhmmss}")
            else:
                _ = D and dbg(f"Empty day_trip_info: {yyyymmdd}")
        else:
            _ = D and dbg(f"Skipping written tripinfo day: {yyyymmdd}")
    return last_date, last_hhmmss


def handle_trip_info(
    manager: VehicleManager, vehicle: Vehicle, number_of_vehicles: int
) -> None:
    """Handle trip info"""
    now = datetime.now()
    filename = "monitor.tripinfo.csv"
    if number_of_vehicles > 1:
        filename = "monitor.tripinfo." + vehicle.VIN + ".csv"
    write_header = False  # create header if file does not exists
    monitor_tripinfo_csv_file = Path(filename)
    if not monitor_tripinfo_csv_file.is_file():
        monitor_tripinfo_csv_file.touch()
        write_header = True
    last_line = get_last_line(Path(filename))
    last_date = last_line.split(",")[0].strip().split(" ")[0].strip()
    last_line_splitted = last_line.split(",")
    last_hhmmss = "000000"
    if len(last_line_splitted) > 6 and "Date," not in last_line:
        last_hhmmss = last_line_splitted[1]
    with monitor_tripinfo_csv_file.open("a", encoding="utf-8") as file:
        from_month = now  # default only get the current month statistics
        if write_header:
            file.write(
                "Date, Start time, Drive time, Idle time, Distance, Avg speed, Max speed\n"  # noqa
            )
            # only last 4 months can be retrieved
            # only fill when header is written
            # because for each day with trips an API call will be made
            from_month = add_months(now, -3)
        else:
            if now.day == 1:  # first day of month also retrieve previous month
                from_month = add_months(now, -1)

        while from_month <= now:
            yyyymm = from_month.strftime("%Y%m")
            from_month = add_months(from_month, 1)
            _ = D and dbg(f"update_month_trip_info: {yyyymm}")
            manager.update_month_trip_info(vehicle.id, yyyymm)
            month_trip_info = vehicle.month_trip_info
            if month_trip_info is not None:
                _ = D and dbg(f"month_trip_info: {month_trip_info}")
                last_date, last_hhmmss = handle_day_trip_info(
                    manager,
                    vehicle,
                    file,
                    month_trip_info,
                    last_date,
                    last_hhmmss,
                    last_line,
                )


def get_odometer_str(vehicle: Vehicle) -> str:
    """get odometer string"""
    odometer = vehicle.odometer
    if odometer is None:
        odometer = 0.0
    if to_miles_needed(vehicle):
        odometer = km_to_mile(odometer)
    odometer_str = f"{float_to_string_no_trailing_zero(odometer)}"
    return odometer_str


def handle_one_vehicle(
    manager: VehicleManager, vehicle_id: str, number_of_vehicles: int
) -> bool:
    """handle one vehicle and return if error occurred"""
    global MONITOR_FORCE_SYNC_COUNT  # pylint:disable=global-statement
    vehicle: Vehicle = MANAGER.vehicles[vehicle_id]
    try:
        handle_trip_info(manager, vehicle, number_of_vehicles)
    except Exception as ex:  # pylint: disable=broad-except
        logging.warning("Warning: handle_trip_info Exception: " + str(ex))
        traceback.print_exc()

    filename = "monitor.csv"
    if number_of_vehicles > 1:
        filename = "monitor." + vehicle.VIN + ".csv"
    prev_line = get_last_line(Path(filename)).strip()
    list_prev_line = prev_line.split(",")

    location_last_updated_at = get_safe_datetime(
        vehicle.location_last_updated_at, vehicle.timezone
    )
    vehicle_last_updated_at = get_safe_datetime(
        vehicle.last_updated_at, vehicle.timezone
    )
    dates = [vehicle_last_updated_at, location_last_updated_at]
    last_updated_at = max(dates)

    # workaround for location is not updated anymore since may 2025
    # force sync when odometer is different when configured
    odometer_str = get_odometer_str(vehicle)
    if (
        MONITOR_INFINITE
        and MONITOR_FORCE_SYNC_WHEN_ODOMETER_DIFFERENT_LOCATION_WORKAROUND
        and MONITOR_FORCE_SYNC_COUNT < MONITOR_FORCE_SYNC_MAX_COUNT
        and len(list_prev_line) == 11
        and odometer_str != list_prev_line[5].strip()
    ):  # odometer different
        MONITOR_FORCE_SYNC_COUNT += 1
        logging.info(
            f"Forced sync, new odometer=[{odometer_str}], old_odometer=[{list_prev_line[5].strip()}]"  # noqa
        )
        logging.info(f"org={vehicle.geocode}")  # noqa
        MANAGER.force_refresh_all_vehicles_states()  # forced sync always
        MANAGER.update_all_vehicles_with_cached_state()  # needed >= 2.0.0
        vehicle = MANAGER.vehicles[vehicle_id]
        logging.info(f"upd={vehicle.geocode}")  # noqa
        _ = D and dbg(f"prev={prev_line}")
        # newest odometer, keep last_updated_at, because force sync changes the latter
        odometer_str = get_odometer_str(vehicle)

    geocode = ""
    if USE_GEOCODE:
        if len(vehicle.geocode) > 0:
            # replace comma by semicolon for easier splitting
            geocode_name = vehicle.geocode[0]
            if geocode_name is not None and geocode_name != "":
                geocode = geocode_name.replace(",", ";")

    location_longitude = get_safe_float(vehicle.location_longitude)
    location_latitude = get_safe_float(vehicle.location_latitude)

    ev_driving_range = to_int(f"{vehicle.ev_driving_range}")

    # server cache last_updated_at sometimes shows 2 (timezone) hours difference
    # https://github.com/Hyundai-Kia-Connect/kia_uvo/issues/931#issuecomment-2381025284
    if len(list_prev_line) == 11:
        # convert timezone string to datetime and see if it is in utcoffset range
        previous_updated_at_string = list_prev_line[0]  # get datetime
        if (
            len(previous_updated_at_string) == 25
        ):  # datetime string must be 25 in length
            previous_updated_at = datetime.strptime(
                previous_updated_at_string, "%Y-%m-%d %H:%M:%S%z"
            )
            if last_updated_at < previous_updated_at:
                utcoffset = last_updated_at.utcoffset()
                if utcoffset:
                    newest_updated_at_corrected = last_updated_at + utcoffset
                    if newest_updated_at_corrected >= previous_updated_at:
                        _ = D and dbg(
                            f"fixed newest_updated_at: old: {last_updated_at} new: {newest_updated_at_corrected} previous: {previous_updated_at}"  # noqa
                        )
                        last_updated_at = newest_updated_at_corrected
                last_updated_at = max(last_updated_at, previous_updated_at)

    ev_battery_percentage = vehicle.ev_battery_percentage
    if ev_battery_percentage is None:
        ev_battery_percentage = 100
    ev_battery_is_charging = get_safe_bool(vehicle.ev_battery_is_charging)
    ev_battery_is_plugged_in = get_safe_bool(vehicle.ev_battery_is_plugged_in)

    line = f"{last_updated_at}, {location_longitude}, {location_latitude}, {vehicle.engine_is_running}, {vehicle.car_battery_percentage}, {odometer_str}, {ev_battery_percentage}, {ev_battery_is_charging}, {ev_battery_is_plugged_in}, {geocode}, {ev_driving_range}"  # noqa
    if "None, None" in line:  # something gone wrong, retry
        logging.warning(f"Skipping Unexpected line: {line}")
        return True  # exit subroutine with error

    if line != prev_line:
        # check if everything is the same without timestamp and address
        # seems that the server sometimes returns wrong timestamp
        list_current_line = line.split(",")
        same = False
        if len(list_current_line) == 11 and len(list_prev_line) == 11:
            same = True
            for index, value in enumerate(list_current_line):
                if index != 0 and index != 9 and value != list_prev_line[index]:
                    # excluded last_updated_at and geocode
                    same = False
                    break  # finished
        if not same:
            logging.info("Writing monitor.csv line")
            logging.info(f"curr={line}")
            _ = D and dbg(f"prev={prev_line}")
            _ = D and dbg(f"newest: {last_updated_at} from {dates}")
            if TEST:
                send_monitor_csv_line_to_mqtt(prev_line)
                send_monitor_csv_line_to_domoticz(prev_line)
            else:
                send_monitor_csv_line_to_mqtt(line)
                send_monitor_csv_line_to_domoticz(line)
            writeln(filename, line)

    handle_daily_stats(vehicle, number_of_vehicles)
    vehicle_stats = [
        str(vehicle_last_updated_at),
        str(location_last_updated_at),
        line,
        "",
    ]
    write_last_run(vehicle, number_of_vehicles, vehicle_stats)
    return False


def handle_exception(ex: Exception, retries: int, stacktrace=False) -> tuple[int, str]:
    """
    If an error is found, an exception is raised.
    retCode known values:
    - S: success
    - F: failure
    resCode / resMsg known values:
    - 0000: no error
    - 4004: "Duplicate request"
    - 4081: "Request timeout"
    - 5031: "Unavailable remote control - Service Temporary Unavailable"
    - 5091: "Exceeds number of requests"
    - 5921: "No Data Found v2 - No Data Found v2"
    - 9999: "Undefined Error - Response timeout"
    """
    exception_str = str(ex)
    error_string = f"Exception: {exception_str}"
    logging.warning(error_string)
    if stacktrace and "Service Temporary Unavailable" not in exception_str:
        traceback.print_exc()
    retries = sleep_a_minute(retries)
    return retries, error_string


def run_commands():
    """run_commands"""
    commands = MONITOR_EXECUTE_COMMANDS_WHEN_SOMETHING_WRITTEN_OR_ERROR.split(";")
    count = 0
    for command in commands:
        count += 1
        command = command.strip()
        if len(command) > 0:
            _ = D and dbg(f"full command: {command}")
            output_filename = f"command{count}.log"
            open_mode = "w"
            if ">>" in command:  # append to file
                open_mode = "a"
                command = command.replace(">>", ">")
            if ">" in command:  # write to file
                splitted = command.split(">")
                command = splitted[0].strip()
                output_filename = splitted[1].strip()
            _ = D and dbg(f"command: {command}")
            _ = D and dbg(f"output_filename: {output_filename}")
            _ = D and dbg(f"open_mode: {open_mode}")
            returncode = 0
            try:
                with open(output_filename, open_mode, encoding="utf-8") as outfile:
                    process = subprocess.run(
                        command,
                        check=True,
                        shell=True,
                        stderr=subprocess.STDOUT,
                        stdout=outfile,
                    )
                returncode = process.returncode
                if returncode != 0:
                    logging.error(
                        f"Error in running {command}: returncode {returncode}"
                    )

            except Exception as ex:  # pylint: disable=broad-except
                returncode = 112
                (_, error_string) = handle_exception(ex, 1, True)
                logging.error(f"Error in running {command}: {error_string}")

            if returncode == 112:
                die("Unexpected end of subprocess")


# get MANAGER only once
MANAGER: typing.Union[VehicleManager, None] = None


def handle_vehicles(login: bool) -> bool:
    """handle vehicles"""
    global MANAGER, MONITOR_SOMETHING_WRITTEN_OR_ERROR  # pylint:disable=global-statement  # noqa
    retries = 15  # retry for maximum of 15 minutes (15 x 60 seconds sleep)
    while retries > 0:
        error_string = ""
        try:
            if login:
                logging.info("Login using VehicleManager")
                # get information and add to comma separated file
                MANAGER = VehicleManager(
                    region=int(REGION),
                    brand=int(BRAND),
                    username=USERNAME,
                    password=PASSWORD,
                    pin=PIN,
                    geocode_api_enable=USE_GEOCODE,
                    geocode_api_use_email=USE_GEOCODE_EMAIL,
                    geocode_provider=GEOCODE_PROVIDER,
                    geocode_api_key=GOOGLE_API_KEY,
                    language=LANGUAGE,
                )

            if MANAGER:
                MANAGER.check_and_refresh_token()
                MANAGER.update_all_vehicles_with_cached_state()  # needed >= 2.0.0
                error = False
                number_of_vehicles = len(MANAGER.vehicles)
                for vehicle_id, vehicle in MANAGER.vehicles.items():
                    if TEST:  # use fake VIN
                        set_vin("KMHKR81CPNU012345")
                    else:
                        set_vin(vehicle.VIN)
                    try:
                        error = handle_one_vehicle(
                            MANAGER, vehicle_id, number_of_vehicles
                        )
                    except Exception as ex_one_vehicle:  # pylint: disable=broad-except
                        logging.error(f"handle_one_vehicle exception: {ex_one_vehicle}")
                        error = True
                    if error:  # something gone wrong, exit vehicles loop
                        error_string = "Error occurred in handle_one_vehicle()"
                        break

            if error or MANAGER is None:  # something gone wrong, retry
                retries = sleep_a_minute(retries)
            else:
                retries = -1  # successfully end while loop without error
        except exceptions.AuthenticationError as ex:
            (retries, error_string) = handle_exception(ex, retries)
        except exceptions.RateLimitingError as ex:
            (retries, error_string) = handle_exception(ex, retries)
        except exceptions.NoDataFound as ex:
            (retries, error_string) = handle_exception(ex, retries)
        except exceptions.DuplicateRequestError as ex:
            (retries, error_string) = handle_exception(ex, retries)
        except exceptions.RequestTimeoutError as ex:
            (retries, error_string) = handle_exception(ex, retries)
        # Not yet available, so workaround for now in handle_exception
        # except exceptions.ServiceTemporaryUnavailable as ex:
        #    retries = handle_exception(ex, retries)
        except exceptions.InvalidAPIResponseError as ex:
            (retries, error_string) = handle_exception(ex, retries, True)
        except exceptions.APIError as ex:
            (retries, error_string) = handle_exception(ex, retries, True)
        except exceptions.HyundaiKiaException as ex:
            (retries, error_string) = handle_exception(ex, retries, True)
        except Exception as ex:  # pylint: disable=broad-except
            (retries, error_string) = handle_exception(ex, retries, True)

    error = retries != -1
    if error:
        logging.error(error_string)
        MONITOR_SOMETHING_WRITTEN_OR_ERROR = True  # indicate error
        try:
            append_error_to_last_run(error_string)
        except Exception as ex:  # pylint: disable=broad-except
            (retries, error_string) = handle_exception(ex, retries, True)

    return error


def monitor():
    """monitor"""
    global MONITOR_SOMETHING_WRITTEN_OR_ERROR, MONITOR_FORCE_SYNC_COUNT  # pylint:disable=global-statement  # noqa
    current_time = datetime.now()
    prev_time = current_time - timedelta(days=1.0)  # once per day login
    not_done_once = True
    error_count = 1
    while not_done_once or MONITOR_INFINITE:
        not_done_once = False
        current_time = datetime.now()
        # login when 4x15 minutes subsequent errors or once at beginning of new day
        login = (error_count % 4 == 0) or not same_day(prev_time, current_time)
        MONITOR_SOMETHING_WRITTEN_OR_ERROR = False
        error = handle_vehicles(login)
        if error:
            logging.error(f"error count: {error_count}")
            error_count += 1
            logging.info("Sleeping a minute")
            sleep_seconds(60)
        else:
            error_count = 1
        if (len(MONITOR_EXECUTE_COMMANDS_WHEN_SOMETHING_WRITTEN_OR_ERROR) > 0) and (
            login or MONITOR_SOMETHING_WRITTEN_OR_ERROR
        ):
            logging.info(
                "New data added or first run today or errors, running configured commands"  # noqa
            )
            run_commands()

        if MONITOR_INFINITE:
            if not same_day(prev_time, current_time):
                MONITOR_FORCE_SYNC_COUNT = (
                    0  # start fresh force sync count when configured
                )
            prev_time = current_time

            # calculate number of seconds to sleep
            next_time = prev_time + timedelta(minutes=MONITOR_INFINITE_INTERVAL_MINUTES)
            current_time = datetime.now()
            delta = next_time - current_time
            total_seconds = delta.total_seconds()
            if total_seconds > 0:
                sleep_seconds(total_seconds)

        if error_count > 96:  # more than 24 hours subsequnt errors
            die("Too many subsequent errors occurred, exiting monitor.py")

    stop_mqtt()
    sys.exit(0)


monitor()
