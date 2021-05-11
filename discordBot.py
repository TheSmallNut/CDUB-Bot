#!/usr/bin/python3
import discord
import json
import tokens
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions


def openJsonDoc(nameOfDoc):
    with open(f'{nameOfDoc}.json', 'r') as f:
        data = json.load(f)
    return data

def get_prefix(client, message):
    prefixes = openJsonDoc("prefixes")
    return prefixes[str(message.guild.id)]

bot = discord.Client()
bot = commands.Bot(command_prefix=get_prefix)


def checkIfNumber(number):
    try:
        int(number)
        return True
    except:
        return False




channels = openJsonDoc('channels')


def writeJsonDoc(dumpData, location = "channels"):
    with open(f'{location}.json', 'w') as f:
        json.dump(dumpData, f, indent=4)


def getNumberOfChildren(mainChannelID, guildID):
    return len(channels[str(guildID)][str(mainChannelID)])


async def createChildVC(mainChannel):
    childs = getNumberOfChildren(mainChannel.id, mainChannel.guild.id) + 1
    fullName = mainChannel.name.rsplit(" ", 1)
    NAME = fullName[0] + ' ' + \
        (str((getNumberOfChildren(mainChannel.id, mainChannel.guild.id)) + 1 + int(fullName[1])))
    print(f"Created channel : {NAME}")
    clonedChannel = await mainChannel.clone(name=NAME)
    channels[str(mainChannel.guild.id)][str(
        mainChannel.id)].append(clonedChannel.id)
    await clonedChannel.edit(position=childs + mainChannel.position)
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
    numberOfMembersInLeafChannel = len(leafChannel.voice_states)
    if numberOfMembersInLeafChannel != 0:
        await createChildVC(MAINCHANNEL)


async def createChildrenForMainChannel(mainChannel, GUILD):
    if getNumberOfChildren(mainChannel, GUILD.id) != 0:
        return
    channel = bot.get_channel(int(mainChannel))
    membersInChannel = channel.voice_states
    #print(f"{channel.name} : {membersInChannel} : {len(membersInChannel)}")
    if len(membersInChannel) != 0:
        await createChildVC(channel)


async def deleteChannel(channel, mainChannel):
    print(f"Deleted channel : {channel.name}")
    await channel.delete()
    channels[str(channel.guild.id)][str(
        mainChannel.id)].remove(channel.id)
    writeJsonDoc(channels)


async def deleteChannelsNoException(mainChannel):
    JSONLocation = channels[str(mainChannel.guild.id)][str(mainChannel.id)]
    for channel in JSONLocation:
        deletableChannel = bot.get_channel(int(channel))
        await deletableChannel.delete()


async def addNumberToVCName(channel):
    nameSplit = channel.name.rsplit(" ", 1)
    if len(nameSplit) == 1:
        await channel.edit(name=channel.name + " 1")
        return
    if not checkIfNumber(nameSplit[1]):
        await channel.edit(name=channel.name + " 1")
        return


async def deleteChannels(mainChannelID):
    MAINCHANNEL = bot.get_channel(int(mainChannelID))
    JSONLocation = channels[str(
        MAINCHANNEL.guild.id)][str(MAINCHANNEL.id)]
    numberOfChildren = getNumberOfChildren(
        MAINCHANNEL.id, MAINCHANNEL.guild.id)
    leafChannelLocation = len(JSONLocation) - 1
    if numberOfChildren == 0:
        return
    leafChannel = bot.get_channel(int(JSONLocation[leafChannelLocation]))
    if leafChannel == None:
        return
    if numberOfChildren == 1:
        if len(MAINCHANNEL.voice_states) == 0:
            await deleteChannel(leafChannel, MAINCHANNEL)
    else:
        secondLeafChannel = bot.get_channel(
            int(JSONLocation[len(JSONLocation)-2]))
        if secondLeafChannel == None:
            return
        if len(secondLeafChannel.voice_states) == 0 and len(leafChannel.voice_states) == 0:
            await deleteChannel(leafChannel, MAINCHANNEL)
            await deleteChannels(MAINCHANNEL.id)

async def sendEmbedMessage(ctx, Title, Description, Color = 0x00ff00):
        embedVar = discord.Embed(title=Title, description = Description, color= Color)
        await ctx.send(embed=embedVar)

@ bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")


@ bot.event
async def on_guild_join(guild):
    prefixes = openJsonDoc("prefixes")
    prefixes[str(guild.id)] = "$"
    writeJsonDoc(prefixes, "prefixes")

    channels[str(guild.id)] = {}
    writeJsonDoc(channels)


@ bot.event
async def on_guild_remove(guild):
    channels.pop(str(guild.id))
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
        # print("Changed Voice Channel")
        print("")
    elif after.channel != before.channel and after.channel != None:
        # print("Joined Voice Channel")
        print("")
    elif after.channel != before.channel and after.channel == None:
        # print("Left Voice Channel")
        print("")
        # print(after)


@ bot.event
async def on_message(ctx):
    await bot.process_commands(ctx)


@ bot.command()
async def ping(ctx):
    await ctx.send('Pong! {0}'.format(round(bot.latency, 4)))

