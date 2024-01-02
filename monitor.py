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
import re
import sys
import io
import configparser
import traceback
import logging
from pathlib import Path
from datetime import datetime
from dateutil.relativedelta import relativedelta
from hyundai_kia_connect_api import VehicleManager, Vehicle, exceptions
from monitor_utils import (
    arg_has,
    get,
    get_last_line,
    get_safe_datetime,
    get_safe_float,
    km_to_mile,
    log,
    sleep,
    to_int,
)


# keep forceupdate and cacheupdate as keyword, but do nothing with them
KEYWORD_LIST = ["forceupdate", "cacheupdate", "debug"]
KEYWORD_ERROR = False
for kindex in range(1, len(sys.argv)):
    if sys.argv[kindex].lower() not in KEYWORD_LIST:
        print("Unknown keyword: " + sys.argv[kindex])
        KEYWORD_ERROR = True

if KEYWORD_ERROR or arg_has("help"):
    print("Usage: python monitor.py")
    exit()

D = arg_has("debug")
if D:
    logging.basicConfig(level=logging.DEBUG)


# == read monitor in monitor.cfg ===========================
parser = configparser.ConfigParser()
parser.read("monitor.cfg")
monitor_settings = dict(parser.items("monitor"))

REGION = monitor_settings["region"]
BRAND = monitor_settings["brand"]
USERNAME = monitor_settings["username"]
PASSWORD = monitor_settings["password"]
PIN = monitor_settings["pin"]
USE_GEOCODE = monitor_settings["use_geocode"].lower() == "true"
USE_GEOCODE_EMAIL = monitor_settings["use_geocode_email"].lower() == "true"
LANGUAGE = monitor_settings["language"]
ODO_METRIC = get(monitor_settings, "odometer_metric", "km").lower()


# == subroutines =============================================================
def dbg(line: str) -> bool:
    """print line if debugging"""
    if D:
        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ": " + line)
    return D  # just to make a lazy evaluation expression possible


def writeln(filename: str, string: str) -> None:
    """append line at monitor text file with end of line character"""
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


def to_miles_needed(vehicle: Vehicle) -> bool:
    """to_miles_needed"""
    return ODO_METRIC == "mi" and vehicle.odometer_unit == "km"


def handle_daily_stats(vehicle: Vehicle, number_of_vehicles: int) -> None:
    """handle daily stats"""
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
        today_time_str = datetime.now().strftime("%H:%M")
        last_line = get_last_line(Path(filename))
        last_date = last_line.split(",")[0].strip().split(" ")[0].strip()
        last_line = re.sub("^[^,]*,", "", last_line).strip()  # get rid of first column
        i = len(daily_stats)
        while i > 0:
            i = i - 1
            stat = daily_stats[i]
            dailystats_date = stat.date.strftime("%Y%m%d")
            if D:
                print(
                    f"{i} dailystats_date:[{dailystats_date}] [{last_date}] {stat}"  # noqa
                )
            if dailystats_date >= last_date:
                # only append not already written daily stats
                distance = float(stat.distance)
                distance_unit = stat.distance_unit
                if to_miles_needed(vehicle):
                    distance = km_to_mile(distance)
                    distance_unit = ODO_METRIC
                    line = f"{distance:.1f}, {distance_unit}, {stat.total_consumed}, {stat.regenerated_energy},  {stat.engine_consumption}, {stat.climate_consumption}, {stat.onboard_electronics_consumption}, {stat.battery_care_consumption}"  # noqa
                else:
                    line = f"{distance:.0f}, {distance_unit}, {stat.total_consumed}, {stat.regenerated_energy},  {stat.engine_consumption}, {stat.climate_consumption}, {stat.onboard_electronics_consumption}, {stat.battery_care_consumption}"  # noqa
                if dailystats_date > last_date or last_line != line:
                    dailystats_date = f"{dailystats_date} {today_time_str}"
                    full_line = f"{dailystats_date}, {line}"
                    if D:
                        print(
                            f"Writing dailystats {dailystats_date} {last_date}\nflin=[{full_line}]\nline=[{line}]\nlast=[{last_line}]"  # noqa
                        )
                    file.write(full_line)
                    file.write("\n")
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


def handle_day_trip_info(
    manager: VehicleManager,
    vehicle: Vehicle,
    file: io.TextIOWrapper,
    month_trip_info,
    last_date: str,
    last_hhmmss: str,
) -> tuple[str, str]:
    """handle_day_trip_info"""
    for day in month_trip_info.day_list:
        yyyymmdd = day.yyyymmdd
        if yyyymmdd >= last_date:
            _ = D and dbg(f"update_day_trip_info: {yyyymmdd}")
            manager.update_day_trip_info(vehicle.id, yyyymmdd)
            day_trip_info = vehicle.day_trip_info
            if day_trip_info is not None:
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
                            line = f"{yyyymmdd},{hhmmss},{trip.drive_time},{trip.idle_time},{distance:.1f},{avg_speed:.0f},{max_speed:.0f}"  # noqa
                        else:
                            line = f"{yyyymmdd},{hhmmss},{trip.drive_time},{trip.idle_time},{distance:.0f},{avg_speed:.0f},{max_speed:.0f}"  # noqa
                        _ = D and dbg(f"Writing tripinfo line:[{line}]")
                        file.write(line)
                        file.write("\n")
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
            from_month = now - relativedelta(months=3)
        else:
            if now.day == 1:  # first day of month also retrieve previous month
                from_month = now - relativedelta(months=1)

        while from_month <= now:
            yyyymm = from_month.strftime("%Y%m")
            from_month = from_month + relativedelta(months=1)
            _ = D and dbg(f"update_month_trip_info: {yyyymm}")
            manager.update_month_trip_info(vehicle.id, yyyymm)
            month_trip_info = vehicle.month_trip_info
            if month_trip_info is not None:
                last_date, last_hhmmss = handle_day_trip_info(
                    manager,
                    vehicle,
                    file,
                    month_trip_info,
                    last_date,
                    last_hhmmss,
                )


