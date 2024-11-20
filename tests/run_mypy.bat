@echo on
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

IF not EXIST tests\run_mypy.bat (
    echo Run this script one directory higher: tests\run_mypy.bat
    goto :error
)

mypy monitor_utils.py
mypy mqtt_utils.py | egrep -v "^Found|paho.mqtt|: note:"
mypy domoticz_utils.py
mypy monitor.py | egrep -v "^Found|hyundai_kia_connect_api|paho.mqtt|: note:"
mypy summary.py | egrep -v "^Found|gspread|paho.mqtt|: note:"
mypy dailystats.py | egrep -v "^Found|gspread|paho.mqtt|: note:|: error: Argument 1 to .next."
mypy kml.py | egrep -v "^Success"
mypy shrink.py | egrep -v "^Success"
mypy debug.py | egrep -v "^Found|hyundai_kia_connect_api"

pause