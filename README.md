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
make summary per TRIP, DAY, WEEK, MONTH, YEAR or a combination with monitor.csv as input

Usage: 
```
python summary.py
or
python summary.py -trip
or
python summary.py day
or
python summary.py trip
or
python summary.py trip day
or
python summary.py week
or
python summary.py month
or
python summary.py year
```
- INPUTFILE: summary.cfg (configuration of kilometers or miles, net battery size in kWh, average cost per kWh and cost currency)
- INPUTFILE: monitor.csv
- standard output: summary per TRIP, DAY, WEEK, MONTH, YEAR in csv format (default all summaries when no parameters given)

Notes:
- add trip, day, week, month, year or -trip or a combination as parameter, which respectively only shows lines for TRIP, DAY, WEEK, MONTH, YEAR or all without TRIP or a combination
- the summary is done in one go, keeping track of TRIP, DAY, WEEK, MONTH and YEAR totals
- the summary is based on the captured data, so in fact there might be e.g. charges or drives missed or consumption for trips is inaccurate

Example configuration of summary.cfg (I have an IONIQ 5 Project 45 with 72.6 kWh battery and 3.5% buffer, so net 70 kWh):
```
[summary]
odometer_metric = km
net_battery_size_kwh = 70.0
average_cost_per_kwh = 0.246
cost_currency = Euro
min_consumption_discharge_kwh = 1.5
ignore_small_positive_delta_soc = 2
ignore_small_negative_delta_soc = -2
show_zero_values = False
```

Explanation of configuration items:
- odometer_metric, e.g. km or mi
- cost_currency, e.g. Euro or Dollar
- min_consumption_discharge_kwh, do not show consumption figures when the discharge in kWh is below this number
- ignore_small_positive_delta_soc, do not see this as charge% when not charging/moved, because with temperature changes the percentage can increase
- ignore_small_negative_delta_soc, do not see this as discharge% when not moved, because with temperature changes the percentage can decrease
- show_zero_values = True shows also zero values in the standard output, can be easier for spreadsheets, but more difficult to read

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

The summary.py standard output of the previous monitor.csv file: https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/summary.py_output.txt


output:
```
C:\Users\Rick\git\monitor>python summary.py
Period, date      , info , delta km,    +kWh,     -kWh, km/kWh, kWh/100km, cost Euro, SOC%AVG,MIN,MAX, 12V%AVG,MIN,MAX, #charges, #drives
DAY   , 2022-09-17, Sat  ,         ,     0.7,         ,       ,          ,          ,      54, 55, 55,      90, 91, 91,        1,
DAY   , 2022-09-18, Sun  ,         ,     2.8,         ,       ,          ,          ,      59, 58, 60,      91, 91, 91,         ,
WEEK  , 2022-09-18, WK 37,         ,     3.5,         ,       ,          ,          ,      59, 55, 60,      91, 91, 91,        1,
TRIP  , 2022-09-19, 15:00,      0.1,        ,         ,       ,          ,          ,      60, 59, 61,      90, 85, 91,         ,       1
TRIP  , 2022-09-19, 16:00,      6.4,        ,     -1.4,       ,          ,          ,      60, 59, 59,      86, 86, 86,         ,       1
DAY   , 2022-09-19, Mon  ,      6.5,        ,         ,       ,          ,          ,      60, 59, 61,      89, 85, 91,         ,       2
TRIP  , 2022-09-20, 08:00,     28.2,        ,     -4.2,    6.7,      14.9,      1.03,      58, 53, 59,      88, 86, 91,         ,       1
TRIP  , 2022-09-20, 15:30,     12.6,        ,     -2.1,    6.0,      16.7,      0.52,      50, 48, 51,      90, 87, 92,         ,       1
TRIP  , 2022-09-20, 15:58,      6.8,        ,     -0.7,       ,          ,          ,      48, 47, 47,      92, 91, 91,         ,       1
DAY   , 2022-09-20, Tue  ,     47.6,        ,     -7.0,    6.8,      14.7,      1.72,      54, 47, 59,      89, 86, 92,         ,       3
TRIP  , 2022-09-21, 12:30,      2.5,     3.5,         ,       ,          ,          ,      46, 45, 52,      91, 91, 92,        1,       1
TRIP  , 2022-09-21, 13:00,      2.7,        ,     -0.7,       ,          ,          ,      52, 51, 51,      92, 91, 91,         ,       1
DAY   , 2022-09-21, Wed  ,      5.2,    15.4,     -0.7,       ,          ,          ,      50, 45, 68,      91, 91, 92,        2,       2
DAY   , 2022-09-22, Thu  ,         ,     1.4,         ,       ,          ,          ,      69, 70, 72,      91, 91, 91,        1,
TRIP  , 2022-09-23, 11:21,      1.9,        ,     -0.7,       ,          ,          ,      72, 71, 72,      91, 88, 91,         ,       1
TRIP  , 2022-09-23, 12:00,      1.7,     0.7,         ,       ,          ,          ,      72, 72, 72,      88, 87, 87,        1,       1
DAY   , 2022-09-23, Fri  ,      3.6,     6.3,     -0.7,       ,          ,          ,      73, 71, 80,      90, 87, 91,        1,       2
TRIP  , 2022-09-24, 09:57,      3.7,    14.0,     -0.7,       ,          ,          ,      91, 99,100,      88, 87, 95,        1,       1
TRIP  , 2022-09-24, 13:21,    198.4,        ,    -32.9,    6.0,      16.6,      8.09,      80, 52, 98,      96, 92, 98,         ,       1
TRIP  , 2022-09-24, 14:31,      3.3,        ,     -0.7,       ,          ,          ,      52, 51, 51,      95, 94, 94,         ,       1
TRIP  , 2022-09-24, 15:23,      4.8,        ,     -0.7,       ,          ,          ,      51, 50, 51,      94, 93, 96,         ,       1
TRIP  , 2022-09-24, 19:00,    197.6,        ,    -31.5,    6.3,      15.9,      7.75,      30,  5, 50,      95, 94, 97,        1,       1
DAY   , 2022-09-24, Sat  ,    407.8,    15.4,    -66.5,    6.1,      16.3,     16.36,      75,  5,100,      91, 87, 98,        2,       5
DAY   , 2022-09-25, Sun  ,         ,    30.1,         ,       ,          ,          ,      29, 42, 50,      97, 97, 97,         ,
WEEK  , 2022-09-25, WK 38,    470.7,    67.2,    -73.5,    6.4,      15.6,     18.08,      60,  5,100,      91, 85, 98,        6,      14
MONTH , 2022-09-25, Sep  ,    470.7,    70.7,    -73.5,    6.4,      15.6,     18.08,      59,  5,100,      91, 85, 98,        7,      14
YEAR  , 2022-09-25, 2022 ,    470.7,    70.7,    -73.5,    6.4,      15.6,     18.08,      59,  5,100,      91, 85, 98,        7,      14
```

