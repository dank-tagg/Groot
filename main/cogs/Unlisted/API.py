from utils._type import *

import topgg

from discord.ext import commands, tasks
from utils import discordbotlist


class API(commands.Shard):
    """Handles interactions with API (top.gg, discordbotlist)"""

    def __init__(self, cog: commands.Cog):
        super().__init__(cog)
        self.bot = cog.bot

        # Top GG
        self.topgg = topgg.DBLClient(self.bot, self.bot.config.get("Groot", "topgg"))
        self.webhook = topgg.WebhookManager(self.bot)
        self.webhook.dbl_webhook(
            "https://grootdiscordbot.xyz/api/webhook", auth_key="realwebhook"
        )

        # Discord Bot List
        self.dbl = discordbotlist.Client(self.bot, self.bot.config.get("Groot", "dbl"))

        self.update_stats.start()

    @tasks.loop(minutes=10)
    async def update_stats(self):
        """
        This function runs every 30 minutes
        to automatically update all API's stats
        """
        await self.topgg.post_guild_count()
        await self.dbl.post_stats()


def setup(cog):
    cog.add_shard(API(cog))
