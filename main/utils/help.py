import discord
from discord.ext import commands
from utils.useful import Embed


class GrootHelp(commands.HelpCommand):
    async def send_bot_help(self, mapping):

        query = "SELECT sum(counter) FROM usage"
        cur = await self.context.bot.db.execute(query)
        row = await cur.fetchone()
        total_usage = row[0]

        em = Embed()
        em.description(
            f"Prefix `{self.context.prefix}`\n"
            f"Total commands: {len(self.context.bot.commands)} | Commands used: {total_usage}\n"
            "```diff\n- [] = optional argument\n"
            "- <> = required argument\n"
            f"+ Type {self.context.prefix}help [command | category] for "
            "more help on a specific category or command!```"
            "[Support](<https://discord.gg/nUUJPgemFE>) | "
            "[Vote](https://top.gg/bot/812395879146717214/vote) | "
            f"[Invite]({discord.utils.oauth_url(812395879146717214)})\n",
        )
        em.set_author(name=self.context.author, icon_url=self.context.author.avatar_url)
        channel = self.get_destination()
        await channel.send_bot_help(mapping)

    async def send_command_help(self, command):
        return await super().send_command_help(command)

    async def send_group_help(self, group):
        return await super().send_group_help(group)

    async def send_cog_help(self, cog):
        return await super().send_cog_help(cog)
