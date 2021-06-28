from __future__ import annotations
import typing
if typing.TYPE_CHECKING:
    from utils._type import *

import datetime
import time
import discord
import humanize
import inspect
import os

from discord.ext import commands
from utils.chat_formatting import hyperlink
from utils.useful import Embed


class Information(commands.Cog):
    def __init__(self, bot: GrootBot):
        self.bot = bot

    @commands.command(name="ping", brief="Shows the bots latency")
    async def ping(self, ctx: customContext):
        """
        Shows the bot's latency in miliseconds.\n
        Useful if you want to know if the bot is lagging or not
        """
        start = time.perf_counter()
        msg = await ctx.send("<a:typing:826939777290076230> pinging...")
        end = time.perf_counter()
        typing_ping = (end - start) * 1000
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"

        async with self.bot.db.execute(query) as cur:
            row = await cur.fetchall()
        a = [i[0] for i in row]
        start = time.perf_counter()
        for name in a:
            query = f"SELECT * FROM {name}"
            async with self.bot.db.execute(query):
                end = time.perf_counter()

        sql_ping = (end - start) * 1000
        await msg.edit(
            content=f"{self.bot.icons['typing']} ** | Typing**: {round(typing_ping, 1)} ms\n{self.bot.icons['groot']} ** | Websocket**: {round(self.bot.latency*1000)} ms\n{self.bot.icons['database']} ** | Database**: {round(sql_ping, 1)} ms"
        )

    @commands.command(name="vote", brief="The links where you can vote for the bot.")
    async def _vote(self, ctx: customContext):
        """
        Sends an embed containing two hyperlinks,\n
        one for Top.gg and one for discordbotlist.com
        """
        em = Embed(
            title="Vote for Groot!",
            description=f'{hyperlink("**top.gg**", "https://top.gg/bot/812395879146717214/vote")}\n\n'
            f'{hyperlink("**discordbotlist.com**", "https://discordbotlist.com/bots/groot/upvote")}',
        )
        em.set_thumbnail(url=self.bot.user.avatar_url)
        await ctx.send(embed=em)

    @commands.command(name="invite", brief="Sends an invite for the bot.")
    async def invite(self, ctx: customContext):
        """
        Sends an invite for the bot with no permissions.\n
        Note that a few permissions are required to let the bot run smoothly,\n
        as shown in `perms`
        """
        em = Embed(title=f"Invite {self.bot.user.name} to your server!", color=0x2F3136)
        em.add_field(
            name=f"Invite the bot",
            value=f"{hyperlink('**Click Here**', f'{discord.utils.oauth_url(812395879146717214)}')}",
            inline=False,
        )

        em.add_field(
            name="Support server",
            value=f"{hyperlink('**Click Here**','https://discord.gg/nUUJPgemFE')}",
            inline=False,
        )
        em.set_thumbnail(url=self.bot.user.avatar_url)
        await ctx.send(embed=em)


    @commands.command(name="uptime", brief="Shows the bot's uptime")
    async def _uptime(self, ctx: customContext):
        """
        Shows the bot's uptime in days | hours | minutes | seconds
        """
        em = Embed(
            description=f"{humanize.precisedelta(datetime.datetime.utcnow() - self.bot.launch_time, format='%.0f')}",
            colour=0x2F3136,
        )
        em.set_author(name="Uptime")
        em.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=em)

    @commands.command()
    async def source(self, ctx: customContext, *, command: str = None):
        """Displays my full source code or for a specific command.
        To display the source code of a subcommand you can separate it by
        periods, e.g. tag.create for the create subcommand of the tag command
        or by spaces.
        """
        source_url = 'https://github.com/dank-tagg/Groot'
        branch = 'main'
        if command is None:
            return await ctx.send(source_url)

        obj = self.bot.get_command(command.replace('.', ' '))
        if obj is None:
            return await ctx.send('Could not find command.')

        src = obj.callback.__code__
        module = obj.callback.__module__
        filename = src.co_filename

        lines, firstlineno = inspect.getsourcelines(src)
        location = os.path.relpath(filename).replace('\\', '/')

        final_url = f'<{source_url}/tree/{branch}/main/{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}>'
        await ctx.send(final_url)

def setup(bot):
    bot.add_cog(Information(bot), category="Information")
