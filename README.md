# hyundai_kia_connect_monitor
Python scripts to monitor over time/transform Hyundai bluelink or Kia UVO Connect using hyundai_kia_connect_api

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

Outputfile (appended): monitor.csv

Usage:
```
python monitor.py
```

# Utilities
## shrink_monitor_csv.py
Simple Python3 script to shrink monitor.csv.
identical lines removed (first date/time column excluded)

Inputfile: monitor.csv
Outputfile: shrinked_monitor.csv

Usage: 
```
python shrink_monitor_csv.py
```

## monitor_csv_to_kml.py
Simple Python3 script to convert monitor.csv to kml
identical (longitude, latitude) lines to previous line are removed

How to import kml in Google Maps:
https://www.spotzi.com/en/about/help-center/how-to-import-a-kml-into-google-maps/

Inputfile: monitor.csv
Outputfile: monitor.kml
Usage: 
```
python monitor_csv_to_kml.py
```

## Raspberry pi Configuration
Steps:
* create a directory hyundai_kia_connect_monitor in your home directory
* copy run_monitor_once.sh, monitor.py and monitor.cfg in this hyundai_kia_connect_monitor directory
* change inside monitor.cfg the hyundai_kia_connect settings
* chmod + x run_monitor_once.sh
* add the following line in your crontab -e to run it once per hour:

```
0 * * * * ~/hyundai_kia_connect_monitor/run_monitor_once.sh >> ~/hyundai_kia_connect_monitor/run_monitor_once.log 2>&1
```