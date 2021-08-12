import discord
from discord.ext import commands

class ShardOne(commands.Shard):

    @commands.command()
    async def sayhello(self, ctx):
        await ctx.send('hi')

def setup(cog):
    cog.add_shard(ShardOne(cog))
