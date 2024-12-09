@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

IF not EXIST tests\run_mypy.bat (
    echo Run this script one directory higher: tests\run_mypy.bat
    goto :error
)

echo mypy monitor_utils.py
mypy monitor_utils.py | egrep -v "Success: no issues found in 1 source file"

echo mypy mqtt_utils.py
mypy mqtt_utils.py | egrep -v "^Found|paho.mqtt|: note:"

echo mypy domoticz_utils.py
mypy domoticz_utils.py | egrep -v "Success: no issues found in 1 source file"

echo mypy monitor.py
mypy monitor.py | egrep -v "^Found|hyundai_kia_connect_api|paho.mqtt|: note:"

echo mypy summary.py
mypy summary.py | egrep -v "^Found|gspread|paho.mqtt|: note:"

echo mypy dailystats.p
mypy dailystats.py | egrep -v "^Found|gspread|paho.mqtt|: note:|: error: Argument 1 to .next."

echo mypy kml.py
mypy kml.py | egrep -v "^Success"

echo mypy shrink.py
mypy shrink.py | egrep -v "^Success"

echo mypy debug.py
mypy debug.py | egrep -v "^Found|hyundai_kia_connect_api"
