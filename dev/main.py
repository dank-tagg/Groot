import sys
sys.dont_write_bytecode = True
import discord
import configparser
from os import environ

environ["JISHAKU_NO_UNDERSCORE"] = "True"
environ["JISHAKU_NO_DM_TRACEBACK"] = "True"

config = configparser.ConfigParser()
config.read(f'../main/config/config.ini')

bot = discord.Bot()

TEST_GUILD = 707869808129081364

@bot.event
async def on_ready():
    print('Ready')

@bot.command(guild_ids=[TEST_GUILD])
async def test(ctx):
    await ctx.send('test')


bot.run(config.get('GrootDev', 'dev'))
