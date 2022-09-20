# hyundai_kia_connect_monitor
Automatic trip administration tools for Hyundai Bluelink or Kia UVO Connect users.
Determining afterwards your private and/or business trips and information about those trips and usage of the car.

Run monitor.py e.g. once per hour (I use it on a Raspberry Pi) and you can always check afterwards:
- captured locations
- odometer at specific day/hour
- how much driven at a specific day
- how much battery% used at a specific day (for BEV or HEV users)
- where you have been at a specific day/hour
- when you have charged and how much
- see your 12 volt battery percentage fluctuation

Idea is that you can analyze the information over time with other scripts or e.g. with Excel:
- daily summary (I am thinking about adding a daily_summary.py script)
- weekly/monthly summary
- odometer trend over the lifetime
- SOC trend and charging trend
- 12V battery fluctuations

Note that the number of API calls is restricted for Hyundai Bluelink or Kia UVO Connect users, see this page for API Rate Limits: https://github.com/Hacksore/bluelinky/wiki/API-Rate-Limits
```
Region Daily Limits    Per Action  Comments
- USA  30              10  
- CA   TBD             TBD         You must wait 90 seconds before vehicle commands
- EU   200         
- KR   ???
```

So maybe you can capture more than once per hour, but you might run into the problem that you use too much API calls, especially when you also regularly use the Hyndai Bluelink or Kia UVO Connect app. 
You also can consider not to monitor between e.g. 22:00 and 6:00 (saves 1/3 of the calls).

The following tools are available as pure Python3 scripts:
- monitor.py: Simple Python3 script to monitor values using hyundai_kia_connect_api https://github.com/Hyundai-Kia-Connect/hyundai_kia_connect_api
- monitor_csv_to_kml.py: transform the monitor.csv data to monitor.kml, so you can use it in e.g. Google My Maps to see on a map the captured locations
- shrink_monitor_csv.py: Simple Python3 script to shrink monitor.csv, identical lines removed (first date/time column excluded)
- Raspberry pi configuration: example script to run monitor.py once per hour on a linux based system
- debug.py: same sort of python script as monitor.py, but debug logging enabled and all the (internal) data is just printed to standard output in pretty print

# Tools

## monitor.py
Simple Python3 script to monitor values using hyundai_kia_connect_api https://github.com/Hyundai-Kia-Connect/hyundai_kia_connect_api

Usage:
```
python monitor.py
```
- INPUTFILE: monitor.cfg (configuration of input to hyundai_kia_connect_api)
- OUTPUTFILE: monitor.csv (appended)

Following information from hyundai_kia_connect_api is added to the monitor.csv file:
- datetime
- longitude
- latitude
- engineOn
- 12V%
- odometer
- SOC%
- charging
- plugged

Example output file monitor.csv: https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/monitor.csv

## monitor_csv_to_kml.py
transform the monitor.csv data to monitor.kml, so you can use it in e.g. Google My Maps to see on a map the captured locations.
Lines are not written, when the following info is the same as previous line: longitude, latitude, engineOn, charging

Usage: 
```
python monitor_csv_to_kml.py
```
- INPUTFILE: monitor.csv
- OUTPUTFILE: monitor.kml
- standard output: summary per kml placemark

The following information is written in the kml file:
- document name: monitor + now in format "yyyymmdd hh:mm"
- per placemark
- - name of place (index of Google Maps): datetime in format "yyyymmdd hh:mm" and optionally "C" when charging and "D" when in drive
- - description: SOC: nn% 12V: nn% ODO: odometer [(+distance since yyyymmdd hh:mm)] [drive] [charging] [plugged: n]
- - coordinate (longitude, latitude)

Note:
- the placemark lines are one-liners, so you can also search in monitor.kml

Example standard output: https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/monitor_csv_to_kml.py_output.txt
Example output file monitor.kml: https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/monitor.kml

How to import kml in Google Maps:
https://www.spotzi.com/en/about/help-center/how-to-import-a-kml-into-google-maps/

Example screenshot (yes, I have adjusted the locations for privacy, so I park/drive in the meadows):
- ![alt text](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/MonitorGoogleMyMaps.jpg)

## shrink_monitor_csv.py
Simple Python3 script to shrink monitor.csv, identical lines removed (first date/time column excluded).  Handy for analyzing with other tools (e.g. Excel) with less data.

Usage:
```
python shrink_monitor_csv.py
```
- INPUTFILE: monitor.csv
- OUTPUTFILE: shrinked_monitor.csv

Example (based on earlier example monitor.csv) outputfile shrinked_monitor.csv: https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/shrinked_monitor.csv

## Raspberry pi configuration
Example script to run monitor.py once per hour on a linux based system.

Steps:
- create a directory hyundai_kia_connect_monitor in your home directory
- copy hyundai_kia_connect_api as subdirectory of directory hyundai_kia_connect_monitor
- copy run_monitor_once.sh, monitor.py and monitor.cfg in the hyundai_kia_connect_monitor directory
- change inside monitor.cfg the hyundai_kia_connect settings
- chmod + x run_monitor_once.sh
- add the following line in your crontab -e to run it once per hour:

crontab -e:
```
0 * * * * ~/hyundai_kia_connect_monitor/run_monitor_once.sh >> ~/hyundai_kia_connect_monitor/run_monitor_once.log 2>&1
```

Note: 
- there is a limit in the number of request per country, but 1 request per hour should not hamper using the Bluelink or UVO Connect App at the same time

## debug.py
Same sort of python script as monitor.py, but debug logging enabled and all the (internal) data is just printed to standard output in pretty print. It uses the configuration from monitor.cfg

Usage:
```
python debug.py
```
- INPUTFILE: monitor.cfg (configuration of input to hyundai_kia_connect_api)
- standard output: debug output and pretty print of the data got from API calls
