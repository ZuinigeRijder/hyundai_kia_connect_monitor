#!/bin/bash
# ---------------------------------------------------------------
# A script to run monitor infinite.
# if still running, do not start new one
# Assumption is that monitor.cfg is configured to run infinite (monitor_infinite = True) and 
#     monitor_execute_commands_when_something_written_or_error is configured to run summary.py and/or dailystats.py, e.g. 
#         monitor_execute_commands_when_something_written_or_error = python -u summary.py sheetupdate > summary.log;python -u dailystats.py sheetupdate > dailystats.log
# Add to your crontab to run once per hour to restart after crashes or reboot (crontab -e)
# 9 * * * * ~/hyundai_kia_connect_monitor/run_monitor_infinite.sh >> ~/hyundai_kia_connect_monitor/crontab_run_monitor_infinite.log 2>&1
# @reboot sleep 125 && ~/hyundai_kia_connect_monitor/run_monitor_infinite.sh >> ~/hyundai_kia_connect_monitor/crontab_run_monitor_infinite.log 2>&1
# ---------------------------------------------------------------
script_name=$(basename -- "$0")
cd ~/hyundai_kia_connect_monitor

now=$(date)
if pidof -x "$script_name" -o $$ >/dev/null
then
    echo "$now: $script_name still running"
else
    echo "$now: starting $script_name" >> run_monitor_infinite.log
    /usr/bin/python -u ~/hyundai_kia_connect_monitor/monitor.py >> run_monitor_infinite.log 2>&1
    now=$(date)
    echo "$now: $script_name exited" >> run_monitor_infinite.log
fi
