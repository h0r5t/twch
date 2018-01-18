import sys

sys.path.append(sys.path[0] + "/..")
import app.api as api


def loadConfig(path_to_file):
    f = open(path_to_file, "r")
    d = {}

    for line in f:
        if line.startswith("#") or line == "" or line == "\n":
            continue
        s = line.split("=")
        d[s[0]] = s[1].strip()

    f.close()
    return d


def saveConfig(path_to_file, config_data):
    f = open(path_to_file, "w")

    for key in config_data:
        f.write(str(key) + "=" + str(config_data[key]) + "\n")

    f.close()


def loadQuickList(path_to_file):
    d = {}
    f = open(path_to_file, "r")

    counter = 0
    for line in f:
        s = line.split(" ")
        d[counter] = api.TwitchAccount(s[0].strip(), s[1].strip(), 0)
        counter += 1

    f.close()
    return d


def saveQuickList(l_list, path_to_file):
    out_string = ""

    counter = 0
    for obj in l_list:
        out_string += obj.getDisplayName() + " " + obj.getLoginName() + "\n"
        counter += 1

    f = open(path_to_file, "w")
    f.write(out_string)
    f.close()
