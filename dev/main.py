import sys
sys.dont_write_bytecode = True

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


bot.load_extension("jishaku")
bot.load_extension("commands")

bot.run(environ["main"])
