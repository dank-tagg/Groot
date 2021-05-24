import asyncio
import collections
import datetime
import io
import math
import os
import traceback

import discord
import mystbin
import tabulate
import utils.json_loader
from discord.ext import commands
from jishaku.codeblocks import codeblock_converter
from jishaku.models import copy_context_with
from utils.chat_formatting import box, hyperlink
from utils.useful import Embed



class Developer(commands.Cog):
    """dev-only commands that make the bot dynamic."""

    def __init__(self, bot):
        self.bot = bot
        self._last_result = None
        self.sessions = set()
        self.task_count = 0
        self.tasks = collections.deque()

    @staticmethod
    async def run_shell(code: str) -> bytes:
        proc = await asyncio.create_subprocess_shell(
            code, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()

        if stdout:
            stdout = f"```$ {code}\n{stdout.decode()}```"
        if stderr:
            stderr = f"```$ {code}\n{stderr.decode()}```"

        return stderr if stderr else stdout
    
    async def git(self, *, arguments):
        text = await self.run_shell(
            f"cd {str(__import__('pathlib').Path(self.bot.cwd).parent)};git {arguments}"
        )
        if not isinstance(text, str):
            text = text.decode("ascii")
        return text.replace(
                f"cd {str(__import__('pathlib').Path(self.bot.cwd).parent)};", 
                ""
            )

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.group(invoke_without_command=True, case_insensitive=True)
    async def dev(self, ctx):
        return

    @dev.command(name="update")
    async def _update(self, ctx, link: str, *, message: str):
        await ctx.send("Are you sure you want update me? `(y/n)`")

        msg = await self.bot.wait_for(
            "message", timeout=10, check=lambda m: m.author == ctx.author
        )
        if msg.content.lower() == "y":
            async with ctx.typing():
                data = utils.json_loader.read_json("updates")
                data["upDATE"] = str(datetime.datetime.utcnow())
                data["update"] = message
                data["link"] = link
                utils.json_loader.write_json(data, "updates")

    @dev.command(name="eval", aliases=["run"])
    async def _eval(self, ctx, *, code: codeblock_converter):
        """Evaluates a code"""

        jsk = self.bot.get_command("jishaku py")
        return await jsk(ctx, argument=code)

    @_eval.error
    async def _eval_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            error = getattr(error, "original", error)
            if error.code == 50035:
                output = (
                    self.bot.value + self.bot.ret if self.bot.ret else self.bot.value
                )
                mystbin_client = mystbin.Client()
                paste = await mystbin_client.post(f"{output}", syntax="python")
                await mystbin_client.close()
                em = Embed(color=0x2F3136)
                em.add_field(
                    name="Output:",
                    value=f"{box(output[0:10] + '... # Truncated', 'py')}",
                )
                em.add_field(
                    name="Your output was too long!\n",
                    value=f"I pasted your output {hyperlink('here', paste)}",
                    inline=False,
                )
                em.set_author(name="Evaluated your code!")
                await ctx.send(embed=em)

    @dev.command(name="guilds")
    async def _guilds(self, ctx, page: int = 1):
        GUILDSa = self.bot.guilds
        alist = []
        for GUILDS in GUILDSa:
            alist.append(self.bot.get_guild(GUILDS.id))

        alist = [
            (guild.name, guild.id, guild.owner_id, len(guild.members))
            for i, guild in enumerate(alist)
        ]
        alist = sorted(alist, key=lambda guild: guild[3], reverse=True)

        page = page

        items_per_page = 5
        pages = math.ceil(len(alist) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue = ""
        embed = (
            Embed(
                description="**Servers [{}]**\n\n{}".format(len(GUILDSa), queue),
                color=0x2F3136,
            )
            .set_footer(
                text="Viewing page {}/{}".format(page, pages),
                icon_url=self.bot.user.avatar_url,
            )
            .set_author(name=f"{ctx.author}", icon_url=f"{ctx.author.avatar_url}")
        )

        for i, guild in enumerate(alist[start:end], start=start):
            owner = await self.bot.fetch_user(int(guild[2]))
            owner = owner.mention
            embed.add_field(
                name=f"{guild[0]}\n",
                value=f"Members: {guild[3]:,}\nGuild ID: `{guild[1]}`\nOwner: {owner}\n\n",
                inline=False,
            )
        msg = await ctx.send(embed=embed)

    @dev.command(name="inviteme")
    async def _inviteme(self, ctx, *, guildid: int):
        guild = self.bot.get_guild(guildid)
        await ctx.author.send(f"{await guild.text_channels[0].create_invite()}")

    @dev.command(name="sync")
    async def _sync(self, ctx, extension: str = None):

        text = await self.git(arguments="pull")
        fail = ""

        if extension is None:
            async with ctx.typing():
                for file in os.listdir(f"{self.bot.cwd}/cogs"):
                    if file.endswith(".py"):
                        try:
                            self.bot.reload_extension(f"cogs.{file[:-3]}")
                        except discord.ext.commands.ExtensionNotLoaded as e:
                            fail += f"```diff\n- {e.name} is not loaded```"
                        except discord.ext.commands.ExtensionFailed as e:
                            exc_info = type(e), e.original, e.__traceback__
                            etype, value, trace = exc_info
                            traceback_content = "".join(
                                traceback.format_exception(etype, value, trace, 10)
                            ).replace("``", "`\u200b`")
                            fail += (
                                f"```diff\n- {e.name} failed to reload.```"
                                + f"```py\n{traceback_content}```"
                            )

            if fail == "":
                em = Embed(color=0x3CA374)
                em.add_field(
                    name="Pulling from GitHub",
                    value=text,
                    inline=False
                )
                em.add_field(
                    name=f"{self.bot.greenTick} Cogs Reloading",
                    value="```diff\n+ All cogs were reloaded successfully```",
                )

                await ctx.reply(embed=em, mention_author=False)
            else:
                em = Embed(color=0xFFCC33)
                em.add_field(
                    name="Pulling from GitHub",
                    value=text,
                    inline=False
                )
                em.add_field(
                    name="<:idle:817035319165059102> **Failed to reload all cogs**",
                    value=fail,
                )
                await ctx.reply(
                    embed=em, mention_author=False
                )

        else:
            try:
                self.bot.reload_extension(f"cogs.{extension}")
                em = Embed(
                    description=f"{self.bot.greenTick} "
                    f"**Reloaded cogs.{extension}**",
                    color=0x3CA374,
                )
                em.add_field(
                    name="Pulling from GitHub",
                    value=text,
                    inline=False
                )

                await ctx.reply(embed=em, mention_author=False)

            except discord.ext.commands.ExtensionFailed as e:
                exc_info = type(e), e.original, e.__traceback__
                etype, value, trace = exc_info
                traceback_content = "".join(
                    traceback.format_exception(etype, value, trace, 10)
                ).replace("``", "`\u200b`")

                em = Embed(color=0xF04D4B)
                em.add_field(
                    name="Pulling from GitHub",
                    value=text,
                    inline=False
                )
                em.add_field(
                    name=f"{self.bot.redTick} " f"Failed to reload {e.name}",
                    value=f"```py\n{traceback_content}```",
                )
                await ctx.reply(embed=em, mention_author=False)

    @dev.command(name="sudo")
    async def _sudo(self, ctx: commands.Context, *, command_string: str):
        """
        Run a command bypassing all checks and cooldowns.

        This also bypasses permission checks so this has a high possibility of making commands raise exceptions.
        """

        alt_ctx = await copy_context_with(ctx, content=ctx.prefix + command_string)

        if alt_ctx.command is None:
            return await ctx.send(f'Command "{alt_ctx.invoked_with}" is not found')

        return await alt_ctx.command.reinvoke(alt_ctx)

    @dev.command(name="reload")
    async def _reloadmodule(self, ctx, *, module: str):
        cmd = self.bot.get_command("dev eval")
        await ctx.invoke(
            cmd, code="import imp\n" f"import {module}\n" f"print(imp.reload({module}))"
        )

    @dev.command()
    async def tables(self, ctx):
        cmd = self.bot.get_command("dev sql")
        await ctx.invoke(
            cmd,
            query="SELECT name FROM sqlite_master WHERE type ='table' AND name NOT LIKE 'sqlite_%';",
        )

    @dev.command()
    async def sql(self, ctx, *, query: str):
        async with self.bot.db.execute(query) as cur:
            await self.bot.db.commit()
            if cur.description:
                columns = [tuple[0] for tuple in cur.description]
            else:
                columns = "keys"
            thing = await cur.fetchall()
            if len(thing) == 0:
                return await ctx.message.add_reaction(f"{self.bot.greenTick}")
            thing = tabulate.tabulate(thing, headers=columns, tablefmt="psql")
            byte = io.BytesIO(str(thing).encode("utf-8"))
            return await ctx.send(file=discord.File(fp=byte, filename="table.txt"))

    @sql.error
    async def sql_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.message.add_reaction(f"{self.bot.redTick}")
            await ctx.send(str.capitalize(str(error.original)))

    @dev.command(name="git")
    async def _git(self, ctx, *, arguments):
        text = await self.git(arguments=arguments)
        await ctx.send(text or "No output.")

    @commands.command(name="delete", aliases=["del", "d"])
    async def delete_bot_message(self, ctx):
        try:
            message = ctx.channel.get_partial_message(ctx.message.reference.message_id)
        except AttributeError:
            await ctx.message.add_reaction("❌")
            return
        try:
            await message.delete()
            await ctx.message.add_reaction("✅")
        except discord.Forbidden:
            await ctx.message.add_reaction("❌")

    @commands.command(name="close")
    async def _close(self, ctx):
        await self.bot.logout()
        for user in self.bot.cached_users:
            query = "UPDATE currency_data SET wallet = ?, bank = ?, max_bank = ?, boost = ?, exp = ?, lvl = ? WHERE user_id = ?"
            await self.bot.db.execute(
                query,
                (
                    self.bot.cached_users[user]["wallet"],
                    self.bot.cached_users[user]["bank"],
                    self.bot.cached_users[user]["max_bank"],
                    round(self.bot.cached_users[user]["boost"], 2),
                    self.bot.cached_users[user]["exp"],
                    self.bot.cached_users[user]["lvl"],
                    user,
                ),
            )

        await self.bot.db.commit()


def setup(bot):
    bot.add_cog(Developer(bot))
