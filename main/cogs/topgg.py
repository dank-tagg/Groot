from os import environ

import dbl
from discord.ext import commands, tasks


class TopGG(commands.Cog):
    """Handles interactions with the top.gg API"""

    def __init__(self, bot):
        self.bot = bot
        self.token = environ.get("topgg")
        self.dblpy = dbl.DBLClient(self.bot, self.token)

    @tasks.loop(minutes=30.0)
    async def update_stats(self):
        """
        This function runs every 30 minutes
        to automatically update your server count
        """
        try:
            await self.dblpy.post_guild_count()

        except Exception as e:
            print(e)

    @commands.Cog.listener()
    async def on_dbl_vote(self, data):
        print(data)


def setup(bot):
    bot.add_cog(TopGG(bot))
