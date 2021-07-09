from utils._type import *

import datetime
import time
import discord
import humanize
import inspect
import os
import pygit2
import itertools

from discord.ext import commands
from utils.chat_formatting import hyperlink
from utils.useful import Embed


class Information(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def format_commit(self, commit):
        short, _, _ = commit.message.partition('\n')
        short_sha2 = commit.hex[0:6]
        
        # [`hash`](url) message (offset)
        return f'[`{short_sha2}`](https://github.com/dank-tagg/Groot/commit/{commit.hex}) \\{short} (<t:{commit.commit_time}:R>)'

    def get_last_commits(self, count=3):
        repo = pygit2.Repository(f'{self.bot.cwd}/../.git')
        commits = list(itertools.islice(repo.walk(repo.head.target, pygit2.GIT_SORT_TOPOLOGICAL), count))
        return '\n'.join(self.format_commit(c) for c in commits)

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

    @commands.command(name="about")
    async def _about_me(self, ctx: customContext):
        revision = self.get_last_commits()
        em = Embed(
            title="Invite me to your server!",
            url="https://grootdiscordbot.xyz/invite",
            description="Groot is a simple yet feature-rich discord bot.\nFeaturing over 150 commands, the best discord bot you could ask for!\n" +
                        f"Made by [`{self.bot.get_user(396805720353275924)}`](https://discord.com/users/396805720353275924) with \💖\n\n",
            color=0x3CA374
        )
        # Recent changes
        em.add_field(name="Latest changes:", value=revision, inline=False)
        em.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)

        # Contributors
        contributors = [
            711057339360477184,
            746807014658801704,
            797044260196319282,
            144126010642792449,
            852788943229288449,
            525843819850104842,
            750135653638865017
        ]
        em.add_field(name="Contributors:\n", value=" ".join(f"[`{self.bot.get_user(m)}`](https://discord.com/users/{m})" for m in contributors))

        em.add_field(name="Uptime:", value=humanize.precisedelta(datetime.datetime.utcnow() - self.bot.launch_time, format='%.0f'))
        await ctx.send(embed=em)

def setup(bot):
    bot.add_cog(Information(bot), cat_name="Information")
