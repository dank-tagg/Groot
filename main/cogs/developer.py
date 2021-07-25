from utils._type import *

import asyncio
import datetime
import io
import os
import pathlib
import traceback
import discord
import mystbin
import contextlib
import tabulate

from discord.ext import commands
from jishaku.codeblocks import codeblock_converter
from utils.useful import Embed, pages, fuzzy
from utils.json import read_json, write_json

@pages()
async def show_result(self, menu, entry):
    return f"```\n{entry}```"

class Developer(commands.Cog):
    """dev-only commands that make the bot dynamic."""

    def __init__(self, bot):
        self.bot = bot

    # Rerun edited messages
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if not after.author == self.bot.owner:
            return
        await self.bot.process_commands(after)

    @staticmethod
    async def run_shell(code: str) -> bytes:
        proc = await asyncio.create_subprocess_shell(
            code, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()
        await asyncio.sleep(1.5)
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

    async def cog_check(self, ctx: customContext):
        return await self.bot.is_owner(ctx.author)

    @commands.group(invoke_without_command=True, case_insensitive=True)
    async def dev(self, ctx: customContext):
        """It literally returns and does nothing."""
        return

    @dev.command(name="update")
    async def _update(self, ctx: customContext, link: str, *, message: str):
        """Updates the bot."""
        await ctx.send("Are you sure you want update me? `(y/n)`")

        msg = await self.bot.wait_for(
            "message", timeout=10, check=lambda m: m.author == ctx.author
        )
        if msg.content.lower() == "y":
            async with ctx.typing():
                data = read_json("config")
                data["updates"]["date"] = str(discord.utils.utcnow())
                data["updates"]["message"] = message
                data["updates"]["link"] = link
                write_json(data, "config")
            await ctx.send("Done!")

    @dev.command(name="eval", aliases=["run"])
    async def _eval(self, ctx: customContext, *, code: codeblock_converter):
        """Evaluates a code"""

        jsk = self.bot.get_command("jishaku py")
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            await jsk(ctx, argument=code)
        
        stdout = f.getvalue()
        if stdout:
            await ctx.send(f"```ps\n[stdout] {stdout}```")

    @dev.command(name="inviteme")
    async def _inviteme(self, ctx: customContext, *, guildid: int):
        """Sends an invite to the channel the command was executed in."""
        guild = self.bot.get_guild(guildid)
        await ctx.author.send(f"{await guild.text_channels[0].create_invite()}")

    @dev.command(name="restart")
    async def _restart(self, ctx: customContext):
        """Restarts the bot."""
        # Stuff to do first before start
        async with ctx.processing(ctx, message="Restarting bot...") as process:
            await self.git(arguments="pull")
            await self.bot.db.commit()

        data = read_json("config")
        data['messages']['lastMessage'] = process.m.id
        data['messages']['lastChannel'] = process.m.channel.id
        write_json(data, "config")
        os._exit(0)

    @dev.command(name="sync")
    async def _sync(self, ctx: customContext):
        '''"Syncs" the bot by reloading all the cogs.'''

        text = await self.git(arguments="pull")
        fail = ""

        async with ctx.typing():
            for file in os.listdir(f"{self.bot.cwd}/cogs"):
                if file.endswith(".py") and file[:-3] not in self.bot.non_sync:
                    try:
                        self.bot.reload_extension(f"cogs.{file[:-3]}")
                    except discord.ext.commands.ExtensionNotLoaded as e:
                        fail += f"```diff\n- {e.name} is not loaded```"
                    except discord.ext.commands.ExtensionFailed as e:
                        exc_info = type(e), e.original, e.__traceback__
                        etype, value, trace = exc_info
                        traceback_content = "".join(
                            traceback.format_exception(etype, value, trace, 0)
                        ).replace("``", "`\u200b`")
                        fail += (
                            f"```diff\n- {e.name} failed to reload.```"
                            + f"```py\n{traceback_content}```"
                        )

        if not fail:
            em = Embed(color=0x3CA374)
            em.add_field(name=f"{self.bot.icons['online']} Pulling from GitHub", value=text, inline=False)
            em.add_field(
                name=f"{self.bot.icons['greenTick']} Cogs Reloading",
                value="```diff\n+ All cogs were reloaded successfully```",
            )

            await ctx.reply(embed=em, mention_author=False)
        else:
            em = Embed(color=0xFFCC33)
            em.add_field(name=f"{self.bot.icons['online']} Pulling from GitHub", value=text, inline=False)
            em.add_field(
                name=f"{self.bot.icons['idle']} **Failed to reload all cogs**",
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

    @dev.command(name="reload")
    async def _reload_ext(self, ctx: customContext, *, to_search: str):
        """Reloads a cog."""
        
        all_cogs = [cog.lower() for cog in self.bot.cogs]
        try:
            ext = fuzzy.finder(to_search, all_cogs, lazy=False)[0]
        except IndexError:
            await ctx.send(f'Could not find `{to_search}` with the fuzzy algorithm. Try again with a more specific name.')
            return

        async with ctx.processing(ctx, message="Reloading extension...", delete_after=True) as process:
            try:
                self.bot.reload_extension(f"cogs.{ext}")
            except commands.ExtensionNotLoaded:
                await ctx.send(f'`cogs.{ext}` is not loaded.')
                return
        await ctx.send(f"{self.bot.icons['greenTick']} Reloaded `cogs.{ext}` in {process.time * 1000:.2f} ms")

    @dev.command()
    async def sql(self, ctx: customContext, *, query: str):
        cur = await self.bot.db.execute(query)
        if cur.description:
            columns = [tuple[0] for tuple in cur.description]
        else:
            columns = "keys"
        thing = await cur.fetchall()
        if len(thing) == 0:
            return await ctx.message.add_reaction(f"{self.bot.icons['greenTick']}")
        thing = tabulate.tabulate(thing, headers=columns, tablefmt="psql")
        byte = io.BytesIO(str(thing).encode("utf-8"))
        return await ctx.send(file=discord.File(fp=byte, filename="table.txt"))

    @sql.error
    async def sql_error(self, ctx: customContext, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.message.add_reaction(f"{self.bot.icons['redTick']}")
            await ctx.send(str.capitalize(str(error.original)))

    @dev.command(name="git")
    async def _git(self, ctx: customContext, *, arguments):
        text = await self.git(arguments=arguments)
        await ctx.send(text or "No output.")

    @commands.command(name="delete", aliases=["del", "d"])
    async def delete_bot_message(self, ctx: customContext):
        """Deletes bot messages."""
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


def setup(bot):
    bot.add_cog(Developer(bot))
