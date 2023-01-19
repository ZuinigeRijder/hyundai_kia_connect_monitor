#!/bin/bash
# ---------------------------------------------------------------
# A script to run monitor once.
# if still running, kill the previous running script and start new one
# Add to your crontab to run once per hour
# 0 * * * * ~/hyundai_kia_connect_monitor/run_monitor_once.sh >> ~/hyundai_kia_connect_monitor/run_monitor_once.log 2>&1
# run every 15 minutes to get cached update between 6 and 22 hour
# */15 6-21 * * * ~/hyundai_kia_connect_monitor/run_monitor_once.sh >> ~/hyundai_kia_connect_monitor/run_monitor_once.log 2>&1
# ---------------------------------------------------------------
script_name=$(basename -- "$0")
cd ~/hyundai_kia_connect_monitor

now=$(date)
if pidof -x "$script_name" -o $$ >/dev/null;then
   echo "$now: $script_name already running" >> run_monitor_once.log 2>&1
   kill $(pidof $script_name) >> run_monitor_once.log 2>&1
fi

/usr/bin/python -u ~/hyundai_kia_connect_monitor/monitor.py >> run_monitor_once.log 2>&1
/usr/bin/python -u ~/hyundai_kia_connect_monitor/summary.py sheetupdate > run_monitor_once.summary.log 2>&1
/usr/bin/python -u ~/hyundai_kia_connect_monitor/dailystats.py sheetupdate > run_monitor_once.dailystats.log 2>&1

