# == debug.py Author: Zuinige Rijder =========================================
"""Simple Python3 script to debug hyundai_kia_connect_api values"""
import configparser
from datetime import datetime
import logging
from hyundai_kia_connect_api import VehicleManager, Vehicle
from monitor_utils import die, get_filepath, get, get_bool, to_int

logging.basicConfig(level=logging.DEBUG)

# == read monitor settings in monitor.cfg ==================
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


# == get_child_value =========================================================
def get_child_value(data: dict, key: str) -> dict:
    """get child value"""
    value = data
    for k in key.split("."):
        try:
            value = value[k]
            # pylint: disable=broad-except
        except Exception:
            try:
                value = value[int(k)]
                # pylint: disable=broad-except
            except Exception:
                value = {}
    return value


# == print_indent ==========================================================
def print_indent(indent: int) -> None:
    """print indent"""
    print()
    i = 0
    while i < indent:
        i += 1
        print("    ", end="")


# == print_indented ==========================================================
def print_indented(string: str) -> None:
    """print indented"""
    indent = 0
    for char in string:
        if char == "{" or char == "[" or char == "(":
            print_indent(indent)
            print(char, end="")
            indent += 1
            print_indent(indent)
        elif char == "}" or char == "]" or char == ")":
            indent -= 1
            print_indent(indent)
            print(char, end="")
        elif char == ",":
            print(char, end="")
            print_indent(indent)
        else:
            print(char, end="")

    print()


# == print_info ==========================================================
def print_info(vehicles: dict) -> None:
    """print info"""
    for key in vehicles:
        vehicle: Vehicle = vehicles[key]
        target_soc_list = get_child_value(
            vehicle.data,
            "vehicleStatus.evStatus.reservChargeInfos.targetSOClist",
        )
        print("targetSOClist:")
        print_indented(str(target_soc_list))
        print("Summary: ")
        for item in target_soc_list:
            target_soc_level = get_child_value(item, "targetSOClevel")
            target_soc_range = get_child_value(
                item, "dte.rangeByFuel.totalAvailableRange.value"
            )
            print("Target SOC level        : " + str(target_soc_level))
            print("Target SOC range        : " + str(target_soc_range))

        print("Last updated at         : " + str(vehicle.last_updated_at))
        print("Location Last updated at: " + str(vehicle.location_last_updated_at))
        print("Location                : " + str(vehicle.location))
        print("Air temperature         : " + str(vehicle.air_temperature))
        print("Driving range           : " + str(vehicle.ev_driving_range))
        print("Charge limits AC        : " + str(vehicle.ev_charge_limits_ac))
        print("Charge limits DC        : " + str(vehicle.ev_charge_limits_dc))
        print("Odometer                : " + str(vehicle.odometer))
        print("Total driving range     : " + str(vehicle.total_driving_range))
        print("Battery SOC             : " + str(vehicle.ev_battery_percentage))
        print("12V percentage          : " + str(vehicle.car_battery_percentage))
        print("Locked                  : " + str(vehicle.is_locked))


vm = VehicleManager(
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

for KEY in vm.vehicles:
    VEHICLE = vm.vehicles[KEY]
    print(f"timezone: {VEHICLE.timezone}")
    print(f"vehicle: {VEHICLE}")

vm.check_and_refresh_token()
# vm.force_refresh_all_vehicles_states()
vm.update_all_vehicles_with_cached_state()  # needed >= 2.0.0
vm.update_all_vehicles_with_cached_state()  # do twice to check geocode cache

for KEY in vm.vehicles:
    VEHICLE = vm.vehicles[KEY]
    print(f"timezone: {VEHICLE.timezone}")
    print(f"Last updated at: {VEHICLE.last_updated_at}")
    print(f"Location Last updated at: {VEHICLE.location_last_updated_at}")
    print(f"Location: {VEHICLE.location}")
    print(f"vehicle: {VEHICLE}")

    now = datetime.now()
    yyyymm = now.strftime("%Y%m")
    yyyymmdd = now.strftime("%Y%m%d")
    vm.update_month_trip_info(VEHICLE.id, yyyymm)
    if VEHICLE.month_trip_info is not None:
        for day in VEHICLE.month_trip_info.day_list:  # ordered on day
            if yyyymmdd == day.yyyymmdd:  # in example only interested in current day
                vm.update_day_trip_info(VEHICLE.id, day.yyyymmdd)
                if VEHICLE.day_trip_info is not None:
                    for trip in reversed(
                        VEHICLE.day_trip_info.trip_list
                    ):  # show oldest first
                        print(
                            f"{day.yyyymmdd},{trip.hhmmss},{trip.drive_time},{trip.idle_time},{trip.distance},{trip.avg_speed},{trip.max_speed}"  # noqa
                        )

print(type(vm.vehicles))
print(vm.vehicles)
print("Pretty print vm.vehicles:")
print_indented(str(vm.vehicles))
print_info(vm.vehicles)
