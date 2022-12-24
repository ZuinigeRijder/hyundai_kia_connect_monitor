# index
- [Introduction](#introduction-hyundai_kia_connect_monitor)
- [How to install python, packages and hyundai_connect_monitor](#how-to-install-python-packages-and-hyundai_connect_monitor)
- [monitor.py](#monitorpy)
- [python monitor.py cacheupdate](#python-monitorpy-cacheupdate)
- [python monitor.py forceupdate](#python-monitorpy-forceupdate)
- [summary.py](#summarypy)
- [summary.py sheetupdate](#summarypy-sheetupdate)
- - [configuration of gspread for "python summary.py sheetupdate"](#configuration-of-gspread-for-python-summarypy-sheetupdate)
- [kml.py](#kmlpy)
- [shrink.py](#shrinkpy)
- [Raspberry Pi configuration](#raspberry-pi-configuration)
- [debug.py](#debugpy)
- [Examples](#examples)
- - [monitor.csv](#monitorcsv)
- - [python summary.py](#python-summarypy)
- - [python summary.py sheetupdate](#python-summarypy-sheetupdate)
- - [python kml.py](#python-kmlpy)
- - [python shrink.py](#python-shrinkpy)
- [Remarks of using the tools for a month](#remarks-of-using-the-tools-for-a-month)

# Introduction hyundai_kia_connect_monitor
Automatic trip administration tools for Hyundai Bluelink or Kia UVO Connect users.
Determining afterwards your private and/or business trips and information about those trips and usage of the car.
Best of all is the fact that it does NOT drain your 12 volt battery of the car, because it default uses the cached server information!

[This video shows why it is important to avoid awakening the car for actual values.](https://youtu.be/rpLWEe-2aUU?t=121) 30 nov 6:10 a forceupdate has been done and you see a dip from 12.92 Volt to 12.42 Volt for a moment and then back to 12.83 Volt. Note by default the tool asks only for server cache updates and the car decides when to send push notifications with actual values to the server.

Run monitor.py e.g. once per hour (I use it on a Raspberry Pi and on Windows 10 with pure Python, buit it will also run on Mac or a linux Operating System) and you can always check afterwards:
- captured locations
- odometer at specific day/hour
- how much driven at a specific day
- how much battery% used at a specific day (for BEV or HEV users)
- where you have been at a specific day/hour
- when you have charged and how much
- see your 12 volt battery percentage fluctuation

You can analyze the information over time with other scripts or e.g. with Excel:
- summaries (see summary.py script)
- odometer trend over the lifetime
- SOC trend and charging trend
- 12V battery fluctuations

The following tools are available as pure Python3 scripts:
- monitor.py: Simple Python3 script to monitor values using [hyundai_kia_connect_api](https://github.com/Hyundai-Kia-Connect/hyundai_kia_connect_api)
- kml.py: transform the monitor.csv data to monitor.kml, so you can use it in e.g. Google My Maps to see on a map the captured locations
- summary.py: make summary per TRIP, DAY, WEEK, MONTH, YEAR with monitor.csv as input
- shrink.py: Simple Python3 script to shrink monitor.csv, identical lines removed (first date/time column excluded)
- Raspberry pi configuration: example script to run monitor.py once per hour on a linux based system
- debug.py: same sort of python script as monitor.py, but debug logging enabled and all the (internal) data is just printed to standard output in pretty print

# How to install python, packages and hyundai_connect_monitor
Explanation for someone with no knowledge of python. I don't know what computer you have. Part of the tools is the regular retrieval of the data with the Python script monitor.py.
For this you need to install Python. I have installed Python 3.9.13.
[Here is more information about installing Python](https://realpython.com/installing-python/)

Steps:
- Download the source code of [hyundai_kia_connect_api v1.50.3 here](https://github.com/Hyundai-Kia-Connect/hyundai_kia_connect_api/releases/tag/v1.50.3)
- Download the [latest hyundai_kia_connect_monitor release here](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases)
- Extract both and move the hyundai_kia_connect_api subfolder of hyundai_kia_connect_api-1.50.3 under hyundai_kia_connect_monitor.
- Then configure monitor.cfg
- Then run: python monitor.py

Probably some packages needed for Hyundai Connect API are not installed (error messages). [Learn more about installing Python packages](https://packaging.python.org/en/latest/tutorials/installing-packages/)
I have installed the following packages (e.g. use python -m pip install "package_name"), see [requirements.txt](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/requirements.txt)

    beautifulsoup4==4.11.1
    python_dateutil==2.8.2
    pytz==2022.2.1
    requests==2.28.1
    
In hyundai_kia_connect_monitor summary.py also the following packages are used:

    gspread==5.6.2
    
If everything works, it's a matter of regularly collecting the information, for example by running the "python monitor.py" command once an hour. A server is of course best, I use a Raspberry Pi, but it can also regularly be done on a Windows 10 or Mac computer, provided the computer is on.

By then, if you want to show the summary information in monitor.csv, configure the summary.cfg once and run the command: python summary.py

# monitor.py
Simple Python3 script to monitor values using [hyundai_kia_connect_api](https://github.com/Hyundai-Kia-Connect/hyundai_kia_connect_api)

Usage:
```
python monitor.py
or
python monitor.py cacheupdate
or
python monitor.py forceupdate
```
INPUTFILE: 
- monitor.cfg (configuration of input to hyundai_kia_connect_api)

OUTPUTFILES:
- monitor.csv (appended when the last line is different) or monitor.VIN.csv (latter when multiple vehicles found)
- monitor.dailystats.csv (appended with daily stats after last written daily stats date and not today) or monitor.dailystats.VIN.csv (latter when multiple vehicles found)
- monitor.lastrun (rewritten with last run date/time of monitor.py) 

Make sure to configure monitor.cfg once:
```
[monitor]
region = 1
brand = 2
username = your_email
password = your_password
pin =
force_update_seconds = 604800
use_geocode = True
use_geocode_email = True
language = en
```

Explanation of the configuration items:
- region: 1: REGION_EUROPE, 2: REGION_CANADA, 3: REGION_USA
- brand: 1: BRAND_KIA, 2: BRAND_HYUNDAI
- username: your bluelink account email address
- password: password of your bluelink account
- pin: pincode of your bluelink account, required for CANADA, and potentially USA, otherwise pass a blank string
- force_update_seconds: do a forceupdate when the latest cached server information is older than the specified seconds (604800 seconds = 7 days)
- use_geocode: (default: True) find address with the longitude/latitude for each entry
- use_geocode_email: (default: True) use email to avoid abuse of address lookup
- language: (default: en) the Bluelink App is reset to English for users who have set another language in the Bluelink App in Europe when using hyundai_kia_connect_api, you can configure another language as workaround

Note: language is only implemented for Europe currently.
[For a list of language codes, see here.](https://www.science.co.il/language/Codes.php). Currently in Europe the Bluelink App shows the following languages:
- "en" English
- "de" German 
- "fr" French
- "it" Italian
- "es" Spanish
- "sv" Swedish
- "nl" Dutch
- "no" Norwegian
- "cs" Czech
- "sk" Slovak
- "hu" Hungarian
- "da" Danish
- "pl" Polish
- "fi" Finnish
- "pt" Portuguese

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
- address (dependent on use_geocode configuration)

Following information from hyundai_kia_connect_api is added to the monitor.dailystats.csv file (gathered by the car, so not computed by summary.py), with per day the following information:
- date
- distance
- distance_unit
- total_consumed Wh
- regenerated_energy Wh
- engine_consumption Wh
- climate_consumption Wh
- onboard_electronics_consumption Wh
- battery_care_consumption Wh

This information is used by the other tools:
- summary.py
- kml.py
- shrink.py

The monitor tool will by default only do a forced update when the last server update is more than 7 days ago, so the 12 volt battery is NOT drained by the tool. 
This time difference is configurable, so you can decide to do it more often, e.g. once a day.
But you have also the option to only use cacheupdate as parameter to monitor.py, so never the car is asked for actual values by the tool.
And you can also run a forceupdate as parameter to monitor.py, or e.g. once a day.
Choose the options you like the most.

Note that the number of API calls is restricted for Hyundai Bluelink or Kia UVO Connect users, see [this page for API Rate Limits](https://github.com/Hacksore/bluelinky/wiki/API-Rate-Limits)
```
Region Daily Limits    Per Action  Comments
- USA  30              10  
- CA   TBD             TBD         You must wait 90 seconds before vehicle commands
- EU   200         
- KR   ???
```

So maybe you can capture more than once per hour, but you might run into the problem that you use too much API calls, especially when you also regularly use the Hyndai Bluelink or Kia UVO Connect app.
You also can consider only to monitor between e.g. 6:00 and 22:00 (saves 1/3 of the calls). Dependent on your regular driving habit, choose the best option for you. Examples:
- twice a day, e.g. 6.00 and 21:00, when you normally do not drive that late in the evening and charge in the night after 21:00
- each hour means 24 requests per day
- each hour between 6:00 and 19:00 means 13 requests per day
- each hour between 6:00 and 22:00 means 16 requests per day
- each half hour means 48 requests per day
- each half hour between 6:00 and 19:00 means 26 requests per day
- each half hour between 6:00 and 22:00 means 32 requests per day
- each quarter hour means 96 requests per day
- each quarter hour between 6:00 and 19:00 means 52 requests per day
- each quarter hour between 6:00 and 22:00 means 64 requests per day

## python monitor.py cacheupdate
If you only ask for cached values, the car will not be woken up, the 12 volt battery of the car will not be drained by the tool and you will only get the cached values from the server.

The car sends the updates (push messages) to the server when something happens on the car side. This is the case when the car is started or switched off, when charging is complete and possibly in other situations.
So no extra drain of the 12 volt battery because of the hyundai_kia_connect_monitor tool!

And of course when you run an update or command through the Bluelink app, but that is on purpose.

I do not know if the cacheupdate calls are part of the daily limits or if this is only related to forceupdate.
Because in Europe the limit is 200, I did choose to run once per 15 minutes, so more accurate trips and charging sessions are recorded.
No 12 volt battery drain, because of server calls using cached values only.
- python monitor.py cacheupdate

See also [Raspberry Pi Configuration](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor#raspberry-pi-configuration)

## python monitor.py forceupdate
I did choose to run forceupdate once per day at 6:10 in the morning:
- python monitor.py forceupdate

Note that if you do a lot of forceupdate calls, than definitely the car 12 volt battery can be drained.
See [here some results of someone with an IONIQ 5 using forceupdate](https://community.home-assistant.io/t/hyundai-bluelink-integration/319129/132), so use this forceupdate option carefully:
```
With 15-minute forced updates:
95% to 80% in 8 hours, approx. 1.8%/hour

With 60-minute forced updates:
93% to 82% in 14 hours, approx. 0.78%/hour
```

# summary.py
make summary per TRIP, DAY, WEEK, MONTH, YEAR or a combination with monitor.csv as input or monitor.VIN.csv (latter if vin=VIN is given as parameter)

Usage: 
```
python summary.py
or 
python summary.py vin=VIN
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
- INPUTFILE: monitor.csv or monitor.VIN.csv (latter if vin=VIN is given as parameter)
- standard output: summary per TRIP, DAY, WEEK, MONTH, YEAR in csv format, default all summaries when no parameters given

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

# summary.py sheetupdate
make summary per DAY, WEEK, MONTH, YEAR with monitor.csv as input and write summary to Google Spreadsheet

Usage: 
```
python summary.py sheetupdate
or
python summary.py sheetupdate vin=VIN
```

- INPUTFILE: summary.cfg (configuration of kilometers or miles, net battery size in kWh, average cost per kWh and cost currency)
- INPUTFILE: monitor.csv or or monitor.VIN.csv (latter if vin=VIN is given as parameter)
- standard output: summary per DAY, WEEK, MONTH, YEAR in csv format
- Google spreadsheet update with name: hyundai-kia-connect-monitor or monitor.VIN or (latter if vin=VIN is given as parameter)

For easier use on a mobile phone, the spreadsheet will contain first the overall information in row 1 till 20:
- Last update
- Last entry
- Odometer km
- Driven km
- +kWh
- -kWh
-  km/kWh
- kWh/100km
- Cost Euro
- Current SOC%
- Average SOC%
- Min SOC%
- Max SOC%
- Current 12V%
- Average 12V%
- Min 12V%
- Max 12V%
- #Charges
- #Trips

And thereafter the last 50 lines of the summary in reverse order, so you do not need to scroll to the bottom for the latest values. The following columns per row:
```
  Period     date        info    odometer    delta km       +kWh         -kWh    km/kWh  kWh/100km   cost Euro   SOC%CUR    AVG MIN MAX  12V%CUR    AVG MIN MAX  #charges      #trips      address
```
  
## configuration of gspread for "python summary.py sheetupdate"
For updating the Google Spreadsheet, summary.py is using the package gspread. For Authentication with Google Spreadsheet you have to configure authentication for gspread. This [authentication configuration is described here](https://docs.gspread.org/en/latest/oauth2.html)
The summary.py script uses access to the Google spreadsheets on behalf of a bot account using Service Account.
Follow the steps in this link above, here is the summary of these steps:
- Enable API Access for a Project
- - Head to [Google Developers Console](https://console.developers.google.com/) and create a new project (or select the one you already have).
- - In the box labeled "Search for APIs and Services", search for "Google Drive API" and enable it.
- - In the box labeled "Search for APIs and Services", search for "Google Sheets API" and enable it
- For Bots: Using Service Account
- - Go to "APIs & Services > Credentials" and choose "Create credentials > Service account key".
- - Fill out the form
- - Click "Create" and "Done".
- - Press "Manage service accounts" above Service Accounts.
- - Press on : near recently created service account and select Manage keys and then click on "ADD KEY > Create new key".
- - Select JSON key type and press "Create".
- - You will automatically download a JSON file with credentials
- - Remember the path to the downloaded credentials json file. Also, in the next step you will need the value of client_email from this file.
- - Move the downloaded json file to ~/.config/gspread/service_account.json. Windows users should put this file to %APPDATA%\gspread\service_account.json.
- Setup a Google Spreasheet to be updated by sheetupdate
- - In Google Spreadsheet, create an empty Google Spreadsheet with the name: hyundai-kia-connect-monitor or monitor.VIN (latter if if vin=VIN is given as parameter)
- - Go to your spreadsheet and share it with a client_email from the step above
- run "python summary.py sheetupdate" and if everything is correct, the hyundai-kia-connect-monitor or monitor.VIN spreadheet will be updated with a summary and the last 50 lines of standard output
- configure to run "python summary.py sheetupdate" regularly, after having run "python monitor.py"

# kml.py
Transform the monitor.csv data to monitor.kml, so you can use it in e.g. Google My Maps to see on a map the captured locations.
Lines are not written, when the following info is the same as previous line: longitude, latitude, engineOn, charging

Usage: 
```
python kml.py 
or
python kml.py vin=VIN
```
- INPUTFILE: monitor.csv or monitor.VIN.csv (latter if vin=VIN as parameter given)
- OUTPUTFILE: monitor.kml or monitor.VIN.kml (latter if vin=VIN as parameter given)
- standard output: summary per kml placemark

The following information is written in the kml file:
- document name: monitor + now in format "yyyymmdd hh:mm"
- per placemark
- - name of place (index of Google Maps): datetime in format "yyyymmdd hh:mm" and optionally "C" when charging and "D" when in drive
- - description: SOC: nn% 12V: nn% ODO: odometer [(+distance since yyyymmdd hh:mm)] [drive] [charging] [plugged: n]
- - coordinate (longitude, latitude)

Note:
- the placemark lines are one-liners, so you can also search in monitor.kml

[How to import kml in Google Maps](https://www.spotzi.com/en/about/help-center/how-to-import-a-kml-into-google-maps/)

# shrink.py
Simple Python3 script to shrink monitor.csv, identical lines removed (first date/time column excluded). Handy for analyzing with other tools (e.g. Excel) with less data.

Usage:
```
python shrink.py
or
python shrink.py vin=VIN
```
- INPUTFILE: monitor.csv or monitor.VIN.csv (latter if vin=VIN as parameter given)
- OUTPUTFILE: shrinked_monitor.csv or shrinked_monitor.vin.csv (latter if vin=VIN as parameter given)

Note: 
- True and False for EngineOn and Driving are replaced into respectively 1 and 0, so it is shorter and easier usable in e.g. Excel.

# Raspberry pi configuration
Example script [run_monitor_once.sh](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/run_monitor_once.sh) to run monitor.py on a linux based system.

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

I also want to update the google spreadsheet, so I adapted [run_monitor_once.sh](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/run_monitor_once.sh) to run a summary after running cacheupdate.
The last line of run_monitor_once.sh is changed into:
```
/usr/bin/python -u ~/hyundai_kia_connect_monitor/monitor.py cacheupdate >> run_monitor_once.log 2>&1
/usr/bin/python -u ~/hyundai_kia_connect_monitor/summary.py trip sheetupdate > run_monitor_once.summary.log 2>&1
```

And I did configure to run cacheupdate every 15 minutes (I have a 200 API calls limit in Europe and cacheupdate does not drain 12 volt battery).
crontab -e:
```
*/15 * * * * ~/hyundai_kia_connect_monitor/run_monitor_once.sh >> ~/hyundai_kia_connect_monitor/run_monitor_once.log 2>&1
```

# debug.py
Same sort of python script as monitor.py, but debug logging enabled and all the (internal) data is just printed to standard output in pretty print.
It uses the configuration from monitor.cfg.

Usage:
```
python debug.py
```
- INPUTFILE: monitor.cfg (configuration of input to hyundai_kia_connect_api)
- standard output: debug output and pretty print of the data got from API calls

# Examples
## monitor.csv

Here a csv file from 2022-09-17 till 2022-09-25 (about one week). I started with capturing once per hour. At 2022-09-20 I changed into once each half hour between 6:00 and 19:30, because I barely drive in the evening and still not too many captures per day. 

Example output file [monitor.csv](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/monitor.csv)

My crontab for this:

```
*/30 6-19 * * * ~/hyundai_kia_connect_monitor/run_monitor_once.sh >> ~/hyundai_kia_connect_monitor/run_monitor_once.log 2>&1
```

Example output file [monitor.dailystats.csv](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/monitor.dailystats.csv)

## python summary.py

The summary.py [standard output of the previous monitor.csv file](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/summary.py_output.txt)

output:
```
C:\Users\Rick\git\monitor>python summary.py
  Period, date      , info , odometer, delta km,    +kWh,     -kWh, km/kWh, kWh/100km, cost Euro, SOC%CUR,AVG,MIN,MAX, 12V%CUR,AVG,MIN,MAX, #charges,   #trips
DAY     , 2022-09-17, Sat  ,  17324.2,         ,     2.8,         ,       ,          ,          ,      58, 55, 55, 58,      91, 91, 91, 91,      1  ,         
DAY     , 2022-09-18, Sun  ,  17324.2,         ,     0.7,         ,       ,          ,          ,      59, 59, 59, 60,      91, 91, 91, 91,         ,         
WEEK    , 2022-09-18, WK 37,  17324.2,         ,     3.5,         ,       ,          ,          ,      59, 59, 55, 60,      91, 91, 91, 91,      1  ,         
TRIP    , 2022-09-19, 15:00,  17324.3,      0.1,        ,         ,       ,          ,          ,      61, 60, 60, 61,      85, 90, 85, 91,         ,      1  
TRIP    , 2022-09-19, 16:00,  17330.7,      6.4,        ,     -1.4,       ,          ,          ,      59, 60, 59, 59,      86, 85, 86, 86,         ,      1  
DAY     , 2022-09-19, Mon  ,  17330.7,      6.5,        ,         ,       ,          ,          ,      59, 60, 59, 61,      86, 88, 85, 91,         ,      2  
TRIP    , 2022-09-20, 08:00,  17358.9,     28.2,        ,     -4.2,    6.7,      14.9,      1.03,      53, 57, 53, 59,      91, 88, 88, 91,         ,      1  
TRIP    , 2022-09-20, 15:30,  17371.5,     12.6,        ,     -2.1,    6.0,      16.7,      0.52,      48, 50, 48, 51,      92, 90, 87, 92,         ,      1  
TRIP    , 2022-09-20, 15:58,  17378.3,      6.8,        ,     -0.7,       ,          ,          ,      47, 47, 47, 47,      91, 91, 91, 91,         ,      1  
DAY     , 2022-09-20, Tue  ,  17378.3,     47.6,        ,     -7.0,    6.8,      14.7,      1.72,      45, 48, 45, 59,      91, 91, 87, 92,         ,      3  
TRIP    , 2022-09-21, 12:30,  17380.8,      2.5,     4.9,         ,       ,          ,          ,      52, 48, 46, 52,      92, 91, 91, 92,      1  ,      1  
TRIP    , 2022-09-21, 13:00,  17383.5,      2.7,        ,     -0.7,       ,          ,          ,      51, 51, 51, 51,      91, 91, 91, 91,         ,      1  
DAY     , 2022-09-21, Wed  ,  17383.5,      5.2,    18.2,     -0.7,       ,          ,          ,      70, 63, 46, 70,      91, 91, 91, 92,      2  ,      2  
DAY     , 2022-09-22, Thu  ,  17383.5,         ,        ,         ,       ,          ,          ,      72, 72, 72, 72,      91, 91, 91, 91,      1  ,         
TRIP    , 2022-09-23, 11:21,  17385.4,      1.9,        ,     -0.7,       ,          ,          ,      71, 71, 71, 71,      88, 89, 88, 88,         ,      1  
TRIP    , 2022-09-23, 12:00,  17387.1,      1.7,     0.7,         ,       ,          ,          ,      72, 71, 72, 72,      87, 87, 87, 87,      1  ,      1  
DAY     , 2022-09-23, Fri  ,  17387.1,      3.6,    20.3,     -0.7,       ,          ,          ,     100, 86, 71,100,      87, 87, 87, 88,      2  ,      2  
TRIP    , 2022-09-24, 09:57,  17390.8,      3.7,        ,     -0.7,       ,          ,          ,      99,100, 99,100,      95, 94, 95, 95,         ,      1  
TRIP    , 2022-09-24, 13:21,  17589.2,    198.4,        ,    -32.9,    6.0,      16.6,      8.09,      52, 80, 52, 98,      96, 96, 92, 98,         ,      1  
TRIP    , 2022-09-24, 14:31,  17592.5,      3.3,        ,     -0.7,       ,          ,          ,      51, 51, 51, 51,      94, 95, 94, 94,         ,      1  
TRIP    , 2022-09-24, 15:23,  17597.3,      4.8,        ,     -0.7,       ,          ,          ,      50, 51, 50, 51,      96, 94, 93, 96,         ,      1  
TRIP    , 2022-09-24, 19:00,  17794.9,    197.6,        ,    -31.5,    6.3,      15.9,      7.75,       5, 30,  5, 50,      97, 95, 94, 97,      1  ,      1  
DAY     , 2022-09-24, Sat  ,  17794.9,    407.8,    25.9,    -66.5,    6.1,      16.3,     16.36,      42, 40,  5,100,      97, 96, 92, 98,      1  ,      5  
DAY     , 2022-09-25, Sun  ,  17794.9,         ,     5.6,         ,       ,          ,          ,      50, 50, 43, 50,      97, 97, 97, 97,         ,         
WEEK    , 2022-09-25, WK 38,  17794.9,    470.7,    67.2,    -73.5,    6.4,      15.6,     18.08,      50, 50,  5,100,      97, 97, 85, 98,      6  ,     14  
MONTH   , 2022-09-25, Sep  ,  17794.9,    470.7,    70.7,    -73.5,    6.4,      15.6,     18.08,      50, 50,  5,100,      97, 97, 85, 98,      7  ,     14  
YEAR    , 2022-09-25, 2022 ,  17794.9,    470.7,    70.7,    -73.5,    6.4,      15.6,     18.08,      50, 50,  5,100,      97, 97, 85, 98,      7  ,     14  
TRIPAVG , 2022-09-25,  14t ,  17794.9,     33.6,     5.0,     -5.2,    6.4,      15.6,      1.29,      50, 50,  5,100,      97, 97, 85, 98,      0.5,      1  
DAYAVG  , 2022-09-25,   9d ,  17794.9,     52.3,     7.9,     -8.2,    6.4,      15.6,      2.01,      50, 50,  5,100,      97, 97, 85, 98,      0.8,      1.6
WEEKAVG , 2022-09-25,   9d ,  17794.9,    366.1,    55.0,    -57.2,    6.4,      15.6,     14.06,      50, 50,  5,100,      97, 97, 85, 98,      5.4,     10.9
MONTHAVG, 2022-09-25,   9d ,  17794.9,   1590.8,   238.9,   -248.4,    6.4,      15.6,     61.11,      50, 50,  5,100,      97, 97, 85, 98,     23.7,     47.3
YEARLY  , 2022-09-25,   9d ,  17794.9,  19089.5,  2867.3,  -2980.8,    6.4,      15.6,    733.29,      50, 50,  5,100,      97, 97, 85, 98,    283.9,    567.8
```

- 2022-09-24 I did a trip from 100% SOC to 5% SOC (-66.5 kWh)
- have driven 407.8 km and started charging when back at home. 
- 198.4 km one way with 6.0 km/kWh and 16.6 kWh/100km, 197.6 km back with 6.3 km/kWh and 15.9 km/kWh.
- also shown is the average, minimum and maximum State Of Charge percentage and average, minimum and maximum of 12 Volt percentage. 
- for better readability zero values are left out, because of configuration show_zero_values = False
- At the end, averages are shown based on the data so far, TRIPAVG, DAYAVG, WEEKAVG, MONTHAVG and the prediction for a year: YEARLY

The SOC% can be used to see your habits about charging. Because wrongly someone posted for the IONIQ 5:
> My dealer told me that Hyundai has no restrictions on battery charging. So that it is not an issue to just load up to 100% (and leave it). Have you heard any stories other than this?

Depends on how long you want to drive it :-) The car is guaranteed up to 70% capacity (8 years or 160,000 km). 
- You can charge a battery maybe about 1000x (from 0% to 100% or 2x from 50% to 100%, etc) with the dealers advice (do not look at it). With a 72 kWh battery and 5 km/kWh you can drive 360,000 km until it is 70%. 
- Only if you do care about your battery and, for example, do not leave it at 100% for a long time and only charge to 100% when necessary, do not drive completely empty before you start charging again, drive economically, you can charge up to maybe 4000x. With a 72 kWh battery and 6 km/kWh you can drive almost 2 million km until it is 70%. The advantage is that you hardly lose any range over the years. 

There is also a buffer in the batteries so opponents will say that 100% is maybe only 95% and the manufacturer has already taken this into account. Yes, to claim under the warranty yes, but it is simply better not to always fully charge the batteries and almost completely empty. That is true even with a phone. 
A lease driver may not care, I bought the car privately and want to use it as long as possible. And of course it is also better for the climate not to wear out batteries unnecessarily. 

My previous Kia EV Soul with 27 kWh battery has driven 145,000 km in 7 years and the State Of Health (SOH) was still 91% and I was able to make someone else happy (I hope). There are plenty of people who have had to replace the battery because it was already below 70% SOH under warranty (7 years or 150,000 km). So being sensible with the battery certainly helps. 

But in the summary above, you see that my average SOC is 59%, which is pretty good.

Also the 12 Volt battery is shown and it has not become beneath 85%, with an average of 91%. Here the mapping of percentage to volt for a typical Lead Acid Battery:

![alt text](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/Lead-Acid-Battery-Voltage-Charts.jpg)

Example output when filtering on DAY:
```
C:\Users\Rick\git\monitor>python summary.py day
  Period, date      , info , odometer, delta km,    +kWh,     -kWh, km/kWh, kWh/100km, cost Euro, SOC%CUR,AVG,MIN,MAX, 12V%CUR,AVG,MIN,MAX, #charges,   #trips
DAY     , 2022-09-17, Sat  ,  17324.2,         ,     2.8,         ,       ,          ,          ,      58, 55, 55, 58,      91, 91, 91, 91,      1  ,         
DAY     , 2022-09-18, Sun  ,  17324.2,         ,     0.7,         ,       ,          ,          ,      59, 59, 59, 60,      91, 91, 91, 91,         ,         
DAY     , 2022-09-19, Mon  ,  17330.7,      6.5,        ,         ,       ,          ,          ,      59, 60, 59, 61,      86, 88, 85, 91,         ,      2  
DAY     , 2022-09-20, Tue  ,  17378.3,     47.6,        ,     -7.0,    6.8,      14.7,      1.72,      45, 48, 45, 59,      91, 91, 87, 92,         ,      3  
DAY     , 2022-09-21, Wed  ,  17383.5,      5.2,    18.2,     -0.7,       ,          ,          ,      70, 63, 46, 70,      91, 91, 91, 92,      2  ,      2  
DAY     , 2022-09-22, Thu  ,  17383.5,         ,        ,         ,       ,          ,          ,      72, 72, 72, 72,      91, 91, 91, 91,      1  ,         
DAY     , 2022-09-23, Fri  ,  17387.1,      3.6,    20.3,     -0.7,       ,          ,          ,     100, 86, 71,100,      87, 87, 87, 88,      2  ,      2  
DAY     , 2022-09-24, Sat  ,  17794.9,    407.8,    25.9,    -66.5,    6.1,      16.3,     16.36,      42, 40,  5,100,      97, 96, 92, 98,      1  ,      5  
DAY     , 2022-09-25, Sun  ,  17794.9,         ,     5.6,         ,       ,          ,          ,      50, 50, 43, 50,      97, 97, 97, 97,         ,         
```

Example output when filtering on TRIP:
```
C:\Users\Rick\git\monitor>python summary.py trip
Period, date      , info , odometer, delta km,    +kWh,     -kWh, km/kWh, kWh/100km, cost Euro, SOC%CUR,AVG,MIN,MAX, 12V%CUR,AVG,MIN,MAX, #charges, #drives
TRIP  , 2022-09-19, 15:00,  17324.3,      0.1,        ,         ,       ,          ,          ,      61, 60, 60, 61,      85, 90, 85, 91,         ,       1
TRIP  , 2022-09-19, 16:00,  17330.7,      6.4,        ,     -1.4,       ,          ,          ,      59, 60, 59, 59,      86, 85, 86, 86,         ,       1
TRIP  , 2022-09-20, 08:00,  17358.9,     28.2,        ,     -4.2,    6.7,      14.9,      1.03,      53, 57, 53, 59,      91, 88, 88, 91,         ,       1
TRIP  , 2022-09-20, 15:30,  17371.5,     12.6,        ,     -2.1,    6.0,      16.7,      0.52,      48, 50, 48, 51,      92, 90, 87, 92,         ,       1
TRIP  , 2022-09-20, 15:58,  17378.3,      6.8,        ,     -0.7,       ,          ,          ,      47, 47, 47, 47,      91, 91, 91, 91,         ,       1
TRIP  , 2022-09-21, 12:30,  17380.8,      2.5,     4.9,         ,       ,          ,          ,      52, 48, 46, 52,      92, 91, 91, 92,        1,       1
TRIP  , 2022-09-21, 13:00,  17383.5,      2.7,        ,     -0.7,       ,          ,          ,      51, 51, 51, 51,      91, 91, 91, 91,         ,       1
TRIP  , 2022-09-23, 11:21,  17385.4,      1.9,        ,     -0.7,       ,          ,          ,      71, 71, 71, 71,      88, 89, 88, 88,         ,       1
TRIP  , 2022-09-23, 12:00,  17387.1,      1.7,     0.7,         ,       ,          ,          ,      72, 71, 72, 72,      87, 87, 87, 87,        1,       1
TRIP  , 2022-09-24, 09:57,  17390.8,      3.7,        ,     -0.7,       ,          ,          ,      99,100, 99,100,      95, 94, 95, 95,         ,       1
TRIP  , 2022-09-24, 13:21,  17589.2,    198.4,        ,    -32.9,    6.0,      16.6,      8.09,      52, 80, 52, 98,      96, 96, 92, 98,         ,       1
TRIP  , 2022-09-24, 14:31,  17592.5,      3.3,        ,     -0.7,       ,          ,          ,      51, 51, 51, 51,      94, 95, 94, 94,         ,       1
TRIP  , 2022-09-24, 15:23,  17597.3,      4.8,        ,     -0.7,       ,          ,          ,      50, 51, 50, 51,      96, 94, 93, 96,         ,       1
TRIP  , 2022-09-24, 19:00,  17794.9,    197.6,        ,    -31.5,    6.3,      15.9,      7.75,       5, 30,  5, 50,      97, 95, 94, 97,        1,       1

```

Example output when filtering on DAY and TRIP:
```
C:\Users\Rick\git\monitor>python summary.py day trip
  Period, date      , info , odometer, delta km,    +kWh,     -kWh, km/kWh, kWh/100km, cost Euro, SOC%CUR,AVG,MIN,MAX, 12V%CUR,AVG,MIN,MAX, #charges,   #trips
DAY     , 2022-09-17, Sat  ,  17324.2,         ,     2.8,         ,       ,          ,          ,      58, 55, 55, 58,      91, 91, 91, 91,      1  ,         
DAY     , 2022-09-18, Sun  ,  17324.2,         ,     0.7,         ,       ,          ,          ,      59, 59, 59, 60,      91, 91, 91, 91,         ,         
TRIP    , 2022-09-19, 15:00,  17324.3,      0.1,        ,         ,       ,          ,          ,      61, 60, 60, 61,      85, 90, 85, 91,         ,      1  
TRIP    , 2022-09-19, 16:00,  17330.7,      6.4,        ,     -1.4,       ,          ,          ,      59, 60, 59, 59,      86, 85, 86, 86,         ,      1  
DAY     , 2022-09-19, Mon  ,  17330.7,      6.5,        ,         ,       ,          ,          ,      59, 60, 59, 61,      86, 88, 85, 91,         ,      2  
TRIP    , 2022-09-20, 08:00,  17358.9,     28.2,        ,     -4.2,    6.7,      14.9,      1.03,      53, 57, 53, 59,      91, 88, 88, 91,         ,      1  
TRIP    , 2022-09-20, 15:30,  17371.5,     12.6,        ,     -2.1,    6.0,      16.7,      0.52,      48, 50, 48, 51,      92, 90, 87, 92,         ,      1  
TRIP    , 2022-09-20, 15:58,  17378.3,      6.8,        ,     -0.7,       ,          ,          ,      47, 47, 47, 47,      91, 91, 91, 91,         ,      1  
DAY     , 2022-09-20, Tue  ,  17378.3,     47.6,        ,     -7.0,    6.8,      14.7,      1.72,      45, 48, 45, 59,      91, 91, 87, 92,         ,      3  
TRIP    , 2022-09-21, 12:30,  17380.8,      2.5,     4.9,         ,       ,          ,          ,      52, 48, 46, 52,      92, 91, 91, 92,      1  ,      1  
TRIP    , 2022-09-21, 13:00,  17383.5,      2.7,        ,     -0.7,       ,          ,          ,      51, 51, 51, 51,      91, 91, 91, 91,         ,      1  
DAY     , 2022-09-21, Wed  ,  17383.5,      5.2,    18.2,     -0.7,       ,          ,          ,      70, 63, 46, 70,      91, 91, 91, 92,      2  ,      2  
DAY     , 2022-09-22, Thu  ,  17383.5,         ,        ,         ,       ,          ,          ,      72, 72, 72, 72,      91, 91, 91, 91,      1  ,         
TRIP    , 2022-09-23, 11:21,  17385.4,      1.9,        ,     -0.7,       ,          ,          ,      71, 71, 71, 71,      88, 89, 88, 88,         ,      1  
TRIP    , 2022-09-23, 12:00,  17387.1,      1.7,     0.7,         ,       ,          ,          ,      72, 71, 72, 72,      87, 87, 87, 87,      1  ,      1  
DAY     , 2022-09-23, Fri  ,  17387.1,      3.6,    20.3,     -0.7,       ,          ,          ,     100, 86, 71,100,      87, 87, 87, 88,      2  ,      2  
TRIP    , 2022-09-24, 09:57,  17390.8,      3.7,        ,     -0.7,       ,          ,          ,      99,100, 99,100,      95, 94, 95, 95,         ,      1  
TRIP    , 2022-09-24, 13:21,  17589.2,    198.4,        ,    -32.9,    6.0,      16.6,      8.09,      52, 80, 52, 98,      96, 96, 92, 98,         ,      1  
TRIP    , 2022-09-24, 14:31,  17592.5,      3.3,        ,     -0.7,       ,          ,          ,      51, 51, 51, 51,      94, 95, 94, 94,         ,      1  
TRIP    , 2022-09-24, 15:23,  17597.3,      4.8,        ,     -0.7,       ,          ,          ,      50, 51, 50, 51,      96, 94, 93, 96,         ,      1  
TRIP    , 2022-09-24, 19:00,  17794.9,    197.6,        ,    -31.5,    6.3,      15.9,      7.75,       5, 30,  5, 50,      97, 95, 94, 97,      1  ,      1  
DAY     , 2022-09-24, Sat  ,  17794.9,    407.8,    25.9,    -66.5,    6.1,      16.3,     16.36,      42, 40,  5,100,      97, 96, 92, 98,      1  ,      5  
DAY     , 2022-09-25, Sun  ,  17794.9,         ,     5.6,         ,       ,          ,          ,      50, 50, 43, 50,      97, 97, 97, 97,         ,         
```

Example output when filtering on WEEK:
```
C:\Users\Rick\git\monitor>python summary.py week
  Period, date      , info , odometer, delta km,    +kWh,     -kWh, km/kWh, kWh/100km, cost Euro, SOC%CUR,AVG,MIN,MAX, 12V%CUR,AVG,MIN,MAX, #charges,   #trips
WEEK    , 2022-09-18, WK 37,  17324.2,         ,     3.5,         ,       ,          ,          ,      59, 59, 55, 60,      91, 91, 91, 91,      1  ,         
WEEK    , 2022-09-25, WK 38,  17794.9,    470.7,    67.2,    -73.5,    6.4,      15.6,     18.08,      50, 50,  5,100,      97, 97, 85, 98,      6  ,     14  
```

Example output when filtering on MONTH:
```
C:\Users\Rick\git\monitor>python summary.py month
  Period, date      , info , odometer, delta km,    +kWh,     -kWh, km/kWh, kWh/100km, cost Euro, SOC%CUR,AVG,MIN,MAX, 12V%CUR,AVG,MIN,MAX, #charges,   #trips
MONTH   , 2022-09-25, Sep  ,  17794.9,    470.7,    70.7,    -73.5,    6.4,      15.6,     18.08,      50, 50,  5,100,      97, 97, 85, 98,      7  ,     14  
```

Example output when filtering on YEAR:
```
C:\Users\Rick\git\monitor>python summary.py year
  Period, date      , info , odometer, delta km,    +kWh,     -kWh, km/kWh, kWh/100km, cost Euro, SOC%CUR,AVG,MIN,MAX, 12V%CUR,AVG,MIN,MAX, #charges,   #trips
YEAR    , 2022-09-25, 2022 ,  17794.9,    470.7,    70.7,    -73.5,    6.4,      15.6,     18.08,      50, 50,  5,100,      97, 97, 85, 98,      7  ,     14  
TRIPAVG , 2022-09-25,  14t ,  17794.9,     33.6,     5.0,     -5.2,    6.4,      15.6,      1.29,      50, 50,  5,100,      97, 97, 85, 98,      0.5,      1  
DAYAVG  , 2022-09-25,   9d ,  17794.9,     52.3,     7.9,     -8.2,    6.4,      15.6,      2.01,      50, 50,  5,100,      97, 97, 85, 98,      0.8,      1.6
WEEKAVG , 2022-09-25,   9d ,  17794.9,    366.1,    55.0,    -57.2,    6.4,      15.6,     14.06,      50, 50,  5,100,      97, 97, 85, 98,      5.4,     10.9
MONTHAVG, 2022-09-25,   9d ,  17794.9,   1590.8,   238.9,   -248.4,    6.4,      15.6,     61.11,      50, 50,  5,100,      97, 97, 85, 98,     23.7,     47.3
YEARLY  , 2022-09-25,   9d ,  17794.9,  19089.5,  2867.3,  -2980.8,    6.4,      15.6,    733.29,      50, 50,  5,100,      97, 97, 85, 98,    283.9,    567.8
```

Note that you see also a prediction (YEARLY) how many kilometers (or miles) you will drive, based on the 9 days of capture. 
Also how much kWh you will approximately need for this distance, and based on the consumption and cost per kWh, how much this will cost.
Averages for DAY, WEEK, MONTH are shown, based on these 9 days. And also the average per trip, based on 14 trips in this example.

Example output when showing everything except TRIP:
```
C:\Users\Rick\git\monitor>python summary.py -trip
  Period, date      , info , odometer, delta km,    +kWh,     -kWh, km/kWh, kWh/100km, cost Euro, SOC%CUR,AVG,MIN,MAX, 12V%CUR,AVG,MIN,MAX, #charges,   #trips
DAY     , 2022-09-17, Sat  ,  17324.2,         ,     2.8,         ,       ,          ,          ,      58, 55, 55, 58,      91, 91, 91, 91,      1  ,         
DAY     , 2022-09-18, Sun  ,  17324.2,         ,     0.7,         ,       ,          ,          ,      59, 59, 59, 60,      91, 91, 91, 91,         ,         
WEEK    , 2022-09-18, WK 37,  17324.2,         ,     3.5,         ,       ,          ,          ,      59, 59, 55, 60,      91, 91, 91, 91,      1  ,         
DAY     , 2022-09-19, Mon  ,  17330.7,      6.5,        ,         ,       ,          ,          ,      59, 60, 59, 61,      86, 88, 85, 91,         ,      2  
DAY     , 2022-09-20, Tue  ,  17378.3,     47.6,        ,     -7.0,    6.8,      14.7,      1.72,      45, 48, 45, 59,      91, 91, 87, 92,         ,      3  
DAY     , 2022-09-21, Wed  ,  17383.5,      5.2,    18.2,     -0.7,       ,          ,          ,      70, 63, 46, 70,      91, 91, 91, 92,      2  ,      2  
DAY     , 2022-09-22, Thu  ,  17383.5,         ,        ,         ,       ,          ,          ,      72, 72, 72, 72,      91, 91, 91, 91,      1  ,         
DAY     , 2022-09-23, Fri  ,  17387.1,      3.6,    20.3,     -0.7,       ,          ,          ,     100, 86, 71,100,      87, 87, 87, 88,      2  ,      2  
DAY     , 2022-09-24, Sat  ,  17794.9,    407.8,    25.9,    -66.5,    6.1,      16.3,     16.36,      42, 40,  5,100,      97, 96, 92, 98,      1  ,      5  
DAY     , 2022-09-25, Sun  ,  17794.9,         ,     5.6,         ,       ,          ,          ,      50, 50, 43, 50,      97, 97, 97, 97,         ,         
WEEK    , 2022-09-25, WK 38,  17794.9,    470.7,    67.2,    -73.5,    6.4,      15.6,     18.08,      50, 50,  5,100,      97, 97, 85, 98,      6  ,     14  
MONTH   , 2022-09-25, Sep  ,  17794.9,    470.7,    70.7,    -73.5,    6.4,      15.6,     18.08,      50, 50,  5,100,      97, 97, 85, 98,      7  ,     14  
YEAR    , 2022-09-25, 2022 ,  17794.9,    470.7,    70.7,    -73.5,    6.4,      15.6,     18.08,      50, 50,  5,100,      97, 97, 85, 98,      7  ,     14  
TRIPAVG , 2022-09-25,  14t ,  17794.9,     33.6,     5.0,     -5.2,    6.4,      15.6,      1.29,      50, 50,  5,100,      97, 97, 85, 98,      0.5,      1  
DAYAVG  , 2022-09-25,   9d ,  17794.9,     52.3,     7.9,     -8.2,    6.4,      15.6,      2.01,      50, 50,  5,100,      97, 97, 85, 98,      0.8,      1.6
WEEKAVG , 2022-09-25,   9d ,  17794.9,    366.1,    55.0,    -57.2,    6.4,      15.6,     14.06,      50, 50,  5,100,      97, 97, 85, 98,      5.4,     10.9
MONTHAVG, 2022-09-25,   9d ,  17794.9,   1590.8,   238.9,   -248.4,    6.4,      15.6,     61.11,      50, 50,  5,100,      97, 97, 85, 98,     23.7,     47.3
YEARLY  , 2022-09-25,   9d ,  17794.9,  19089.5,  2867.3,  -2980.8,    6.4,      15.6,    733.29,      50, 50,  5,100,      97, 97, 85, 98,    283.9,    567.8
```

You can redirect the standard output to a file, e.g. [summary.day.csv](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/summary.day.csv)

[Excel example using python summary.py day > summary.day.csv](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/blob/main/examples/summary.day.xlsx)

Screenshot of excel example with some graphs:
![alt text](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/summary.day.png)

Below a larger example of using monitor for more than a month:
```
C:\Users\Rick\git\monitor>python summary.py
  Period, date      , info , odometer, delta km,    +kWh,     -kWh, km/kWh, kWh/100km, cost Euro, SOC%CUR,AVG,MIN,MAX, 12V%CUR,AVG,MIN,MAX, #charges,   #trips
DAY     , 2022-09-17, Sat  ,  17324.2,         ,     2.8,         ,       ,          ,          ,      58, 55, 55, 58,      91, 91, 91, 91,      1  ,         
DAY     , 2022-09-18, Sun  ,  17324.2,         ,     0.7,         ,       ,          ,          ,      59, 59, 59, 60,      91, 91, 91, 91,         ,         
WEEK    , 2022-09-18, WK 37,  17324.2,         ,     3.5,         ,       ,          ,          ,      59, 59, 55, 60,      91, 91, 91, 91,      1  ,         
TRIP    , 2022-09-19, 15:00,  17324.3,      0.1,        ,         ,       ,          ,          ,      61, 60, 60, 61,      85, 90, 85, 91,         ,      1  
TRIP    , 2022-09-19, 16:00,  17330.7,      6.4,        ,     -1.4,       ,          ,          ,      59, 60, 59, 59,      86, 85, 86, 86,         ,      1  
DAY     , 2022-09-19, Mon  ,  17330.7,      6.5,        ,         ,       ,          ,          ,      59, 60, 59, 61,      86, 88, 85, 91,         ,      2  
TRIP    , 2022-09-20, 08:00,  17358.9,     28.2,        ,     -4.2,    6.7,      14.9,      1.03,      53, 57, 53, 59,      91, 88, 88, 91,         ,      1  
TRIP    , 2022-09-20, 15:30,  17371.5,     12.6,        ,     -2.1,    6.0,      16.7,      0.52,      48, 51, 48, 53,      92, 90, 87, 92,         ,      1  
TRIP    , 2022-09-20, 15:58,  17378.3,      6.8,        ,     -0.7,       ,          ,          ,      47, 47, 47, 47,      91, 91, 91, 91,         ,      1  
DAY     , 2022-09-20, Tue  ,  17378.3,     47.6,        ,     -7.0,    6.8,      14.7,      1.72,      45, 49, 45, 59,      91, 91, 87, 92,         ,      3  
TRIP    , 2022-09-21, 12:30,  17380.8,      2.5,     4.9,         ,       ,          ,          ,      52, 48, 46, 52,      92, 91, 91, 92,      1  ,      1  
TRIP    , 2022-09-21, 13:00,  17383.5,      2.7,        ,     -0.7,       ,          ,          ,      51, 51, 51, 51,      91, 91, 91, 91,         ,      1  
DAY     , 2022-09-21, Wed  ,  17383.5,      5.2,    18.2,     -0.7,       ,          ,          ,      70, 63, 46, 70,      91, 91, 91, 92,      2  ,      2  
DAY     , 2022-09-22, Thu  ,  17383.5,         ,        ,         ,       ,          ,          ,      72, 72, 72, 72,      91, 91, 91, 91,      1  ,         
TRIP    , 2022-09-23, 11:21,  17385.4,      1.9,        ,     -0.7,       ,          ,          ,      71, 71, 71, 71,      88, 89, 88, 88,         ,      1  
TRIP    , 2022-09-23, 12:00,  17387.1,      1.7,     0.7,         ,       ,          ,          ,      72, 71, 72, 72,      87, 87, 87, 87,      1  ,      1  
DAY     , 2022-09-23, Fri  ,  17387.1,      3.6,    20.3,     -0.7,       ,          ,          ,     100, 86, 71,100,      87, 87, 87, 88,      2  ,      2  
TRIP    , 2022-09-24, 09:57,  17390.8,      3.7,        ,     -0.7,       ,          ,          ,      99,100, 99,100,      95, 94, 95, 95,         ,      1  
TRIP    , 2022-09-24, 13:21,  17589.2,    198.4,        ,    -32.9,    6.0,      16.6,      8.09,      52, 83, 52, 99,      96, 96, 92, 98,         ,      1  
TRIP    , 2022-09-24, 14:31,  17592.5,      3.3,        ,     -0.7,       ,          ,          ,      51, 51, 51, 51,      94, 95, 94, 94,         ,      1  
TRIP    , 2022-09-24, 15:23,  17597.3,      4.8,        ,     -0.7,       ,          ,          ,      50, 51, 50, 51,      96, 94, 93, 96,         ,      1  
TRIP    , 2022-09-24, 19:00,  17794.9,    197.6,        ,    -31.5,    6.3,      15.9,      7.75,       5, 30,  5, 50,      97, 95, 94, 97,      1  ,      1  
DAY     , 2022-09-24, Sat  ,  17794.9,    407.8,    25.9,    -66.5,    6.1,      16.3,     16.36,      42, 42,  5,100,      97, 96, 92, 98,      1  ,      5  
TRIP    , 2022-09-25, 15:00,  17802.8,      7.9,    12.6,     -0.7,       ,          ,          ,      59, 52, 43, 60,      94, 97, 94, 97,         ,      1  
TRIP    , 2022-09-25, 18:00,  17810.9,      8.1,        ,     -0.7,       ,          ,          ,      58, 58, 58, 59,      92, 93, 91, 94,         ,      1  
DAY     , 2022-09-25, Sun  ,  17810.9,     16.0,    12.6,     -0.7,       ,          ,          ,      59, 56, 43, 60,      92, 94, 91, 97,         ,      2  
WEEK    , 2022-09-25, WK 38,  17810.9,    486.7,    74.2,    -74.2,    6.6,      15.2,     18.25,      59, 59,  5,100,      92, 92, 85, 98,      6  ,     16  
DAY     , 2022-09-26, Mon  ,  17810.9,         ,        ,         ,       ,          ,          ,      58, 58, 58, 58,      92, 92, 92, 92,         ,         
TRIP    , 2022-09-27, 07:30,  17817.9,      7.0,        ,     -3.5,    2.0,      50.0,      0.86,      53, 56, 53, 57,      95, 94, 94, 95,         ,      1  
TRIP    , 2022-09-27, 08:00,  17839.1,     21.2,        ,     -0.7,       ,          ,          ,      52, 52, 52, 52,      96, 95, 96, 96,         ,      1  
TRIP    , 2022-09-27, 09:30,  17841.8,      2.7,        ,     -0.7,       ,          ,          ,      51, 51, 51, 51,      94, 94, 94, 94,         ,      1  
TRIP    , 2022-09-27, 10:00,  17844.5,      2.7,        ,     -0.7,       ,          ,          ,      50, 50, 50, 50,      93, 93, 93, 93,         ,      1  
TRIP    , 2022-09-27, 11:00,  17844.6,      0.1,        ,         ,       ,          ,          ,      50, 50, 50, 50,      91, 92, 91, 91,         ,      1  
TRIP    , 2022-09-27, 11:30,  17846.9,      2.3,        ,         ,       ,          ,          ,      50, 50, 50, 50,      92, 91, 92, 92,         ,      1  
TRIP    , 2022-09-27, 16:00,  17853.4,      6.5,        ,     -1.4,       ,          ,          ,      48, 49, 48, 49,      95, 92, 88, 95,         ,      1  
DAY     , 2022-09-27, Tue  ,  17853.4,     42.5,        ,     -9.8,    4.3,      23.1,      2.41,      44, 48, 44, 57,      95, 94, 88, 96,         ,      7  
TRIP    , 2022-09-28, 09:30,  17858.5,      5.1,        ,     -0.7,       ,          ,          ,      43, 43, 43, 43,      89, 92, 89, 89,         ,      1  
TRIP    , 2022-09-28, 12:30,  17863.6,      5.1,        ,     -0.7,       ,          ,          ,      42, 42, 42, 42,      88, 88, 88, 88,         ,      1  
DAY     , 2022-09-28, Wed  ,  17863.6,     10.2,        ,     -1.4,       ,          ,          ,      42, 42, 42, 43,      88, 88, 88, 89,         ,      2  
DAY     , 2022-09-29, Thu  ,  17863.6,         ,        ,         ,       ,          ,          ,      41, 41, 41, 41,      88, 88, 88, 88,         ,         
TRIP    , 2022-09-30, 11:00,  17865.4,      1.8,        ,         ,       ,          ,          ,      41, 41, 41, 41,      89, 88, 88, 89,         ,      1  
TRIP    , 2022-09-30, 11:00,  17867.2,      1.8,        ,         ,       ,          ,          ,      41,  0, 41, 41,      89,  0, 89, 89,         ,      1  
DAY     , 2022-09-30, Fri  ,  17867.2,      3.6,    13.3,         ,       ,          ,          ,      60, 55, 41, 60,      88, 88, 88, 89,      1  ,      2  
MONTH   , 2022-09-30, Sep  ,  17867.2,    543.0,    89.6,    -85.4,    6.4,      15.7,     21.01,      60, 56,  5,100,      88, 91, 85, 98,      8  ,     27  
TRIP    , 2022-10-01, 10:00,  17871.2,      4.0,        ,     -0.7,       ,          ,          ,      59, 59, 59, 59,      90, 89, 90, 90,         ,      1  
DAY     , 2022-10-01, Sat  ,  17871.2,      4.0,        ,         ,       ,          ,          ,      61, 60, 59, 61,      90, 90, 90, 90,      1  ,      1  
TRIP    , 2022-10-02, 11:30,  17948.6,     77.4,        ,    -12.6,    6.1,      16.3,      3.10,      43, 51, 43, 57,      92, 90, 90, 92,         ,      1  
TRIP    , 2022-10-02, 17:00,  18026.2,     77.6,        ,    -12.6,    6.2,      16.2,      3.10,      25, 32, 25, 35,      96, 95, 94, 96,         ,      1  
DAY     , 2022-10-02, Sun  ,  18026.2,    155.0,    17.5,    -25.2,    6.2,      16.3,      6.20,      50, 38, 25, 57,      96, 95, 90, 96,      1  ,      2  
WEEK    , 2022-10-02, WK 39,  18026.2,    215.3,    29.4,    -35.7,    6.0,      16.6,      8.78,      50, 49, 25, 61,      96, 91, 88, 96,      3  ,     14  
DAY     , 2022-10-03, Mon  ,  18026.2,         ,     6.3,         ,       ,          ,          ,      59, 58, 52, 60,      96, 96, 96, 96,         ,         
TRIP    , 2022-10-04, 12:00,  18036.3,     10.1,        ,     -1.4,       ,          ,          ,      57, 57, 57, 57,      92, 93, 92, 92,         ,      1  
TRIP    , 2022-10-04, 12:30,  18045.8,      9.5,        ,     -0.7,       ,          ,          ,      56, 56, 56, 56,      94, 93, 94, 94,         ,      1  
TRIP    , 2022-10-04, 15:00,  18049.8,      4.0,        ,     -2.1,    1.9,      52.5,      0.52,      53, 55, 53, 56,      95, 93, 92, 95,         ,      1  
TRIP    , 2022-10-04, 15:30,  18065.6,     15.8,        ,     -0.7,       ,          ,          ,      52, 52, 52, 52,      96, 95, 96, 96,         ,      1  
DAY     , 2022-10-04, Tue  ,  18065.6,     39.4,        ,     -4.9,    8.0,      12.4,      1.21,      51, 53, 51, 57,      96, 95, 92, 96,         ,      4  
TRIP    , 2022-10-05, 15:30,  18070.6,      5.0,        ,     -0.7,       ,          ,          ,      49, 50, 49, 50,      87, 94, 87, 96,         ,      1  
TRIP    , 2022-10-05, 16:30,  18075.4,      4.8,        ,     -0.7,       ,          ,          ,      48, 48, 48, 48,      86, 86, 86, 86,         ,      1  
TRIP    , 2022-10-05, 18:30,  18076.6,      1.2,        ,     -0.7,       ,          ,          ,      47, 47, 47, 47,      85, 85, 85, 85,         ,      1  
TRIP    , 2022-10-05, 19:01,  18082.7,      6.1,        ,         ,       ,          ,          ,      47, 47, 47, 47,      86, 85, 86, 86,         ,      1  
TRIP    , 2022-10-05, 23:59,  18088.7,      6.0,        ,     -1.4,       ,          ,          ,      45, 46, 45, 47,      86, 85, 84, 86,         ,      1  
DAY     , 2022-10-05, Wed  ,  18088.7,     23.1,        ,     -3.5,    6.6,      15.2,      0.86,      45, 47, 45, 50,      86, 86, 84, 96,         ,      5  
DAY     , 2022-10-06, Thu  ,  18088.7,         ,        ,         ,       ,          ,          ,      44, 44, 44, 45,      86, 86, 86, 86,         ,         
TRIP    , 2022-10-07, 09:30,  18088.8,      0.1,        ,     -0.7,       ,          ,          ,      43, 43, 43, 43,      90, 88, 90, 90,         ,      1  
TRIP    , 2022-10-07, 10:00,  18094.1,      5.3,        ,         ,       ,          ,          ,      43, 43, 43, 43,      91, 90, 91, 91,         ,      1  
TRIP    , 2022-10-07, 10:30,  18098.8,      4.7,        ,     -0.7,       ,          ,          ,      42, 42, 42, 42,      90, 90, 90, 90,         ,      1  
DAY     , 2022-10-07, Fri  ,  18098.8,     10.1,        ,     -1.4,       ,          ,          ,      42, 42, 42, 43,      90, 90, 90, 91,         ,      3  
TRIP    , 2022-10-08, 10:00,  18101.8,      3.0,        ,     -0.7,       ,          ,          ,      41, 41, 41, 41,      86, 88, 86, 86,         ,      1  
TRIP    , 2022-10-08, 11:00,  18105.2,      3.4,        ,     -0.7,       ,          ,          ,      40, 40, 40, 40,      87, 86, 87, 87,         ,      1  
TRIP    , 2022-10-08, 15:00,  18110.3,      5.1,        ,     -0.7,       ,          ,          ,      39, 40, 39, 40,      86, 87, 86, 87,         ,      1  
TRIP    , 2022-10-08, 17:00,  18115.4,      5.1,        ,     -0.7,       ,          ,          ,      38, 38, 38, 38,      87, 86, 87, 87,         ,      1  
DAY     , 2022-10-08, Sat  ,  18115.4,     16.6,        ,     -2.8,    5.9,      16.9,      0.69,      37, 38, 37, 41,      87, 87, 86, 87,         ,      4  
DAY     , 2022-10-09, Sun  ,  18115.4,         ,    14.7,         ,       ,          ,          ,      58, 54, 38, 58,      81, 81, 81, 81,      1  ,         
WEEK    , 2022-10-09, WK 40,  18115.4,     89.2,    18.2,    -12.6,    7.1,      14.1,      3.10,      58, 49, 37, 60,      81, 89, 81, 96,      1  ,     16  
TRIP    , 2022-10-10, 10:30,  18119.5,      4.1,        ,     -2.8,    1.5,      68.3,      0.69,      54, 56, 54, 54,      87, 84, 87, 87,         ,      1  
TRIP    , 2022-10-10, 11:00,  18138.5,     19.0,        ,         ,       ,          ,          ,      54, 54, 54, 54,      88, 87, 88, 88,         ,      1  
TRIP    , 2022-10-10, 17:31,  18161.6,     23.1,        ,     -2.8,    8.3,      12.1,      0.69,      49, 51, 49, 53,      91, 89, 88, 91,         ,      1  
DAY     , 2022-10-10, Mon  ,  18161.6,     46.2,        ,     -5.6,    8.3,      12.1,      1.38,      48, 49, 48, 54,      91, 90, 87, 91,         ,      3  
TRIP    , 2022-10-11, 14:31,  18164.2,      2.6,        ,     -0.7,       ,          ,          ,      47, 48, 47, 48,      87, 90, 87, 91,         ,      1  
TRIP    , 2022-10-11, 14:45,  18165.5,      1.3,        ,         ,       ,          ,          ,      47, 47, 47, 47,      87, 87, 87, 87,         ,      1  
TRIP    , 2022-10-11, 15:30,  18174.0,      8.5,        ,     -1.4,       ,          ,          ,      45, 46, 45, 45,      88, 87, 88, 88,         ,      1  
TRIP    , 2022-10-11, 16:30,  18181.3,      7.3,        ,     -0.7,       ,          ,          ,      44, 45, 44, 45,      88, 87, 87, 88,         ,      1  
DAY     , 2022-10-11, Tue  ,  18181.3,     19.7,        ,     -2.8,    7.0,      14.2,      0.69,      43, 44, 43, 48,      88, 88, 87, 91,         ,      4  
TRIP    , 2022-10-12, 13:30,  18186.8,      5.5,        ,     -0.7,       ,          ,          ,      42, 42, 42, 42,      86, 87, 86, 86,         ,      1  
TRIP    , 2022-10-12, 15:30,  18192.8,      6.0,        ,     -0.7,       ,          ,          ,      41, 41, 41, 41,      85, 85, 85, 85,         ,      1  
DAY     , 2022-10-12, Wed  ,  18192.8,     11.5,        ,     -1.4,       ,          ,          ,      41, 41, 41, 42,      85, 85, 85, 86,         ,      2  
TRIP    , 2022-10-13, 07:30,  18199.7,      6.9,        ,     -4.2,    1.6,      60.9,      1.03,      35, 38, 35, 39,      95, 92, 94, 95,         ,      1  
TRIP    , 2022-10-13, 08:00,  18221.0,     21.3,        ,         ,       ,          ,          ,      35, 35, 35, 35,      95, 95, 95, 95,         ,      1  
DAY     , 2022-10-13, Thu  ,  18221.0,     28.2,    17.5,     -4.2,    6.7,      14.9,      1.03,      60, 51, 35, 60,      95, 95, 94, 95,      2  ,      2  
TRIP    , 2022-10-14, 10:30,  18222.8,      1.8,        ,     -0.7,       ,          ,          ,      59, 59, 59, 59,      97, 96, 96, 97,         ,      1  
TRIP    , 2022-10-14, 11:00,  18224.5,      1.7,        ,         ,       ,          ,          ,      59, 59, 59, 59,      98, 97, 98, 98,         ,      1  
TRIP    , 2022-10-14, 13:30,  18228.2,      3.7,        ,     -0.7,       ,          ,          ,      58, 59, 58, 59,      97, 98, 97, 98,         ,      1  
TRIP    , 2022-10-14, 14:30,  18231.5,      3.3,        ,     -0.7,       ,          ,          ,      57, 58, 57, 58,      98, 97, 96, 98,         ,      1  
TRIP    , 2022-10-14, 15:30,  18239.8,      8.3,        ,     -0.7,       ,          ,          ,      56, 56, 56, 56,      99, 98, 99, 99,         ,      1  
TRIP    , 2022-10-14, 16:00,  18248.3,      8.5,        ,     -1.4,       ,          ,          ,      54, 55, 54, 54,      99, 99, 99, 99,         ,      1  
DAY     , 2022-10-14, Fri  ,  18248.3,     27.3,        ,     -4.2,    6.5,      15.4,      1.03,      54, 55, 54, 59,      99, 98, 96, 99,         ,      6  
TRIP    , 2022-10-15, 10:00,  18250.2,      1.9,        ,         ,       ,          ,          ,      54, 54, 54, 54,      85, 88, 85, 85,         ,      1  
TRIP    , 2022-10-15, 11:00,  18252.1,      1.9,        ,     -0.7,       ,          ,          ,      53, 54, 53, 54,      85, 85, 85, 85,         ,      1  
DAY     , 2022-10-15, Sat  ,  18252.1,      3.8,     4.2,         ,       ,          ,          ,      61, 59, 53, 61,      85, 85, 85, 85,      2  ,      2  
TRIP    , 2022-10-16, 11:30,  18329.5,     77.4,        ,    -12.6,    6.1,      16.3,      3.10,      43, 52, 43, 61,      92, 91, 91, 92,         ,      1  
TRIP    , 2022-10-16, 17:30,  18406.7,     77.2,        ,    -10.5,    7.4,      13.6,      2.58,      28, 38, 28, 41,      91, 90, 89, 91,         ,      1  
DAY     , 2022-10-16, Sun  ,  18406.7,    154.6,    16.1,    -23.1,    6.7,      14.9,      5.68,      51, 41, 28, 61,      91, 91, 89, 92,      1  ,      2  
WEEK    , 2022-10-16, WK 41,  18406.7,    291.3,    35.7,    -40.6,    7.2,      13.9,      9.99,      51, 49, 28, 61,      91, 91, 85, 99,      5  ,     21  
DAY     , 2022-10-17, Mon  ,  18406.7,         ,     5.6,         ,       ,          ,          ,      60, 59, 52, 60,      91, 91, 91, 91,         ,         
TRIP    , 2022-10-18, 07:30,  18413.8,      7.1,        ,     -2.8,    2.5,      39.4,      0.69,      56, 59, 56, 60,      85, 86, 85, 85,         ,      1  
TRIP    , 2022-10-18, 08:00,  18435.6,     21.8,        ,     -1.4,       ,          ,          ,      54, 55, 54, 54,      86, 85, 86, 86,         ,      1  
TRIP    , 2022-10-18, 15:00,  18437.8,      2.2,        ,         ,       ,          ,          ,      52, 52, 52, 52,      -1, 42, -1, 86,         ,      1  
TRIP    , 2022-10-18, 15:30,  18439.7,      1.9,        ,     -0.7,       ,          ,          ,      51, 51, 51, 51,      -1, -1, -1, -1,         ,      1  
DAY     , 2022-10-18, Tue  ,  18439.7,     33.0,        ,     -4.9,    6.7,      14.8,      1.21,      51, 52, 51, 60,      -1, 13, -1, 86,         ,      4  
TRIP    , 2022-10-19, 13:03,  18445.0,      5.3,        ,     -0.7,       ,          ,          ,      49, 50, 49, 50,      72, 45, -1, 72,         ,      1  
TRIP    , 2022-10-19, 15:00,  18448.5,      3.5,        ,         ,       ,          ,          ,      48, 48, 48, 48,      73, 73, 73, 73,         ,      1  
TRIP    , 2022-10-19, 16:30,  18452.1,      3.6,        ,     -0.7,       ,          ,          ,      47, 47, 47, 47,      71, 72, 71, 71,         ,      1  
TRIP    , 2022-10-19, 19:30,  18458.2,      6.1,        ,     -1.4,       ,          ,          ,      45, 46, 45, 46,      73, 72, 72, 73,         ,      1  
TRIP    , 2022-10-19, 23:59,  18464.2,      6.0,        ,     -0.7,       ,          ,          ,      44, 44, 44, 44,      73, 73, 73, 73,         ,      1  
DAY     , 2022-10-19, Wed  ,  18464.2,     24.5,        ,     -3.5,    7.0,      14.3,      0.86,      44, 46, 44, 50,      73, 69, -1, 73,         ,      5  
TRIP    , 2022-10-20, 13:46,  18486.2,     22.0,        ,     -3.5,    6.3,      15.9,      0.86,      38, 42, 38, 43,      87, 79, 73, 87,         ,      1  
TRIP    , 2022-10-20, 16:01,  18508.2,     22.0,        ,     -2.8,    7.9,      12.7,      0.69,      34, 36, 34, 37,      87, 86, 85, 87,         ,      1  
DAY     , 2022-10-20, Thu  ,  18508.2,     44.0,        ,     -6.3,    7.0,      14.3,      1.55,      34, 35, 34, 43,      87, 86, 73, 87,         ,      2  
TRIP    , 2022-10-21, 11:00,  18510.0,      1.8,        ,         ,       ,          ,          ,      34, 34, 34, 34,      90, 88, 90, 90,         ,      1  
TRIP    , 2022-10-21, 12:00,  18511.7,      1.7,        ,     -0.7,       ,          ,          ,      33, 33, 33, 33,      89, 89, 89, 89,         ,      1  
TRIP    , 2022-10-21, 14:00,  18512.7,      1.0,     5.6,         ,       ,          ,          ,      41, 34, 32, 41,      94, 93, 94, 95,      1  ,      1  
TRIP    , 2022-10-21, 16:00,  18525.0,     12.3,    11.9,         ,       ,          ,          ,      58, 52, 55, 58,      95, 94, 94, 95,         ,      1  
TRIP    , 2022-10-21, 17:01,  18530.4,      5.4,        ,     -0.7,       ,          ,          ,      57, 57, 57, 57,      93, 94, 93, 93,         ,      1  
DAY     , 2022-10-21, Fri  ,  18530.4,     22.2,    17.5,         ,       ,          ,          ,      59, 52, 32, 59,      93, 93, 89, 95,      2  ,      5  
TRIP    , 2022-10-22, 10:00,  18532.3,      1.9,        ,     -0.7,       ,          ,          ,      58, 58, 58, 58,      86, 89, 86, 86,         ,      1  
TRIP    , 2022-10-22, 12:00,  18534.6,      2.3,     7.0,         ,       ,          ,          ,      68, 60, 58, 68,      86, 85, 85, 86,      1  ,      1  
TRIP    , 2022-10-22, 13:50,  18535.1,      0.5,     8.4,     -0.7,       ,          ,          ,      79, 76, 79, 80,      88, 86, 86, 88,         ,      1  
TRIP    , 2022-10-22, 15:00,  18542.5,      7.4,        ,     -0.7,       ,          ,          ,      78, 78, 78, 78,      86, 87, 86, 86,         ,      1  
TRIP    , 2022-10-22, 16:00,  18550.6,      8.1,        ,     -0.7,       ,          ,          ,      77, 77, 77, 77,      87, 86, 87, 87,         ,      1  
TRIP    , 2022-10-22, 19:00,  18564.9,     14.3,        ,     -2.1,    6.8,      14.7,      0.52,      74, 76, 74, 76,      88, 87, 87, 88,         ,      1  
DAY     , 2022-10-22, Sat  ,  18564.9,     34.5,    33.6,     -4.9,    7.0,      14.2,      1.21,     100, 79, 58,100,      88, 87, 85, 88,      2  ,      6  
TRIP    , 2022-10-23, 12:00,  18762.2,    197.3,        ,    -31.5,    6.3,      16.0,      7.75,      55, 77, 55, 96,      89, 90, 89, 91,         ,      1  
TRIP    , 2022-10-23, 13:00,  18765.6,      3.4,    14.7,         ,       ,          ,          ,      76, 65, 76, 76,      91, 90, 91, 91,      1  ,      1  
TRIP    , 2022-10-23, 14:00,  18772.3,      6.7,        ,     -0.7,       ,          ,          ,      75, 75, 75, 75,      91, 91, 91, 91,         ,      1  
TRIP    , 2022-10-23, 16:00,  18775.7,      3.4,        ,     -9.8,    0.3,     288.2,      2.41,      61, 71, 61, 74,      91, 90, 90, 91,         ,      1  
TRIP    , 2022-10-23, 17:30,  18973.0,    197.3,        ,    -25.2,    7.8,      12.8,      6.20,      25, 42, 25, 36,      92, 91, 91, 92,         ,      1  
TRIP    , 2022-10-23, 23:59,  18973.4,      0.4,    22.4,         ,       ,          ,          ,      57, 51, 29, 57,      93, 92, 92, 93,      1  ,      1  
DAY     , 2022-10-23, Sun  ,  18973.4,    408.5,    37.1,    -67.2,    6.1,      16.5,     16.53,      57, 58, 25, 96,      93, 91, 89, 93,      2  ,      6  
WEEK    , 2022-10-23, WK 42,  18973.4,    566.7,    90.3,    -86.1,    6.6,      15.2,     21.18,      57, 56, 25,100,      93, 78, -1, 95,      6  ,     28  
TRIP    , 2022-10-24, 08:00,  18984.5,     11.1,        ,     -3.5,    3.2,      31.5,      0.86,      52, 56, 52, 57,      97, 95, 96, 97,         ,      1  
TRIP    , 2022-10-24, 09:00,  19008.7,     24.2,        ,     -1.4,       ,          ,          ,      50, 51, 50, 50,      97, 97, 97, 97,         ,      1  
TRIP    , 2022-10-24, 19:00,  19026.6,     17.9,        ,     -2.1,    8.5,      11.7,      0.52,      47, 48, 47, 47,      94, 95, 94, 94,         ,      1  
TRIP    , 2022-10-24, 23:59,  19043.9,     17.3,        ,     -2.8,    6.2,      16.2,      0.69,      43, 45, 43, 47,      95, 94, 94, 95,         ,      1  
DAY     , 2022-10-24, Mon  ,  19043.9,     70.5,        ,     -9.8,    7.2,      13.9,      2.41,      43, 47, 43, 57,      95, 95, 94, 97,         ,      4  
TRIP    , 2022-10-25, 07:42,  19072.1,     28.2,        ,     -4.2,    6.7,      14.9,      1.03,      37, 41, 37, 42,      90, 90, 87, 90,         ,      1  
DAY     , 2022-10-25, Tue  ,  19072.1,     28.2,        ,     -4.2,    6.7,      14.9,      1.03,      35, 36, 35, 42,      87, 88, 85, 90,         ,      1  
TRIP    , 2022-10-26, 10:00,  19077.2,      5.1,        ,     -0.7,       ,          ,          ,      34, 34, 34, 34,      85, 86, 85, 85,         ,      1  
TRIP    , 2022-10-26, 13:00,  19082.2,      5.0,        ,     -0.7,       ,          ,          ,      33, 33, 33, 33,      84, 84, 84, 84,         ,      1  
DAY     , 2022-10-26, Wed  ,  19082.2,     10.1,        ,     -1.4,       ,          ,          ,      33, 33, 33, 34,      84, 84, 84, 85,         ,      2  
TRIP    , 2022-10-27, 10:00,  19082.7,      0.5,        ,         ,       ,          ,          ,      33, 33, 33, 33,      71, 77, 71, 71,      1  ,      1  
TRIP    , 2022-10-27, 13:00,  19083.1,      0.4,    25.2,         ,       ,          ,          ,      69, 53, 47, 69,      81, 73, 71, 81,         ,      1  
DAY     , 2022-10-27, Thu  ,  19083.1,      0.9,    27.3,         ,       ,          ,          ,      72, 66, 33, 72,      81, 79, 71, 81,      2  ,      2  
TRIP    , 2022-10-28, 11:00,  19088.0,      4.9,        ,     -0.7,       ,          ,          ,      71, 72, 71, 72,      87, 84, 84, 87,         ,      1  
TRIP    , 2022-10-28, 12:01,  19092.9,      4.9,        ,     -0.7,       ,          ,          ,      70, 70, 70, 70,      86, 86, 86, 86,         ,      1  
DAY     , 2022-10-28, Fri  ,  19092.9,      9.8,        ,     -1.4,       ,          ,          ,      70, 70, 70, 72,      86, 86, 84, 87,         ,      2  
DAY     , 2022-10-29, Sat  ,  19092.9,         ,        ,         ,       ,          ,          ,      70, 70, 70, 70,      86, 86, 86, 86,         ,         
WEEK    , 2022-10-29, WK 43,  19092.9,    119.5,    25.9,    -16.8,    7.1,      14.1,      4.13,      70, 70, 33, 72,      86, 86, 71, 97,      2  ,     11  
MONTH   , 2022-10-29, Oct  ,  19092.9,   1225.7,   187.6,   -180.6,    6.8,      14.7,     44.43,      70, 70, 25,100,      86, 86, -1, 99,     16  ,     79  
YEAR    , 2022-10-29, 2022 ,  19092.9,   1768.7,   277.2,   -266.0,    6.6,      15.0,     65.44,      70, 70,  5,100,      86, 86, -1, 99,     24  ,    106  
TRIPAVG , 2022-10-29, 106t ,  19092.9,     16.7,     2.6,     -2.5,    6.6,      15.0,      0.62,      70, 70,  5,100,      86, 86, -1, 99,      0.2,      1  
DAYAVG  , 2022-10-29,  43d ,  19092.9,     41.1,     6.4,     -6.2,    6.6,      15.0,      1.52,      70, 70,  5,100,      86, 86, -1, 99,      0.6,      2.5
WEEKAVG , 2022-10-29,  43d ,  19092.9,    287.9,    45.1,    -43.3,    6.6,      15.0,     10.65,      70, 70,  5,100,      86, 86, -1, 99,      3.9,     17.3
MONTHAVG, 2022-10-29,  43d ,  19092.9,   1251.1,   196.1,   -188.2,    6.6,      15.0,     46.29,      70, 70,  5,100,      86, 86, -1, 99,     17  ,     75  
YEARLY  , 2022-10-29,  43d ,  19092.9,  15013.4,  2353.0,  -2257.9,    6.6,      15.0,    555.45,      70, 70,  5,100,      86, 86, -1, 99,    203.7,    899.8
```

Notes:
- when the -kWh is below the configured threshold, no consumption data is shown
- sometimes with TRIP the used kWh is counted by the previous trip, this is because of the moment of capturing data and then consumption is off for both trips AND the odometer is only updated after the car is switched off (apparently the behavior of bluelink)

Example of wrong consumption shown for trip:

```
TRIP  , 2022-10-13, 07:30,  18199.7,      6.9,        ,     -4.2,    1.6,      60.9,      1.03,      35, 38, 35, 39,      95, 92, 94, 95,         ,       1,      2
TRIP  , 2022-10-13, 08:00,  18221.0,     21.3,        ,         ,       ,          ,          ,      35, 35, 35, 35,      95, 95, 95, 95,         ,       1,      1
DAY   , 2022-10-13, Thu  ,  18221.0,     28.2,    17.5,     -4.2,    6.7,      14.9,      1.03,      60, 51, 35, 60,      95, 95, 94, 95,        2,       2,      3
```

If you look at the corresponding entries of monitor.csv:
```
2022-10-12 19:30:42+02:00, 5.124957, 51.68260, False, 85, 18192.8, 41, False, 0
2022-10-13 06:00:42+02:00, 5.124957, 51.68260, False, 85, 18192.8, 41, False, 0
2022-10-13 06:30:44+02:00, 5.124957, 51.68260, False, 85, 18192.8, 41, False, 0
2022-10-13 07:00:34+02:00, 5.066594, 51.692425, True, 94, 18192.8, 39, False, 0
2022-10-13 07:30:32+02:00, 5.156569, 51.697092, True, 95, 18199.7, 35, False, 0
2022-10-13 08:00:50+02:00, 5.124957, 51.68260, False, 95, 18221, 35, False, 0
2022-10-13 08:30:43+02:00, 5.124957, 51.68260, False, 95, 18221, 35, False, 0
```

What has happened on those TRIPs:
- till 07:30 I have driven 6.9 km till 07:05, put the car off (odometer is updated) and started a new trip around 7:10, which trip ended around 7:25, but did NOT put the car off (odometer is NOT updated).
- these intermediate trips are not captured
- At 7:25 I drove home again, only a few km, got home after 7:30, which has been captured at 8:00
- because I have not switched off the car at 7:25, the odometer is not updated and seen at 7:30 is the short trip end of 7:05, but already 6% SOC change has been recorded
- the way back home is only a few km, so the consumption has not decreased
- the consumption of 6% is given to the first trip (there was a odometer change), but actually the consumption should have been divided between the 2 trips
- I cannot detect these situations and also do not know how to divide these, because of the moment of capturing AND odometer is not constantly updated
- you can compute a better consumption by combining those 2 trips, in this case the DAY gives the real consumption

## python summary.py sheetupdate

Example standard output:
```
C:\Users\Rick\git\monitor>python summary.py sheetupdate
  Period, date      , info , odometer, delta km,    +kWh,     -kWh, km/kWh, kWh/100km, cost Euro, SOC%CUR,AVG,MIN,MAX, 12V%CUR,AVG,MIN,MAX, #charges,   #trips
DAY     , 2022-09-17, Sat  ,  17324.2,         ,     2.8,         ,       ,          ,          ,      58, 55, 55, 58,      91, 91, 91, 91,      1  ,         
DAY     , 2022-09-18, Sun  ,  17324.2,         ,     0.7,         ,       ,          ,          ,      59, 59, 59, 60,      91, 91, 91, 91,         ,         
WEEK    , 2022-09-18, WK 37,  17324.2,         ,     3.5,         ,       ,          ,          ,      59, 59, 55, 60,      91, 91, 91, 91,      1  ,         
DAY     , 2022-09-19, Mon  ,  17330.7,      6.5,        ,         ,       ,          ,          ,      59, 60, 59, 61,      86, 88, 85, 91,         ,      2  
DAY     , 2022-09-20, Tue  ,  17378.3,     47.6,        ,     -7.0,    6.8,      14.7,      1.72,      45, 48, 45, 59,      91, 91, 87, 92,         ,      3  
DAY     , 2022-09-21, Wed  ,  17383.5,      5.2,    18.2,     -0.7,       ,          ,          ,      70, 63, 46, 70,      91, 91, 91, 92,      2  ,      2  
DAY     , 2022-09-22, Thu  ,  17383.5,         ,        ,         ,       ,          ,          ,      72, 72, 72, 72,      91, 91, 91, 91,      1  ,         
DAY     , 2022-09-23, Fri  ,  17387.1,      3.6,    20.3,     -0.7,       ,          ,          ,     100, 86, 71,100,      87, 87, 87, 88,      2  ,      2  
DAY     , 2022-09-24, Sat  ,  17794.9,    407.8,    25.9,    -66.5,    6.1,      16.3,     16.36,      42, 40,  5,100,      97, 96, 92, 98,      1  ,      5  
DAY     , 2022-09-25, Sun  ,  17794.9,         ,     5.6,         ,       ,          ,          ,      50, 46, 43, 50,      97, 97, 97, 97,         ,         
WEEK    , 2022-09-25, WK 38,  17794.9,    470.7,    67.2,    -73.5,    6.4,      15.6,     18.08,      50, 60,  5,100,      97, 91, 85, 98,      6  ,     14  
MONTH   , 2022-09-25, Sep  ,  17794.9,    470.7,    70.7,    -73.5,    6.4,      15.6,     18.08,      50, 59,  5,100,      97, 91, 85, 98,      7  ,     14  
YEAR    , 2022-09-25, 2022 ,  17794.9,    470.7,    70.7,    -73.5,    6.4,      15.6,     18.08,      50, 59,  5,100,      97, 91, 85, 98,      7  ,     14  
TRIPAVG , 2022-09-25,  14t ,  17794.9,     33.6,     5.0,     -5.2,    6.4,      15.6,      1.29,      50, 59,  5,100,      97, 91, 85, 98,      0.5,      1  
DAYAVG  , 2022-09-25,   9d ,  17794.9,     52.3,     7.9,     -8.2,    6.4,      15.6,      2.01,      50, 59,  5,100,      97, 91, 85, 98,      0.8,      1.6
WEEKAVG , 2022-09-25,   9d ,  17794.9,    366.1,    55.0,    -57.2,    6.4,      15.6,     14.06,      50, 59,  5,100,      97, 91, 85, 98,      5.4,     10.9
MONTHAVG, 2022-09-25,   9d ,  17794.9,   1590.8,   238.9,   -248.4,    6.4,      15.6,     61.11,      50, 59,  5,100,      97, 91, 85, 98,     23.7,     47.3
YEARLY  , 2022-09-25,   9d ,  17794.9,  19089.5,  2867.3,  -2980.8,    6.4,      15.6,    733.29,      50, 59,  5,100,      97, 91, 85, 98,    283.9,    567.8
  Period, date      , info , odometer, delta km,    +kWh,     -kWh, km/kWh, kWh/100km, cost Euro, SOC%CUR,AVG,MIN,MAX, 12V%CUR,AVG,MIN,MAX, #charges,   #trips
```

Screenshot of spreadsheet:
![alt text](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/GoogleSpreadsheet.png)

## python kml.py

Input is previous monitor.csv file.

[The kml standard output](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/kml.py_output.txt)
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

The kml output file [monitor.kml](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/monitor.kml)

2022-09-24 I did a trip from 100% SOC to 5% SOC and driven around 400 km and started charging when back at home.

Screenshot after imported into Google My Maps (yes, I have adjusted the locations for privacy):
- ![alt text](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/MonitorGoogleMyMaps.jpg)

I changed the style to "sequence numbering" so you see the order of locations in the map. You can also adjust the base map, so less information is shown, but your locations are better visible. You can also view the Google My Map in Google Earth (via the Google My Maps menu) and zoom in interactively to the different locations.  

It is also possible to add addresses to kml.
```
C:\Users\Rick\git\monitor>python kml.py address
  1: 20220917 15:00    (5.124957,51.68260 ) SOC: 54% 12V: 90% ODO: 17324.2 Address: "26, Keniaring, Drunen, Heusden, Noord-Brabant, Nederland, 5152 MX, Nederland"
  2: 20220917 23:00 C  (5.124957,51.68260 ) SOC: 55% 12V: 91% ODO: 17324.2 Address: "26, Keniaring, Drunen, Heusden, Noord-Brabant, Nederland, 5152 MX, Nederland"       charging plugged:2
  3: 20220918 01:00    (5.124957,51.68260 ) SOC: 60% 12V: 91% ODO: 17324.2 Address: "26, Keniaring, Drunen, Heusden, Noord-Brabant, Nederland, 5152 MX, Nederland"       plugged:2
  4: 20220919 15:00  D (5.125942,51.679128) SOC: 61% 12V: 85% ODO: 17324.3 Address: "Statenlaan, Drunen, Heusden, Noord-Brabant, Nederland, 5152 SG, Nederland"       (+0.1 since 20220919 14:00) drive
  5: 20220919 16:00    (5.124957,51.68260 ) SOC: 59% 12V: 86% ODO: 17330.7 Address: "26, Keniaring, Drunen, Heusden, Noord-Brabant, Nederland, 5152 MX, Nederland"       (+6.4 since 20220919 15:00)
  6: 20220920 07:00  D (5.091594,51.684361) SOC: 59% 12V: 88% ODO: 17330.7 Address: "Akkerlaan, Bloemenoord, Waalwijk, Noord-Brabant, Nederland, 5143 ND, Nederland"       drive
  7: 20220920 08:00    (5.124957,51.68260 ) SOC: 53% 12V: 91% ODO: 17358.9 Address: "26, Keniaring, Drunen, Heusden, Noord-Brabant, Nederland, 5152 MX, Nederland"       (+28.2 since 20220920 07:00)
  8: 20220920 14:30  D (5.135242,51.692605) SOC: 50% 12V: 87% ODO: 17358.9 Address: "18, Leliestraat, Drunen, Heusden, Noord-Brabant, Nederland, 5151 TP, Nederland"       drive
  9: 20220920 15:00  D (5.078042,51.693758) SOC: 49% 12V: 91% ODO: 17358.9 Address: "Desso Tarkett, 15, Taxandriaweg, Laageinde, Waalwijk, Noord-Brabant, Nederland, 5142 PA, Nederland"       drive
 10: 20220920 15:30    (5.04708 ,51.688192) SOC: 48% 12V: 92% ODO: 17371.5 Address: "29b, Westeinde, Besoijen, Waalwijk, Noord-Brabant, Nederland, 5141 AA, Nederland"       (+12.6 since 20220920 15:00)
 11: 20220920 15:58    (5.124957,51.68260 ) SOC: 47% 12V: 91% ODO: 17378.3 Address: "26, Keniaring, Drunen, Heusden, Noord-Brabant, Nederland, 5152 MX, Nederland"       (+6.8 since 20220920 15:30)
 12: 20220921 10:30 C  (5.124957,51.68260 ) SOC: 46% 12V: 91% ODO: 17378.3 Address: "26, Keniaring, Drunen, Heusden, Noord-Brabant, Nederland, 5152 MX, Nederland"       charging plugged:2
 13: 20220921 12:30    (5.135183,51.692608) SOC: 52% 12V: 92% ODO: 17380.8 Address: "18, Leliestraat, Drunen, Heusden, Noord-Brabant, Nederland, 5151 TP, Nederland"       (+2.5 since 20220921 12:00)
 14: 20220921 13:00    (5.124957,51.68260 ) SOC: 51% 12V: 91% ODO: 17383.5 Address: "26, Keniaring, Drunen, Heusden, Noord-Brabant, Nederland, 5152 MX, Nederland"       (+2.7 since 20220921 12:30)
 15: 20220921 14:31 C  (5.124957,51.68260 ) SOC: 52% 12V: 91% ODO: 17383.5 Address: "26, Keniaring, Drunen, Heusden, Noord-Brabant, Nederland, 5152 MX, Nederland"       charging plugged:2
 16: 20220922 06:00    (5.124957,51.68260 ) SOC: 70% 12V: 91% ODO: 17383.5 Address: "26, Keniaring, Drunen, Heusden, Noord-Brabant, Nederland, 5152 MX, Nederland"       plugged:2
 17: 20220923 11:21    (5.132119,51.685055) SOC: 71% 12V: 88% ODO: 17385.4 Address: "Jumbo Aalbersestraat, 5, Aalbersestraat, Drunen, Heusden, Noord-Brabant, Nederland, 5151 EE, Nederland"       (+1.9 since 20220923 11:00)
 18: 20220923 12:00 C  (5.124957,51.68260 ) SOC: 72% 12V: 87% ODO: 17387.1 Address: "26, Keniaring, Drunen, Heusden, Noord-Brabant, Nederland, 5152 MX, Nederland"       (+1.7 since 20220923 11:21) charging plugged:2
 19: 20220923 15:00    (5.124957,51.68260 ) SOC: 80% 12V: 87% ODO: 17387.1 Address: "26, Keniaring, Drunen, Heusden, Noord-Brabant, Nederland, 5152 MX, Nederland"       plugged:2
 20: 20220924 08:00  D (5.124957,51.68260 ) SOC:100% 12V: 95% ODO: 17387.1 Address: "26, Keniaring, Drunen, Heusden, Noord-Brabant, Nederland, 5152 MX, Nederland"       drive
 21: 20220924 08:30    (5.124957,51.68260 ) SOC:100% 12V: 95% ODO: 17387.1 Address: "26, Keniaring, Drunen, Heusden, Noord-Brabant, Nederland, 5152 MX, Nederland"
 22: 20220924 11:00  D (5.129967,51.674819) SOC: 98% 12V: 92% ODO: 17390.8 Address: "140, Torenstraat, Drunen, Heusden, Noord-Brabant, Nederland, 5151 JN, Nederland"       drive
 23: 20220924 11:30  D (5.204728,51.883719) SOC: 91% 12V: 97% ODO: 17390.8 Address: "Rijksweg A2, Enspijk, West Betuwe, Gelderland, Nederland, 4153 RN, Nederland"       drive
 24: 20220924 12:00  D (5.250064,52.256122) SOC: 81% 12V: 98% ODO: 17390.8 Address: "Rijksweg A27, Eemnes, Utrecht, Nederland, 3755 AS, Nederland"       drive
 25: 20220924 12:30  D (5.540714,52.575733) SOC: 69% 12V: 98% ODO: 17390.8 Address: "Rijksweg A6, Lelystad, Flevoland, Nederland, 8221 RD, Nederland"       drive
 26: 20220924 13:00  D (5.768325,52.898894) SOC: 57% 12V: 98% ODO: 17390.8 Address: "A6, Oldeouwer, De Fryske Marren, FryslÃ¢n, Nederland, 8516 DD, Nederland"       drive
 27: 20220924 13:21    (5.683261,53.036686) SOC: 52% 12V: 96% ODO: 17589.2 Address: "17-101, Dekamalaan, Sneek, SÃºdwest-FryslÃ¢n, FryslÃ¢n, Nederland, 8604 ZG, Nederland"       (+198.4 since 20220924 13:00)
 28: 20220924 14:31    (5.681147,53.016858) SOC: 51% 12V: 94% ODO: 17592.5 Address: "Van der Valk Hotel Sneek, 1, Burgemeester Rasterhofflaan, Houkesloot, Sneek, SÃºdwest-FryslÃ¢n, FryslÃ¢n, Nederland, 8606 KZ, Nederland"       (+3.3 since 20220924 14:00)
 29: 20220924 15:00  D (5.686422,53.030697) SOC: 51% 12V: 93% ODO: 17592.5 Address: "Stadsrondweg-Oost, Houkesloot, Sneek, SÃºdwest-FryslÃ¢n, FryslÃ¢n, Nederland, 8604 GC, Nederland"       drive
 30: 20220924 15:23    (5.68325 ,53.036683) SOC: 50% 12V: 96% ODO: 17597.3 Address: "17-101, Dekamalaan, Sneek, SÃºdwest-FryslÃ¢n, FryslÃ¢n, Nederland, 8604 ZG, Nederland"       (+4.8 since 20220924 15:00)
 31: 20220924 16:30  D (5.6802  ,53.035853) SOC: 50% 12V: 94% ODO: 17597.3 Address: "10, Groenedijk, Sneek, SÃºdwest-FryslÃ¢n, FryslÃ¢n, Nederland, 8604 AB, Nederland"       drive
 32: 20220924 17:00  D (5.771994,52.709039) SOC: 40% 12V: 94% ODO: 17597.3 Address: "A6, De Zuidert, Emmeloord, Noordoostpolder, Flevoland, Nederland, 8305 AC, Nederland"       drive
 33: 20220924 17:30  D (5.375436,52.411236) SOC: 30% 12V: 95% ODO: 17597.3 Address: "Rijksweg A6, Lelystad, Flevoland, Nederland, 3897 MA, Nederland"       drive
 34: 20220924 18:00  D (5.158522,52.095317) SOC: 21% 12V: 94% ODO: 17597.3 Address: "A27, Rijnsweerd, Utrecht, Nederland, 3731 GC, Nederland"       drive
 35: 20220924 18:30  D (5.293333,51.748758) SOC: 10% 12V: 96% ODO: 17597.3 Address: "A2, Hoenzadriel, Maasdriel, Gelderland, Nederland, 5334 NV, Nederland"       drive
 36: 20220924 19:00 C  (5.124957,51.68260 ) SOC:  5% 12V: 97% ODO: 17794.9 Address: "26, Keniaring, Drunen, Heusden, Noord-Brabant, Nederland, 5152 MX, Nederland"       (+197.6 since 20220924 18:30) charging plugged:2
```

Note: "address" shows the address of a coordinate with geopy, because Nominatim has a 1000 query limit per day and bulk queries are not appreciated, one second sleep is added per address lookup.

## python shrink.py

Example (based on earlier monitor.csv) outputfile [shrinked_monitor.csv](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/shrinked_monitor.csv)

[Excel example using shrinked_monitor.csv](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/blob/main/examples/shrinked_monitor.xlsx)

Screenshot of excel example with some graphs:
![alt text](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/shrinked_monitor.jpg)

# Remarks of using the tools for a month
- The hyundai_kia_connect_api gives regularly exceptions, [see this issue 62](https://github.com/Hyundai-Kia-Connect/hyundai_kia_connect_api/issues/62#issuecomment-1280045102)
- The retry mechanism (wait one minute and retry twice) seems a good workaround
- If the car cannot be reached by bluelink then an exception will be thrown and no entry will appear in monitor.csv
- I do not know what happens if the number of calls allowed per day have been exceeded, probably an exception will be thrown and no entry will appear in monitor.csv
- I have seen small drops and increases of SOC% (on my IONIQ 5 around 1% to 2%), because of temperature changes between e.g. evening and morning, I made this configurable via summary.cfg
- Small trips will give inaccurate consumption figures, on the IONIQ 5 1% SOC difference is 0.7 kWh difference, so I made the minimum kWh consumption configurable via summary.cfg. A Smaller battery will have better accuracy, because 1% of e.g. 27 kWh makes 0.27 kWh delta's instead of 0.7 kWh in my case
- I have seen once that SOC was reported wrongly in monitor.csv as zero, in summary.py I corrected this when the previous SOC% was not zero and delta is greater than 5

Occurrence of SOC% of 0: 
```
2022-10-11 11:30:47+02:00, 5.124957, 51.68260, False, 91, 18161.6, 48, False, 0
2022-10-11 12:00:54+02:00, 5.124957, 51.68260, False, 91, 18161.6, 0, False, 0
2022-10-11 12:30:48+02:00, 5.124957, 51.68260, False, 91, 18161.6, 48, False, 0
```
