@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

IF not EXIST tests\run_tests.bat (
    echo Run this script one directory higher: tests\run_tests.bat
    goto :error
)

set BC="C:\Program Files (x86)\Beyond Compare 3\BComp.com"
if not EXIST %BC% (
   echo Beyond Compare does not exist: %BC%
   goto :error
)

set SED="tests\unxutils_sed.exe"

echo ###### Current directory: %CD%

set FULL=%1

rem backup original monitor.cfg
copy /Y monitor.cfg monitor.cfg.backup >NUL

rem backup original summary.cfg
copy /Y summary.cfg summary.cfg.backup >NUL

%SED% -e "s?language = .*?language = en?" monitor.cfg | %SED% -e "s?send_to_mqtt = False?send_to_mqtt = True?" | %SED% -e "s?send_to_domoticz = False?send_to_domoticz = True?" > monitor.cfg.en.tmp
copy /Y monitor.cfg.en.tmp monitor.cfg >NUL

start tests\MQTTServer.bat

call :CLEAN_INPUT

call :RUN_MYPY

call :COPY_INPUT

call :CHECK_SUMMARY trip test.summary.logtrip
rem summary.day.csv will not be filled
call :CHECK_DAILYSTATS "" test.dailystats.logtrip

call :CHECK_SUMMARY day test.summary.logday
rem summary.trip.csv will not be filled
call :CHECK_DAILYSTATS "" test.dailystats.logday

call :CHECK_SUMMARY sheetupdate test.summary.log
call :CHECK_DAILYSTATS sheetupdate test.dailystats.log

call :CHECK_TRANSLATIONS

call :CHECK_SUMMARY_MQTT_DOMOTICZ

call :CHECK_DAILYSTATS_MQTT_DOMOTICZ

rem restore original monitor.cfg
copy /Y monitor.cfg.backup monitor.cfg >NUL

rem restore original summary.cfg
copy /Y summary.cfg.backup summary.cfg >NUL

call :CHECK_KML

call :CHECK_SHRINK

call :CLEAN_INPUT

rem restore original monitor.cfg
copy /Y monitor.cfg.backup monitor.cfg >NUL

rem restore original summary.cfg
copy /Y summary.cfg.backup summary.cfg >NUL

taskkill /F /FI "IMAGENAME eq mosquitto.exe" /T

goto :EOF

:CLEAN_INPUT
echo ################## cleaning INPUT #############
del /Q *.tmp
del /Q *.dump
del /Q test.*
IF EXIST summary.charge.csv del /Q summary.charge.csv
IF EXIST summary.trip.csv del /Q summary.trip.csv
IF EXIST monitor.kml del /Q monitor.kml

exit /B

:COPY_INPUT
echo ################## copying INPUT ##############
copy /Y tests\INPUT\* .

exit /B

:RUN_MYPY
call tests\run_mypy.bat

exit /B

rem #######################
:CHECK_SHRINK
if "%FULL%" == "" exit /B
echo ################## python shrink.py ###########
call python shrink.py
call :CHECK_FILE shrinked_monitor.csv shrinked_monitor.csv

EXIT /B

rem #######################
:CHECK_KML
if "%FULL%" == "" exit /B
echo ################## python kml.py ^> test.kml.log #############
call python kml.py > test.kml.log
call :CHECK_FILE test.kml.log test.kml.log

%SED% -e "s?^<name>monitor 20.*?<name>monitor 20....</name>?" monitor.kml > monitor.kml.tmp

call :CHECK_FILE monitor.kml.tmp monitor.kml

EXIT /B


rem #######################
:CHECK_TRANSLATIONS
if "%FULL%" == "" exit /B

for %%x in (nl de fr it es sv no da fi pt pl cs sk hu en) do (
    echo # language: %%x
    %SED% -e "s?language = .*?language = %%x?" monitor.cfg > monitor.cfg.%%x.tmp
    copy /Y monitor.cfg.%%x.tmp monitor.cfg >NUL
 
    call :CHECK_SUMMARY "" test.summary.%%x.log
 
    call :CHECK_DAILYSTATS "" test.dailystats.%%x.logtrip
)

exit /B

rem #######################
:CHECK_DAILYSTATS
set args=%1
set output=%2
IF "%~1" == "" set args=

echo ################## python dailystats.py %args% ^> %output% #############
call python dailystats.py %args% > %output%

rem the first line of the file will be different so change the first line of both files
%SED% -e "1s?20..-..-.. *..:...*?20yy-mm-dd hh:mm WWW?" %output% > %output%.tmp

call :CHECK_FILE %output%.tmp %output%

