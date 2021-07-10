import sys
sys.dont_write_bytecode = True

import os
import discord
from discord.ext import commands
from os import environ
from dotenv import load_dotenv

environ["JISHAKU_NO_UNDERSCORE"] = "True"
environ["JISHAKU_NO_DM_TRACEBACK"] = "True"

load_dotenv("../main/bot_config/secrets.env")

async def get_prefix(bot, message):
    if message.author.id == 396805720353275924:
        return ["g,", "i love jotte;"]
    return "g,"

bot = commands.Bot(command_prefix=get_prefix, intents=discord.Intents.all())

@bot.event
async def on_ready():
    print("Logged in...")

@bot.event
async def on_message_edit(before, after):
    if after.author.id != 396805720353275924:
        return
    await bot.process_commands(after)


cogs = ()
for file in os.listdir("cogs"):
    if file.endswith(".py"):
        cogs += (file[:-3],)

cogs += ("jishaku", )
for cog in cogs:
    ext = "cogs." if cog != "jishaku" else ""
    bot.load_extension(f"{ext}{cog}")

bot.run(environ["main"])
