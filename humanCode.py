def joinChannelBool():
    didJoinChannel = True
    return didJoinChannel


def leftChannelBool():
    didLeaveChannel = True
    return didLeaveChannel


def checkIfChannelEmpty(channel):
    if channel == "Empty":
        return True
    else:
        return False


def putChannelInJson(mainID, channelID):
    print("Put channel in Json!")
