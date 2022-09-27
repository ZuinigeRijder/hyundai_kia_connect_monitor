# hyundai_kia_connect_monitor
Automatic trip administration tools for Hyundai Bluelink or Kia UVO Connect users.
Determining afterwards your private and/or business trips and information about those trips and usage of the car.

Run monitor.py e.g. once per hour (I use it on a Raspberry Pi and on Windows 10 with pure Python) and you can always check afterwards:
- captured locations
- odometer at specific day/hour
- how much driven at a specific day
- how much battery% used at a specific day (for BEV or HEV users)
- where you have been at a specific day/hour
- when you have charged and how much
- see your 12 volt battery percentage fluctuation

Idea is that you can analyze the information over time with other scripts or e.g. with Excel:
- summaries (see summary.py script)
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
You also can consider only to monitor between e.g. 6:00 and 22:00 (saves 1/3 of the calls). Dependent on your regular driving habit, choose the best option for you. Examples:
- each hour means 24 requests per day
- each hour between 6:00 and 19:00 means 13 requests per day
- each hour between 6:00 and 22:00 means 16 requests per day
- each half hour means 48 requests per day
- each half hour between 6:00 and 19:00 means 26 requests per day
- each half hour between 6:00 and 22:00 means 32 requests per day
- each quarter hour means 96 requests per day
- each quarter hour between 6:00 and 19:00 means 52 requests per day
- each quarter hour between 6:00 and 22:00 means 64 requests per day

The following tools are available as pure Python3 scripts:
- monitor.py: Simple Python3 script to monitor values using hyundai_kia_connect_api https://github.com/Hyundai-Kia-Connect/hyundai_kia_connect_api
- kml.py: transform the monitor.csv data to monitor.kml, so you can use it in e.g. Google My Maps to see on a map the captured locations
- summary.py: make summary per DAY, WEEK, MONTH, YEAR with monitor.csv as input
- shrink.py: Simple Python3 script to shrink monitor.csv, identical lines removed (first date/time column excluded)
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

## summary.py
make summary per DAY, WEEK, MONTH, YEAR with monitor.csv as input

Usage: 
```
python summary.py
```
- INPUTFILE: summary.cfg (configuration of kilometers or miles, net battery size in kWh, average cost per kWh and cost currency)
- INPUTFILE: monitor.csv
- standard output: summary per DAY, WEEK, MONTH, YEAR in csv format

Notes:
- the summary is done in one go, keeping track of DAY, WEEK, MONTH and YEAR totals
- the summary is based on the captured data, so in fact there might be e.g. charges or drives missed
- you can grep the output for DAY, WEEK, MONTH or YEAR to only have those lines shown

Example configuration of summary.cfg (I have an IONIQ 5 Project 45 with 72.6 kWh battery and 3.5% buffer, so net 70 kWh):
```
[summary]
odometer_metric = km
net_battery_size_kwh = 70.0
```

## kml.py
transform the monitor.csv data to monitor.kml, so you can use it in e.g. Google My Maps to see on a map the captured locations.
Lines are not written, when the following info is the same as previous line: longitude, latitude, engineOn, charging

