import asyncio
import collections
import datetime
import io
import math
import os
import textwrap
import traceback
import typing
from contextlib import redirect_stdout

import discord
import mystbin
import tabulate
import utils.json_loader
from discord.ext import commands
from jishaku.models import copy_context_with
from utils.chat_formatting import box, hyperlink
from utils.useful import Embed

CommandTask = collections.namedtuple("CommandTask", "index ctx task")


class admin(commands.Cog):
    """admin-only commands that make the bot dynamic."""

    def __init__(self, bot):
        self.bot = bot
        self._last_result = None
        self.sessions = set()
        self.task_count = 0
        self.tasks = collections.deque()

    @staticmethod
    def cleanup_code(content):
        """Automatically removes code blocks from the code."""

        if content.startswith("```") and content.endswith("```"):
            return "\n".join(content.split("\n")[1:-1])

        return content.strip("` \n")

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @staticmethod
    def clean_code(content):
        if content.startswith("```") and content.endswith("```"):
            return "\n".join(content.split("\n")[1:][:-3])

    @commands.group(name="mod", invoke_without_command=True, case_insensitive=True)
    @commands.is_owner()
    async def mod(self, ctx):
        cmd = self.bot.get_command("help")
        await ctx.invoke(cmd, command="mod")

    @mod.command(name="blacklist", hidden=True, aliases=["bl", "poo"])
    async def _blacklist(
        self,
        ctx,
        target: typing.Union[discord.User, discord.Guild],
        *,
        mode: str = "add",
    ):

        if mode != "remove" and mode != "add":
            return await ctx.send(
                f"{self.bot.redTick} Accepted values are `add/remove` for `mode`"
            )

        target_type = "user" if isinstance(target, discord.User) else "guild"

        blacklist = "TRUE" if mode == "add" else "FALSE"
        query = (
            "UPDATE users_data SET blacklisted = ? WHERE user_id = ?"
            if target_type == "user"
            else "UPDATE guild_config SET blacklisted = ? WHERE guild_id = ?"
        )

        cur = await self.bot.db.execute(query, (blacklist, target.id))
        if mode == "add":
            msg = f"**{target.name}** now got blacklisted! bad bad bad"
            self.bot.blacklist.add(target.id)
        else:
            msg = f"**{target.name}** now got unblacklisted! phew..."
            try:
                self.bot.blacklist.remove(target.id)
            except KeyError:
                msg = f"{target.name} is not blacklisted!"

        await ctx.send(msg)

    @mod.command(name="givepremium", hidden=True, aliases=["givep"])
    async def _givepremium(
        self,
        ctx,
        target: typing.Union[discord.User, discord.Guild],
        *,
        mode: str = "add",
    ):

        if mode != "remove" and mode != "add":
            return await ctx.send(
                f"{self.bot.redTick} Accepted values are `add/remove` for `mode`"
            )

        target_type = "user" if isinstance(target, discord.User) else "guild"

        premium = "TRUE" if mode == "add" else "FALSE"
        query = (
            "UPDATE users_data SET premium = ? WHERE user_id = ?"
            if target_type == "user"
            else "UPDATE guild_config SET premium = ? WHERE guild_id = ?"
        )

        cur = await self.bot.db.execute(query, (premium, target.id))
        if mode == "add":
            msg = f"<:Boosters:814930829461553152> **{target.name}** now got premium perks!"
            self.bot.premiums.add(target.id)
        else:
            msg = f"<:Boosters:814930829461553152> **{target.name}** got their premium removed. oof..."
            try:
                self.bot.premiums.remove(target.id)
            except KeyError:
                msg = f"{target.name} is not premium!"

        await ctx.send(msg)

    @mod.command(name="edit")
    async def _edit_(
        self, ctx, action, user: typing.Union[discord.Member, discord.User], amount: int
    ):
        self.bot.cached_users[user.id][action] += amount
        return await ctx.send(
            f"{self.bot.greenTick} Successfully gave {user.mention} {amount:,} `{action}`."
        )

    @mod.command(name="create")
    async def _create_item_for_shop(self, ctx):
        q = [
            "What should the item be called?",
            "What should it's price be?",
            "Write a brief description of the item.",
            "Write a long and detailed description of the item.",
            "Give it an ID.",
        ]

        a = []
        for question in q:
            question += "\nType `stop` to stop this process. Timeout is 300 seconds."
            await ctx.send(question)
            try:
                response = await self.bot.wait_for(
                    "message",
                    timeout=300,
                    check=lambda m: m.author == ctx.author and m.channel == ctx.channel,
                )
            except asyncio.TimeoutError:
                await ctx.reply("Okay, I'm leaving. Bye.")
            else:
                if response.content.lower() == "stop":
                    return await ctx.send("Terminated")
                a.append(response.content)

        query = """
                INSERT INTO item_info
                VALUES (?,?,?,?,?)
                """
        await self.bot.db.execute(query, (a[4], a[1], a[0], a[3], a[2]))
        await self.bot.db.commit()
        cmd = self.bot.get_command("shop")
        return await ctx.invoke(cmd, item=a[0])

    @mod.command(name="delete")
    async def _delete_item_from_shop(self, ctx, *, item):
        item = item.lower()
        query = """
                DELETE FROM item_info
                WHERE lower(item_name) = ?
                """
        await self.bot.db.execute(query, (item,))
        await self.bot.db.commit()
        return await ctx.send(f"{self.bot.greenTick} Deleted item `{item}` from shop.")

    @commands.group(invoke_without_command=True, case_insensitive=True)
    async def dev(self, ctx):
        return

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
            text = text.decode("ascii").replace(
                f"cd {str(__import__('pathlib').Path(self.bot.cwd).parent)};", ""
            )
        return text

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

    @dev.command(name="eval")
    async def _eval(self, ctx, *, code: str):
        """Evaluates a code"""

        env = {
            "bot": self.bot,
            "ctx": ctx,
            "channel": ctx.channel,
            "author": ctx.author,
            "guild": ctx.guild,
            "message": ctx.message,
            "_": self._last_result,
        }

        env.update(globals())

        code = self.cleanup_code(code)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(code, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            emb = Embed(title="", description="Evaluated your code", color=0x2F3136)
            emb.add_field(
                name="Output:", value=f"```py\n{e.__class__.__name__}: {e}\n```"
            )
            return await ctx.send(embed=emb)

        func = env["func"]
        try:
            with redirect_stdout(stdout):
                self.bot.ret = await func()
        except Exception:
            self.bot.value = stdout.getvalue()
            emb = Embed(title="", description="Evaluated your code", color=0x2F3136)
            emb.add_field(
                name="Output:",
                value=f"```py\n{self.bot.value}{traceback.format_exc()}\n```",
            )
            return await ctx.send(embed=emb)

        else:
            self.bot.value = stdout.getvalue()
            try:
                await ctx.message.add_reaction("\u2705")
            except:
                pass

            if self.bot.ret is None:
                if self.bot.value:
                    emb = Embed(
                        title="", description="Evaluated your code", color=0x2F3136
                    )
                    emb.add_field(name="Output:", value=f"```py\n{self.bot.value}\n```")
                    return await ctx.send(embed=emb)

            else:
                self._last_result = self.bot.ret
                emb = Embed(title="", description="Evaluated your code", color=0x2F3136)
                emb.add_field(
                    name="Output:", value=f"```py\n{self.bot.value}{self.bot.ret}\n```"
                )
                return await ctx.send(embed=emb)

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

        text = await self.git(ctx=ctx, arguments="pull", output=False)
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
                    name=f"{self.bot.greenTick} Cogs Reloading",
                    value="```diff\n+ All cogs were reloaded successfully```",
                )

                await ctx.reply(embed=em, mention_author=False)
            else:
                em = Embed(color=0xFFCC33)
                em.add_field(
                    name="<:idle:817035319165059102> **Failed to reload all cogs**",
                    value=fail,
                )
                await ctx.reply(
                    content=f"```\n{text}```", embed=em, mention_author=False
                )

        else:
            try:
                self.bot.reload_extension(f"cogs.{extension}")
                em = Embed(
                    description=f"{self.bot.greenTick} "
                    f"**Reloaded cogs.{extension}**",
                    color=0x3CA374,
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
    bot.add_cog(admin(bot))