@ bot.command(name="changePrefix", aliases=["cp", "CP", "cP", "changeprefix", "CHANGEPREFIX"])
@ has_permissions(administrator=True)
async def _changePrefix(ctx, prefix):
    prefixes = openJsonDoc("prefixes")
    prefixes[str(ctx.guild.id)] = prefix
    writeJsonDoc(prefixes, "prefixes")
    await sendEmbedMessage(ctx, "Changed Prefix", f"Changed prefix to {prefix} ")

@ bot.command(name="clear", aliases=["c","CLEAR","C"])
@ has_permissions(manage_messages=True)
async def _clear(ctx, amount = 10):
    try:
        await ctx.channel.purge(limit = int(amount) + 1)
    except:
        await sendEmbedMessage(ctx,"ERROR", f"Messages are already being deleted, please try again after they stop being deleted", 0xff0000)


@ bot.command(name="currentVoiceChannels", aliases=["CVC", "cvc", "current", "Current", "CURRENTVOICECHANNELS", "currentvoicechannels"])
@ has_permissions(manage_channels=True)
async def _currentVoiceChannels(ctx):
    bigString = ""
    for channelID in channels[str(ctx.guild.id)]:
        channel = bot.get_channel(int(channelID))
        children = getNumberOfChildren(channelID, ctx.guild.id)
        bigString += f"\n **{channel.name}** | {children} children"
    await sendEmbedMessage(ctx, "All voice channels", bigString)


@ bot.command(name="addVoiceChannel", aliases=["AVC", "avc", "addvoicechannel", "ADDVOICECHANNEL"])
@ has_permissions(manage_channels=True)
async def addVoiceChannelAsMain(ctx, *, voiceChannel):
    if voiceChannel.isdecimal():
        try:
            channel = bot.get_channel(int(voiceChannel))
            await addNumberToVCName(channel)
            await sendEmbedMessage(ctx, "Set Voice Channel", f"Set voice channel: **{channel.name}** as a main voice channel")
            ##await ctx.send(f"Set voice channel: \"**{channel.name}**\" as a main voice channel")
            channels[str(ctx.guild.id)][str(voiceChannel)] = []
            writeJsonDoc(channels)
            return
        except AttributeError:
            pass
    allChannels = ctx.guild.channels
    channel = discord.utils.find(
        lambda c: c.name.lower() == voiceChannel.lower() and c.type.name == 'voice', allChannels)
    if channel == None:
        await sendEmbedMessage(ctx, "ERROR", f"**{channel.name}** is not an actual channel name", 0xff0000)
        ##await ctx.send("Please send an actual voice channel")
        return
    if str(channel.id) in channels[str(ctx.guild.id)]:
        await sendEmbedMessage(ctx, "ERROR", f"**{channel.name}** is already a main voice channel", 0xff0000)
        ##await ctx.send(f"**{channel.name}** is already a main voice channel")
        return
    await addNumberToVCName(channel)
    await sendEmbedMessage(ctx, "Set Voice Channel", f"Set voice channel: **{channel.name}** as a main voice channel")
    ##await ctx.send(f"Set voice channel: \"**{channel.name}**\" as a main voice channel")
    channels[str(ctx.guild.id)][str(channel.id)] = []
    writeJsonDoc(channels)

    # convert to integer from string


@ bot.command(name="removeVoiceChannel", aliases=["RVC", "rvc", "removevoicechannel", "REMOVEVOICECHANNEL"])
@ has_permissions(manage_channels=True)
async def removeVoiceChannelAsMain(ctx, *, voiceChannel):
    if checkIfNumber(voiceChannel):
        try:
            channel = bot.get_channel(int(voiceChannel))
            ##await ctx.send(f"Removed voice channel: **{channel.name}** as a main channel")
            await sendEmbedMessage(ctx, "Removed Voice Channel", f"Removed voice channel: **{channel.name}** as a main channel")
            channels[str(channel.guild.id)].pop(str(channel.id))
            writeJsonDoc(channels)
            return
        except AttributeError:
            pass
        except KeyError:
            pass
    allChannels = ctx.guild.channels
    channel = discord.utils.find(
        lambda c: c.name.lower() == voiceChannel.lower() and c.type.name == 'voice', allChannels)
    if channel == None:
        await sendEmbedMessage(ctx, "ERROR", f"**{channel.name}** is not an actual channel name", 0xff0000)
        ##await ctx.send("Please send an actual voice channel")
        return
    try:
        await deleteChannelsNoException(channel)
        channels[str(channel.guild.id)].pop(str(channel.id))
        await sendEmbedMessage(ctx, "Removed Voice Channel", f"Removed voice channel: **{channel.name}** as a main channel")
        ##await ctx.send(f"Removed voice channel: **{channel.name}** as a main channel")
        writeJsonDoc(channels)
    except KeyError:
        await sendEmbedMessage(ctx, "ERROR", f"**{channel.name}** is not a main voice channel", 0xff0000)
        ##await ctx.send(f"**{channel.name}** is not a Main Channel")

bot.run(tokens.CDUBTOKEN)
