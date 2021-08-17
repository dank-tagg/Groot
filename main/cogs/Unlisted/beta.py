from utils._type import *

import discord

from discord.ext import commands
from utils.useful import Embed

class Beta(commands.Shard):
    """
    A cog with commands available to only the beta-testers
    """
    def __init__(self, cog: commands.Cog):
        super().__init__(cog)
        self.bot = cog.bot

    def cog_check(self, ctx: customContext):
        member: discord.Member = self.bot.get_guild(self.bot.config.getint('Other', 'SUPPORT_SERVER')).get_member(ctx.author.id)
        if member is None:
            return False
        check = ctx.author == self.bot.owner or discord.utils.get(member.roles, id=823951076193337384)
        return check

    @commands.command()
    async def testers(self, ctx: customContext):
        support_server = self.bot.get_guild(self.bot.config.getint('Other', 'SUPPORT_SERVER'))

        em = Embed(
            description=''.join(m.mention for m in support_server.get_role(823951076193337384).members)
        )

        await ctx.send(embed=em)

def setup(cog):
    cog.add_shard(Beta(cog))