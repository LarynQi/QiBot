import discord
from discord.ext import commands, tasks
import os
import json
import datetime
import pytz
import time
import random
import youtube_dl

client = commands.Bot(command_prefix="/")

def special_check(ctx):
    return ctx.author.id == int(os.environ.get('MY_ID'))

@client.event
async def on_ready():
    global start_monitor
    read_games()
    add_games.start()
    change_game.start()
    curr_time, secs = datetime.datetime.now(), time.time()
    pacific = pytz.timezone('US/Pacific')
    loc_dt = pacific.localize(curr_time)
    start_monitor = loc_dt.strftime(fmt)
    scheduled_send.start()
    print('QiBot on standby.')

games = []
my_games = []
monitoring = True
start_monitor = ''
fmt = '%Y-%m-%d %H:%M:%S %Z%z'
players = {}


@client.command(aliases=['exit', 'quit'])
@commands.check(special_check)
async def _quit(ctx, save='save'):
    if monitoring and save != 'ds':
        curr_time, secs = datetime.datetime.now(), time.time()
        pacific = pytz.timezone('US/Pacific')
        loc_dt = pacific.localize(curr_time)
        end = loc_dt.strftime(fmt)
        with open('monitor.json', 'r') as f:
            data = json.load(f)
        if not data:
            data[1] = {'from': start_monitor, 'end': end}
        else:
            int_keys = [int(k) for k in data]
            data[max(int_keys) + 1] = {'from': start_monitor, 'end': end}
        with open('monitor.json', 'w') as f:
            json.dump(data, f, indent=4)
    await client.change_presence(status=discord.Status.offline)
    await client.logout()


def read_games():
    with open('games.json', 'r') as f:
        games_list = json.load(f)
    for game in games_list:
        if games_list[game] not in games:
            games.append(games_list[game])
    with open('my_games.json', 'r') as f:
        games_list = json.load(f)
    for game in games_list:
        if games_list[game] not in my_games:
            my_games.append(games_list[game])

@tasks.loop(minutes=15)
async def add_games():
    for user in client.get_all_members():
        if user.status != discord.Status.offline and user.activity and user.activity.type == discord.ActivityType.playing and not user.bot:
            name = user.activity.name
            if name not in games:
                games.append(user.activity.name)
    with open('games.json', 'r') as f:
        data = json.load(f)
    count = 1
    size = len(data)
    for i in range(size, len(games)):
        data[size + count] = games[i]
        count += 1
    with open('games.json', 'w') as f:
        json.dump(data, f, indent=4)


@tasks.loop(minutes=30)
async def change_game():
    choices = list(dict.fromkeys(games + my_games))
    if client.activity:
        sel = client.activity.name
        while sel == client.activity.name:
            sel = random.choice(choices)
        await client.change_presence(activity=discord.Game(sel))
    else:
        await client.change_presence(activity=discord.Game(random.choice(choices)))

# TODO:
# https://www.youtube.com/watch?v=MbhXIddT2YY
# https://gist.github.com/EvieePy/ab667b74e9758433b3eb806c53a19f34
# @client.command(aliases=[])
# @commands.check(special_check)
# async def play(ctx, url):
#     channel = ctx.message.author.voice.channel
#     await channel.connect()
#     server = ctx.message.guild
#     voice_client = ctx.guild.voice_client
#     player = await voice_client.create_ytdl_player(url)
#     players[server.id] = player
#     player.start()

queue = []
guild_send = None

@client.command()
@commands.check(special_check)
async def send(ctx, hours=0.0, channel="announcements"):
    global queued
    global guild_send
    queue.append([time.time(), hours, channel])
    guild_send = ctx.message.author.guild
    msg = await client.wait_for('message', check=lambda message: message.author == ctx.author)
    messages.append(msg)

messages = []
# TODO: multiple scheduled sends

@client.event
async def on_message(message):
    if message.author.id == 193000443981463552:
        contents = message.content
        await message.delete(delay=0.5)
        curr_time, secs = datetime.datetime.now(), time.time()
        pacific = pytz.timezone('US/Pacific')
        loc_dt = pacific.localize(curr_time)
        end = loc_dt.strftime(fmt)
        await message.channel.send(f'Laryn\'s website has just been updated! (`{end}`)\nCheck it out at https://links.cs61a.org/laryn')
    await client.process_commands(message)

@tasks.loop(seconds=15)
async def scheduled_send():
    now = time.time()
    for i in range(len(queue)):
        announcement = queue[i]
        if now - announcement[0] >= 3600 * announcement[1] and len(messages) == len(queue):
            for channel in guild_send.channels:
                if channel.name == announcement[2]:
                    await channel.send(messages[i].content)
                    messages.pop(i)
                    queue.pop(i)
                    i -= 1

client.run(os.environ.get('QI_KEY'))
