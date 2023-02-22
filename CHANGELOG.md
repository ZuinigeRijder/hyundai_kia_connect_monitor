<a name="R3.8.0"></a>
# [Added summary day consumption to dailystats and other improvements (R3.8.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R3.8.0) - 22 Feb 2023

summary.py:
- write summary.day.csv, like summary.trip.csv, so this can be used by dailystats.py
- improved the SOC readings, when the odometer between two monitor.csv entries are the same, but the next SOC is lower within 20 minutes, skip the first entry, because the SOC is sometimes updated later
- because of this general skipping, the workaround for TRIP could be removed
- this improves the consumption figures a bit for DAY, WEEK, MONTH, YEAR 
- some small code improvements

monitor_utils.py:
- safe_divide returns now 0.0 when divide by zero
- added methods get_safe_float and get_safe_datettime

monitor.py:
- avoid runtime errors by getting safe float and datetime, also when this is None for vehicle.location_longitude, vehicle.location_latitude, vehicle.last_updated_at and vehicle.location_last_updated_at

dailystats.py:
- added total consumption from summary.day.csv to totals between round brackets
- added consumption per day to overview between round brackets
- made column D 2 spaces wider
- avoid divide by zero
- some small code improvements

BEFORE without day consumption between round brackets:
````
     Totals Recuperation   Consumption    Engine  Climate  Electr. Batt.Care
    31.8kWh       4.8kWh     5.6km/kWh   27.8kWh   1.2kWh   2.8kWh    0.0kWh
      178km        14.9% 17.9kWh/100km       87%     3.7%     8.9%      0.0%
 (+33.6kWh)         Trip                Distance Avg km/h Max km/h      Idle
                  201min                   178km   60km/h  103km/h     28min
                                                                            
 2023-01-18 Recuperation   Consumption    Engine  Climate  Electr. Batt.Care
     1.9kWh       0.4kWh     5.1km/kWh    1.4kWh   0.2kWh   0.4kWh    0.0kWh
       10km        23.1% 19.4kWh/100km       71%     9.2%    20.1%      0.0%
                    Trip                Distance Avg km/h Max km/h      Idle
   (0.7kWh)  12:07-12:15   (7.3km/kWh)       5km   43km/h   63km/h      1min
   (1.4kWh)  09:38-09:47   (3.6km/kWh)       5km   40km/h   63km/h      1min

````

AFTER with day consumption between round brackets:
````
     Totals Recuperation   Consumption    Engine  Climate  Electr. Batt.Care
    31.8kWh       4.8kWh     5.6km/kWh   27.8kWh   1.2kWh   2.8kWh    0.0kWh
      178km        14.9% 17.9kWh/100km       87%     3.7%     8.9%      0.0%
 (+33.6kWh)         Trip   (5.4km/kWh)  Distance Avg km/h Max km/h      Idle
                  201min                   178km   60km/h  103km/h     28min
                                                                            
 2023-01-18 Recuperation   Consumption    Engine  Climate  Electr. Batt.Care
     1.9kWh       0.4kWh     5.1km/kWh    1.4kWh   0.2kWh   0.4kWh    0.0kWh
       10km        23.1% 19.4kWh/100km       71%     9.2%    20.1%      0.0%
                    Trip   (4.9km/kWh)  Distance Avg km/h Max km/h      Idle
   (0.7kWh)  12:07-12:15   (7.3km/kWh)       5km   43km/h   63km/h      1min
   (1.4kWh)  09:38-09:47   (3.6km/kWh)       5km   40km/h   63km/h      1min
````

debug.py:
- print also vehicle.location_last_updated_at (for USA this datetime was not filled, so this is now more clear)

check_monitor.py (new): 
- program for testing: when the odometer between two monitor.csv entries are the same, but the next SOC is lower within 20 minutes, skip the first entry, because the SOC is sometimes updated later

requirements.txt:
- added minimum versions instead of exact versions
- update to higher version of hyundai_kia_connect_api>=3.1.0

README.md:
- tested and updated with hyundai_kia_connect_api v3.1.0
- summary.py: added output summary.day.csv 
- dailystats.py: added use of summary.day.csv
- added check_monitor.py
- added examples

tests\run_tests.bat:
- added checking for summary.day.csv
- added option to run limited test (no parameters) or full test (with parameter)

tests\INPUT\*:
- added summary.cfg used for running the tests
- much larger real world example input files

tests\OUTPUT\*:
- new reference files

[Changes][R3.8.0]


<a name="R3.7.0"></a>
# [fix placemark bug in kml.py (R3.7.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R3.7.0) - 15 Feb 2023

fix placemark bug in kml.py

[Changes][R3.7.0]


<a name="R3.6.0"></a>
# [Some small improvements and added CHANGELOG.md (R3.6.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R3.6.0) - 15 Feb 2023

monitor.py:
- fix that identical lines are not added to monitor.csv, also do not add when only the address is different

summary.py:
- go to beginning of spreadsheet

dailystats.py:
- go to beginning of spreadsheet

monitor_utils.py:
- Only sleep for 60 seconds when retries > 0



[Changes][R3.6.0]


<a name="R3.5.0"></a>
# [Add multiple dailystats to monitor.dailystats.csv with timestamp (R3.5.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R3.5.0) - 10 Feb 2023

This is a preparation for a future feature, consumption kWh for trips in dailystats.py.

Now monitor.dailystats.csv will add a new line, when the previous line is different.
Example:
````
20230210 13:45, 1, km, 375, 134,  189, 36, 150, 0
````

Earlier, the last day was NOT added to monitor.dailystats.csv, but now it can add several times a day add the last day, with the consumption till then, to monitor.dailystats.csv. The dailystats.py is changed, that it will skip the not latest dailystats of that day.

In the future the monitor.dailystats.csv entries could maybe be matched to trips, so also there detailed trip consumption figures like dailystats can be computes/added to dailystats.py.

This release is for already collecting the intermediate dailystats with monitor.py when they are different.

[Changes][R3.5.0]


<a name="R3.4.0"></a>
# [Added dailystats diagrams and total trip info (R3.4.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R3.4.0) - 08 Feb 2023

