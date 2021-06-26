from discord.ext import commands, ipc
import logging
import humanize
import datetime
import textwrap
import io
from contextlib import redirect_stdout
import traceback

class Ipc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @ipc.server.route()
    async def get_member_count(self, data):
        guild = self.bot.get_guild(data.guild_id)
        return guild.member_count
    
    @ipc.server.route()
    async def get_stats(self, data):
        stats = {
            "users": len(self.bot.users),
            "guilds": len(self.bot.guilds),
            "commands": len(self.bot.commands),
            "uptime": humanize.precisedelta(datetime.datetime.utcnow() - self.bot.launch_time, format='%.0f')
        }
        return stats
    

    # Events
    @ipc.server.route()
    async def on_vote(self, data):
        data = data.vote_data
        user_id = int(data['user'])
        source = "Discord Bot List" if data['source'] == "dbl" else "Top GG"
        user = self.bot.get_user(user_id)
        channel = self.bot.get_channel(849309529342607360)
        await channel.send(
            f"{user.mention} voted for the bot on **{source}**! Thank you for your support :>\n"
            "To vote, click here:\n"
            "<https://top.gg/bot/812395879146717214/vote>\n"
            "<https://discordbotlist.com/bots/groot/upvote>"
        )

def setup(bot):
    bot.add_cog(Ipc(bot))
