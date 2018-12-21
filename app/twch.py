import sys
import time
import subprocess
import os
import persistence
import api
import util
from difflib import SequenceMatcher

directory = sys.path[0]

quick_list_path = os.path.join(directory, "../data/quicklist.txt")
config_file_path = os.path.join(directory, "../config/config.cfg")
config_data = persistence.loadConfig(config_file_path)


class Command:

    def __init__(self, identifiers, func):
        self.identifiers = identifiers
        self.func = func

    def matches(self, c):
        for i in self.identifiers:
            if i == c:
                return True

        return False

    def runCommand(self, args):
        self.func(args)


def openStream(direct_link):
    if not "twitch.tv/" in direct_link:
        direct_link = "twitch.tv/" + direct_link

    watch_command = config_data["watch_command"]
    watch_command = watch_command.replace("$link", direct_link)

    com_list = watch_command.split(" ")
    print(com_list)

    # call() the specified command with arguments
    # redirect output to devnull
    f_null = open(os.devnull, 'w')
    subprocess.Popen(com_list, stdout=f_null, stderr=subprocess.STDOUT)


def watchStream(arg):
    arg = str(arg[0])

    # if arg is number, run QuickList item
    if arg.isdigit():
        runQuickListedItem(int(arg))
    else:
        # TODO check here if stream exists and is live (causes delay..)
        # TODO if not, run sloppy command with similar items
        openStream(arg)


def printFollowedStreamsThatAreLive(args):
    acc_id = api.getTwitchAccIdForAccName(config_data["client_id"], config_data["account_name"])
    stream_list = api.getFollowedStreamsThatAreLive(config_data["client_id"], acc_id=acc_id)

    # sort by viewer count
    stream_list.sort(key=lambda x: x.getViewerCount(), reverse=True)

    # print pretty table and save to quicklist
    printStreamTableAndSaveQuicklist(stream_list)


def printFollowedStreamsThatAreLiveForGame(args):
    game_name = str(args[0])
    # TODO: this should be configurable
    games = {}
    games["dota2"] = 29595
    games["fortnite"] = 33214
    game_id = games[game_name]

    acc_id = api.getTwitchAccIdForAccName(config_data["client_id"], config_data["account_name"])
    stream_list = api.getFollowedStreamsThatAreLive(config_data["client_id"], acc_id=acc_id)

    temp_list = stream_list[:]
    for s in temp_list:
        if not int(s.getGameID()) == game_id:
            stream_list.remove(s)


    # sort by viewer count
    stream_list.sort(key=lambda x: x.getViewerCount(), reverse=True)

    # print pretty table and save to quicklist
    printStreamTableAndSaveQuicklist(stream_list)


def runQuickListedItem(num):
    quick_list = persistence.loadQuickList(quick_list_path)
    if num not in quick_list:
        print("no item for number in nd file: " + str(num))
        return

    stream_obj = quick_list[num]

    print("running item: " + stream_obj.getDisplayName())

    # code for running the stream goes here
    openStream(stream_obj.getLoginName())


def printFittingStreams(args):
    query_string = str(args[0])
    results = getFittingStreamsForQuery(query_string)

    # save the accounts in ND file
    persistence.saveQuickList(results, quick_list_path)

    # print the accounts
    print(" I found these for \"" + query_string + "\"")

    counter = 0
    for element in results:
        print("  " + str(counter) + " " + element.getDisplayName())
        counter += 1


def getFittingStreamsForQuery(query):
    acc_id = api.getTwitchAccIdForAccName(config_data["client_id"], config_data["account_name"])
    stream_obj_list = api.getTwitchFollowedStreamsForAccID(config_data["client_id"], acc_id)

    # check each item if it contains the query
    # if true add to list
    results = []
    for item in stream_obj_list:
        if query.lower() in item.getDisplayName().lower():
            results.append(item)

    return results


def printTopDotA2LiveStreams(args):
    # args should contain an int (max=100)
    num_to_display = 25
    if len(args) >= 1:
        num_to_display = int(args[0])

    top_streams = api.getTopStreamsForGameID(config_data["client_id"], 29595, num_to_display)

    printStreamTableAndSaveQuicklist(top_streams)


def printStreamTableAndSaveQuicklist(streams):
    stream_table_list = []
    title_bar_list = ["QL", "Name", "Viewers", "Live", "D", "Title"]
    stream_table_list.append(title_bar_list)

    max_title_len = int(config_data["table_max_title_length"])

    quicklist = []
    c = 0
    for stream in streams:
        # calculate online time from start date (UTC + 0)
        timestamp = util.dateToTimestamp(stream.getStartTime())
        diff = time.time() - timestamp
        online_time = util.secondsToHourFormat(diff)

        # shorten title if necessary
        stream_title = stream.getTitle()
        if len(stream_title) > max_title_len:
            stream_title = stream_title[0:max_title_len]

        playing_d2_char = "o"
        if not stream.isStreamingD2():
            playing_d2_char = " "

        t_list = [str(c), stream.getAccName(), stream.getViewerCount(), online_time, playing_d2_char, stream_title]
        stream_table_list.append(t_list)

        quicklist.append(api.TwitchAccount(stream.getAccName(), stream.getAccName().lower(), stream.getAccID()))

        c += 1

    util.tablePrint(stream_table_list)

    # save quicklist
    persistence.saveQuickList(quicklist, quick_list_path)


def showQuickList(args):
    quick_list = persistence.loadQuickList(quick_list_path)
    print(" Current QuickList:")
    for index in quick_list:
        print("  " + str(index) + " " + quick_list[index].getDisplayName())


def setStreamQuality(args):
    watch_command = config_data["watch_command"]
    split_list = watch_command.split(" ")

    # only works with streamlink links
    if split_list[0] != "streamlink":
        print(" Not using streamlink... please change quality manually in .cfg")
        return

    # if no arg provided, print current quality
    if len(args) == 0:
        print(" Current quality: " + str(split_list[-1]))
        return

    # else, set quality to provided arg
    quality = str(args[0])

    split_list[len(split_list) - 1] = quality

    watch_command = ""
    for s in split_list:
        watch_command += s + " "

    watch_command = watch_command[:-1]

    config_data["watch_command"] = watch_command
    persistence.saveConfig(config_file_path, config_data)

    print(" Quality was set to: " + quality)



def printHelp(args):
    print(" Usage: twch [options] [args]")
    print("   Options:")
    print("    -s, --sloppy")
    print("    -l, --list")
    print("    -f, --following")
    print("    -fg, --followedgame")
    print("    -w, --watch")
    print("    -ql,--quicklist")
    print("    -q, --quality")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        printHelp("")
        sys.exit(0)

    cmd = sys.argv[1]
    args = sys.argv[2:len(sys.argv)]

    commands = []
    commands.append(Command(["-h", "--help"], printHelp))
    commands.append(Command(["-s", "--sloppy"], printFittingStreams))
    commands.append(Command(["-l", "--list"], printTopDotA2LiveStreams))
    commands.append(Command(["-f", "--following"], printFollowedStreamsThatAreLive))
    commands.append(Command(["-fg", "--followedgame"], printFollowedStreamsThatAreLiveForGame))
    commands.append(Command(["-w", "--watch"], watchStream))
    commands.append(Command(["-ql", "--quicklist"], showQuickList))
    commands.append(Command(["-q", "--quality"], setStreamQuality))

    found = False
    for c in commands:
        if c.matches(cmd):
            c.runCommand(args)
            found = True
            break

    if not found:
        printHelp("")