- 2022-09-24 I did a trip from 100% SOC to 5% SOC (-66.5 kWh)
- have driven 407.8 km and started charging when back at home. 
- 198.4 km one way with 6.0 km/kWh and 16.6 kWh/100km, 197.6 km back with 6.3 km/kWh and 15.9 km/kWh.
- also shown is the average, minimum and maximum State Of Charge percentage and average, minimum and maximum of 12 Volt percentage. 
- for better readability zero values are left out, because of configuration show_zero_values = False

The SOC% can be used to see your habits about charging. Because wrongly someone posted for the IONIQ 5:
> My dealer told me that Hyundai has no restrictions on battery charging. So that it is not an issue to just load up to 100% (and leave it). Have you heard any stories other than this?

Depends on how long you want to drive it :-) The car is guaranteed up to 70% capacity (8 years or 160,000 km). 
- You can charge a battery maybe about 1000x (from 0% to 100% or 2x from 50% to 100%, etc) with the dealers advice (do not look at it). With a 72 kWh battery and 5 km/kWh you can drive 360,000 km until it is 70%. 
- Only if you do care about your battery and, for example, do not leave it at 100% for a long time and only charge to 100% when necessary, do not drive completely empty before you start charging again, drive economically, you can charge up to maybe 4000x. With a 72 kWh battery and 6 km/kWh you can drive almost 2 million km until it is 70%. The advantage is that you hardly lose any range over the years. 

There is also a buffer in the batteries so opponents will say that 100% is maybe only 95% and the manufacturer has already taken this into account. Yes, to claim under the warranty yes, but it is simply better not to always fully charge the batteries and almost completely empty. That is true even with a phone. 
A lease driver may not care, I bought the car privately and want to use it as long as possible. And of course it is also better for the climate not to wear out batteries unnecessarily. 

My previous Kia EV Soul with 27 kWh battery has driven 145,000 km in 7 years and the State Of Health (SOH) was still 91% and I was able to make someone else happy (I hope). There are plenty of people who have had to replace the battery because it was already below 70% SOH under warranty (7 years or 150,000 km). So being sensible with the battery certainly helps. 

But in the summary above, you see that my average SOC is 59%, which is pretty good.

Also the 12 Volt battery is shown and it has not become beneath 85%, with an average of 91%.

Example output when filtering on DAY:
```
C:\Users\Rick\git\monitor>python summary.py day
Period, date      , info , delta km,    +kWh,     -kWh, km/kWh, kWh/100km, cost Euro, SOC%AVG,MIN,MAX, 12V%AVG,MIN,MAX, #charges, #drives
DAY   , 2022-09-17, Sat  ,         ,     0.7,         ,       ,          ,          ,      54, 55, 55,      90, 91, 91,        1,
DAY   , 2022-09-18, Sun  ,         ,     2.8,         ,       ,          ,          ,      59, 58, 60,      91, 91, 91,         ,
DAY   , 2022-09-19, Mon  ,      6.5,        ,         ,       ,          ,          ,      60, 59, 61,      89, 85, 91,         ,       2
DAY   , 2022-09-20, Tue  ,     47.6,        ,     -7.0,    6.8,      14.7,      1.72,      54, 47, 59,      89, 86, 92,         ,       3
DAY   , 2022-09-21, Wed  ,      5.2,    15.4,     -0.7,       ,          ,          ,      50, 45, 68,      91, 91, 92,        2,       2
DAY   , 2022-09-22, Thu  ,         ,     1.4,         ,       ,          ,          ,      69, 70, 72,      91, 91, 91,        1,
DAY   , 2022-09-23, Fri  ,      3.6,     6.3,     -0.7,       ,          ,          ,      73, 71, 80,      90, 87, 91,        1,       2
DAY   , 2022-09-24, Sat  ,    407.8,    15.4,    -66.5,    6.1,      16.3,     16.36,      75,  5,100,      91, 87, 98,        2,       5
DAY   , 2022-09-25, Sun  ,         ,    30.1,         ,       ,          ,          ,      29, 42, 50,      97, 97, 97,         ,
```

