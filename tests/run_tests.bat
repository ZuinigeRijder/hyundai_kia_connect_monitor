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

call :CLEAN_INPUT

call :RUN_MYPY

call :COPY_INPUT

call :CHECK_SUMMARY trip test.summary.logtrip
call :CHECK_DAILYSTATS "" test.dailystats.logtrip

call :CHECK_SUMMARY day test.summary.logday
rem summary.trips will not be filled
call :CHECK_DAILYSTATS "" test.dailystats.logday

call :CHECK_SUMMARY sheetupdate test.summary.log
call :CHECK_DAILYSTATS sheetupdate test.dailystats.log

call :CHECK_TRANSLATIONS

call :CHECK_KML

call :CHECK_SHRINK

call :CLEAN_INPUT

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
echo ################## running mypy ###############
mypy monitor.py | egrep -v "^Found|hyundai_kia_connect_api"
mypy summary.py | egrep -v "^Found|gspread|: note:"
mypy dailystats.py | egrep -v "^Found|gspread|: note:|: error: Argument 1 to .next."
mypy kml.py | egrep -v "^Success"
mypy shrink.py | egrep -v "^Success"
mypy debug.py | egrep -v "^Found|hyundai_kia_connect_api"

exit /B

rem #######################
:CHECK_SHRINK
echo ################## python shrink.py ###########
call python shrink.py
call :CHECK_FILE shrinked_monitor.csv shrinked_monitor.csv

EXIT /B

rem #######################
:CHECK_KML
echo ################## python kml.py ^> test.kml.log #############
call python kml.py > test.kml.log
call :CHECK_FILE test.kml.log test.kml.log

%SED% -e "s?^<name>monitor 20.*?<name>monitor 20....</name>?" monitor.kml > monitor.kml.tmp

call :CHECK_FILE monitor.kml.tmp monitor.kml

EXIT /B


rem #######################
:CHECK_TRANSLATIONS

rem backup original monitor.csg
copy /Y monitor.cfg monitor.cfg.backup >NUL

rem no translation yet for summary, so just run once
call :CHECK_SUMMARY "" test.summary.log

for %%x in (nl de fr it es sv no da fi pt pl cs sk hu en) do (
    echo # language: %%x
    %SED% -e "s?language = .*?language = %%x?" monitor.cfg > monitor.cfg.%%x.tmp
    copy /Y monitor.cfg.%%x.tmp monitor.cfg >NUL
 
    call :CHECK_DAILYSTATS "" test.dailystats.%%x.logtrip
)

rem restore original monitor.csg
copy /Y monitor.cfg.backup monitor.cfg >NUL

exit /B

rem #######################
:CHECK_DAILYSTATS
set args=%1
set output=%2
IF "%~1" == "" set args=

echo ################## python dailystats.py %args% ^> %output% #############
call python dailystats.py %args% > %output%

rem the first line of the file will be different so change the first line of both files
%SED% -e "1s?20..-..-.. ..:...*?20yy-mm-dd hh:mm WWW?" %output% > %output%.tmp

call :CHECK_FILE %output%.tmp %output%

if "%args%" == "sheetupdate" (
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
call python summary.py  %args% > %output%

call :CHECK_FILE %output% %output%
call :CHECK_FILE summary.charge.csv summary.charge.csv%args%
call :CHECK_FILE summary.trip.csv summary.trip.csv%args%

if "%args%" == "sheetupdate" (
    call python tests\dump_sheet.py hyundai-kia-connect-monitor > hyundai-kia-connect-monitor.dump
    %SED% -e "1s?^1: A: \[Last run\], B: \[20.*?1: A: [Last run], B: [20...?" hyundai-kia-connect-monitor.dump > hyundai-kia-connect-monitor.dump.tmp

    call :CHECK_FILE hyundai-kia-connect-monitor.dump.tmp hyundai-kia-connect-monitor.dump
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