[Here a video](http://www.youtube.com/watch?feature=player_embedded&v=W5syq4uqo7U) with some nice diagrams in Google Spreadsheet, showing:

Daily Statistics:
- Total
- Recuperation
- Consumption
- Engine
- Climate
- Electric devices
- Battery Care

Trip information:
- Totals
- Trip Start Time
- Trip End Time
- Matched consumption or distance figures from summary.py between round brackets
- Distance
- Average speed
- Maximum speed
- Idle minutes

<a href="http://www.youtube.com/watch?feature=player_embedded&v=W5syq4uqo7U" target="_blank"><img src="http://img.youtube.com/vi/W5syq4uqo7U/0.jpg" alt="monitor.dailystats Google Spreadsheet" width="240" height="180" border="10" /></a>

Screenshot in browser with nice diagrams:
![alt text](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/dailystats.py_GoogleSpreadsheet.Browser.jpg)

If you want these diagrams, you can copy this [example Google spreadsheet](https://docs.google.com/spreadsheets/d/1WwdosLQ0ViTHct_kBSNddnd-H3IUc604_Tz-0dgYI9A/edit?usp=sharing) and change e.g. diagram titles into your own language.



[Changes][R3.4.0]


<a name="R3.3.2"></a>
# [fixed some Norwegian translations (R3.3.2)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R3.3.2) - 31 Jan 2023

fixed some Norwegian translations
https://elbilforum.no/index.php?topic=62636.msg1089237#msg1089237

[Changes][R3.3.2]


<a name="R3.3.1"></a>
# [Small bugfix in formatting dailystats.py sheetupdate (R3.3.1)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R3.3.1) - 30 Jan 2023

Small bugfix in formatting dailystats.py sheetupdate

[Changes][R3.3.1]


<a name="R3.3.0"></a>
# [summary.py: Added translations for standard output and sheetupdate (R3.3.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R3.3.0) - 30 Jan 2023

**summary.py: Added translations for standard output and sheetupdate**

Here are some screenshots for the dailystats.py and summary.py spreadsheets.

### English screenshot of dailystats.py spreadsheet:
![alt text](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/dailystats.py_GoogleSpreadsheet.png)

### Dutch screenshot of dailystats.py spreadsheet:
![alt text](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/dailystats.py_GoogleSpreadsheet.nl.png)

### German screenshot of dailystats.py spreadsheet:
![alt text](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/dailystats.py_GoogleSpreadsheet.de.png)



### English screenshot of summary.py spreadsheet:
![alt text](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/summary.py_GoogleSpreadsheet.png)

### Dutch screenshot of summary.py spreadsheet:
![alt text](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/summary.py_GoogleSpreadsheet.nl.png)

### German screenshot of summary.py spreadsheet:
![alt text](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/summary.py_GoogleSpreadsheet.de.png)



[Changes][R3.3.0]


<a name="R3.2.1"></a>
# [Shortened translations (R3.2.1)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R3.2.1) - 28 Jan 2023

Shortened translations for several languages.

[Changes][R3.2.1]


<a name="R3.2.0"></a>
# [dailystats.py: Added translations for standard output and sheetupdate (R3.2.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R3.2.0) - 27 Jan 2023

# Translations
There are translations available for the following tools (only the standard output and sheetupdate, not the other generated csv files):
- dailystats.py
- summary.py (future update)

Remarks:
- The configured language in monitor.cfg is used for the translations, see monitor.cfg in [monitor.py](#monitorpy).
- Translations are inside monitor.translations.xlsx for easier Unicode editing and are saved in monitor.translations.csv as comma separated csv file in UTF-8 format, so unicode characters are preserved.
- All the supported languages have been translated with Google Translate and German is checked/corrected by a goingelectric.de user (thanks)
- Polish, Czech, Slovak, Hungarian are not translated, feel free to provide translations for those languages
- If (some) translations are not correct, please submit an issue with the proposed corrections, but be careful to provide them as unicode text, preferably using monitor.translations.xlsx

**Example translations of standard output (only first line is not the finally translated one, your browser might not display the unicode characters correct):**
- ["en" English](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/tests/OUTPUT/test.dailystats.en.logtrip)
- ["de" German](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/tests/OUTPUT/test.dailystats.de.logtrip)
- ["fr" French](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/tests/OUTPUT/test.dailystats.fr.logtrip)
- ["it" Italian](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/tests/OUTPUT/test.dailystats.it.logtrip)
- ["es" Spanish](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/tests/OUTPUT/test.dailystats.es.logtrip)
- ["sv" Swedish](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/tests/OUTPUT/test.dailystats.sv.logtrip)
- ["nl" Dutch](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/tests/OUTPUT/test.dailystats.nl.logtrip)
- ["no" Norwegian](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/tests/OUTPUT/test.dailystats.no.logtrip)
- "cs" Czech (no translation yet)
- "sk" Slovak (no translation yet)
- "hu" Hungarian (no translation yet)
- ["da" Danish](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/tests/OUTPUT/test.dailystats.da.logtrip)
- "pl" Polish (no translation yet)
- ["fi" Finnish](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/tests/OUTPUT/test.dailystats.fi.logtrip)
- ["pt" Portuguese](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/tests/OUTPUT/test.dailystats.pt.logtrip)


[Changes][R3.2.0]


<a name="R3.1.0"></a>
# [Added Type-hints, automatic tests and other improvements (R3.1.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R3.1.0) - 26 Jan 2023

**Added Type-hints, automatic tests and other improvements.**

General:
- all python scripts adapted to use type hints
- all python scripts static checked on type violations with mypy
- fixed mypy warnings

dailystats.py:
- improved matching of summary.trip.csv trips into dailystats 
- fixed unendless loop when summary.trip.csv contains unexpected line and changed ERROR into Warning

monitor.py:
- catch exceptions and only print stacktrace for general exceptions

summary.py:
- introduced dataclass Totals and GrandTotals for better readability, so T_* constants could be removed and type hints could be better implemented
- better check prefix that it startswith DAY or TRIP, to avoid wrong matching
- always rewrite summary.trip.csv, also when no trip is generated

tests\*:
- introduced automatic tests which check that output is as expected with same input, see tests\README.md





[Changes][R3.1.0]


<a name="R3.0.1"></a>
# [bug fix: avoid IndexError: list index out of range (R3.0.1)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R3.0.1) - 19 Jan 2023

Reported problem:
````
Traceback (most recent call last):
  File "/app/hyundai_kia_connect_monitor/dailystats.py", line 676, in <module>
    reverse_print_dailystats(TODAY_DAILY_STATS_LINE)  # and then dailystats
  File "/app/hyundai_kia_connect_monitor/dailystats.py", line 599, in reverse_print_dailystats
    reverse_print_dailystats_one_line(today_daily_stats_line)
  File "/app/hyundai_kia_connect_monitor/dailystats.py", line 592, in reverse_print_dailystats_one_line
    print_day_trip_info(date)
  File "/app/hyundai_kia_connect_monitor/dailystats.py", line 453, in print_day_trip_info
    print_tripinfo(
  File "/app/hyundai_kia_connect_monitor/dailystats.py", line 420, in print_tripinfo
    distance_summary_trip, kwh_consumed = get_trip_for_datetime(
  File "/app/hyundai_kia_connect_monitor/dailystats.py", line 372, in get_trip_for_datetime
    trip_time = trip_datetime.split(" ")[1]
IndexError: list index out of range
````

Solution: 
- updated dailystats.py to check length and skip header line correctly.

[Changes][R3.0.1]


<a name="R3.0.0"></a>
# [Major new release: Tripinfo from the car (Europe only) and other improvements (R3.0.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R3.0.0) - 19 Jan 2023

**Major new release: Tripinfo from the car (Europe only) and other improvements**

I have contributed the tripinfo of the car via a Pull Request to hyundai_kia_connect_api: https://github.com/Hyundai-Kia-Connect/hyundai_kia_connect_api/pull/259
Now the hyundai_kia_connect_monitor uses this information to show in dailystats.py.
Important to also upgrade hyundai_kia_connect_api to v2.4.0: https://github.com/Hyundai-Kia-Connect/hyundai_kia_connect_api/releases/tag/v2.4.0

![dailystats py_GoogleSpreadsheet](https://user-images.githubusercontent.com/90704821/213483967-17b9e0bf-1295-4d3d-9a27-77c486f9dd95.png)

# General:
I had an odometer bug in my IONIQ 5 with infotainment version 221129. Hyundai has fixed this in version 221223. Also other Hyundai and Kia users reported this odometer problem is solved with the newest infotainment update.
My tooling tried to workaround this problem a bit, but of course this was not ideal. Therefore I started with new examples from 2023-01-13 onwards (then I installed the update on my car), so I did not have strange results in combining detected trips and dailystats.

# monitor.py:
- new feature: append monitor.tripinfo.csv with latest tripinfo (first time it will try to go back 3 months)
- use vehicle.location_last_updated_at (needs hyundai_kia_connect_api >= 2.1.2)

![monitor xlsx](https://user-images.githubusercontent.com/90704821/213481972-32cc4bd0-d66f-40b9-86b0-b35db04f8b9a.jpg)

# summary.py:
- new: writes detected trips in file summary.trip.csv (date, odometer, distance, -kWh, +kWh)
- show larger number of lines in sheetupdate (increased from 50 to 122)
- show inaccurate summary values for trips
- workaround for trips, that sometimes SOC is decreased in next line, so the trip information shows not the correct used kWh
- sheetupdate default includes trip 

![summary py_GoogleSpreadsheet](https://user-images.githubusercontent.com/90704821/213482096-be084b24-e6ec-47b4-a845-d8760178e04d.png)

![summary day](https://user-images.githubusercontent.com/90704821/213482222-1c307e1f-9e6d-497f-b310-4ddd0fabee31.jpg)

![summary charge](https://user-images.githubusercontent.com/90704821/213482313-1fdc0626-bf29-4f7d-8fd4-4ddc7b12507c.jpg)

# dailystats.py (Europe only tool):
- shows monitor.tripinfo.csv info (trip info from the car) below the daily stastiscs
- shows summary.charge.csv info (charge info detected by summary.py)
- shows summary.trip.csv info  (trip info detected by summary.py, values between round brackets)

![dailystats py_GoogleSpreadsheet](https://user-images.githubusercontent.com/90704821/213483967-17b9e0bf-1295-4d3d-9a27-77c486f9dd95.png)

# debug.py:
- fixed extra needed call for hyundai_kia_connect_api  >= 2.0.0

# kml.py:
- cosmetic source code changes
- 
![kml py_GoogleMyMaps](https://user-images.githubusercontent.com/90704821/213482522-2fbd81c8-5205-4aed-81a3-e2ef79817bb3.jpg)

![kml py_GoogleMyMaps2](https://user-images.githubusercontent.com/90704821/213482615-ef1c3e3f-f6db-409f-af63-efa280652a06.jpg)

# README.rst:
- rewritten with the latest examples



[Changes][R3.0.0]


<a name="R2.18.0"></a>
# [Cosmetic changes to Google Spreadsheet output (R2.18.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R2.18.0) - 14 Jan 2023

Cosmetic changes to Google Spreadsheet output.

dailystats.py:
- headers are now in bold underline italic, so the difference is more clear
- Let Google Spreadsheet center the cells instead of adding spaces around by the tool

![monitor dailystats GoogleSpreadsheet](https://user-images.githubusercontent.com/90704821/212463905-71b4d2cf-e20a-4ecf-a79b-5ea9cb1acb5a.png)

summary.py:
- headers are now in bold underline italic, so the difference is more clear
- Let Google Spreadsheet center the cells instead of adding spaces around by the tool
- the first column headers are now right aligned and the values in column 2 left aligned, so they are closer to each other
- Switched columns EV range (now column U) and Address (now column V), because Address is the longest in content

![Screenshot_20230114-094116](https://user-images.githubusercontent.com/90704821/212464031-06923088-c7ef-4842-96d4-c9222c38849e.png)


[Changes][R2.18.0]


<a name="R2.17.0"></a>
# [NEW: summary.charge.csv for the detected charges and other improvements (R2.17.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R2.17.0) - 12 Jan 2023

NEW: summary.charge.csv for the detected charges and other improvements

summary.py:
- NEW: write summary.charge.csv for the detected charges, showing per day "date, odometer, +kWh, end of charge SOC%" (can be used by other tools)
- handle 0 and 1 also as False and True, so previous shrink.py output can be used by summary.py
- Improved the first few lines of Google spreadsheet to be better understandable
- Fixed the problem that empty information of the next day was shown (now till end of day is shown)

Other improvements

General:
- (Automatically) formatted python scripts by Black coding style
- Optimized performance by lazy execution of debug statements, so they are not executed in non-debug mode

monitor.py:
- added in monitor.lastrun the dailystats line of today (line 5)
- changed the labels in monitor.lastrun lines (can be used by other tools)

dailystats.py: 
- maximum of rows in Google spreadsheet output
- also show the dailystats for the current day, using monitor.lastrun

shrink.py:
- do not replace False and True by 0 and 1

Example output of summary.charged.csv:
````
date, odometer, +kWh, end charged SOC%
2022-09-21, 17383.5, 15.4, 68
2022-09-23, 17387.1, 6.3, 80
2022-09-24, 17794.9, 15.4, 7
2022-09-25, 17810.9, 37.1, 60
2022-09-30, 17867.2, 12.6, 60
2022-10-03, 18026.2, 23.8, 60
2022-10-09, 18115.4, 14.0, 58
2022-10-13, 18221.0, 13.3, 54
2022-10-14, 18248.3, 4.2, 60
2022-10-15, 18252.1, 4.2, 60
2022-10-17, 18406.7, 21.7, 59
2022-10-21, 18530.4, 17.5, 58
2022-10-22, 18564.9, 15.4, 80
2022-10-23, 18973.0, 51.1, 51
2022-10-24, 19026.6, 4.2, 57
2022-10-27, 19083.1, 27.3, 72
2022-10-31, 19262.4, 28.7, 72
2022-11-09, 19454.7, 15.4, 62
2022-11-16, 19555.6, 22.4, 70
2022-11-26, 20005.7, 13.3, 60
2022-11-27, 20428.2, 56.0, 30
2022-11-28, 20443.8, 48.3, 100
2022-12-04, 20779.8, 42.0, 90
2022-12-12, 20879.4, 23.1, 74
2022-12-21, 20994.2, 31.5, 80
2022-12-23, 21168.1, 42.0, 100
2022-12-24, 21579.5, 51.1, 70
2022-12-25, 21706.6, 5.6, 77
2022-12-31, 21746.9, 15.4, 76
2023-01-08, 22055.4, 42.7, 80
````

Screenshot of Excel example using summary.charged.csv: 
![summary charge](https://user-images.githubusercontent.com/90704821/212039031-62c1c79a-a674-4294-a5a2-b2293fc64f16.jpg)


[Changes][R2.17.0]


<a name="R2.16.0"></a>
# [fix to support also 2.1.2 and other improvements (R2.16.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R2.16.0) - 05 Jan 2023

- Fix to support for hyundai_kia_connect_api 2.1.2

monitor.py: 
- debug parameter now also enables hyundai_kia_connect_api debug logging
- improved monitor.lastrun or monitor.VIN.lastrun, contents contains now: 
- - last run
- - vin
- - newest updated at
- - last updated at
- - location last updated at
- - last_line

dailstats.py: 
- formatted the dates as yyyy-mm-dd instead of yyyymmdd
- added lastrun to dailystats.py

![monitor dailystats GoogleSpreadsheet](https://user-images.githubusercontent.com/90704821/210878366-683016ed-31ed-4a4a-a903-088404bc0cc3.png)

summary.py: added to sheetupdate:
- newest datetime of vehicle last updated at and location last updated at
- last update at datetime
- location last updated at datetime

![GoogleSpreadsheet](https://user-images.githubusercontent.com/90704821/210878443-6d223b41-aa95-4e64-8485-93565b3213f8.png)


[Changes][R2.16.0]


<a name="R2.15.0"></a>
# [(temporary) fix for wrong date/time stamps in monitor.csv (R2.15.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R2.15.0) - 03 Jan 2023

See this issue:  [date/timestamp sometimes wrong, old date/timestamp, while the longitude/latitude has been changed [#234](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/issues/234)] (https://github.com/Hyundai-Kia-Connect/hyundai_kia_connect_api/issues/234)

Compute the newest date from:
- vehicle.last_updated_at
- vehicle._location_last_set_time

Other fix: write the EV range without decimal point.


[Changes][R2.15.0]


<a name="R2.14.0"></a>
# [Bugfixes: get_last_line and to_int (R2.14.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R2.14.0) - 02 Jan 2023

Spotted a bug, when you run monitor.py for the first time or if monitor.csv does not yet exists, monitor.py will throw an exception in get_last_line, because this is run before the file is created.

Also the newer hyundai_kia_connect_api releases, e.g. [1.52.12](https://github.com/Hyundai-Kia-Connect/hyundai_kia_connect_api/releases/tag/v1.52.12), it is possible that a previous int value is now represented as float value. Made the tools resilient for that change, by stripping the digits after the decimal point in to_int.

[Changes][R2.14.0]


<a name="R2.13.0"></a>
# [Remove unneeded extra server calls and removed forceupdate possibility (R2.13.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R2.13.0) - 02 Jan 2023

For the following calls, the second is redundant, so removed:
````
vm.check_and_refresh_token()
vm.update_all_vehicles_with_cached_state()
````

See also this issue [Example code in README wrong, so the server is called too often, were less calls would be sufficient?](https://github.com/Hyundai-Kia-Connect/hyundai_kia_connect_api/issues/226)

Because I never want 12 volt battery drain as side effect by using the monitor tool, removed also the forceupdate possibility.

[Changes][R2.13.0]


<a name="R2.12.0"></a>
# [Added "python dailystats.py sheetupdate" and other improvements (R2.12.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R2.12.0) - 28 Dec 2022

- Added sheetupdate option to dailystats.py to update shared monitor.dailystats Google Spreadsheet
- Added EV range column to monitor.py, summary.py
- clear Google Spreadsheets with 1 instruction instead of looping
- Added/Updated examples
- Updated README

Note: dailystats from hyundai_kia_connect_api only available for Europe

Example monitor.dailystats Google spreadsheet screenshot:

![monitor dailystats GoogleSpreadsheet](https://user-images.githubusercontent.com/90704821/209866785-a1f42576-015b-465d-b0f6-13f959f44f07.png)

Example summary.py sheetupdate screenshot (with row 21 the EV range and extra EV range column):

![GoogleSpreadsheet](https://user-images.githubusercontent.com/90704821/209866847-805ef6fe-1aa7-4704-a371-b566b1b29559.png)


[Changes][R2.12.0]


<a name="R2.11.0"></a>
# [first version of dailystats.py (R2.11.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R2.11.0) - 27 Dec 2022

# dailystats.py
Read the monitor.dailystats.csv file and represent the totals and statistics per day in a nice formatted text to standard output.

Usage: 
```
python dailystats.py
or 
python dailystats.py vin=VIN
```
- INPUTFILE: monitor.dailystats.csv or monitor.dailystats.VIN.csv (latter if vin=VIN is given as parameter)
- standard output: totals and per day in a nice formatted text to standard output

Following information from hyundai_kia_connect_api from the monitor.dailystats.csv file (gathered by the car, so not computed by summary.py), with per day the following information:
- date
- distance
- distance_unit
- total_consumed Wh
- regenerated_energy Wh
- engine_consumption Wh
- climate_consumption Wh
- onboard_electronics_consumption Wh
- battery_care_consumption Wh

The dailystats.py [standard output of the monitor.dailystats.csv file](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/dailystats.py_output.txt)

output:
```
C:\Users\Rick\git\monitor>python dailystats.py
  Totals   Regen     Consumption    Engine   Climate  Electronics BatteryCare
 313.6kWh 47.4kWh     5.6km/kWh    268.5kWh  12.8kWh    32.3kWh      0.0kWh
  1756km   15.1%    17.9kWh/100km    86%       4.1%      10.3%        0.0%

 20221225  Regen     Consumption    Engine   Climate  Electronics BatteryCare
 26.8kWh   4.1kWh     5.9km/kWh    24.3kWh    0.5kWh     1.9kWh      0.0kWh
  159km    15.4%    16.8kWh/100km    91%       2.0%       7.1%        0.0%

 20221224  Regen     Consumption    Engine   Climate  Electronics BatteryCare
 69.2kWh   3.6kWh     5.9km/kWh    64.6kWh    1.4kWh     3.2kWh      0.0kWh
  407km     5.3%    17.0kWh/100km    93%       2.0%       4.7%        0.0%

 20221223  Regen     Consumption    Engine   Climate  Electronics BatteryCare
 23.8kWh   4.3kWh     6.5km/kWh    21.7kWh    0.3kWh     1.9kWh      0.0kWh
  154km    18.1%    15.5kWh/100km    91%       1.2%       7.9%        0.0%

 20221222  Regen     Consumption    Engine   Climate  Electronics BatteryCare
  3.2kWh   0.7kWh     5.0km/kWh     2.4kWh    0.1kWh     0.7kWh      0.0kWh
   16km    22.2%    20.1kWh/100km    75%       4.3%      20.9%        0.0%

 20221221  Regen     Consumption    Engine   Climate  Electronics BatteryCare
  3.6kWh   1.1kWh     4.4km/kWh     2.3kWh    0.3kWh     1.0kWh      0.0kWh
   16km    29.9%    22.6kWh/100km    63%       8.7%      28.7%        0.0%

 20221220  Regen     Consumption    Engine   Climate  Electronics BatteryCare
  1.2kWh   0.3kWh     4.3km/kWh     0.7kWh    0.1kWh     0.4kWh      0.0kWh
   5km     29.1%    23.3kWh/100km    59%      10.0%      30.9%        0.0%

 20221216  Regen     Consumption    Engine   Climate  Electronics BatteryCare
  4.1kWh   0.8kWh     2.9km/kWh     1.8kWh    1.1kWh     1.2kWh      0.0kWh
   12km    19.9%    34.1kWh/100km    44%      25.8%      30.3%        0.0%

 20221214  Regen     Consumption    Engine   Climate  Electronics BatteryCare
  2.4kWh   1.0kWh     3.7km/kWh     1.3kWh    0.4kWh     0.7kWh      0.0kWh
   9km     40.5%    26.9kWh/100km    56%      17.5%      26.8%        0.0%

 20221213  Regen     Consumption    Engine   Climate  Electronics BatteryCare
  4.9kWh   1.4kWh     4.3km/kWh     2.9kWh    0.9kWh     1.1kWh      0.0kWh
   21km    28.5%    23.3kWh/100km    59%      19.3%      21.8%        0.0%

 20221212  Regen     Consumption    Engine   Climate  Electronics BatteryCare
  9.1kWh   1.8kWh     5.0km/kWh     6.9kWh    1.1kWh     1.0kWh      0.0kWh
   45km    19.5%    20.2kWh/100km    76%      12.2%      11.3%        0.0%

 20221211  Regen     Consumption    Engine   Climate  Electronics BatteryCare
  1.2kWh   0.4kWh     4.0km/kWh     0.8kWh    0.1kWh     0.3kWh      0.0kWh
   5km     35.7%    25.0kWh/100km    63%       9.2%      28.0%        0.0%

 20221210  Regen     Consumption    Engine   Climate  Electronics BatteryCare
  1.9kWh   0.7kWh     3.7km/kWh     1.2kWh    0.2kWh     0.5kWh      0.0kWh
   7km     34.7%    27.3kWh/100km    63%       8.5%      28.3%        0.0%

 20221209  Regen     Consumption    Engine   Climate  Electronics BatteryCare
  6.9kWh   1.7kWh     4.9km/kWh     5.1kWh    0.5kWh     1.3kWh      0.0kWh
   34km    25.2%    20.3kWh/100km    74%       7.6%      18.8%        0.0%

 20221208  Regen     Consumption    Engine   Climate  Electronics BatteryCare
  1.9kWh   0.6kWh     4.2km/kWh     1.0kWh    0.0kWh     0.9kWh      0.0kWh
   8km     33.1%    24.0kWh/100km    54%       0.6%      45.8%        0.0%

 20221207  Regen     Consumption    Engine   Climate  Electronics BatteryCare
  1.8kWh   0.4kWh     4.4km/kWh     1.1kWh    0.1kWh     0.6kWh      0.0kWh
   8km     22.0%    23.0kWh/100km    61%       8.0%      31.0%        0.0%

 20221206  Regen     Consumption    Engine   Climate  Electronics BatteryCare
  2.7kWh   0.9kWh     4.8km/kWh     1.7kWh    0.2kWh     0.8kWh      0.0kWh
   13km    33.2%    20.7kWh/100km    62%       7.0%      30.8%        0.0%

 20221205  Regen     Consumption    Engine   Climate  Electronics BatteryCare
  3.2kWh   1.1kWh     4.4km/kWh     2.0kWh    0.3kWh     0.9kWh      0.0kWh
   14km    34.5%    22.9kWh/100km    62%      10.3%      27.8%        0.0%

 20221204  Regen     Consumption    Engine   Climate  Electronics BatteryCare
 25.7kWh   2.5kWh     6.0km/kWh    23.2kWh    0.9kWh     1.5kWh      0.0kWh
  154km     9.9%    16.7kWh/100km    91%       3.6%       5.8%        0.0%

 20221203  Regen     Consumption    Engine   Climate  Electronics BatteryCare
  7.0kWh   2.4kWh     5.5km/kWh     5.5kWh    0.6kWh     0.9kWh      0.0kWh
   38km    34.1%    18.3kWh/100km    79%       8.0%      13.1%        0.0%

 20221202  Regen     Consumption    Engine   Climate  Electronics BatteryCare
 10.3kWh   3.4kWh     5.3km/kWh     7.8kWh    0.7kWh     1.8kWh      0.0kWh
   54km    33.4%    19.0kWh/100km    76%       6.5%      17.6%        0.0%

 20221201  Regen     Consumption    Engine   Climate  Electronics BatteryCare
  9.5kWh   3.1kWh     6.0km/kWh     7.8kWh    0.4kWh     1.4kWh      0.0kWh
   57km    32.4%    16.7kWh/100km    82%       3.7%      14.5%        0.0%

 20221130  Regen     Consumption    Engine   Climate  Electronics BatteryCare
  1.0kWh   0.5kWh     4.0km/kWh     0.6kWh    0.1kWh     0.3kWh      0.0kWh
   4km     46.2%    25.2kWh/100km    61%       9.2%      29.8%        0.0%

 20221129  Regen     Consumption    Engine   Climate  Electronics BatteryCare
  3.2kWh   1.3kWh     5.6km/kWh     2.3kWh    0.2kWh     0.7kWh      0.0kWh
   18km    39.5%    18.0kWh/100km    70%       7.7%      22.3%        0.0%

 20221128  Regen     Consumption    Engine   Climate  Electronics BatteryCare
  3.0kWh   1.1kWh     4.7km/kWh     1.9kWh    0.2kWh     0.9kWh      0.0kWh
   14km    37.6%    21.4kWh/100km    63%       5.3%      31.4%        0.0%

 20221127  Regen     Consumption    Engine   Climate  Electronics BatteryCare
 74.0kWh   4.0kWh     5.6km/kWh    68.6kWh    1.4kWh     3.9kWh      0.0kWh
  418km     5.4%    17.7kWh/100km    93%       1.9%       5.3%        0.0%

 20221126  Regen     Consumption    Engine   Climate  Electronics BatteryCare
  1.9kWh   0.6kWh     3.7km/kWh     1.1kWh    0.2kWh     0.6kWh      0.0kWh
   7km     33.7%    26.9kWh/100km    60%       9.0%      31.4%        0.0%

 20221124  Regen     Consumption    Engine   Climate  Electronics BatteryCare
  2.8kWh   1.3kWh     6.5km/kWh     2.2kWh    0.1kWh     0.4kWh      0.0kWh
   18km    47.9%    15.5kWh/100km    80%       4.1%      15.8%        0.0%

 20221123  Regen     Consumption    Engine   Climate  Electronics BatteryCare
  7.2kWh   2.1kWh     5.7km/kWh     5.6kWh    0.3kWh     1.3kWh      0.0kWh
   41km    28.5%    17.6kWh/100km    77%       4.5%      18.4%        0.0%

```

[Changes][R2.11.0]


<a name="R2.10.0"></a>
# [added monitor.dailystats.csv and improvements (R2.10.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R2.10.0) - 24 Dec 2022

The hyundai_kia_connect_api also sends daily statistics of the car for Europe. Following information from hyundai_kia_connect_api is added to the monitor.dailystats.csv file (gathered by the car, so not computed by summary.py), with per day the following information:
- date
- distance
- distance_unit
- total_consumed Wh
- regenerated_energy Wh
- engine_consumption Wh
- climate_consumption Wh
- onboard_electronics_consumption Wh
- battery_care_consumption Wh

I am going to use this in a new tool, dailystats.py, which will be released in the near future. But you can already gather this information, because only the daily statistics for a period are send.

Other improvements:
- only append a line to monitor.csv if the line is different
- last update date/time is now written to file monitor.lastrun 
- fix "last entry" in summary.py sheetupdate, it does now contain the whole last line in monitor.csv file.

[Changes][R2.10.0]


<a name="R2.9.0"></a>
# [Add language configuration to avoid language reset in Bluelink or Connect App (R2.9.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R2.9.0) - 21 Dec 2022

The Bluelink App is reset to English in Europe for users who have set another language in the Bluelink App when using hyundai_kia_connect_api. I do not know if this is also for the Kia UVO Connect App, but I assume those users will have the same problem. 

To avoid the side-effect of the reset of the Hyundai Bluelink or Kia Uvo Connect App, you can change the configuration language  in monitor.cfg (default is "en"). I you have a previous monitor.cfg, you have to add the language configuration manually.

Note that you should also update the [hyundai_kia_connect_api to v1.50.3](https://github.com/Hyundai-Kia-Connect/hyundai_kia_connect_api/releases/tag/v1.50.3), because I did provide the changes for this issue:  [Android Bluelink App language is reset to English when using hyundai_kia_connect_api #145](https://github.com/Hyundai-Kia-Connect/hyundai_kia_connect_api/issues/145) in this [Pull Request](https://github.com/Hyundai-Kia-Connect/hyundai_kia_connect_api/pull/201). 

Configuration example for Dutch:
```
language = nl
```

e.g. for German:
```
language = de
```

Note: this is only implemented for Europe currently. For a list of [language codes, see here.](https://www.science.co.il/language/Codes.php). Currently in Europe the Bluelink App shows the following languages:

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


[Changes][R2.9.0]


<a name="R2.8.0"></a>
# [small improvements and workaround for bug in infotainment update 221129 (R2.8.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R2.8.0) - 17 Dec 2022

- Updated summary.py to avoid divide by zero, warning when timestamp is wrong and keep track and use of highest odometer value (latter is poor man's workaround for bug in infotainment update 221129 in Europe)
- Updated monitor.py to check for empty geocode names
- Updated debug.py to be compatible with later hyundai_kia_connect_api versions (API is changed for driving distance changed into driving range and charge limits AC and DC)
- Tested in combination with latest hyundai_kia_connect_api v1.47.1


[Changes][R2.8.0]


<a name="R2.7.1"></a>
# [Bugfix for R2.7.0 (R2.7.1)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R2.7.1) - 08 Dec 2022

Program error fix for R2.7.0.

[Changes][R2.7.1]


<a name="R2.7.0"></a>
# [support multiple vehicles and some small improvements (R2.7.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R2.7.0) - 07 Dec 2022

The hyundai_kia_connect_api supports multiple vehicles under the same bluelink account.

Whenever more vehicles are coupled to the same bluelink account, the monitor.py script will not write the output to monitor.csv, but to the file monitor.VIN.csv, where VIN is the VIN number of the coupled vehicle.

You also need to provide the VIN to the appropriate scripts when multiple vehicles are coupled to your bluelink account, e.g.
- python summary.py vin=VIN
- python summary.py sheetupdate vin=VIN
- python kml.py vin=VIN
- python shrink.py vin=VIN

Note that for "python summary.py sheetupdate vin=VIN" the spreadsheet name should be "monitor.VIN" instead of "hyundai-kia-connect-monitor"", so make sure to configure the Google spreadsheet with that name.

Some other small improvements:
- clear cells in SHEETUPDATE, also W columns
- also show last TRIP of last day

[Changes][R2.7.0]


<a name="R2.6.0"></a>
# [Small improvements (R2.6.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R2.6.0) - 02 Dec 2022

- Small improvements to summary.py sheetupdate, clearing row 21 and removing spaces around latest info
- Default is only forceupdate after 7 days in monitor.cfg, so in practice no forceupdate will occur
- Updated README with video of BM2 Battery Monitor:

[This video shows why it is important to avoid awakening the car for actual values.](https://youtu.be/rpLWEe-2aUU?t=121) 30 nov 6:10 a forceupdate has been done and you see a dip from 12.92 Volt to 12.42 Volt for a moment and then back to 12.83 Volt. Note by default the tool asks only for server cache updates and the car decides when to send push notifications with actual values to the server.

[Changes][R2.6.0]


<a name="R2.5.0"></a>
# [Robustness and cleanup (R2.5.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R2.5.0) - 29 Nov 2022

Robustness and cleanup
- Skip entries in monitor.py with None as odometer, because I have had this twice using the hyundai_kia_connect_api v1.40.12
- Removed MOVE from summary.py, because with the cacheupdate intermediate locations are no longer reported
- Removed ADDRESS parameter from summary.py, because monitor.py has now this option and take over address when provided by monitor.py
- Removed geopy dependency (possible because of removal of ADDRESS possibility)
- Made scripts robust against None values
- Added retry to summary.py SHEETUPDATE, so when the Google service is unavailable it is retried one minute later


[Changes][R2.5.0]


<a name="R2.4.0"></a>
# [added address possibilities to monitor.py and fixed bug in sheetupdate (R2.4.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R2.4.0) - 26 Nov 2022

- fixed bug in sheetupdate
- added address possibilities to monitor.py
- use possible address from monitor.csv in summary.py

Note: you need to add the use_geocode and use_geocode_email configuration to monitor.cfg, if you have an existing monitor.cfg configuration.


[Changes][R2.4.0]


<a name="R2.3.0"></a>
# [Major new release, no more 12 volt battery drain! (R2.3.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R2.3.0) - 24 Nov 2022

- Added force_update_seconds configuration, cacheupdate and forceupdate
- Added check if parameters are not mistyped (wrong keyword as parameter)
- Added help parameter for monitor.py and summary.py
- Improved sheetupdate
- Improved README
 
Best of all is the fact that it does no longer drain your 12 volt battery of the car, because it default uses the cached server information!
This is tested in combination with [hyundai_kia_connect_api v1.40.11](https://github.com/Hyundai-Kia-Connect/hyundai_kia_connect_api/releases/tag/v1.40.11), so consider to upgrade also the api package if you are using an older version. 

The monitor tool will by default only do a forced update when the last car to server update is more than 8 hours ago. So only a maximum of 3 times a day the car could be asked for the latest information with the default configuration. This time difference is configurable, so you can decide to do it even less, e.g. max once a day, or more often, e.g. max 12 times a day. But you have also the option to only use cacheupdate as parameter to monitor.py. And you can also run a forceupdate as parameter to monitor.py, or e.g. once a day. Choose the options you like the most. See [here some crontab examples](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor#raspberry-pi-configuration) 

If you only ask for cached values, the car will not be woken up, the 12 volt battery of the car will not be drained by the tool and you will only get the cached values from the server.

The car sends the updates (push messages) to the server when something happens on the car side. This is the case when the car is started or switched off, when charging is complete and possibly in other situations. So no extra drain of the 12 volt battery because of the hyundai_kia_connect_monitor tool!

And of course when you run an update or command through the Bluelink app, but that is on purpose.

Note that if you do a lot of forceupdate calls, than definitely the car 12 volt battery can be drained. See [here some results of someone with an IONIQ 5 using forceupdate](https://community.home-assistant.io/t/hyundai-bluelink-integration/319129/132), so use this forceupdate option carefully:
```
With 15-minute forced updates:
95% to 80% in 8 hours, approx. 1.8%/hour

With 60-minute forced updates:
93% to 82% in 14 hours, approx. 0.78%/hour
```

Note: do not forget to configure monitor.cfg for the configuration item force_update_seconds 

[Changes][R2.3.0]


<a name="R2.2.0"></a>
# [Fixed weekday bug in sheetupdate (R2.2.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R2.2.0) - 19 Nov 2022

fixed bug that summary.py sheetupdate showed wrong weekday for last update values.

[Changes][R2.2.0]


<a name="R2.1.0"></a>
# [Fixed bug in summary average computation (R2.1.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R2.1.0) - 16 Nov 2022

Fixed bug in summary.py that average were not correctly computed when only 1 entry on a day

[Changes][R2.1.0]


<a name="R2.0.0"></a>
# [Added GoogleSpreadsheet option: python summary.py sheetupdate (R2.0.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R2.0.0) - 05 Nov 2022

- Fixed a bug that the average SOC% and average 12 Volt% for the last entries were incorrect
- Added the option to update a Google Spreadsheet: python summary.py sheetupdate

summary.py does now have a dependency on the package gspread, so install this package, e.g. python -m pip install gspread
When you want to use the summary.py sheetupdate option, you have to configure authentication and setup a shared hyundai-kia-connect-monitor spreadsheet. See this description: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor#configuration-of-gspread-for-python-summarypy-sheetupdate

Example screenshot: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor#python-summarypy-sheetupdate

![alt text](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/GoogleSpreadsheet.png)
 

[Changes][R2.0.0]


<a name="R1.9.0"></a>
# [summary.py: add averages for trip, day, week, month and prediction for year (R1.9.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R1.9.0) - 29 Oct 2022

Do you also want to know how the prediction will be over a year, using the already captured information? 
- How many kilometers or miles you will drive
- How many kWh you need for this?
- What does this cost over this year, using the cost per kWh

Also interesting to know:
- what is the average trip distance (TRIPAVG)?
- what is the average distance you drive per day (DAYAVG)?
- what are the averages per week (WEEKAVG) or month (MONTHAVG)

````
C:\Users\Rick\git\monitor>python summary.py year
  Period, date      , info , odometer, delta km,    +kWh,     -kWh, km/kWh, kWh/100km, cost Euro, SOC%CUR,AVG,MIN,MAX, 12V%CUR,AVG,MIN,MAX, #charges,   #trips,   #moves
YEAR    , 2022-09-25, 2022 ,  17794.9,    470.7,    70.7,    -73.5,    6.4,      15.6,     18.08,      50, 50,  5,100,      97, 97, 85, 98,      7  ,     14  ,     27
TRIPAVG , 2022-09-25,  14t ,  17794.9,     33.6,     5.0,     -5.2,    6.4,      15.6,      1.29,      50, 50,  5,100,      97, 97, 85, 98,      0.5,      1  ,      1.9
DAYAVG  , 2022-09-25,   9d ,  17794.9,     52.3,     7.9,     -8.2,    6.4,      15.6,      2.01,      50, 50,  5,100,      97, 97, 85, 98,      0.8,      1.6,      3
WEEKAVG , 2022-09-25,   9d ,  17794.9,    366.1,    55.0,    -57.2,    6.4,      15.6,     14.06,      50, 50,  5,100,      97, 97, 85, 98,      5.4,     10.9,     21
MONTHAVG, 2022-09-25,   9d ,  17794.9,   1590.8,   238.9,   -248.4,    6.4,      15.6,     61.11,      50, 50,  5,100,      97, 97, 85, 98,     23.7,     47.3,     91.2
YEARLY  , 2022-09-25,   9d ,  17794.9,  19089.5,  2867.3,  -2980.8,    6.4,      15.6,    733.29,      50, 50,  5,100,      97, 97, 85, 98,    283.9,    567.8,   1095
````

[Changes][R1.9.0]


<a name="R1.8.0"></a>
# [Added odometer, current SOC% and current 12V% to summary (R1.8.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R1.8.0) - 27 Oct 2022

For trip administration tools it is of course important also to be able to see the odometer value for a particular day or trip. And I discovered this was NOT in the summary overview. So this is added to summary.py. 

Also the current SOC% is added, so you know what the end SOC was e.g. on a particular day. The same for 12Volt%.

````
C:\Users\Rick\git\monitor>python summary.py
Period, date      , info , odometer, delta km,    +kWh,     -kWh, km/kWh, kWh/100km, cost Euro, SOC%CUR,AVG,MIN,MAX, 12V%CUR,AVG,MIN,MAX, #charges, #drives, #moves
DAY   , 2022-09-17, Sat  ,  17324.2,         ,     2.8,         ,       ,          ,          ,      58, 55, 55, 58,      91, 91, 91, 91,        1,        ,
DAY   , 2022-09-18, Sun  ,  17324.2,         ,     0.7,         ,       ,          ,          ,      59, 59, 59, 60,      91, 91, 91, 91,         ,        ,
WEEK  , 2022-09-18, WK 37,  17324.2,         ,     3.5,         ,       ,          ,          ,      59, 59, 55, 60,      91, 91, 91, 91,        1,        ,
TRIP  , 2022-09-19, 15:00,  17324.3,      0.1,        ,         ,       ,          ,          ,      61, 60, 60, 61,      85, 90, 85, 91,         ,       1,      1
TRIP  , 2022-09-19, 16:00,  17330.7,      6.4,        ,     -1.4,       ,          ,          ,      59, 60, 59, 59,      86, 85, 86, 86,         ,       1,      1
DAY   , 2022-09-19, Mon  ,  17330.7,      6.5,        ,         ,       ,          ,          ,      59, 60, 59, 61,      86, 88, 85, 91,         ,       2,      2
TRIP  , 2022-09-20, 08:00,  17358.9,     28.2,        ,     -4.2,    6.7,      14.9,      1.03,      53, 57, 53, 59,      91, 88, 88, 91,         ,       1,      2
TRIP  , 2022-09-20, 15:30,  17371.5,     12.6,        ,     -2.1,    6.0,      16.7,      0.52,      48, 50, 48, 51,      92, 90, 87, 92,         ,       1,      3
TRIP  , 2022-09-20, 15:58,  17378.3,      6.8,        ,     -0.7,       ,          ,          ,      47, 47, 47, 47,      91, 91, 91, 91,         ,       1,      1
DAY   , 2022-09-20, Tue  ,  17378.3,     47.6,        ,     -7.0,    6.8,      14.7,      1.72,      45, 48, 45, 59,      91, 91, 87, 92,         ,       3,      6
TRIP  , 2022-09-21, 12:30,  17380.8,      2.5,     4.9,         ,       ,          ,          ,      52, 48, 46, 52,      92, 91, 91, 92,        1,       1,      1
TRIP  , 2022-09-21, 13:00,  17383.5,      2.7,        ,     -0.7,       ,          ,          ,      51, 51, 51, 51,      91, 91, 91, 91,         ,       1,      1
DAY   , 2022-09-21, Wed  ,  17383.5,      5.2,    18.2,     -0.7,       ,          ,          ,      70, 63, 46, 70,      91, 91, 91, 92,        2,       2,      2
DAY   , 2022-09-22, Thu  ,  17383.5,         ,        ,         ,       ,          ,          ,      72, 72, 72, 72,      91, 91, 91, 91,        1,        ,
TRIP  , 2022-09-23, 11:21,  17385.4,      1.9,        ,     -0.7,       ,          ,          ,      71, 71, 71, 71,      88, 89, 88, 88,         ,       1,      1
TRIP  , 2022-09-23, 12:00,  17387.1,      1.7,     0.7,         ,       ,          ,          ,      72, 71, 72, 72,      87, 87, 87, 87,        1,       1,      1
DAY   , 2022-09-23, Fri  ,  17387.1,      3.6,    20.3,     -0.7,       ,          ,          ,     100, 86, 71,100,      87, 87, 87, 88,        2,       2,      2
TRIP  , 2022-09-24, 09:57,  17390.8,      3.7,        ,     -0.7,       ,          ,          ,      99,100, 99,100,      95, 94, 95, 95,         ,       1,
TRIP  , 2022-09-24, 13:21,  17589.2,    198.4,        ,    -32.9,    6.0,      16.6,      8.09,      52, 80, 52, 98,      96, 96, 92, 98,         ,       1,      6
TRIP  , 2022-09-24, 14:31,  17592.5,      3.3,        ,     -0.7,       ,          ,          ,      51, 51, 51, 51,      94, 95, 94, 94,         ,       1,      1
TRIP  , 2022-09-24, 15:23,  17597.3,      4.8,        ,     -0.7,       ,          ,          ,      50, 51, 50, 51,      96, 94, 93, 96,         ,       1,      2
TRIP  , 2022-09-24, 19:00,  17794.9,    197.6,        ,    -31.5,    6.3,      15.9,      7.75,       5, 30,  5, 50,      97, 95, 94, 97,        1,       1,      6
DAY   , 2022-09-24, Sat  ,  17794.9,    407.8,    25.9,    -66.5,    6.1,      16.3,     16.36,      42, 40,  5,100,      97, 96, 92, 98,        1,       5,     15
DAY   , 2022-09-25, Sun  ,  17794.9,         ,     5.6,         ,       ,          ,          ,      50, 50, 43, 50,      97, 97, 97, 97,         ,        ,
WEEK  , 2022-09-25, WK 38,  17794.9,    470.7,    67.2,    -73.5,    6.4,      15.6,     18.08,      50, 50,  5,100,      97, 97, 85, 98,        6,      14,     27
MONTH , 2022-09-25, Sep  ,  17794.9,    470.7,    70.7,    -73.5,    6.4,      15.6,     18.08,      50, 50,  5,100,      97, 97, 85, 98,        7,      14,     27
YEAR  , 2022-09-25, 2022 ,  17794.9,    470.7,    70.7,    -73.5,    6.4,      15.6,     18.08,      50, 50,  5,100,      97, 97, 85, 98,        7,      14,     27
````

[Changes][R1.8.0]


<a name="R1.7.0"></a>
# [Added address possibility to kml.py and small improvements (R1.7.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R1.7.0) - 25 Oct 2022

- added address possibility to kml.py
- map None to -1 in kml.py (when no 12 volt percentage is reported)
- added requirements.txt for the needed dependencies
- added dependency hyundai_kia_connect_api==1.34.4
- added kml.py address parameter explanation in README.md
- when day change, use first entry as previous day at 23:59 in summary.py, otherwise trips after the last snapshot of a day are counted wrong

Example:
````
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
 26: 20220924 13:00  D (5.768325,52.898894) SOC: 57% 12V: 98% ODO: 17390.8 Address: "A6, Oldeouwer, De Fryske Marren, Fryslân, Nederland, 8516 DD, Nederland"       drive
 27: 20220924 13:21    (5.683261,53.036686) SOC: 52% 12V: 96% ODO: 17589.2 Address: "17-101, Dekamalaan, Sneek, Súdwest-Fryslân, Fryslân, Nederland, 8604 ZG, Nederland"       (+198.4 since 20220924 13:00)
 28: 20220924 14:31    (5.681147,53.016858) SOC: 51% 12V: 94% ODO: 17592.5 Address: "Van der Valk Hotel Sneek, 1, Burgemeester Rasterhofflaan, Houkesloot, Sneek, Súdwest-Fryslân, Fryslân, Nederland, 8606 KZ, Nederland"       (+3.3 since 20220924 14:00)
 29: 20220924 15:00  D (5.686422,53.030697) SOC: 51% 12V: 93% ODO: 17592.5 Address: "Stadsrondweg-Oost, Houkesloot, Sneek, Súdwest-Fryslân, Fryslân, Nederland, 8604 GC, Nederland"       drive
 30: 20220924 15:23    (5.68325 ,53.036683) SOC: 50% 12V: 96% ODO: 17597.3 Address: "17-101, Dekamalaan, Sneek, Súdwest-Fryslân, Fryslân, Nederland, 8604 ZG, Nederland"       (+4.8 since 20220924 15:00)
 31: 20220924 16:30  D (5.6802  ,53.035853) SOC: 50% 12V: 94% ODO: 17597.3 Address: "10, Groenedijk, Sneek, Súdwest-Fryslân, Fryslân, Nederland, 8604 AB, Nederland"       drive
 32: 20220924 17:00  D (5.771994,52.709039) SOC: 40% 12V: 94% ODO: 17597.3 Address: "A6, De Zuidert, Emmeloord, Noordoostpolder, Flevoland, Nederland, 8305 AC, Nederland"       drive
 33: 20220924 17:30  D (5.375436,52.411236) SOC: 30% 12V: 95% ODO: 17597.3 Address: "Rijksweg A6, Lelystad, Flevoland, Nederland, 3897 MA, Nederland"       drive
 34: 20220924 18:00  D (5.158522,52.095317) SOC: 21% 12V: 94% ODO: 17597.3 Address: "A27, Rijnsweerd, Utrecht, Nederland, 3731 GC, Nederland"       drive
 35: 20220924 18:30  D (5.293333,51.748758) SOC: 10% 12V: 96% ODO: 17597.3 Address: "A2, Hoenzadriel, Maasdriel, Gelderland, Nederland, 5334 NV, Nederland"       drive
 36: 20220924 19:00 C  (5.124957,51.68260 ) SOC:  5% 12V: 97% ODO: 17794.9 Address: "26, Keniaring, Drunen, Heusden, Noord-Brabant, Nederland, 5152 MX, Nederland"       (+197.6 since 20220924 18:30) charging plugged:2
````

[Changes][R1.7.0]


<a name="R1.6.0"></a>
# [summary.py: added moves and addresses possibilities (R1.6.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R1.6.0) - 24 Oct 2022

- Whenever the State Of Charge % or 12 Volt % is returning None, this is mapped to -1 (can occur if car cannot determine the value).
- The number of coordinate changes is now counted (#moves in summary.py)
- The distance between two changed coordinates are computed using geopy (so this is not the actual distance using the road) when move is gives as parameter to summary.py
- The address is computed for move and/or trip when address is given as parameter to summary.py
- Each address lookup will sleep for 1 second, to avoid abuse of the geopy Nominatim service limitations/abuse

Note that you need to install the python package geopy for summary.py
  
Example output when showing day, trip, move and address:
````
C:\Users\Rick\git\monitor>python summary.py day trip move address
Period, date      , info , delta km,    +kWh,     -kWh, km/kWh, kWh/100km, cost Euro, SOC%AVG,MIN,MAX, 12V%AVG,MIN,MAX, #charges, #drives, #moves, Address
DAY   , 2022-09-17, Sat  ,         ,     0.7,         ,       ,          ,          ,      54, 55, 55,      90, 91, 91,        1,        ,       ,
DAY   , 2022-09-18, Sun  ,         ,     2.8,         ,       ,          ,          ,      59, 58, 60,      91, 91, 91,         ,        ,       ,
MOVE  , 2022-09-19, 15:00,      0.4,        ,         ,       ,          ,          ,      61, 61, 61,      88, 85, 85,         ,       1,      1, "Statenlaan, Drunen, Heusden, Noord-Brabant, Nederland, 5152 SG, Nederland"
TRIP  , 2022-09-19, 15:00,      0.1,     3.5,         ,       ,          ,          ,      59, 55, 61,      91, 85, 91,        1,       1,      1, "Statenlaan, Drunen, Heusden, Noord-Brabant, Nederland, 5152 SG, Nederland"
MOVE  , 2022-09-19, 16:00,      0.4,        ,     -1.4,       ,          ,          ,      60, 59, 59,      85, 86, 86,         ,       1,      1, "26, Keniaring, Drunen, Heusden, Noord-Brabant, Nederland, 5152 MX, Nederland"
TRIP  , 2022-09-19, 16:00,      6.4,        ,     -1.4,       ,          ,          ,      60, 59, 59,      85, 86, 86,         ,       1,      1, "26, Keniaring, Drunen, Heusden, Noord-Brabant, Nederland, 5152 MX, Nederland"
DAY   , 2022-09-19, Mon  ,      6.5,        ,         ,       ,          ,          ,      60, 59, 61,      89, 85, 91,         ,       2,      2,
MOVE  , 2022-09-20, 07:00,      2.3,        ,         ,       ,          ,          ,      59, 59, 59,      87, 88, 88,         ,        ,      1, "Akkerlaan, Bloemenoord, Waalwijk, Noord-Brabant, Nederland, 5143 ND, Nederland"
MOVE  , 2022-09-20, 08:00,      2.3,        ,     -4.2,    0.5,     182.6,      1.03,      56, 53, 53,      89, 91, 91,         ,       1,      1, "26, Keniaring, Drunen, Heusden, Noord-Brabant, Nederland, 5152 MX, Nederland"
TRIP  , 2022-09-20, 08:00,     28.2,        ,     -4.2,    6.7,      14.9,      1.03,      58, 53, 59,      87, 86, 91,         ,       1,      2, "26, Keniaring, Drunen, Heusden, Noord-Brabant, Nederland, 5152 MX, Nederland"
MOVE  , 2022-09-20, 14:30,      1.3,        ,     -0.7,       ,          ,          ,      50, 50, 50,      89, 87, 87,         ,        ,      1, "18, Leliestraat, Drunen, Heusden, Noord-Brabant, Nederland, 5151 TP, Nederland"
MOVE  , 2022-09-20, 15:00,      4.0,        ,     -0.7,       ,          ,          ,      49, 49, 49,      89, 91, 91,         ,        ,      1, "Desso Tarkett, 15, Taxandriaweg, Laageinde, Waalwijk, Noord-Brabant, Nederland, 5142 PA, Nederland"
MOVE  , 2022-09-20, 15:30,      2.2,        ,     -0.7,       ,          ,          ,      48, 48, 48,      91, 92, 92,         ,       1,      1, "29b, Westeinde, Besoijen, Waalwijk, Noord-Brabant, Nederland, 5141 AA, Nederland"
TRIP  , 2022-09-20, 15:30,     12.6,        ,     -2.1,    6.0,      16.7,      0.52,      50, 48, 51,      90, 87, 92,         ,       1,      3, "29b, Westeinde, Besoijen, Waalwijk, Noord-Brabant, Nederland, 5141 AA, Nederland"
MOVE  , 2022-09-20, 15:58,      5.4,        ,     -0.7,       ,          ,          ,      47, 47, 47,      91, 91, 91,         ,       1,      1, "26, Keniaring, Drunen, Heusden, Noord-Brabant, Nederland, 5152 MX, Nederland"
TRIP  , 2022-09-20, 15:58,      6.8,        ,     -0.7,       ,          ,          ,      47, 47, 47,      91, 91, 91,         ,       1,      1, "26, Keniaring, Drunen, Heusden, Noord-Brabant, Nederland, 5152 MX, Nederland"
DAY   , 2022-09-20, Tue  ,     47.6,        ,     -7.0,    6.8,      14.7,      1.72,      54, 47, 59,      89, 86, 92,         ,       3,      6,
MOVE  , 2022-09-21, 12:30,      1.3,     0.7,         ,       ,          ,          ,      51, 52, 52,      91, 92, 92,         ,       1,      1, "18, Leliestraat, Drunen, Heusden, Noord-Brabant, Nederland, 5151 TP, Nederland"
TRIP  , 2022-09-21, 12:30,      2.5,     3.5,         ,       ,          ,          ,      46, 45, 52,      91, 91, 92,        1,       1,      1, "18, Leliestraat, Drunen, Heusden, Noord-Brabant, Nederland, 5151 TP, Nederland"
MOVE  , 2022-09-21, 13:00,      1.3,        ,     -0.7,       ,          ,          ,      51, 51, 51,      91, 91, 91,         ,       1,      1, "26, Keniaring, Drunen, Heusden, Noord-Brabant, Nederland, 5152 MX, Nederland"
TRIP  , 2022-09-21, 13:00,      2.7,        ,     -0.7,       ,          ,          ,      51, 51, 51,      91, 91, 91,         ,       1,      1, "26, Keniaring, Drunen, Heusden, Noord-Brabant, Nederland, 5152 MX, Nederland"
DAY   , 2022-09-21, Wed  ,      5.2,    15.4,     -0.7,       ,          ,          ,      50, 45, 68,      91, 91, 92,        2,       2,      2,
DAY   , 2022-09-22, Thu  ,         ,     1.4,         ,       ,          ,          ,      69, 70, 72,      91, 91, 91,        1,        ,       ,
MOVE  , 2022-09-23, 11:21,      0.6,        ,     -0.7,       ,          ,          ,      71, 71, 71,      89, 88, 88,         ,       1,      1, "Jumbo Aalbersestraat, 5, Aalbersestraat, Drunen, Heusden, Noord-Brabant, Nederland, 5151 EE, Nederland"
TRIP  , 2022-09-23, 11:21,      1.9,    13.3,         ,       ,          ,          ,      68, 52, 72,      91, 88, 91,        2,       1,      1, "Jumbo Aalbersestraat, 5, Aalbersestraat, Drunen, Heusden, Noord-Brabant, Nederland, 5151 EE, Nederland"
MOVE  , 2022-09-23, 12:00,      0.6,     0.7,         ,       ,          ,          ,      71, 72, 72,      87, 87, 87,        1,       1,      1, "26, Keniaring, Drunen, Heusden, Noord-Brabant, Nederland, 5152 MX, Nederland"
TRIP  , 2022-09-23, 12:00,      1.7,     0.7,         ,       ,          ,          ,      71, 72, 72,      87, 87, 87,        1,       1,      1, "26, Keniaring, Drunen, Heusden, Noord-Brabant, Nederland, 5152 MX, Nederland"
DAY   , 2022-09-23, Fri  ,      3.6,     6.3,     -0.7,       ,          ,          ,      73, 71, 80,      90, 87, 91,        1,       2,      2,
TRIP  , 2022-09-24, 09:57,      3.7,    19.6,     -0.7,       ,          ,          ,      88, 73,100,      88, 87, 95,        1,       1,       , "26, Keniaring, Drunen, Heusden, Noord-Brabant, Nederland, 5152 MX, Nederland"
MOVE  , 2022-09-24, 11:00,      0.9,        ,     -0.7,       ,          ,          ,      98, 98, 98,      93, 92, 92,         ,        ,      1, "140, Torenstraat, Drunen, Heusden, Noord-Brabant, Nederland, 5151 JN, Nederland"
MOVE  , 2022-09-24, 11:30,     23.8,        ,     -4.9,    4.9,      20.6,      1.21,      94, 91, 91,      94, 97, 97,         ,        ,      1, "Rijksweg A2, Enspijk, West Betuwe, Gelderland, Nederland, 4153 RN, Nederland"
MOVE  , 2022-09-24, 12:00,     41.6,        ,     -7.0,    5.9,      16.8,      1.72,      86, 81, 81,      97, 98, 98,         ,        ,      1, "Rijksweg A27, Eemnes, Utrecht, Nederland, 3755 AS, Nederland"
MOVE  , 2022-09-24, 12:30,     40.7,        ,     -8.4,    4.8,      20.6,      2.07,      75, 69, 69,      98, 98, 98,         ,        ,      1, "Rijksweg A6, Lelystad, Flevoland, Nederland, 8221 RD, Nederland"
MOVE  , 2022-09-24, 13:00,     39.1,        ,     -8.4,    4.7,      21.5,      2.07,      63, 57, 57,      98, 98, 98,         ,        ,      1, "A6, Oldeouwer, De Fryske Marren, Fryslân, Nederland, 8516 DD, Nederland"
MOVE  , 2022-09-24, 13:21,     16.4,        ,     -3.5,    4.7,      21.3,      0.86,      54, 52, 52,      97, 96, 96,         ,       1,      1, "17-101, Dekamalaan, Sneek, Súdwest-Fryslân, Fryslân, Nederland, 8604 ZG, Nederland"
TRIP  , 2022-09-24, 13:21,    198.4,        ,    -32.9,    6.0,      16.6,      8.09,      80, 52, 98,      96, 92, 98,         ,       1,      6, "17-101, Dekamalaan, Sneek, Súdwest-Fryslân, Fryslân, Nederland, 8604 ZG, Nederland"
MOVE  , 2022-09-24, 14:31,      2.2,        ,     -0.7,       ,          ,          ,      51, 51, 51,      95, 94, 94,         ,       1,      1, "Van der Valk Hotel Sneek, 1, Burgemeester Rasterhofflaan, Houkesloot, Sneek, Súdwest-Fryslân, Fryslân, Nederland, 8606 KZ, Nederland"
TRIP  , 2022-09-24, 14:31,      3.3,        ,     -0.7,       ,          ,          ,      51, 51, 51,      95, 94, 94,         ,       1,      1, "Van der Valk Hotel Sneek, 1, Burgemeester Rasterhofflaan, Houkesloot, Sneek, Súdwest-Fryslân, Fryslân, Nederland, 8606 KZ, Nederland"
MOVE  , 2022-09-24, 15:00,      1.6,        ,         ,       ,          ,          ,      51, 51, 51,      93, 93, 93,         ,        ,      1, "Stadsrondweg-Oost, Houkesloot, Sneek, Súdwest-Fryslân, Fryslân, Nederland, 8604 GC, Nederland"
MOVE  , 2022-09-24, 15:23,      0.7,        ,     -0.7,       ,          ,          ,      50, 50, 50,      94, 96, 96,         ,       1,      1, "17-101, Dekamalaan, Sneek, Súdwest-Fryslân, Fryslân, Nederland, 8604 ZG, Nederland"
TRIP  , 2022-09-24, 15:23,      4.8,        ,     -0.7,       ,          ,          ,      51, 50, 51,      94, 93, 96,         ,       1,      2, "17-101, Dekamalaan, Sneek, Súdwest-Fryslân, Fryslân, Nederland, 8604 ZG, Nederland"
MOVE  , 2022-09-24, 16:30,      0.2,        ,         ,       ,          ,          ,      50, 50, 50,      95, 94, 94,         ,        ,      1, "10, Groenedijk, Sneek, Súdwest-Fryslân, Fryslân, Nederland, 8604 AB, Nederland"
MOVE  , 2022-09-24, 17:00,     36.9,        ,     -7.0,    5.3,      19.0,      1.72,      45, 40, 40,      94, 94, 94,         ,        ,      1, "A6, De Zuidert, Emmeloord, Noordoostpolder, Flevoland, Nederland, 8305 AC, Nederland"
MOVE  , 2022-09-24, 17:30,     42.7,        ,     -7.0,    6.1,      16.4,      1.72,      35, 30, 30,      94, 95, 95,         ,        ,      1, "Rijksweg A6, Lelystad, Flevoland, Nederland, 3897 MA, Nederland"
MOVE  , 2022-09-24, 18:00,     38.1,        ,     -6.3,    6.0,      16.5,      1.55,      25, 21, 21,      94, 94, 94,         ,        ,      1, "A27, Rijnsweerd, Utrecht, Nederland, 3731 GC, Nederland"
MOVE  , 2022-09-24, 18:30,     39.7,        ,     -7.7,    5.2,      19.4,      1.89,      15, 10, 10,      95, 96, 96,         ,        ,      1, "A2, Hoenzadriel, Maasdriel, Gelderland, Nederland, 5334 NV, Nederland"
MOVE  , 2022-09-24, 19:00,     13.8,        ,     -3.5,    3.9,      25.4,      0.86,       7,  5,  5,      96, 97, 97,        1,       1,      1, "26, Keniaring, Drunen, Heusden, Noord-Brabant, Nederland, 5152 MX, Nederland"
TRIP  , 2022-09-24, 19:00,    197.6,        ,    -31.5,    6.3,      15.9,      7.75,      30,  5, 50,      95, 94, 97,        1,       1,      6, "26, Keniaring, Drunen, Heusden, Noord-Brabant, Nederland, 5152 MX, Nederland"
DAY   , 2022-09-24, Sat  ,    407.8,    15.4,    -66.5,    6.1,      16.3,     16.36,      75,  5,100,      91, 87, 98,        2,       5,     15,
DAY   , 2022-09-25, Sun  ,         ,    30.1,         ,       ,          ,          ,      29, 42, 50,      97, 97, 97,         ,        ,       ,
````

[Changes][R1.6.0]


<a name="R1.5.0"></a>
# [summary.py improvements , added TRIP, SOC%, 12V% (R1.5.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R1.5.0) - 17 Oct 2022

Many improvements to summary.py:
- added TRIP information
- added average, minimum, maximum State Of Charge%
- added average, minimum, maximum 12 Volt %
- added possibility of combination of arguments
- added information after 1 month of use
- added option to not show zero values for better readability
- configuration when consumption data should be shown (minimum discharge in kWh)
- configuration when small delta's are not seen as charging/discharging when not charging and not moved (e.g. 2% SOC)


[Changes][R1.5.0]


<a name="R1.4.0"></a>
# [summary.py: added charged/discharged kWh, using location to determine moved, small delta SOC improvement (R1.4.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R1.4.0) - 30 Sep 2022

Improvements to summary.py: 

- added charged/discharged kWh
- using location to determine moved
- small delta SOC improvement
- examples adapted 

Example output:
````
C:\Users\Rick\git\monitor>python summary.py
Period, date      , driven km, charged%, charged kWh, discharged%, discharged kWh, #charges, #drives, km/kWh, kWh/100km, cost Euro
DAY   , 2022-09-17,       0.0,      +4%,         2.8,          0%,            0.0,        1,       0,    0.0,       0.0,      0.00
DAY   , 2022-09-18,       0.0,      +2%,         1.4,          0%,            0.0,        0,       0,    0.0,       0.0,      0.00
WEEK  , 2022 W37  ,       0.0,      +6%,         4.2,          0%,            0.0,        1,       0,    0.0,       0.0,      0.00
DAY   , 2022-09-19,       6.5,      +0%,         0.0,         -1%,           -0.7,        0,       2,    0.0,       0.0,      0.00
DAY   , 2022-09-20,      47.6,      +0%,         0.0,        -14%,           -9.8,        0,       2,    4.9,      20.6,      2.41
DAY   , 2022-09-21,       5.2,     +26%,        18.2,         -1%,           -0.7,        2,       2,    0.0,       0.0,      0.00
DAY   , 2022-09-22,       1.9,      +2%,         1.4,         -1%,           -0.7,        1,       1,    0.0,       0.0,      0.00
DAY   , 2022-09-23,       1.7,     +29%,        20.3,          0%,            0.0,        2,       1,    0.0,       0.0,      0.00
DAY   , 2022-09-24,     407.8,     +37%,        25.9,        -95%,          -66.5,        1,       6,    6.1,      16.3,     16.36
DAY   , 2022-09-25,       0.0,      +8%,         5.6,          0%,            0.0,        0,       0,    0.0,       0.0,      0.00
WEEK  , 2022 W38  ,     470.7,    +102%,        71.4,       -112%,          -78.4,        6,      14,    6.0,      16.7,     19.29
MONTH , 2022-09   ,     470.7,    +108%,        75.6,       -112%,          -78.4,        7,      14,    6.0,      16.7,     19.29
YEAR  , 2022      ,     470.7,    +108%,        75.6,       -112%,          -78.4,        7,      14,    6.0,      16.7,     19.29
````

Screenshot of excel example with some graphs:
![alt text](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/summary.day.png)



[Changes][R1.4.0]


<a name="R1.3.0"></a>
# [summary.py improvements and (Excel) examples (R1.3.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R1.3.0) - 28 Sep 2022

[`22270f087d`](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/commit/22270f087d8290bc37726c08d2aa9dcc08b0d5de) (HEAD -> main, origin/main, origin/HEAD) 

- small improvement in charging/discharging counting in summary.py
- added possibility to filter on day/week/month/year
- added (Excel) examples to summary.py

output:
```
C:\Users\Rick\git\monitor>python summary.py
Label, date      , driven km, charged%, discharged%, charges, drives, km/kWh, kWh/100km, cost Euro
DAY  , 2022-09-17,       0.0,      +4%,           0,       1,      0,    0.0,       0.0,      0.00
DAY  , 2022-09-18,       0.0,      +2%,           0,       0,      0,    0.0,       0.0,      0.00
WEEK , 2022 W37  ,       0.0,      +6%,           0,       1,      0,    0.0,       0.0,      0.00
DAY  , 2022-09-19,       6.5,      +0%,           0,       0,      2,    0.0,       0.0,      0.00
DAY  , 2022-09-20,      47.6,      +0%,         -14,       0,      2,    4.9,      20.6,      2.41
DAY  , 2022-09-21,       5.2,     +25%,           0,       2,      2,    0.0,       0.0,      0.00
DAY  , 2022-09-22,       1.9,      +2%,           0,       1,      1,    0.0,       0.0,      0.00
DAY  , 2022-09-23,       1.7,     +28%,           0,       2,      1,    0.0,       0.0,      0.00
DAY  , 2022-09-24,     407.8,     +37%,         -95,       1,      6,    6.1,      16.3,     16.36
DAY  , 2022-09-25,       0.0,      +8%,           0,       0,      0,    0.0,       0.0,      0.00
WEEK , 2022 W38  ,     470.7,    +100%,        -110,       6,     14,    6.1,      16.4,     18.94
MONTH, 2022-09   ,     470.7,    +106%,        -110,       7,     14,    6.1,      16.4,     18.94
YEAR , 2022      ,     470.7,    +106%,        -110,       7,     14,    6.1,      16.4,     18.94
```

2022-09-24 I did a trip from 100% SOC to 5% SOC, have driven 407.8 km and started charging when back at home.

Example output when filtering on DAY:
```
C:\Users\Rick\git\monitor>python summary.py day
Label, date      , driven km, charged%, discharged%, charges, drives, km/kWh, kWh/100km, cost Euro
DAY  , 2022-09-17,       0.0,      +4%,           0,       1,      0,    0.0,       0.0,      0.00
DAY  , 2022-09-18,       0.0,      +2%,           0,       0,      0,    0.0,       0.0,      0.00
DAY  , 2022-09-19,       6.5,      +0%,           0,       0,      2,    0.0,       0.0,      0.00
DAY  , 2022-09-20,      47.6,      +0%,         -14,       0,      2,    4.9,      20.6,      2.41
DAY  , 2022-09-21,       5.2,     +25%,           0,       2,      2,    0.0,       0.0,      0.00
DAY  , 2022-09-22,       1.9,      +2%,           0,       1,      1,    0.0,       0.0,      0.00
DAY  , 2022-09-23,       1.7,     +28%,           0,       2,      1,    0.0,       0.0,      0.00
DAY  , 2022-09-24,     407.8,     +37%,         -95,       1,      6,    6.1,      16.3,     16.36
DAY  , 2022-09-25,       0.0,      +8%,           0,       0,      0,    0.0,       0.0,      0.00
```

![alt text](https://raw.githubusercontent.com/ZuinigeRijder/hyundai_kia_connect_monitor/main/examples/summary.day.jpg)

[Changes][R1.3.0]


<a name="R1.2.0"></a>
# [Added cost to summary.py and added Excel examples to shrink.py (R1.2.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R1.2.0) - 27 Sep 2022

Make sure to configure in summary.cfg the average cost per kWh and cost currency:

````
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
````

[Changes][R1.2.0]


<a name="R1.1.0"></a>
# [Added average consumption to summary.py (R1.1.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R1.1.0) - 26 Sep 2022

Added average consumption: km/kWh, kWh/100km or mi/kWh, kWh/100mi (configure km or mi in summary.cfg and net battery size)

Make sure to configure summary.cfg

Example output:
````
Label, date      , driven km, charged%, discharged%, charges, drives, km/kWh, kWh/100km
DAY  , 2022-09-17,       0.0,      +3%,           0,       1,      0,    0.0,       0.0
DAY  , 2022-09-18,       0.0,      +2%,           0,       0,      0,    0.0,       0.0
WEEK , 2022 W37  ,       0.0,      +5%,           0,       1,      0,    0.0,       0.0
DAY  , 2022-09-19,       6.5,      +0%,           0,       0,      2,    0.0,       0.0
DAY  , 2022-09-20,      47.6,      +0%,         -14,       0,      2,    4.9,      20.6
DAY  , 2022-09-21,       5.2,     +19%,           0,       2,      2,    0.0,       0.0
DAY  , 2022-09-22,       1.9,      +2%,           0,       1,      1,    0.0,       0.0
DAY  , 2022-09-23,       1.7,     +24%,           0,       2,      1,    0.0,       0.0
DAY  , 2022-09-24,     407.8,     +37%,         -95,       1,      6,    6.1,      16.3
DAY  , 2022-09-25,       0.0,      +6%,           0,       0,      0,    0.0,       0.0
WEEK , 2022 W38  ,     470.7,     +88%,         -98,       6,     14,    6.9,      14.6
MONTH, 2022-09   ,     470.7,     +93%,         -97,       7,     14,    6.9,      14.4
YEAR , 2022      ,     470.7,     +93%,         -97,       7,     14,    6.9,      14.4
````

[Changes][R1.1.0]


<a name="R1.0.0"></a>
# [First release (R1.0.0)](https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/releases/tag/R1.0.0) - 25 Sep 2022

First release with the following tools:
- monitor.py
- summary.py
- kml.py
- shrink.py
- debug.py

**Full Changelog**: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/commits/R1.0.0

[Changes][R1.0.0]


[R3.8.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R3.7.0...R3.8.0
[R3.7.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R3.6.0...R3.7.0
[R3.6.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R3.5.0...R3.6.0
[R3.5.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R3.4.0...R3.5.0
[R3.4.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R3.3.2...R3.4.0
[R3.3.2]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R3.3.1...R3.3.2
[R3.3.1]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R3.3.0...R3.3.1
[R3.3.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R3.2.1...R3.3.0
[R3.2.1]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R3.2.0...R3.2.1
[R3.2.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R3.1.0...R3.2.0
[R3.1.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R3.0.1...R3.1.0
[R3.0.1]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R3.0.0...R3.0.1
[R3.0.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R2.18.0...R3.0.0
[R2.18.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R2.17.0...R2.18.0
[R2.17.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R2.16.0...R2.17.0
[R2.16.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R2.15.0...R2.16.0
[R2.15.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R2.14.0...R2.15.0
[R2.14.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R2.13.0...R2.14.0
[R2.13.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R2.12.0...R2.13.0
[R2.12.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R2.11.0...R2.12.0
[R2.11.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R2.10.0...R2.11.0
[R2.10.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R2.9.0...R2.10.0
[R2.9.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R2.8.0...R2.9.0
[R2.8.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R2.7.1...R2.8.0
[R2.7.1]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R2.7.0...R2.7.1
[R2.7.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R2.6.0...R2.7.0
[R2.6.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R2.5.0...R2.6.0
[R2.5.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R2.4.0...R2.5.0
[R2.4.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R2.3.0...R2.4.0
[R2.3.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R2.2.0...R2.3.0
[R2.2.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R2.1.0...R2.2.0
[R2.1.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R2.0.0...R2.1.0
[R2.0.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R1.9.0...R2.0.0
[R1.9.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R1.8.0...R1.9.0
[R1.8.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R1.7.0...R1.8.0
[R1.7.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R1.6.0...R1.7.0
[R1.6.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R1.5.0...R1.6.0
[R1.5.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R1.4.0...R1.5.0
[R1.4.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R1.3.0...R1.4.0
[R1.3.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R1.2.0...R1.3.0
[R1.2.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R1.1.0...R1.2.0
[R1.1.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/compare/R1.0.0...R1.1.0
[R1.0.0]: https://github.com/ZuinigeRijder/hyundai_kia_connect_monitor/tree/R1.0.0

<!-- Generated by https://github.com/rhysd/changelog-from-release v3.7.0 -->
