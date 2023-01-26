# == debug.py Author: Zuinige Rijder =========================================
""" Simple Python3 script to debug hyundai_kia_connect_api values """
import configparser
import logging
from hyundai_kia_connect_api import VehicleManager, Vehicle

logging.basicConfig(level=logging.DEBUG)

# == read monitor settings in monitor.cfg ==================
parser = configparser.ConfigParser()
parser.read("monitor.cfg")
monitor_settings = dict(parser.items("monitor"))

REGION = monitor_settings["region"]
BRAND = monitor_settings["brand"]
USERNAME = monitor_settings["username"]
PASSWORD = monitor_settings["password"]
PIN = monitor_settings["pin"]


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
                value = None
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
            print("Target SOC level      : " + str(target_soc_level))
            print("Target SOC range      : " + str(target_soc_range))

        print("Last updated at       : " + str(vehicle.last_updated_at))
        print("Location              : " + str(vehicle.location))
        print("Air temperature       : " + str(vehicle.air_temperature))
        print("Driving range         : " + str(vehicle.ev_driving_range))
        print("Charge limits AC      : " + str(vehicle.ev_charge_limits_ac))
        print("Charge limits DC      : " + str(vehicle.ev_charge_limits_dc))
        print("Odometer              : " + str(vehicle.odometer))
        print("Total driving range   : " + str(vehicle.total_driving_range))
        print("Battery SOC           : " + str(vehicle.ev_battery_percentage))
        print("12V percentage        : " + str(vehicle.car_battery_percentage))
        print("Locked                : " + str(vehicle.is_locked))


vm = VehicleManager(
    region=int(REGION),
    brand=int(BRAND),
    username=USERNAME,
    password=PASSWORD,
    pin=PIN,
)
vm.check_and_refresh_token()
vm.update_all_vehicles_with_cached_state()  # needed >= 2.0.0
print(type(vm.vehicles))
print(vm.vehicles)
print("Pretty print vm.vehicles:")
print_indented(str(vm.vehicles))
print_info(vm.vehicles)