if "%args%" == "sheetupdate" (
    if "%FULL%" == "" exit /B
    call python tests\dump_sheet.py monitor.dailystats > monitor.dailystats.dump
    %SED% -e "1s?^1: A: \[Last run\], B: \[20.*?1: A: [Last run], B: [20...?" monitor.dailystats.dump > monitor.dailystats.dump.tmp

    call :CHECK_FILE monitor.dailystats.dump.tmp monitor.dailystats.dump
)

EXIT /B

rem #######################
:CHECK_SUMMARY
set args=%1
set output=%2
IF "%~1" == "" set args=
    
echo ################## python summary.py %args% ^> %output% #############
IF EXIST summary.charge.csv del /Q summary.charge.csv
IF EXIST summary.trip.csv del /Q summary.trip.csv
IF EXIST summary.day.csv del /Q summary.day.csv
call python summary.py  %args% > %output%

call :CHECK_FILE %output% %output%
call :CHECK_FILE summary.charge.csv summary.charge.csv%args%
call :CHECK_FILE summary.trip.csv summary.trip.csv%args%
call :CHECK_FILE summary.day.csv summary.day.csv%args%

if "%args%" == "sheetupdate" (
    if "%FULL%" == "" exit /B
    call python tests\dump_sheet.py hyundai-kia-connect-monitor > hyundai-kia-connect-monitor.dump
    %SED% -e "1s?^1: A: \[Last run\], B: \[20.*?1: A: [Last run], B: [20...?" hyundai-kia-connect-monitor.dump > hyundai-kia-connect-monitor.dump.tmp

    call :CHECK_FILE hyundai-kia-connect-monitor.dump.tmp hyundai-kia-connect-monitor.dump
)
EXIT /B

rem #######################
:CHECK_SUMMARY_MQTT_DOMOTICZ
set args=debug trip day week month year
for %%x in (nl de fr it es sv no da fi pt pl cs sk hu en) do (
    echo # language: %%x
    %SED% -e "s?language = .*?language = %%x?" monitor.cfg > monitor.cfg.%%x.tmp
    copy /Y monitor.cfg.%%x.tmp monitor.cfg >NUL
    
    set output=test.summary.mqtt_domoticz.%%x.log
        
    echo ################## python summary.py %args% %%x ^> !output! #############
    call python summary.py  %args% | findstr "send_to_domoticz send_to_mqtt" | %SED% -e "s?^.*send_to_mqtt: ??" | %SED% -e "s?^.*send_to_domoticz: ??" > !output!
    
    call :CHECK_FILE !output! !output!
)

EXIT /B

rem #######################
:CHECK_DAILYSTATS_MQTT_DOMOTICZ
set args=debug

for %%x in (nl de fr it es sv no da fi pt pl cs sk hu en) do (
    echo # language: %%x
    %SED% -e "s?language = .*?language = %%x?" monitor.cfg > monitor.cfg.%%x.tmp
    copy /Y monitor.cfg.%%x.tmp monitor.cfg >NUL
    
    set output=test.dailystats.mqtt_domoticz.%%x.log
    
    echo ################## python dailystats.py %args% %%x ^> !output! #############
    call python dailystats.py  %args% | findstr "send_to_domoticz send_to_mqtt" | %SED% -e "s?^.*send_to_mqtt: ??" | %SED% -e "s?^.*send_to_domoticz: ??" | %SED% -e "s?^dailystats_day_TOTALS_date =.*?dailystats_day_TOTALS_date =?" | %SED% -e "s?^hyundai_kia_connect_monitor/KMHKR81CPNU012345/dailystats_day/TOTALS/date =.*?hyundai_kia_connect_monitor/KMHKR81CPNU012345/dailystats_day/TOTALS/date =?" | %SED% -e "s?idx = 1, dailystats_day_TOTALS_date = 202.-..-..?idx = 1, dailystats_day_TOTALS_date = 2024-11-27?" | %SED% -e "s@svalue=202[4-9]-[0-1][0-9]-[0-3][0-9]@svalue=2024-11-27@" > !output!

    call :CHECK_FILE !output! !output!
)

EXIT /B


rem #######################
:CHECK_FILE
set left=%1
set right=%2
echo ###### checking %left% vs %right% #####
%BC% /qc %left% tests\OUTPUT\%right%

IF %ERRORLEVEL% GEQ 3 (
    echo ### ERROR: %CHECK_FILE% ERRORLEVEL: %ERRORLEVEL%
    %BC% %left% tests\OUTPUT\%right%
) ELSE (
    echo ###### OK: %left%
)
EXIT /B

:error
echo ERROR during running run_tests.bat

:EOF
endlocal


