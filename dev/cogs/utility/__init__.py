import discord
import os

from discord.ext import commands

class FirstCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Loading packages
        for package in os.listdir():
            print(package)

def setup(bot):
    bot.add_cog(FirstCog(bot))
