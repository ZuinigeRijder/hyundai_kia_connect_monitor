Some rudimentary tests, to check that output is as expected with same input:
- Start the tests in the directory above directory **tests**.
- In **tests\INPUT** the reference INPUT files for the programs are stored.
- In **tests\OUTPUT** the expected OUTPUT files for the programs are stored.

**test\run_tests.bat** runs the tests for the tools:
- summary.py
- dailystats.py
- kml.py
- shrink.py

Whenever something visually is changed, the changes can be copied over via Beyond Compare for the test/OUTPUT files.
But when only refactoring has been done or side-effects of improvements are detected, you will see this also in the differences.
And then you should NOT copy this over, but should fix the problem.

**test\run_monitor**.bat runs the tests for the tool:
- monitor.py

There are expected differences running **test\run_monitor**, just look with Beyond Compare if these additions are logical:
- monitor.csv should be added with one entry of latest values
- monitor.dailystats.csv should have added dailystats
- monitor.tripinfo.csv should have added tripinfo

Prerequisites for tests:
- Windows 10 or above
- mypy: program that will "type check" your Python code (not mandatory though)
- Beyond Compare: commandline: C:\Program Files (x86)\Beyond Compare 3\BComp.com
- sed: tests\unxutils_sed.exe
- mosquitto: for testing the MQTT output
  - enable in monitor.cfg "send_to_mqtt = True" and "send_to_domoticz = True"
  - start in a separate windows command MQTTServer.bat

Test programs:
- tests\run_tests.bat
- tests\run_monitor.bat