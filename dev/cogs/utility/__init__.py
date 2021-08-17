import discord
import os

from discord.ext import commands

class FirstCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Loading shards
        for shard in os.listdir('./cogs/utility'):
            if shard != '__init__.py' and shard.endswith('.py'):
                self.load_shard(f'cogs.utility.{shard[:-3]}')


def setup(bot):
    bot.add_cog(FirstCog(bot))
