from discord.ext import commands, ipc


class Ipc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @ipc.server.route()
    async def get_member_count(self, data):
        guild = self.bot.get_guild(
            data.guild_id
        )  # get the guild object using parsed guild_id
        return guild.member_count
    
    @ipc.server.route()
    async def get_stats(self):
        stats = {
            "users": len(self.bot.users),
            "guilds": len(self.bot.guilds)
        }
        return stats


def setup(bot):
    bot.add_cog(Ipc(bot))
