@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

IF not EXIST tests\run_monitor.bat (
    echo Run this script one directory higher: tests\run_monitor.bat
    goto :error
)

set BC="C:\Program Files (x86)\Beyond Compare 3\BComp.com"
if not EXIST %BC% (
   echo Beyond Compare does not exist: %BC%
   goto :error
)

set SED="tests\unxutils_sed.exe"

echo ###### Current directory: %CD%

echo ################## cleaning INPUT #############
del /Q *.tmp
del /Q *.dump
del /Q test.*
IF EXIST summary.charge.csv del /Q summary.charge.csv
IF EXIST summary.trip.csv del /Q summary.trip.csv
IF EXIST monitor.kml del /Q monitor.kml

echo ################## copying  INPUT #############
copy /Y tests\INPUT\* .

echo ################## python monitor.py #############
call python monitor.py > test.monitor.log 2>&1
type test.monitor.log

echo ################## check manually differences with Beyond Compare ####
call :CHECK_FILE monitor.csv monitor.csv
call :CHECK_FILE monitor.dailystats.csv monitor.dailystats.csv
call :CHECK_FILE monitor.tripinfo.csv monitor.tripinfo.csv

goto :EOF

rem #######################
:CHECK_FILE
set left=%1
set right=%2
echo ###### checking %left% vs %right% #####
%BC% /qc %left% tests\INPUT\%right%

IF %ERRORLEVEL% GEQ 3 (
    echo ### ERROR: %CHECK_FILE% ERRORLEVEL: %ERRORLEVEL%
    %BC% %left% tests\INPUT\%right%
) ELSE (
    echo ###### OK: %left%
)
EXIT /B

:error
echo ERROR during running run_tests.bat

:EOF
endlocal


