import time
import datetime


def tablePrint(list_of_lines_list):
    # first line is the title line

    print()

    column_lengths = [0] * len(list_of_lines_list[0])
    for i in range(0, len(list_of_lines_list[0])):
        max_temp = 0
        for o in range(0, len(list_of_lines_list)):
            l = len(str(list_of_lines_list[o][i]))
            if l > max_temp:
                max_temp = l
        column_lengths[i] = max_temp

    # print

    line_c = 0
    for line in list_of_lines_list:
        col_c = 0

        print("| ", end="")
        for column in line:
            text = str(list_of_lines_list[line_c][col_c])
            offset = column_lengths[col_c] - len(text)

            # display each character, catch encoding errors
            for char in text:
                try:
                    print(char, end="")
                except UnicodeEncodeError:
                    print("-", end="")
            for i in range(0, offset):
                print(" ", end="")

            print(" | ", end="")

            col_c += 1

        print()

        # print title bar
        if line_c == 0:
            s = sum(column_lengths)
            s += 3 * len(list_of_lines_list[0]) + 1
            for i in range(0, s):
                print("-", end="")

            print("")

        line_c += 1


def dateToTimestamp(date_string):
    return time.mktime(datetime.datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ").timetuple())


def secondsToHourFormat(seconds):
    # returns hours:minutes string
    hours = seconds / 3600
    minutes = (hours - int(hours)) * 60

    return str(int(hours)) + "h" + str(int(minutes)) + "m"
