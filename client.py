#!/bin/python
import discord
import os
import datetime
import sys
import subprocess
import discord.utils
import asyncio

selectedchannel = None
selectedchannelobj = None
selectedserver = None
userprofile = None
servers = None
selectedserverobj = None
canoutput = False
dayrn = datetime.date.today()

def selectserver():
    global canoutput
    global selectedserver
    global selectedserverobj

    canoutput = False
    options_str = "\n".join(servers)

    try:
        result = subprocess.run(
            ["fzf", "--height", "40%", "--reverse", "--header=Choose an option:"],
            input=options_str,
            text=True,
            capture_output=True,
            check=True
        )
        selected_option = result.stdout.strip()
        selectedserver = selected_option
        selectedserverobj = discord.utils.get(userprofile.guilds, name=selectedserver)
        selectserverchannel()

    except subprocess.CalledProcessError:
        print("No option selected.\n")
        canoutput = True

def selectserverchannel():
    global canoutput
    global selectedchannel

    if selectedserverobj is None:
        print("Server not found.")
        return

    text_channels = [channel.name for channel in selectedserverobj.channels if isinstance(channel, discord.TextChannel)]

    options_str = "\n".join(text_channels)

    try:
        result = subprocess.run(
            ["fzf", "--height", "40%", "--reverse", "--header=Choose an option:"],
            input=options_str,
            text=True,
            capture_output=True,
            check=True
        )
        selected_option = result.stdout.strip()
        selectedchannel = selected_option
    except subprocess.CalledProcessError:
        print("No option selected.\n")
    finally:
        canoutput = True

class MyClient(discord.Client):
    async def on_ready(self):
        global selectedserverobj
        global userprofile
        global servers
        global selectedchannelobj

        userprofile = self
        servers = [guild.name for guild in self.guilds]
        
        selectserver()

        selectedchannelobj = discord.utils.get(
            selectedserverobj.channels, 
            name=selectedchannel, 
            type=discord.ChannelType.text
        )

        print("Successfully logged in!")
        print('Logged on as', self.user)

        await self.print_old_messages()

        start_input_handling()

    async def print_old_messages(self):
        if selectedchannelobj is None:
            print("Selected channel is None.")
            return

        async for message in selectedchannelobj.history(limit=100):
            daycreated = message.created_at.strftime("%D")
            ftime = message.created_at.strftime("%H:%M")
            sender = message.author
            print(f"\033[1m{sender} \033[38;5;250m{daycreated} {ftime}\033[0m")
            print(message.content)

    async def on_message(self, message):
        if message.channel.name != selectedchannel or canoutput == False:
            return
        ftime = datetime.datetime.now().strftime("%H:%M")
        sender = message.author
        print(f"\033[1m{sender} \033[38;5;250mToday at {ftime}\033[0m")
        print(message.content)

def trylogin():
    inputtok = input("Enter token: ")
    try:
        client.run(inputtok)
    except Exception as ex:
        print(f"\033[31mError occured: {ex}")
        print("Try again.\033[0m")
        trylogin()
    else:
        os.mkdir("./info")
        with open("./info/.token", "w") as file:
            file.write(inputtok)

def login():
    if os.path.exists("./info/.token"):
        print("Found ./info/.token, reading token...")
        with open("./info/.token", "r") as file:
            content = file.read()
            try:
                client.run(content)
            except Exception as ex:
                print(f"\033[31mError occured: {ex}")
                print("Exiting...\033[0m")
                sys.exit(1)
    else:
        trylogin()

async def inputhandling():
    global selectedchannelobj
    while True:
        inp = input(f"Message #{selectedchannel}: ")
        if inp == "`SWITCHSERVER":
            selectserver()
        elif inp == "`SWITCHCHANNEL":
            selectserverchannel()
        elif inp == "`EXIT":
            sys.exit(0)
        if selectedchannelobj is not None:
            await selectedchannelobj.send(inp)
        else:
            print("Channel not found!")

def start_input_handling():
    loop = asyncio.get_event_loop()
    loop.create_task(inputhandling())

client = MyClient()
login()