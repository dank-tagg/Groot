import asyncio
import collections
import datetime
import io
import math
import os
import pathlib
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
            f"cd {str(pathlib.Path(self.bot.cwd).parent)};git {arguments}"
        )
        if not isinstance(text, str):
            text = text.decode("ascii")
        return text.replace(f"cd {str(pathlib.Path(self.bot.cwd).parent)};", "")

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

    @dev.command(name="status")
    async def _set_status(self, ctx, *, status):
        data = utils.json_loader.read_json("status")
        data["groot"] = status
        utils.json_loader.write_json(data, "status")
        await ctx.send(f"Set status to {status}")

    @dev.command(name="eval", aliases=["run"])
    async def _eval(self, ctx, *, code: codeblock_converter):
        """Evaluates a code"""

        jsk = self.bot.get_command("jishaku py")
        return await jsk(ctx, argument=code)

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
        await ctx.send(embed=embed)

    @dev.command(name="inviteme")
    async def _inviteme(self, ctx, *, guildid: int):
        guild = self.bot.get_guild(guildid)
        await ctx.author.send(f"{await guild.text_channels[0].create_invite()}")

    @dev.command(name="restart")
    async def _restart(self, ctx):
        await self.git(arguments="pull")
        os._exit(0)

    @dev.command(name="sync")
    async def _sync(self, ctx):

        text = await self.git(arguments="pull")
        fail = ""

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

        if not fail:
            em = Embed(color=0x3CA374)
            em.add_field(name="Pulling from GitHub", value=text, inline=False)
            em.add_field(
                name=f"{self.bot.greenTick} Cogs Reloading",
                value="```diff\n+ All cogs were reloaded successfully```",
            )

            await ctx.reply(embed=em, mention_author=False)
        else:
            em = Embed(color=0xFFCC33)
            em.add_field(name="<:online:808613541774360576> Pulling from GitHub", value=text, inline=False)
            em.add_field(
                name="<:idle:817035319165059102> **Failed to reload all cogs**",
                value=fail,
            )
            try:
                await ctx.reply(embed=em, mention_author=False)
            except Exception:
                mystbin_client = mystbin.Client()
                paste = await mystbin_client.post(fail, syntax="python")
                await mystbin_client.close()
                await ctx.send(
                    f"Oops, an exception occured while handling an exception. Error was send here: {str(paste)}"
                )

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
        jsk = self.bot.get_command("jishaku py")
        await jsk(
            code="import imp\n" f"import {module}\n" f"print(imp.reload({module}))"
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
        for user in self.bot.cache["users"]:
            query = "UPDATE currency_data SET wallet = ?, bank = ?, max_bank = ?, boost = ?, exp = ?, lvl = ? WHERE user_id = ?"
            await self.bot.db.execute(
                query,
                (
                    self.bot.cache["users"][user]["wallet"],
                    self.bot.cache["users"][user]["bank"],
                    self.bot.cache["users"][user]["max_bank"],
                    round(self.bot.cache["users"][user]["boost"], 2),
                    self.bot.cache["users"][user]["exp"],
                    self.bot.cache["users"][user]["lvl"],
                    user,
                ),
            )

        await self.bot.db.commit()


def setup(bot):
    bot.add_cog(Developer(bot))
