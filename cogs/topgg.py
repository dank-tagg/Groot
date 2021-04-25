import dbl
import discord
from discord.ext import commands, tasks

import asyncio


class TopGG(commands.Cog):
    """Handles interactions with the top.gg API"""

    def __init__(self, bot):
        self.bot = bot
        self.token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjgxMjM5NTg3OTE0NjcxNzIxNCIsImJvdCI6dHJ1ZSwiaWF0IjoxNjE4MjEzOTI0fQ.iQtsqVJbONgYMY51uYBHfVAcdwFBRuIEvaTMMI1li9g' # set this to your DBL token
        self.dblpy = dbl.DBLClient(self.bot, self.token)

    # The decorator below will work only on discord.py 1.1.0+
    # In case your discord.py version is below that, you can use self.bot.loop.create_task(self.update_stats())

    @tasks.loop(minutes=30.0)
    async def update_stats(self):
        """This function runs every 30 minutes to automatically update your server count"""
        try:
            await self.dblpy.post_guild_count()
           
        except Exception as e:
            print(e)


    @commands.Cog.listener()
    async def on_dbl_vote(self, data):
        print(data)

def setup(bot):
    bot.add_cog(TopGG(bot))