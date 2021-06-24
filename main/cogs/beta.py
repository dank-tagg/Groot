import discord
from discord.ext import commands


WHITELIST = []

class Beta(commands.Cog):
    """
    A cog with commands available to only the beta-testers
    """
    def __init__(self, bot):
        self.bot = bot
    
    def cog_check(self, ctx):
        return ctx.author.id in [WHITELIST, self.bot.owner.id]
    
def setup(bot):
    bot.add_cog(Beta(bot))