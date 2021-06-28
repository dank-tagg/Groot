from __future__ import annotations
import typing
if typing.TYPE_CHECKING:
    from utils._type import *

import discord

from discord.ext import commands

class Beta(commands.Cog):
    """
    A cog with commands available to only the beta-testers
    """
    def __init__(self, bot: GrootBot):
        self.bot = bot
    
    def cog_check(self, ctx: customContext):
        member: discord.Member = self.bot.get_guild(int(self.bot.config["SUPPORT_SERVER"])).get_member(ctx.author.id)
        if member is None:
            return False
        check = ctx.author == self.bot.owner or discord.utils.get(member.roles, id=823951076193337384)
        return check
    
def setup(bot):
    bot.add_cog(Beta(bot))