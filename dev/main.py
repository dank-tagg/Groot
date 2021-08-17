import sys
sys.dont_write_bytecode = True
import importlib
import configparser
import os
import discord
from discord.ext import commands
from os import environ
from shard import Shard

environ["JISHAKU_NO_UNDERSCORE"] = "True"
environ["JISHAKU_NO_DM_TRACEBACK"] = "True"

config = configparser.ConfigParser()
config.read(f'C:\\Users\\mianz\\Groot\\main\\config\\config.ini')

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

def override_discord():

    def add_command(self: commands.Cog, command: commands.Command):
        self.__cog_commands__ += (command, )

    def load_shard(self: commands.Cog, shard_path: str):
        spec = importlib.util.find_spec(shard_path)
        if spec is None:
            raise commands.ExtensionNotLoaded(shard_path)
        lib = importlib.util.module_from_spec(spec)


        key = shard_path
        sys.modules[key] = lib

        try:
            spec.loader.exec_module(lib)
        except Exception as e:
            del sys.modules[key]
            raise commands.ExtensionFailed(key, e) from e

        try:
            setup = getattr(lib, 'setup')
        except AttributeError:
            del sys.modules[key]
            raise commands.NoEntryPointError(key)

        try:
            setup(self)
        except Exception as e:
            del sys.modules[key]
            raise commands.ExtensionFailed(key, e) from e
        else:
            if not hasattr(self, '__shards'):
                self.__shards = {}
            self.__shards[key] = lib


    def add_shard(self: commands.Cog, shard: Shard):
        shard._inject()
        cog_shards = getattr(self, 'shards', {})
        cog_shards[shard.name] = shard



    commands.Cog.add_command = add_command
    commands.Cog.load_shard = load_shard
    commands.Shard = Shard
    commands.Cog.add_shard = add_shard

override_discord()


cogs = ()
for file in os.listdir("./cogs"):
    if file.endswith(".py"):
        cogs += (file[:-3],)

cogs += ("jishaku", )
for cog in cogs:
    ext = "cogs." if cog != "jishaku" else ""
    bot.load_extension(f"{ext}{cog}")

bot.run(config.get('GrootDev', 'dev'))
