import urllib.request as req
import urllib.parse as parse
import json


class TwitchAccount:

    def __init__(self, display_name, login_name, acc_id):
        self.display_name = display_name
        self.login_name = login_name
        self.acc_id = acc_id

    def getDisplayName(self):
        return self.display_name

    def getLoginName(self):
        return self.login_name

    def getAccID(self):
        return self.acc_id


class Stream:

    def __init__(self, data):
        self.data = data

    def getAccID(self):
        return self.data["user_id"]

    def getAccName(self):
        return self.data["acc_name"]

    def getViewerCount(self):
        return self.data["viewer_count"]

    def getGameID(self):
        return self.data["game_id"]

    def getTitle(self):
        return self.data["title"].strip()

    def getStartTime(self):
        return self.data["started_at"]

    def isStreamingD2(self):
        return int(self.getGameID()) == 29595

    def isStreamingFN(self):
        return int(self.getGameID()) == 33214


def makeApiRequest(api_url, headers, variables=None, mult_var=None):
    full_url = api_url
    if variables is not None:
        full_url = api_url + parse.urlencode(variables)
    if mult_var is not None:
        if variables is not None:
            full_url += "&"
        for key in mult_var:
            for item in mult_var[key]:
                full_url += key + "=" + str(item) + "&"
        # cut trailing ampersand
        full_url = full_url[:-1]

    request = req.Request(full_url)
    for tup in headers:
        request.add_header(tup[0], tup[1])

    data = req.urlopen(request).read().decode('UTF-8')
    json_obj = json.loads(data)
    return json_obj


def getStreamInfoForAccIDs(client_id, acc_id_list):
    headers = []
    client_header = ("Client-ID", client_id)
    headers.append(client_header)

    req_url = "https://api.twitch.tv/helix/streams?"
    pagination_cursor = ""

    data_list = []

    while True:
        mult_var_dict = {}
        variables = {}
        mult_var_dict["user_id"] = acc_id_list
        if pagination_cursor != "":
            variables["after"] = pagination_cursor

        data = makeApiRequest(req_url, headers, mult_var=mult_var_dict, variables=variables)
        if len(data["data"]) == 0:
            break
        for element in data["data"]:
            data_list.append(element)
        pagination_cursor = data["pagination"]["cursor"]

    return data_list


def getFollowedStreamsThatAreLive(client_id, acc_name=None, acc_id=None):
    if acc_id is None:
        acc_id = getTwitchAccIdForAccName(client_id, acc_name=acc_name)
    followed_ids = getTwitchFollowedAccIDsForAccID(client_id, acc_id)

    stream_acc_objs = getTwitchStreamAccountsForAccIDs(client_id, followed_ids)
    stream_acc_dict = {}
    for obj in stream_acc_objs:
        stream_acc_dict[obj.getAccID()] = obj

    # can only do max of 100 ids per request
    stream_objs = []

    index = 0
    while True:

        temp_ids = followed_ids[index:index + 100]

        if len(temp_ids) == 0:
            break

        stream_list = getStreamInfoForAccIDs(client_id, temp_ids)

        stream_objs.extend(stream_list)

        index += 100

    stream_details_list = []
    for stream in stream_objs:
        acc_id = stream["user_id"]
        acc_name = stream_acc_dict[acc_id].getDisplayName()
        # insert acc_name details
        stream["acc_name"] = acc_name

        stream_details_list.append(Stream(stream))

    return stream_details_list


def getTwitchStreamAccountsForAccIDs(client_id, list_of_acc_ids):
    # max request size is 100 ids

    acc_obj_list = []

    index = 0
    # loop until we have all the acc names
    while len(acc_obj_list) < len(list_of_acc_ids):

        # get the next 50 items
        temp_ids = list_of_acc_ids[index:index + 100]
        if len(temp_ids) == 0:
            # happens if some acc data was not sent
            break

        user_profile_data = getTwitchUserInfo(client_id, acc_id_list=temp_ids)

        for element in user_profile_data:
            acc_obj = TwitchAccount(element["display_name"], element["login"], element["id"])
            acc_obj_list.append(acc_obj)

        index += 100

    return acc_obj_list


def getTwitchFollowedAccIDsForAccID(client_id, acc_id):
    headers = []
    client_header = ("Client-ID", client_id)
    headers.append(client_header)

    req_url = "https://api.twitch.tv/helix/users/follows?"

    followers_data = []

    pagination_cursor = ""

    while True:
        vars = {}
        vars["first"] = "100"
        vars["from_id"] = str(acc_id)
        if pagination_cursor != "":
            vars["after"] = pagination_cursor

        data = makeApiRequest(req_url, headers, variables=vars)
        f_data = data["data"]
        followers_data.extend(f_data)

        total_num = int(data["total"])

        if len(followers_data) < total_num:
            pagination_cursor = data["pagination"]["cursor"]
        else:
            break

    # make list with acc ids of the followed accounts
    acc_id_list = []
    for element in followers_data:
        acc_id_list.append(element["to_id"])

    return acc_id_list


def getTwitchFollowedStreamsForAccID(client_id, acc_id):
    acc_id_list = getTwitchFollowedAccIDsForAccID(client_id, acc_id)

    # get stream account objs for the followed account ids
    acc_objs = getTwitchStreamAccountsForAccIDs(client_id, acc_id_list)

    return acc_objs


def getTwitchUserInfo(client_id, acc_name=None, acc_id=None, acc_id_list=None):
    headers = []
    client_header = ("Client-ID", client_id)
    headers.append(client_header)

    req_url = "https://api.twitch.tv/helix/users?"

    vars = {}
    if acc_name is not None:
        vars["login"] = acc_name
    elif acc_id is not None:
        vars["id"] = acc_id

    # noinspection PyDictCreation
    if acc_id_list is not None:
        mult_var_dict = {}
        mult_var_dict["id"] = acc_id_list

        # make request (without setting the variables)
        data = makeApiRequest(req_url, headers, mult_var=mult_var_dict)

        # return list of items
        return data["data"]

    data = makeApiRequest(req_url, headers, variables=vars)
    return data["data"][0]


def getTwitchAccIdForAccName(client_id, acc_name):
    return getTwitchUserInfo(client_id, acc_name=acc_name)["id"]


# noinspection PyDictCreation
def getTopStreamsForGameID(client_id, game_id, num_to_display=10):
    headers = []
    client_header = ("Client-ID", client_id)
    headers.append(client_header)

    req_url = "https://api.twitch.tv/helix/streams?"

    variables = {}
    variables["game_id"] = game_id
    variables["first"] = num_to_display

    data = makeApiRequest(req_url, headers, variables=variables)

    streams = {}
    acc_ids = []
    for element in data["data"]:
        acc_id = int(element["user_id"])
        streams[acc_id] = element

        # we have to fetch the acc_ids after this
        acc_ids.append(acc_id)

    # we will not have more than 100 acc ids, so can do 1 call
    acc_infos = getTwitchUserInfo(client_id, acc_id_list=acc_ids)

    # Stream object list to be returned
    stream_objs = []
    for acc in acc_infos:
        # insert the acc display name into the stream objects
        acc_id = int(acc["id"])
        streams[acc_id]["acc_name"] = acc["display_name"]

        # parse it to a Stream object
        stream_objs.append(Stream(streams[acc_id]))

    return stream_objs


if __name__ == "__main__":
    streams = getTopStreamsForGameID("irdzgaxp09zxrqxcrg2cb0ygo45rqy", 29595, 10)

    for s in streams:
        print(s.getAccName())
