import topgg
from discord.ext import commands, tasks
from utils import discordbotlist


class API(commands.Cog):
    """Handles interactions with API (top.gg, discordbotlist)"""

    def __init__(self, bot):
        self.bot = bot

        # Top GG
        self.topgg = topgg.DBLClient(self.bot, self.bot.config.get("topgg"))
        self.webhook = topgg.WebhookManager(self.bot)
        self.webhook.dbl_webhook(
            "https://grootdiscordbot.xyz/api/webhook", auth_key="realwebhook"
        )

        # Discord Bot List
        self.dbl = discordbotlist.Client(self.bot, self.bot.config.get("dbl"))

        self.update_stats.start()

    @tasks.loop(minutes=10)
    async def update_stats(self):
        """
        This function runs every 30 minutes
        to automatically update all API's stats
        """
        await self.topgg.post_guild_count()
        await self.dbl.post_stats()


def setup(bot):
    bot.add_cog(API(bot))