Example output when filtering on TRIP:
```
C:\Users\Rick\git\monitor>python summary.py trip
Period, date      , info , delta km,    +kWh,     -kWh, km/kWh, kWh/100km, cost Euro, SOC%AVG,MIN,MAX, 12V%AVG,MIN,MAX, #charges, #drives
TRIP  , 2022-09-19, 15:00,      0.1,        ,         ,       ,          ,          ,      60, 59, 61,      90, 85, 91,         ,       1
TRIP  , 2022-09-19, 16:00,      6.4,        ,     -1.4,       ,          ,          ,      60, 59, 59,      86, 86, 86,         ,       1
TRIP  , 2022-09-20, 08:00,     28.2,        ,     -4.2,    6.7,      14.9,      1.03,      58, 53, 59,      88, 86, 91,         ,       1
TRIP  , 2022-09-20, 15:30,     12.6,        ,     -2.1,    6.0,      16.7,      0.52,      50, 48, 51,      90, 87, 92,         ,       1
TRIP  , 2022-09-20, 15:58,      6.8,        ,     -0.7,       ,          ,          ,      48, 47, 47,      92, 91, 91,         ,       1
TRIP  , 2022-09-21, 12:30,      2.5,     3.5,         ,       ,          ,          ,      46, 45, 52,      91, 91, 92,        1,       1
TRIP  , 2022-09-21, 13:00,      2.7,        ,     -0.7,       ,          ,          ,      52, 51, 51,      92, 91, 91,         ,       1
TRIP  , 2022-09-23, 11:21,      1.9,        ,     -0.7,       ,          ,          ,      72, 71, 72,      91, 88, 91,         ,       1
TRIP  , 2022-09-23, 12:00,      1.7,     0.7,         ,       ,          ,          ,      72, 72, 72,      88, 87, 87,        1,       1
TRIP  , 2022-09-24, 09:57,      3.7,    14.0,     -0.7,       ,          ,          ,      91, 99,100,      88, 87, 95,        1,       1
TRIP  , 2022-09-24, 13:21,    198.4,        ,    -32.9,    6.0,      16.6,      8.09,      80, 52, 98,      96, 92, 98,         ,       1
TRIP  , 2022-09-24, 14:31,      3.3,        ,     -0.7,       ,          ,          ,      52, 51, 51,      95, 94, 94,         ,       1
TRIP  , 2022-09-24, 15:23,      4.8,        ,     -0.7,       ,          ,          ,      51, 50, 51,      94, 93, 96,         ,       1
TRIP  , 2022-09-24, 19:00,    197.6,        ,    -31.5,    6.3,      15.9,      7.75,      30,  5, 50,      95, 94, 97,        1,       1
```

Example output when filtering on DAY and TRIP:
```
C:\Users\Rick\git\monitor>python summary.py day trip
Period, date      , info , delta km,    +kWh,     -kWh, km/kWh, kWh/100km, cost Euro, SOC%AVG,MIN,MAX, 12V%AVG,MIN,MAX, #charges, #drives
DAY   , 2022-09-17, Sat  ,         ,     0.7,         ,       ,          ,          ,      54, 55, 55,      90, 91, 91,        1,
DAY   , 2022-09-18, Sun  ,         ,     2.8,         ,       ,          ,          ,      59, 58, 60,      91, 91, 91,         ,
TRIP  , 2022-09-19, 15:00,      0.1,        ,         ,       ,          ,          ,      60, 59, 61,      90, 85, 91,         ,       1
TRIP  , 2022-09-19, 16:00,      6.4,        ,     -1.4,       ,          ,          ,      60, 59, 59,      86, 86, 86,         ,       1
DAY   , 2022-09-19, Mon  ,      6.5,        ,         ,       ,          ,          ,      60, 59, 61,      89, 85, 91,         ,       2
TRIP  , 2022-09-20, 08:00,     28.2,        ,     -4.2,    6.7,      14.9,      1.03,      58, 53, 59,      88, 86, 91,         ,       1
TRIP  , 2022-09-20, 15:30,     12.6,        ,     -2.1,    6.0,      16.7,      0.52,      50, 48, 51,      90, 87, 92,         ,       1
TRIP  , 2022-09-20, 15:58,      6.8,        ,     -0.7,       ,          ,          ,      48, 47, 47,      92, 91, 91,         ,       1
DAY   , 2022-09-20, Tue  ,     47.6,        ,     -7.0,    6.8,      14.7,      1.72,      54, 47, 59,      89, 86, 92,         ,       3
TRIP  , 2022-09-21, 12:30,      2.5,     3.5,         ,       ,          ,          ,      46, 45, 52,      91, 91, 92,        1,       1
TRIP  , 2022-09-21, 13:00,      2.7,        ,     -0.7,       ,          ,          ,      52, 51, 51,      92, 91, 91,         ,       1
DAY   , 2022-09-21, Wed  ,      5.2,    15.4,     -0.7,       ,          ,          ,      50, 45, 68,      91, 91, 92,        2,       2
DAY   , 2022-09-22, Thu  ,         ,     1.4,         ,       ,          ,          ,      69, 70, 72,      91, 91, 91,        1,
TRIP  , 2022-09-23, 11:21,      1.9,        ,     -0.7,       ,          ,          ,      72, 71, 72,      91, 88, 91,         ,       1
TRIP  , 2022-09-23, 12:00,      1.7,     0.7,         ,       ,          ,          ,      72, 72, 72,      88, 87, 87,        1,       1
DAY   , 2022-09-23, Fri  ,      3.6,     6.3,     -0.7,       ,          ,          ,      73, 71, 80,      90, 87, 91,        1,       2
TRIP  , 2022-09-24, 09:57,      3.7,    14.0,     -0.7,       ,          ,          ,      91, 99,100,      88, 87, 95,        1,       1
TRIP  , 2022-09-24, 13:21,    198.4,        ,    -32.9,    6.0,      16.6,      8.09,      80, 52, 98,      96, 92, 98,         ,       1
TRIP  , 2022-09-24, 14:31,      3.3,        ,     -0.7,       ,          ,          ,      52, 51, 51,      95, 94, 94,         ,       1
TRIP  , 2022-09-24, 15:23,      4.8,        ,     -0.7,       ,          ,          ,      51, 50, 51,      94, 93, 96,         ,       1
TRIP  , 2022-09-24, 19:00,    197.6,        ,    -31.5,    6.3,      15.9,      7.75,      30,  5, 50,      95, 94, 97,        1,       1
DAY   , 2022-09-24, Sat  ,    407.8,    15.4,    -66.5,    6.1,      16.3,     16.36,      75,  5,100,      91, 87, 98,        2,       5
DAY   , 2022-09-25, Sun  ,         ,    30.1,         ,       ,          ,          ,      29, 42, 50,      97, 97, 97,         ,
```