def handle_one_vehicle(
    manager: VehicleManager, vehicle: Vehicle, number_of_vehicles: int
) -> bool:
    """handle one vehicle and return if error occurred"""
    try:
        handle_trip_info(manager, vehicle, number_of_vehicles)
    except Exception as ex:  # pylint: disable=broad-except
        log("Warning: handle_trip_info Exception: " + str(ex))
        traceback.print_exc()

    geocode = ""
    if USE_GEOCODE:
        if len(vehicle.geocode) > 0:
            # replace comma by semicolon for easier splitting
            geocode_name = vehicle.geocode[0]
            if geocode_name is not None and geocode_name != "":
                geocode = geocode_name.replace(",", ";")

    location_longitude = get_safe_float(vehicle.location_longitude)
    location_latitude = get_safe_float(vehicle.location_latitude)
    last_updated_at = get_safe_datetime(vehicle.last_updated_at, vehicle.timezone)
    location_last_updated_at = get_safe_datetime(
        vehicle.location_last_updated_at, vehicle.timezone
    )
    dates = [last_updated_at, location_last_updated_at]
    newest_updated_at = max(dates)
    _ = D and dbg(f"newest: {newest_updated_at} from {dates}")
    ev_driving_range = to_int(f"{vehicle.ev_driving_range}")
    odometer = vehicle.odometer
    if to_miles_needed(vehicle):
        odometer = km_to_mile(odometer)
        line = f"{newest_updated_at}, {location_longitude}, {location_latitude}, {vehicle.engine_is_running}, {vehicle.car_battery_percentage}, {odometer:.1f}, {vehicle.ev_battery_percentage}, {vehicle.ev_battery_is_charging}, {vehicle.ev_battery_is_plugged_in}, {geocode}, {ev_driving_range}"  # noqa
    else:
        line = f"{newest_updated_at}, {location_longitude}, {location_latitude}, {vehicle.engine_is_running}, {vehicle.car_battery_percentage}, {odometer:.0f}, {vehicle.ev_battery_percentage}, {vehicle.ev_battery_is_charging}, {vehicle.ev_battery_is_plugged_in}, {geocode}, {ev_driving_range}"  # noqa
    if "None, None" in line:  # something gone wrong, retry
        log(f"Skipping Unexpected line: {line}")
        return True  # exit subroutine with error

    filename = "monitor.csv"
    if number_of_vehicles > 1:
        filename = "monitor." + vehicle.VIN + ".csv"
    last_line = get_last_line(Path(filename)).strip()
    if line != last_line:
        # check if everything is the same without address
        list1 = line.split(",")
        list2 = last_line.split(",")
        same = False
        if len(list1) == 11 and len(list2) == 11:
            list1[9] = ""  # clear address
            list2[9] = ""
            same = True
            for index, value in enumerate(list1):
                if value != list2[index]:
                    same = False
                    break  # finished
        if not same:
            _ = D and dbg(f"Writing1:\nline=[{line}]\nlast=[{last_line}]")
            writeln(filename, line)
    handle_daily_stats(vehicle, number_of_vehicles)
    vehicle_stats = [
        str(last_updated_at),
        str(location_last_updated_at),
        line,
        "",
    ]
    write_last_run(vehicle, number_of_vehicles, vehicle_stats)
    return False


def handle_exception(ex: Exception, retries: int, stacktrace=False) -> int:
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
    log(f"Exception: {exception_str}")
    if stacktrace and "Service Temporary Unavailable" not in exception_str:
        traceback.print_exc()
    retries = sleep(retries)
    return retries


def handle_vehicles() -> None:
    """handle vehicles"""
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
                language=LANGUAGE,
            )
            manager.check_and_refresh_token()
            manager.update_all_vehicles_with_cached_state()  # needed >= 2.0.0

            number_of_vehicles = len(manager.vehicles)
            error = False
            for _, vehicle in manager.vehicles.items():
                error = handle_one_vehicle(manager, vehicle, number_of_vehicles)
                if error:  # something gone wrong, exit loop
                    break

            if error:  # something gone wrong, retry
                retries -= 1
                sleep(retries)
            else:
                retries = 0  # successfully end while loop
        except exceptions.AuthenticationError as ex:
            retries = handle_exception(ex, retries)
        except exceptions.RateLimitingError as ex:
            retries = handle_exception(ex, retries)
        except exceptions.NoDataFound as ex:
            retries = handle_exception(ex, retries)
        except exceptions.DuplicateRequestError as ex:
            retries = handle_exception(ex, retries)
        except exceptions.RequestTimeoutError as ex:
            retries = handle_exception(ex, retries)
        # Not yet available, so workaround for now in handle_exception
        # except exceptions.ServiceTemporaryUnavailable as ex:
        #    retries = handle_exception(ex, retries)
        except exceptions.InvalidAPIResponseError as ex:
            retries = handle_exception(ex, retries, True)
        except exceptions.APIError as ex:
            retries = handle_exception(ex, retries, True)
        except exceptions.HyundaiKiaException as ex:
            retries = handle_exception(ex, retries, True)
        except Exception as ex:  # pylint: disable=broad-except
            retries = handle_exception(ex, retries, True)


handle_vehicles()  # do the work