Usage: 
```
python kml.py
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

How to import kml in Google Maps:
https://www.spotzi.com/en/about/help-center/how-to-import-a-kml-into-google-maps/

## shrink.py
Simple Python3 script to shrink monitor.csv, identical lines removed (first date/time column excluded). Handy for analyzing with other tools (e.g. Excel) with less data.

Usage:
```
python shrink.py
```
- INPUTFILE: monitor.csv
- OUTPUTFILE: shrinked_monitor.csv

Note: 
- True and False for EngineOn and Driving are replaced into respectively 1 and 0, so it is shorter and easier usable in e.g. Excel.

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

# Examples
## monitor.csv

Here a csv file from 2022-09-17 till 2022-09-25 (about one week). I started with capturing once per hour. At 2022-09-20 I changed into once each half hour between 6:00 and 19:30, because I barely drive in the evening and still not too many captures per day. My crontab for this:

```
*/30 6-19 * * * ~/hyundai_kia_connect_monitor/run_monitor_once.sh >> ~/hyundai_kia_connect_monitor/run_monitor_once.log 2>&1
```

Example output file monitor.csv: https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/monitor.csv

## python summary.py

The summary of the previous monitor.csv file.

output:
```
C:\Users\Rick\git\monitor>python summary.py
Label, date      , driven km, charged%, discharged%, charges, drives, km/kWh, kWh/100km, cost Euro
DAY  , 2022-09-17,       0.0,      +3%,           0,       1,      0,    0.0,       0.0,      0.00
DAY  , 2022-09-18,       0.0,      +2%,           0,       0,      0,    0.0,       0.0,      0.00
WEEK , 2022 W37  ,       0.0,      +5%,           0,       1,      0,    0.0,       0.0,      0.00
DAY  , 2022-09-19,       6.5,      +0%,           0,       0,      2,    0.0,       0.0,      0.00
DAY  , 2022-09-20,      47.6,      +0%,         -14,       0,      2,    4.9,      20.6,      2.41
DAY  , 2022-09-21,       5.2,     +19%,           0,       2,      2,    0.0,       0.0,      0.00
DAY  , 2022-09-22,       1.9,      +2%,           0,       1,      1,    0.0,       0.0,      0.00
DAY  , 2022-09-23,       1.7,     +24%,           0,       2,      1,    0.0,       0.0,      0.00
DAY  , 2022-09-24,     407.8,     +37%,         -95,       1,      6,    6.1,      16.3,     16.36
DAY  , 2022-09-25,       0.0,      +6%,           0,       0,      0,    0.0,       0.0,      0.00
WEEK , 2022 W38  ,     470.7,     +88%,         -98,       6,     14,    6.9,      14.6,     16.88
MONTH, 2022-09   ,     470.7,     +93%,         -97,       7,     14,    6.9,      14.4,     16.70
YEAR , 2022      ,     470.7,     +93%,         -97,       7,     14,    6.9,      14.4,     16.70
```

2022-09-24 I did a trip from 100% SOC to 5% SOC, have driven 407.8 km and started charging when back at home.

## python kml.py

Input is previous monitor.csv file.

The kml standard output: https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/kml.py_output.txt
```
C:\Users\Rick\git\monitor>python kml.py
  1: 20220917 15:00    (5.124957,51.68260 ) SOC: 54% 12V: 90% ODO: 17324.2
  2: 20220917 23:00 C  (5.124957,51.68260 ) SOC: 55% 12V: 91% ODO: 17324.2 charging plugged:2
  3: 20220918 01:00    (5.124957,51.68260 ) SOC: 60% 12V: 91% ODO: 17324.2 plugged:2
  4: 20220919 15:00  D (5.125942,51.679128) SOC: 61% 12V: 85% ODO: 17324.3 (+0.1 since 20220919 14:00) drive
  5: 20220919 16:00    (5.124957,51.68260 ) SOC: 59% 12V: 86% ODO: 17330.7 (+6.4 since 20220919 15:00)
  6: 20220920 07:00  D (5.091594,51.684361) SOC: 59% 12V: 88% ODO: 17330.7 drive
  7: 20220920 08:00    (5.124957,51.68260 ) SOC: 53% 12V: 91% ODO: 17358.9 (+28.2 since 20220920 07:00)
  8: 20220920 14:30  D (5.135242,51.692605) SOC: 50% 12V: 87% ODO: 17358.9 drive
  9: 20220920 15:00  D (5.078042,51.693758) SOC: 49% 12V: 91% ODO: 17358.9 drive
 10: 20220920 15:30    (5.04708 ,51.688192) SOC: 48% 12V: 92% ODO: 17371.5 (+12.6 since 20220920 15:00)
 11: 20220920 15:58    (5.124957,51.68260 ) SOC: 47% 12V: 91% ODO: 17378.3 (+6.8 since 20220920 15:30)
 12: 20220921 10:30 C  (5.124957,51.68260 ) SOC: 46% 12V: 91% ODO: 17378.3 charging plugged:2
 13: 20220921 12:30    (5.135183,51.692608) SOC: 52% 12V: 92% ODO: 17380.8 (+2.5 since 20220921 12:00)
 14: 20220921 13:00    (5.124957,51.68260 ) SOC: 51% 12V: 91% ODO: 17383.5 (+2.7 since 20220921 12:30)
 15: 20220921 14:31 C  (5.124957,51.68260 ) SOC: 52% 12V: 91% ODO: 17383.5 charging plugged:2
 16: 20220922 06:00    (5.124957,51.68260 ) SOC: 70% 12V: 91% ODO: 17383.5 plugged:2
 17: 20220923 11:21    (5.132119,51.685055) SOC: 71% 12V: 88% ODO: 17385.4 (+1.9 since 20220923 11:00)
 18: 20220923 12:00 C  (5.124957,51.68260 ) SOC: 72% 12V: 87% ODO: 17387.1 (+1.7 since 20220923 11:21) charging plugged:2
 19: 20220923 15:00    (5.124957,51.68260 ) SOC: 80% 12V: 87% ODO: 17387.1 plugged:2
 20: 20220924 08:00  D (5.124957,51.68260 ) SOC:100% 12V: 95% ODO: 17387.1 drive
 21: 20220924 08:30    (5.124957,51.68260 ) SOC:100% 12V: 95% ODO: 17387.1
 22: 20220924 11:00  D (5.129967,51.674819) SOC: 98% 12V: 92% ODO: 17390.8 drive
 23: 20220924 11:30  D (5.204728,51.883719) SOC: 91% 12V: 97% ODO: 17390.8 drive
 24: 20220924 12:00  D (5.250064,52.256122) SOC: 81% 12V: 98% ODO: 17390.8 drive
 25: 20220924 12:30  D (5.540714,52.575733) SOC: 69% 12V: 98% ODO: 17390.8 drive
 26: 20220924 13:00  D (5.768325,52.898894) SOC: 57% 12V: 98% ODO: 17390.8 drive
 27: 20220924 13:21    (5.683261,53.036686) SOC: 52% 12V: 96% ODO: 17589.2 (+198.4 since 20220924 13:00)
 28: 20220924 14:31    (5.681147,53.016858) SOC: 51% 12V: 94% ODO: 17592.5 (+3.3 since 20220924 14:00)
 29: 20220924 15:00  D (5.686422,53.030697) SOC: 51% 12V: 93% ODO: 17592.5 drive
 30: 20220924 15:23    (5.68325 ,53.036683) SOC: 50% 12V: 96% ODO: 17597.3 (+4.8 since 20220924 15:00)
 31: 20220924 16:30  D (5.6802  ,53.035853) SOC: 50% 12V: 94% ODO: 17597.3 drive
 32: 20220924 17:00  D (5.771994,52.709039) SOC: 40% 12V: 94% ODO: 17597.3 drive
 33: 20220924 17:30  D (5.375436,52.411236) SOC: 30% 12V: 95% ODO: 17597.3 drive
 34: 20220924 18:00  D (5.158522,52.095317) SOC: 21% 12V: 94% ODO: 17597.3 drive
 35: 20220924 18:30  D (5.293333,51.748758) SOC: 10% 12V: 96% ODO: 17597.3 drive
 36: 20220924 19:00 C  (5.124957,51.68260 ) SOC:  5% 12V: 97% ODO: 17794.9 (+197.6 since 20220924 18:30) charging plugged:2
```

The kml output file monitor.kml: https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/monitor.kml

2022-09-24 I did a trip from 100% SOC to 5% SOC and driven around 400 km and started charging when back at home.

Screenshot after imported into Google My Maps (yes, I have adjusted the locations for privacy):
- ![alt text](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/MonitorGoogleMyMaps.jpg)

I changed the style to "sequence numbering" so you see the order of locations in the map. You can also adjust the base map, so less information is shown, but your locations are better visible. You can also view the Google My Map in Google Earth (via the Google My Maps menu) and zoom in interactively to the different locations.  

## python shrink.py

Example (based on earlier monitor.csv) outputfile shrinked_monitor.csv: https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/shrinked_monitor.csv

Excel example using shrinked_monitor.csv: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/blob/main/examples/shrinked_monitor.xlsx

Screenshot of excel example with some graphs:
![alt text](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/shrinked_monitor.jpg)