Example output when filtering on WEEK:
```
C:\Users\Rick\git\monitor>python summary.py week
PPeriod, date      , info , delta km,    +kWh,     -kWh, km/kWh, kWh/100km, cost Euro, SOC%AVG,MIN,MAX, 12V%AVG,MIN,MAX, #charges, #drives
WEEK  , 2022-09-18, WK 37,         ,     3.5,         ,       ,          ,          ,      59, 55, 60,      91, 91, 91,        1,
WEEK  , 2022-09-25, WK 38,    470.7,    67.2,    -73.5,    6.4,      15.6,     18.08,      60,  5,100,      91, 85, 98,        6,      14
```

Example output when filtering on MONTH:
```
C:\Users\Rick\git\monitor>python summary.py month
Period, date      , info , delta km,    +kWh,     -kWh, km/kWh, kWh/100km, cost Euro, SOC%AVG,MIN,MAX, 12V%AVG,MIN,MAX, #charges, #drives
MONTH , 2022-09-25, Sep  ,    470.7,    70.7,    -73.5,    6.4,      15.6,     18.08,      59,  5,100,      91, 85, 98,        7,      14
```

Example output when filtering on YEAR:
```
C:\Users\Rick\git\monitor>python summary.py year
Period, date      , info , delta km,    +kWh,     -kWh, km/kWh, kWh/100km, cost Euro, SOC%AVG,MIN,MAX, 12V%AVG,MIN,MAX, #charges, #drives
YEAR  , 2022-09-25, 2022 ,    470.7,    70.7,    -73.5,    6.4,      15.6,     18.08,      59,  5,100,      91, 85, 98,        7,      14
```

Example output when showing everything except TRIP:
```
C:\Users\Rick\git\monitor>python summary.py -trip
Period, date      , info , delta km,    +kWh,     -kWh, km/kWh, kWh/100km, cost Euro, SOC%AVG,MIN,MAX, 12V%AVG,MIN,MAX, #charges, #drives
DAY   , 2022-09-17, Sat  ,         ,     0.7,         ,       ,          ,          ,      54, 55, 55,      90, 91, 91,        1,
DAY   , 2022-09-18, Sun  ,         ,     2.8,         ,       ,          ,          ,      59, 58, 60,      91, 91, 91,         ,
WEEK  , 2022-09-18, WK 37,         ,     3.5,         ,       ,          ,          ,      59, 55, 60,      91, 91, 91,        1,
DAY   , 2022-09-19, Mon  ,      6.5,        ,         ,       ,          ,          ,      60, 59, 61,      89, 85, 91,         ,       2
DAY   , 2022-09-20, Tue  ,     47.6,        ,     -7.0,    6.8,      14.7,      1.72,      54, 47, 59,      89, 86, 92,         ,       3
DAY   , 2022-09-21, Wed  ,      5.2,    15.4,     -0.7,       ,          ,          ,      50, 45, 68,      91, 91, 92,        2,       2
DAY   , 2022-09-22, Thu  ,         ,     1.4,         ,       ,          ,          ,      69, 70, 72,      91, 91, 91,        1,
DAY   , 2022-09-23, Fri  ,      3.6,     6.3,     -0.7,       ,          ,          ,      73, 71, 80,      90, 87, 91,        1,       2
DAY   , 2022-09-24, Sat  ,    407.8,    15.4,    -66.5,    6.1,      16.3,     16.36,      75,  5,100,      91, 87, 98,        2,       5
DAY   , 2022-09-25, Sun  ,         ,    30.1,         ,       ,          ,          ,      29, 42, 50,      97, 97, 97,         ,
WEEK  , 2022-09-25, WK 38,    470.7,    67.2,    -73.5,    6.4,      15.6,     18.08,      60,  5,100,      91, 85, 98,        6,      14
MONTH , 2022-09-25, Sep  ,    470.7,    70.7,    -73.5,    6.4,      15.6,     18.08,      59,  5,100,      91, 85, 98,        7,      14
YEAR  , 2022-09-25, 2022 ,    470.7,    70.7,    -73.5,    6.4,      15.6,     18.08,      59,  5,100,      91, 85, 98,        7,      14
```

You can redirect this standard output to a file, e.g. summary.day.csv: https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/summary.day.csv

Excel example using python summary.py day > summary.day.csv: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/blob/main/examples/summary.day.xlsx

Screenshot of excel example with some graphs:
![alt text](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/summary.day.png)

