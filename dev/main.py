import sys
sys.dont_write_bytecode = True
import configparser
import os
import discord
from discord.ext import commands
from os import environ

environ["JISHAKU_NO_UNDERSCORE"] = "True"
environ["JISHAKU_NO_DM_TRACEBACK"] = "True"

config = configparser.ConfigParser()
config.read(f'/home/dank-tagg/Groot/main/config/config.ini')

async def get_prefix(bot, message):
    if message.author.id == 396805720353275924:
        return ["g,", "i love jotte;"]
    return "g,"

bot = commands.Bot(command_prefix=get_prefix)

@bot.event
async def on_ready():
    print("Logged in...")

@bot.event
async def on_message_edit(before, after):
    if after.author.id != 396805720353275924:
        return
    await bot.process_commands(after)

def override_discord():

    def add_command(self: commands.Cog, command: commands.Command):
        self.__cog_commands__ += (command, )
        command.cog = self
        if hasattr(self, 'bot'):
            self.bot.add_command(command)

    commands.Cog.add_command = add_command

override_discord()


cogs = ()
for file in os.listdir("cogs"):
    if file.endswith(".py"):
        cogs += (file[:-3],)

cogs += ("jishaku", )
for cog in cogs:
    ext = "cogs." if cog != "jishaku" else ""
    bot.load_extension(f"{ext}{cog}")

bot.run(config.get('Groot', 'token'))
