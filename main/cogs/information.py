from utils._type import *

import datetime
import time
import discord
import humanize
import inspect
import os
import io
import pygit2
import itertools
import textwrap
import contextlib

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
        Shows the bot's latency in miliseconds.
        Useful if you want to know if the bot is lagging or not
        """
        start = time.perf_counter()
        msg = await ctx.send("<a:typing:826939777290076230> pinging...")
        end = time.perf_counter()
        typing_ping = (end - start) * 1000

        start = time.perf_counter()
        await self.bot.db.execute('SELECT 1')
        end = time.perf_counter()

        sql_ping = (end - start) * 1000
        await msg.edit(
            content=f"{self.bot.icons['typing']} ** | Typing**: {round(typing_ping, 1)} ms\n{self.bot.icons['groot']} ** | Websocket**: {round(self.bot.latency*1000)} ms\n{self.bot.icons['database']} ** | Database**: {round(sql_ping, 1)} ms"
        )

    @commands.command(name="vote", brief="The links where you can vote for the bot.")
    async def _vote(self, ctx: customContext):
        """
        Sends an embed containing two hyperlinks,
        one for Top.gg and one for discordbotlist.com
        """
        em = Embed(
            title="Vote for Groot!",
            description='With your votes, we can grow faster\nsupporting the development of Groot.'
        )
        em.set_thumbnail(url=self.bot.user.avatar.url)

        class VoteView(discord.ui.View):
            def __init__(self):
                super().__init__()
                self.add_item(discord.ui.Button(label='top.gg', url='https://top.gg/bot/812395879146717214/vote'))
                self.add_item(discord.ui.Button(label='discordbotlist.com', url='https://discordbotlist.com/bots/groot/upvote'))
        
        await ctx.send(embed=em, view=VoteView())

    @commands.command(name="invite", aliases=["support"], brief="Sends an invite for the bot.")
    async def invite(self, ctx: customContext):
        """
        Sends an invite for the bot with no permissions.
        Note that a few permissions are required to let the bot run smoothly,
        as shown in `perms`
        """
        em = Embed(title=f"Invite {self.bot.user.name} to your server!")
        em.description = f'You like me huh? Invite me to your server with the link below. \n \
                          Run into any problems? Join the support server where we can help you out.\n\n\
                          Thank you for using me! \n\n \
                          {hyperlink("Vote", "https://top.gg/bot/812395879146717214/vote")} | \
                          {hyperlink("Website", "https://grootdiscordbot.xyz")} | \
                          {hyperlink("Source", "https://github.com/dank-tagg/Groot")}'

        class InviteView(discord.ui.View):
            def __init__(self):
                super().__init__()
                self.add_item(discord.ui.Button(label='Invite Groot!', url=discord.utils.oauth_url(812395879146717214)))
                self.add_item(discord.ui.Button(label='Support Server', url='https://discord.gg/nUUJPgemFE'))
        
        await ctx.send(embed=em, view=InviteView())


    @commands.command(name="uptime", brief="Shows the bot's uptime")
    async def _uptime(self, ctx: customContext):
        """
        Shows the bot's uptime in days | hours | minutes | seconds
        """
        em = Embed(
            description=f"{humanize.precisedelta(discord.utils.utcnow() - self.bot.launch_time, format='%.0f')}",
            colour=0x2F3136,
        )
        em.set_author(name="Uptime")
        em.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
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
        filename = src.co_filename

        lines, firstlineno = inspect.getsourcelines(src)
        location = os.path.relpath(filename).replace('\\', '/')

        final_url = f'{source_url}/tree/{branch}/main/{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}'

        class SourceView(discord.ui.View):
            def __init__(self, ctx: customContext):
                super().__init__()
                self.ctx = ctx
                self.add_item(discord.ui.Button(label='Source URL', url=final_url))
            
            @discord.ui.button(emoji='<:trashcan:822050746333003776>')
            async def delete(self, button: discord.ui.Button, interaction: discord.Interaction):
                with contextlib.suppress(discord.HTTPException):
                    await self.ctx.message.delete()
                await interaction.message.delete()

            @discord.ui.button(label='Source File')
            async def send_file(self, button: discord.ui.Button, interaction: discord.Interaction):
                if interaction.user != self.ctx.author:
                    await interaction.response.send_message('Oops. This is not your interaction.', ephemeral=True)
                    return
                
                await interaction.channel.send(file=discord.File(io.BytesIO(textwrap.dedent(''.join(lines)).encode('ascii')), 'source.py'))
                button.disabled = True
                await interaction.response.edit_message(view=self)

        em = Embed(title=f'Here is the source for {obj.qualified_name}')

        if len("".join(lines)) < 2000:
            zwsp = '\u200b'
            em.description = f'```py\n{textwrap.dedent("".join(lines).replace("``", f"`{zwsp}`"))}\n```'
        else:
            em.description = '```\nSource was too long to be shown here. Click Source File/Source URL below to see it.```'
        await ctx.send(embed=em, view=SourceView(ctx))

    @commands.command(name="about", aliases=['info'])
    async def _about_me(self, ctx: customContext):
        """Sends some information about Groot."""
        revision = self.get_last_commits()
        em = Embed(
            title="Invite me to your server!",
            url="https://grootdiscordbot.xyz/invite",
            description="Groot is a simple yet feature-rich discord bot.\nFeaturing over 150 commands, the best discord bot you could ask for!\n" +
                        f"Made by [`{self.bot.get_user(396805720353275924)}`](https://discord.com/users/396805720353275924) with \💖\n" + 
                        f"{hyperlink('Website', 'https://grootdiscordbot.xyz')} | {hyperlink('Source', 'https://github.com/dank-tagg/Groot')} | {hyperlink('Vote', 'https://top.gg/bot/812395879146717214/vote')}",
            color=0x3CA374
        )
        # Recent changes
        em.add_field(name="Latest changes:", value=revision, inline=False)
        em.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)

        # Contributors
        contributors = [
            711057339360477184,
            746807014658801704,
            797044260196319282,
            144126010642792449,
            852788943229288449,
            525843819850104842,
            750135653638865017,
            526711399137673232
        ]
        em.add_field(name="Contributors:\n", value=" ".join(f"[`{self.bot.get_user(m)}`](https://discord.com/users/{m})" for m in contributors))

        em.add_field(name="Uptime:", value=humanize.precisedelta(discord.utils.utcnow() - self.bot.launch_time, format='%.0f'))
        await ctx.send(embed=em)

def setup(bot):
    bot.add_cog(Information(bot), cat_name="Information")