Below a larger example of using monitor for a month:
```
C:\Users\Rick\git\monitor>python summary.py
Period, date      , info , delta km,    +kWh,     -kWh, km/kWh, kWh/100km, cost Euro, SOC%AVG,MIN,MAX, 12V%AVG,MIN,MAX, #charges, #drives
DAY   , 2022-09-17, Sat  ,         ,     0.7,         ,       ,          ,          ,      54, 55, 55,      90, 91, 91,        1,
DAY   , 2022-09-18, Sun  ,         ,     2.8,         ,       ,          ,          ,      59, 58, 60,      91, 91, 91,         ,
WEEK  , 2022-09-18, WK 37,         ,     3.5,         ,       ,          ,          ,      59, 55, 60,      91, 91, 91,        1,
TRIP  , 2022-09-19, 15:00,      0.1,        ,         ,       ,          ,          ,      60, 59, 61,      90, 85, 91,         ,       1
TRIP  , 2022-09-19, 16:00,      6.4,        ,     -1.4,       ,          ,          ,      60, 59, 59,      86, 86, 86,         ,       1
DAY   , 2022-09-19, Mon  ,      6.5,        ,         ,       ,          ,          ,      60, 59, 61,      89, 85, 91,         ,       2
TRIP  , 2022-09-20, 08:00,     28.2,        ,     -4.2,    6.7,      14.9,      1.03,      58, 53, 59,      88, 86, 91,         ,       1
TRIP  , 2022-09-20, 15:30,     12.6,        ,     -2.1,    6.0,      16.7,      0.52,      51, 48, 53,      91, 87, 92,         ,       1
TRIP  , 2022-09-20, 15:58,      6.8,        ,     -0.7,       ,          ,          ,      48, 47, 47,      92, 91, 91,         ,       1
DAY   , 2022-09-20, Tue  ,     47.6,        ,     -7.0,    6.8,      14.7,      1.72,      54, 47, 59,      89, 86, 92,         ,       3
TRIP  , 2022-09-21, 12:30,      2.5,     3.5,         ,       ,          ,          ,      46, 45, 52,      91, 91, 92,        1,       1
TRIP  , 2022-09-21, 13:00,      2.7,        ,     -0.7,       ,          ,          ,      52, 51, 51,      92, 91, 91,         ,       1
DAY   , 2022-09-21, Wed  ,      5.2,    15.4,     -0.7,       ,          ,          ,      50, 45, 68,      91, 91, 92,        2,       2
DAY   , 2022-09-22, Thu  ,         ,     1.4,         ,       ,          ,          ,      69, 70, 72,      91, 91, 91,        1,
TRIP  , 2022-09-23, 11:21,      1.9,        ,     -0.7,       ,          ,          ,      72, 71, 72,      91, 88, 91,         ,       1
TRIP  , 2022-09-23, 12:00,      1.7,     0.7,         ,       ,          ,          ,      72, 72, 72,      88, 87, 87,        1,       1
DAY   , 2022-09-23, Fri  ,      3.6,     6.3,     -0.7,       ,          ,          ,      73, 71, 80,      90, 87, 91,        1,       2
TRIP  , 2022-09-24, 09:57,      3.7,    14.0,     -0.7,       ,          ,          ,      91, 99,100,      88, 87, 95,        1,       1
TRIP  , 2022-09-24, 13:21,    198.4,        ,    -32.9,    6.0,      16.6,      8.09,      83, 52, 99,      96, 92, 98,         ,       1
TRIP  , 2022-09-24, 14:31,      3.3,        ,     -0.7,       ,          ,          ,      52, 51, 51,      95, 94, 94,         ,       1
TRIP  , 2022-09-24, 15:23,      4.8,        ,     -0.7,       ,          ,          ,      51, 50, 51,      94, 93, 96,         ,       1
TRIP  , 2022-09-24, 19:00,    197.6,        ,    -31.5,    6.3,      15.9,      7.75,      30,  5, 50,      95, 94, 97,        1,       1
DAY   , 2022-09-24, Sat  ,    407.8,    15.4,    -66.5,    6.1,      16.3,     16.36,      76,  5,100,      91, 87, 98,        2,       5
TRIP  , 2022-09-25, 15:00,      7.9,    37.1,     -0.7,       ,          ,          ,      35, 42, 60,      97, 94, 97,         ,       1
TRIP  , 2022-09-25, 18:00,      8.1,        ,     -0.7,       ,          ,          ,      58, 58, 59,      93, 91, 94,         ,       1
DAY   , 2022-09-25, Sun  ,     16.0,    37.1,     -1.4,       ,          ,          ,      37, 42, 60,      97, 91, 97,         ,       2
WEEK  , 2022-09-25, WK 38,    486.7,    74.2,    -74.9,    6.5,      15.4,     18.43,      59,  5,100,      92, 85, 98,        6,      16
DAY   , 2022-09-26, Mon  ,         ,        ,         ,       ,          ,          ,      58, 58, 59,      92, 92, 92,         ,
TRIP  , 2022-09-27, 07:30,      7.0,        ,     -3.5,    2.0,      50.0,      0.86,      58, 53, 58,      92, 92, 95,         ,       1
TRIP  , 2022-09-27, 08:00,     21.2,        ,     -0.7,       ,          ,          ,      52, 52, 52,      96, 96, 96,         ,       1
TRIP  , 2022-09-27, 09:30,      2.7,        ,     -0.7,       ,          ,          ,      51, 51, 51,      94, 94, 94,         ,       1
TRIP  , 2022-09-27, 10:00,      2.7,        ,     -0.7,       ,          ,          ,      50, 50, 50,      94, 93, 93,         ,       1
TRIP  , 2022-09-27, 11:00,      0.1,        ,         ,       ,          ,          ,      50, 50, 50,      92, 91, 91,         ,       1
TRIP  , 2022-09-27, 11:30,      2.3,        ,         ,       ,          ,          ,      50, 50, 50,      92, 92, 92,         ,       1
TRIP  , 2022-09-27, 16:00,      6.5,        ,     -1.4,       ,          ,          ,      49, 48, 49,      92, 88, 95,         ,       1
DAY   , 2022-09-27, Tue  ,     42.5,        ,     -7.0,    6.1,      16.5,      1.72,      55, 48, 58,      92, 88, 96,         ,       7
TRIP  , 2022-09-28, 09:30,      5.1,        ,     -3.5,    1.5,      68.6,      0.86,      46, 43, 44,      95, 89, 95,         ,       1
TRIP  , 2022-09-28, 12:30,      5.1,        ,     -0.7,       ,          ,          ,      42, 42, 42,      88, 88, 88,         ,       1
DAY   , 2022-09-28, Wed  ,     10.2,        ,     -4.2,    2.4,      41.2,      1.03,      46, 42, 44,      95, 88, 95,         ,       2
DAY   , 2022-09-29, Thu  ,         ,        ,         ,       ,          ,          ,      42, 42, 42,      88, 88, 88,         ,
TRIP  , 2022-09-30, 11:00,      1.8,        ,         ,       ,          ,          ,      41, 41, 41,      88, 88, 89,         ,       1
TRIP  , 2022-09-30, 11:00,      1.8,        ,         ,       ,          ,          ,       0, 41, 41,       0, 89, 89,         ,       1
DAY   , 2022-09-30, Fri  ,      3.6,    12.6,         ,       ,          ,          ,      45, 41, 60,      88, 88, 89,        1,       2
MONTH , 2022-09-30, Sep  ,    543.0,    89.6,    -85.4,    6.4,      15.7,     21.01,      55,  5,100,      91, 85, 98,        8,      27
TRIP  , 2022-10-01, 10:00,      4.0,        ,     -0.7,       ,          ,          ,      60, 59, 60,      88, 88, 90,         ,       1
DAY   , 2022-10-01, Sat  ,      4.0,        ,     -0.7,       ,          ,          ,      60, 59, 60,      88, 88, 90,         ,       1
TRIP  , 2022-10-02, 11:30,     77.4,        ,    -11.2,    6.9,      14.5,      2.76,      59, 43, 61,      90, 90, 92,        1,       1
TRIP  , 2022-10-02, 17:00,     77.6,        ,    -12.6,    6.2,      16.2,      3.10,      32, 25, 35,      95, 94, 96,         ,       1
DAY   , 2022-10-02, Sun  ,    155.0,        ,    -23.8,    6.5,      15.4,      5.85,      56, 25, 61,      91, 90, 96,        1,       2
WEEK  , 2022-10-02, WK 39,    215.3,    11.9,    -35.0,    6.2,      16.3,      8.61,      52, 25, 61,      90, 88, 96,        2,      14
DAY   , 2022-10-03, Mon  ,         ,    23.8,         ,       ,          ,          ,      42, 50, 60,      96, 96, 96,        1,
TRIP  , 2022-10-04, 12:00,     10.1,        ,     -1.4,       ,          ,          ,      59, 57, 59,      96, 92, 96,         ,       1
TRIP  , 2022-10-04, 12:30,      9.5,        ,     -0.7,       ,          ,          ,      56, 56, 56,      93, 94, 94,         ,       1
TRIP  , 2022-10-04, 15:00,      4.0,        ,     -2.1,    1.9,      52.5,      0.52,      55, 53, 56,      94, 92, 95,         ,       1
TRIP  , 2022-10-04, 15:30,     15.8,        ,     -0.7,       ,          ,          ,      52, 52, 52,      96, 96, 96,         ,       1
DAY   , 2022-10-04, Tue  ,     39.4,        ,     -4.9,    8.0,      12.4,      1.21,      58, 52, 59,      95, 92, 96,         ,       4
TRIP  , 2022-10-05, 15:30,      5.0,        ,     -0.7,       ,          ,          ,      51, 49, 51,      96, 87, 96,         ,       1
TRIP  , 2022-10-05, 16:30,      4.8,        ,     -0.7,       ,          ,          ,      48, 48, 48,      86, 86, 86,         ,       1
TRIP  , 2022-10-05, 18:30,      1.2,        ,     -0.7,       ,          ,          ,      48, 47, 47,      86, 85, 85,         ,       1
TRIP  , 2022-10-05, 19:01,      6.1,        ,         ,       ,          ,          ,      47, 47, 47,      86, 86, 86,         ,       1
DAY   , 2022-10-05, Wed  ,     23.1,        ,     -2.1,   11.0,       9.1,      0.52,      51, 47, 51,      94, 84, 96,         ,       4
TRIP  , 2022-10-06, 06:00,         ,        ,     -1.4,       ,          ,          ,      46, 45, 45,      85, 86, 86,         ,       1
DAY   , 2022-10-06, Thu  ,         ,        ,     -1.4,       ,          ,          ,      46, 44, 45,      85, 86, 86,         ,       1
TRIP  , 2022-10-07, 09:30,      0.1,        ,     -0.7,       ,          ,          ,      44, 43, 44,      86, 86, 90,         ,       1
TRIP  , 2022-10-07, 10:00,      5.3,        ,         ,       ,          ,          ,      43, 43, 43,      90, 91, 91,         ,       1
TRIP  , 2022-10-07, 10:30,      4.7,        ,     -0.7,       ,          ,          ,      42, 42, 42,      90, 90, 90,         ,       1
DAY   , 2022-10-07, Fri  ,     10.1,        ,     -1.4,       ,          ,          ,      44, 42, 44,      86, 86, 91,         ,       3
TRIP  , 2022-10-08, 10:00,      3.0,        ,     -0.7,       ,          ,          ,      42, 41, 42,      90, 86, 90,         ,       1
TRIP  , 2022-10-08, 11:00,      3.4,        ,     -0.7,       ,          ,          ,      40, 40, 40,      86, 87, 87,         ,       1
TRIP  , 2022-10-08, 15:00,      5.1,        ,     -0.7,       ,          ,          ,      40, 39, 40,      87, 86, 87,         ,       1
TRIP  , 2022-10-08, 17:00,      5.1,        ,     -0.7,       ,          ,          ,      38, 38, 38,      86, 87, 87,         ,       1
DAY   , 2022-10-08, Sat  ,     16.6,        ,     -2.8,    5.9,      16.9,      0.69,      42, 38, 42,      89, 86, 90,         ,       4
DAY   , 2022-10-09, Sun  ,         ,    14.0,         ,       ,          ,          ,      42, 37, 58,      85, 81, 87,        1,
WEEK  , 2022-10-09, WK 40,     89.2,    35.7,    -12.6,    7.1,      14.1,      3.10,      46, 37, 60,      90, 81, 96,        2,      16
TRIP  , 2022-10-10, 10:30,      4.1,        ,     -2.8,    1.5,      68.3,      0.69,      58, 54, 58,      81, 81, 87,         ,       1
TRIP  , 2022-10-10, 11:00,     19.0,        ,         ,       ,          ,          ,      54, 54, 54,      88, 88, 88,         ,       1
TRIP  , 2022-10-10, 17:31,     23.1,        ,     -2.8,    8.3,      12.1,      0.69,      52, 49, 53,      90, 88, 91,         ,       1
DAY   , 2022-10-10, Mon  ,     46.2,        ,     -5.6,    8.3,      12.1,      1.38,      57, 49, 58,      82, 81, 91,         ,       3
TRIP  , 2022-10-11, 14:31,      2.6,        ,     -0.7,       ,          ,          ,      48, 47, 48,      91, 87, 91,         ,       1
TRIP  , 2022-10-11, 14:45,      1.3,        ,         ,       ,          ,          ,      47, 47, 47,      87, 87, 87,         ,       1
TRIP  , 2022-10-11, 15:30,      8.5,        ,     -1.4,       ,          ,          ,      46, 45, 45,      88, 88, 88,         ,       1
TRIP  , 2022-10-11, 16:30,      7.3,        ,     -0.7,       ,          ,          ,      45, 44, 45,      88, 87, 88,         ,       1
DAY   , 2022-10-11, Tue  ,     19.7,        ,     -2.8,    7.0,      14.2,      0.69,      48, 44, 48,      90, 87, 91,         ,       4
TRIP  , 2022-10-12, 13:30,      5.5,        ,     -0.7,       ,          ,          ,      43, 42, 43,      88, 86, 88,         ,       1
TRIP  , 2022-10-12, 15:30,      6.0,        ,     -0.7,       ,          ,          ,      42, 41, 41,      86, 85, 85,         ,       1
DAY   , 2022-10-12, Wed  ,     11.5,        ,     -1.4,       ,          ,          ,      43, 41, 43,      88, 85, 88,         ,       2
TRIP  , 2022-10-13, 07:30,      6.9,        ,     -4.2,    1.6,      60.9,      1.03,      41, 35, 41,      86, 85, 95,         ,       1
TRIP  , 2022-10-13, 08:00,     21.3,        ,         ,       ,          ,          ,      35, 35, 35,      95, 95, 95,         ,       1
DAY   , 2022-10-13, Thu  ,     28.2,    13.3,     -4.2,    6.7,      14.9,      1.03,      42, 35, 54,      89, 85, 95,        1,       2
TRIP  , 2022-10-14, 10:30,      1.8,     4.2,     -0.7,       ,          ,          ,      57, 59, 60,      95, 95, 97,        1,       1
TRIP  , 2022-10-14, 11:00,      1.7,        ,         ,       ,          ,          ,      59, 59, 59,      98, 98, 98,         ,       1
TRIP  , 2022-10-14, 13:30,      3.7,        ,     -0.7,       ,          ,          ,      59, 58, 59,      98, 97, 98,         ,       1
TRIP  , 2022-10-14, 14:30,      3.3,        ,     -0.7,       ,          ,          ,      58, 57, 58,      97, 96, 98,         ,       1
TRIP  , 2022-10-14, 15:30,      8.3,        ,     -0.7,       ,          ,          ,      56, 56, 56,      98, 99, 99,         ,       1
TRIP  , 2022-10-14, 16:00,      8.5,        ,     -1.4,       ,          ,          ,      55, 54, 54,      99, 99, 99,         ,       1
DAY   , 2022-10-14, Fri  ,     27.3,     4.2,     -4.2,    6.5,      15.4,      1.03,      57, 54, 60,      96, 95, 99,        1,       6
TRIP  , 2022-10-15, 10:00,      1.9,        ,         ,       ,          ,          ,      54, 54, 54,      98, 85, 99,         ,       1
TRIP  , 2022-10-15, 11:00,      1.9,        ,     -0.7,       ,          ,          ,      54, 53, 54,      85, 85, 85,         ,       1
DAY   , 2022-10-15, Sat  ,      3.8,     4.2,         ,       ,          ,          ,      55, 53, 61,      94, 85, 99,        2,       2
TRIP  , 2022-10-16, 11:30,     77.4,        ,    -12.6,    6.1,      16.3,      3.10,      60, 43, 61,      86, 85, 92,         ,       1
TRIP  , 2022-10-16, 17:30,     77.2,        ,    -10.5,    7.4,      13.6,      2.58,      38, 28, 41,      90, 89, 91,         ,       1
DAY   , 2022-10-16, Sun  ,    154.6,        ,    -23.1,    6.7,      14.9,      5.68,      57, 28, 61,      86, 85, 92,         ,       2
WEEK  , 2022-10-16, WK 41,    291.3,    19.6,    -40.6,    7.2,      13.9,      9.99,      51, 28, 61,      90, 81, 99,        4,      21
DAY   , 2022-10-17, Mon  ,         ,    21.7,         ,       ,          ,          ,      43, 51, 59,      91, 91, 91,        1,
WEEK  , 2022-10-17, WK 42,         ,    21.7,         ,       ,          ,          ,      43, 51, 59,      91, 91, 91,        1,
MONTH , 2022-10-17, Oct  ,    539.5,    77.0,    -77.7,    6.9,      14.4,     19.11,      49, 25, 61,      90, 81, 99,        8,      40
YEAR  , 2022-10-17, 2022 ,   1082.5,   166.6,   -163.1,    6.6,      15.1,     40.12,      52,  5,100,      91, 81, 99,       16,      67
```

