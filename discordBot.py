import discord
import json
import tokens
from discord.ext import commands


bot = discord.Client()
bot = commands.Bot(command_prefix='$')


def checkIfNumber(number):
    try:
        int(number)
        return True
    except:
        return False


def openJsonDoc(nameOfDoc):
    with open(f'{nameOfDoc}.json', 'r') as f:
        data = json.load(f)
    return data


channels = openJsonDoc('channels')


def writeJsonDoc(dumpData):
    with open(f'channels.json', 'w') as f:
        json.dump(dumpData, f, indent=4)


def getMainChannel(channelID, guildID):
    for channel in channels[str(guildID)]:
        if channel == str(channelID):
            return channel
    return False


def getNumberOfChildren(mainChannelID, guildID):
    return len(channels[str(guildID)][str(mainChannelID)])


def getLeaf(mainChannelID, guildID):
    numberOfChildren = getNumberOfChildren(mainChannel, guildID)
    if numberOfChildren == 0:
        return mainChannel
    else:
        return channels[guildID][mainChannelID][numberOfChildren - 1]


async def createChildVC(mainChannel):
    fullName = mainChannel.name.rsplit(" ", 1)
    NAME = fullName[0] + ' ' + \
        (str((getNumberOfChildren(mainChannel.id, mainChannel.guild.id)) + 2))
    print(NAME)
    clonedChannel = await mainChannel.clone(name=NAME)
    channels[str(mainChannel.guild.id)][str(
        mainChannel.id)].append(clonedChannel.id)
    writeJsonDoc(channels)


async def createChildFromLeaf(mainChannel):
    MAINCHANNEL = bot.get_channel(int(mainChannel))
    mainChannelJSONLocation = channels[str(
        MAINCHANNEL.guild.id)][str(MAINCHANNEL.id)]
    numberOfChildren = getNumberOfChildren(
        MAINCHANNEL.id, MAINCHANNEL.guild.id)
    if numberOfChildren == 0:
        return
    channelID = mainChannelJSONLocation[len(mainChannelJSONLocation) - 1]
    leafChannel = bot.get_channel(int(channelID))
    numberOfMembersInLeafChannel = len(leafChannel.members)
    if numberOfMembersInLeafChannel != 0:
        await createChildVC(MAINCHANNEL)


async def createChildrenForMainChannel(mainChannel, GUILD):
    if getNumberOfChildren(mainChannel, GUILD.id) != 0:
        return
    channel = bot.get_channel(int(mainChannel))
    membersInChannel = channel.members
    if len(membersInChannel) != 0:
        await createChildVC(channel)


async def deleteChannel(channel, mainChannel):
    await channel.delete()
    channels[str(channel.guild.id)][str(
        mainChannel.id)].remove(channel.id)
    writeJsonDoc(channels)


async def deleteChannels(mainChannel):
    MAINCHANNEL = bot.get_channel(int(mainChannel))
    JSONLocation = channels[str(
        MAINCHANNEL.guild.id)][str(MAINCHANNEL.id)]
    numberOfChildren = numberOfChildren = getNumberOfChildren(
        MAINCHANNEL.id, MAINCHANNEL.guild.id)
    leafChannelLocation = len(JSONLocation) - 1
    if numberOfChildren == 0:
        return
    leafChannel = bot.get_channel(int(JSONLocation[leafChannelLocation]))
    if numberOfChildren == 1:
        if len(MAINCHANNEL.members) == 0:
            await deleteChannel(leafChannel, MAINCHANNEL)
    else:
        secondLeafChannel = bot.get_channel(
            int(JSONLocation[len(JSONLocation)-2]))
        if len(secondLeafChannel.members) == 0 and len(leafChannel.members) == 0:
            await deleteChannel(leafChannel, MAINCHANNEL)
            await deleteChannels(mainChannel)


@ bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")


@ bot.event
async def on_guild_join(guild):
    channels[guild.id] = {}
    writeJsonDoc(channels)


@ bot.event
async def on_guild_remove(guild):
    channels.pop(guild.id)
    writeJsonDoc(channels)


@ bot.event
async def on_voice_state_update(member, before, after):
    GUILD = member.guild
    BEFORECHANNEL = before.channel
    AFTERCHANNEL = after.channel

    # Makes sure they arent just deafening and undeafening
    if BEFORECHANNEL == AFTERCHANNEL:
        return
    for mainChannel in channels[str(GUILD.id)]:
        await createChildrenForMainChannel(mainChannel, GUILD)
        await createChildFromLeaf(mainChannel)
        await deleteChannels(mainChannel)

    if after.channel != before.channel and after.channel != None and before.channel != None:
        print("Changed Voice Channel")
    elif after.channel != before.channel and after.channel != None:
        print("Joined Voice Channel")
    elif after.channel != before.channel and after.channel == None:
        print("Left Voice Channel")
    # print(after)


@ bot.event
async def on_message(ctx):
    print(ctx.content)
    await bot.process_commands(ctx)


@ bot.command()
async def ping(ctx):
    await ctx.send(f"pong")


@ bot.command()
async def setPosition(ctx, voiceChannelID, position):
    channel = bot.get_channel(int(voiceChannelID))
    await channel.edit(position=int(position))
    await ctx.send(f"Position of {channel.name} is now {channel.position}")


@ bot.command()
async def addVoiceChannelAsMain(ctx, voiceChannelID):
    # convert to integer from string
    if not checkIfNumber(voiceChannelID):
        ctx.send("The ID you specified is not a number")
        return
    try:
        channel = bot.get_channel(int(voiceChannelID))
        await channel.edit(position=100, name="Casual Party 1")
    except AttributeError:
        ctx.send("Please send an actual voice channel ID")
    print(channel.position)
    channels[str(ctx.guild.id)][str(voiceChannelID)] = []
    writeJsonDoc(channels)
    await ctx.send(f"Set voice channel: \"**{channel.name}**\" as a main voice channel")


bot.run(tokens.TOKEN)
