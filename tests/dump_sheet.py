# == dump_sheet.py Author: Zuinige Rijder =====================================
"""
Simple Python3 script to dump spreadsheet to standard output
Usage: python dump_sheet.py spreadheetname
"""
import sys
import time
import gspread

COLUMN_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def dump_sheet(spreadsheet_name):
    """dump sheet"""
    retries = 1
    while retries > 0:
        try:
            gspread_client = gspread.service_account()
            spreadsheet = gspread_client.open(spreadsheet_name)
            sheet = spreadsheet.sheet1
            list_of_lists = sheet.get_all_values()
            row_count = 0
            for row in list_of_lists:
                row_count += 1
                print(f"{row_count}:", end=" ")
                column_count = 0
                for column in row:
                    column_letter = COLUMN_LETTERS[column_count]
                    column_count += 1
                    print(f"{column_letter}: [{column}]", end=", ")
                print()

            retries = 0
        except Exception as ex:  # pylint: disable=broad-except
            print("Exception: " + str(ex))
            retries -= 1
            print("Sleeping a minute")
            time.sleep(60)


if len(sys.argv) != 2:
    print("Usage: python dump_sheet spreadsheet_name")
else:
    dump_sheet(sys.argv[1])