Notes:
- when the -kWh is below the configured threshold, no consumption data is shown
- sometimes with TRIP the used kWh is counted by the previous trip, this is because of the moment of capturing data and then consumption is off for both trips AND the odometer is only updated after the car is switched off (apparently the behavior of bluelink)

Example of wrong consumption shown for trip:

```
TRIP  , 2022-10-13, 07:30,      6.9,        ,     -4.2,    1.6,      60.9,      1.03,      41, 35, 41,      86, 85, 95,         ,       1
TRIP  , 2022-10-13, 08:00,     21.3,        ,         ,       ,          ,          ,      35, 35, 35,      95, 95, 95,         ,       1
DAY   , 2022-10-13, Thu  ,     28.2,    13.3,     -4.2,    6.7,      14.9,      1.03,      42, 35, 54,      89, 85, 95,        1,       2
```

If you look at the corresonding entries of monitor.csv:
```
2022-10-12 19:30:42+02:00, 5.118697, 51.680767, False, 85, 18192.8, 41, False, 0
2022-10-13 06:00:42+02:00, 5.118697, 51.680767, False, 85, 18192.8, 41, False, 0
2022-10-13 06:30:44+02:00, 5.118697, 51.680767, False, 85, 18192.8, 41, False, 0
2022-10-13 07:00:34+02:00, 5.066594, 51.692425, True, 94, 18192.8, 39, False, 0
2022-10-13 07:30:32+02:00, 5.156569, 51.697092, True, 95, 18199.7, 35, False, 0
2022-10-13 08:00:50+02:00, 5.118764, 51.6808, False, 95, 18221, 35, False, 0
2022-10-13 08:30:43+02:00, 5.118764, 51.6808, False, 95, 18221, 35, False, 0
```

