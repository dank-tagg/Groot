import os

from discord.ext import commands

class Information(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Loading shards
        for shard in os.listdir(f'{self.bot.cwd}/cogs/{self.__class__.__name__}'):
            if shard != '__init__.py' and shard.endswith('.py'):
                self.load_shard(f'cogs.{self.__class__.__name__}.{shard[:-3]}')


def setup(bot):
    bot.add_cog(Information(bot))