What has happended on those TRIPs:
- till 07:30 I have driven 6.9 km till 07:05, put the car off (odometer is updated) and started a new trip around 7:10, which trip ended around 7:25, but did NOT put the car off (odometer is NOT updated).
- these intermediate trips are not captured
- At 7:25 I drove home again, only a few km, got home after 7:30, which has been captured at 8:00
- because I have not switched off the car at 7:25, the odometer is not updated and seen at 7:30 is the short trip end of 7:05, but already 6% SOC change has been recorded
- the way back home is only a few km, so the consumption has not decreased
- the consumption of 6% is given to the first trip (there was a odometer change), but actually the consumption should have been divided between the 2 trips
- I cannot detect these situations and also do not know how to divide these, because of the moment of capturing AND odometer is not constantly updated
- you can compute a better consumption by combining those 2 trips, in this case the DAY gives the real consumption

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

## Remarks of using the tools for a month
- The hyundai_kia_connect_api gives regularly exceptions, see this issue: https://github.com/Hyundai-Kia-Connect/hyundai_kia_connect_api/issues/62#issuecomment-1280045102
- the retry mechanism (wait one minute and retry twice) seems a good workaround
- I do not know what happens if the car cannot be reached by bluelink or when the number of calls allowed per day have been exceeded
- I have seen small drops and increases of SOC% (on my IONIQ 5 around 1% to 2%), because of temperature changes between e.g. evening and morning, I made this configurable via summary.cfg
- Small trips will give inaccurate consumption figures, on the IONIQ 5 1% SOC difference is 0.7 kWh difference, so I made the minimum kWh consumption configurable via summary.cfg. A Smaller battery will have better accurracy, because 1% of e.g. 27 kWh makes 0.27 kWh delta's instead of 0.7 kWh in my case
- I have seen once that SOC was reported wrongly in monitor.csv as zero, in summary.py I corrected this when the previous SOC% was not zero and delta is greather than 5

Occurrence of SOC% of 0: 
```
2022-10-11 11:30:47+02:00, 5.118592, 51.680736, False, 91, 18161.6, 48, False, 0
2022-10-11 12:00:54+02:00, 5.118592, 51.680736, False, 91, 18161.6, 0, False, 0
2022-10-11 12:30:48+02:00, 5.118592, 51.680736, False, 91, 18161.6, 48, False, 0
```
