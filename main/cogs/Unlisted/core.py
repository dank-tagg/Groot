from utils._type import *

import datetime as dt
import traceback
import discord
import humanize
import re

from discord.ext import commands, tasks
from utils.useful import Embed, Cooldown
from cogs.Fun.games import GameExit

class Core(commands.Shard):
    def __init__(self, cog: commands.Cog):
        super().__init__(cog)
        self.bot = cog.bot
        self.cache = {}
        self.cache_usage = {}
        self.loops.start()

    async def send_error(self, ctx: customContext, exc_info: dict):
        em = Embed(
            title=f"{self.bot.icons['redTick']} Error while running command {exc_info['command']}",
            description=f"```py\n{exc_info['short']}```[Report error](https://discord.gg/nUUJPgemFE)"
        )
        em.set_footer(text="Please report this error in our support server if it persists.")
        await ctx.send(embed=em)

    async def handle_error(self, ctx: customContext, exc_info: dict):
        # Shortcut if the invoking user was the bot owner
        if ctx.author == self.bot.owner:
            await self.send_error(ctx, exc_info)
            return

        traceback = exc_info['error'].replace('``', '`\u200b`')

        paginator = commands.Paginator(prefix='```py')
        for line in traceback.split('\n'):
            paginator.add_line(line)

        await self.bot.log_channel.send(f"**Command:** {ctx.message.content}\n" \
                                        f"**Message ID:** `{ctx.message.id}`\n" \
                                        f"**Author:** `{ctx.author}`\n" \
                                        f"**Guild:** `{ctx.guild}`\n" \
                                        f"**Channel:** `{ctx.channel}`\n" \
                                        f"**Jump:** {ctx.message.jump_url}"
        )
        for page in paginator.pages:
            await self.bot.log_channel.send(page)

        await self.send_error(ctx, exc_info)



    @commands.Cog.listener()
    async def on_command_error(self, ctx: customContext, error):
        """Error handles everything"""

        # Returns if the command has a local handler. Look into this later if it sends uncaught exceptions.
        if ctx.command and ctx.command.has_error_handler():
            return

        if isinstance(error, commands.CommandInvokeError):
            error = error.original

            if isinstance(error, discord.errors.Forbidden):
                try:
                    return await ctx.reply(
                        f"{self.bot.icons['redTick']} I am missing permissions to do that!"
                    )
                except discord.Forbidden:
                    return await ctx.author.send(
                        f"{self.bot.icons['redTick']} I am missing permissions to do that!"
                    )

            elif isinstance(error, GameExit):
                await ctx.send(f'The game was ended {ctx.author.mention}.')
                return

        # Cooldowns
        elif isinstance(error, commands.MaxConcurrencyReached):
            return await ctx.send(
                f"{self.bot.icons['redTick']} The maximum concurrency is already reached for `{ctx.command}` ({error.number}). Try again later."
            )

        elif isinstance(error, commands.CommandOnCooldown): # rework this embed?
            command = ctx.command
            default = discord.utils.find(
                lambda c: isinstance(c, Cooldown), command.checks
            ).default_mapping._cooldown.per
            altered = discord.utils.find(
                lambda c: isinstance(c, Cooldown), command.checks
            ).altered_mapping._cooldown.per
            cooldowns = f""
            if default is not None and altered is not None:
                cooldowns += (
                    f"\n\n**Cooldowns:**\nDefault: `{default}s`\nPremium: `{altered}s`"
                )
            em = Embed(
                description=f"You are on cooldown! Try again in **{humanize.precisedelta(dt.timedelta(seconds=error.retry_after), format='%.0f' if error.retry_after > 1 else '%.1f')}**"
                + cooldowns
            )
            return await ctx.send(embed=em)

        # Bad arguments
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=ctx.bot.help_command.get_command_help(ctx.command))
            return

        elif isinstance(error, commands.BadArgument):
            # If it is flag related
            if isinstance(error, commands.TooManyFlags):
                await ctx.reply(f'The flag `{error.flag.name}` has received {len(error.values)} arguments, but expected {error.flag.max_args}.')
                return
            # Everything else (MissingRequiredFlag ...)
            elif isinstance(error, commands.FlagError):
                await ctx.send_help(ctx.command)
                return

            await ctx.reply(str(error))
            return

        elif isinstance(error, commands.BadUnionArgument):
            await ctx.send_help(ctx.command)
            return

        elif isinstance(error, commands.TooManyArguments):
            return

        # Not found (member, role, command)
        elif isinstance(error, commands.MemberNotFound):
            return await ctx.send(
                f"{self.bot.icons['redTick']} I couldn't find `{error.argument}`. Have you spelled their name correctly? Try mentioning them."
            )

        elif isinstance(error, commands.RoleNotFound):
            return await ctx.send(
                f"{self.bot.icons['redTick']} I couldn't find the role `{error.argument}`. Did you spell it correctly? Capitalization matters!"
            )

        elif isinstance(error, commands.CommandNotFound):
            return

        # Permissions (whether author can run this command or not)
        elif isinstance(error, commands.MissingPermissions):
            return await ctx.send(
                f"{self.bot.icons['redTick']} You are missing the `{error.missing_permissions[0]}` permission to do that!"
            )

        elif isinstance(error, commands.NSFWChannelRequired):
            await ctx.send('Oops! This command is marked NSFW. Use this in a NSFW channel.')
            return

        elif isinstance(error, commands.CheckFailure):
            await ctx.send("You do not have permissions to use this command!")
            return



        # Catch uncaught errors
        exc_info = {
            "command": ctx.command,
            "error": "".join(traceback.format_exception(type(error), error, error.__traceback__, 2)).replace("``", "`\u200b`"),
            "short": "".join(traceback.format_exception(type(error), error, error.__traceback__, 0)).replace("``", "`\u200b`"),
        }

        await self.handle_error(ctx, exc_info)
        self.bot.logger.exception(exc_info['error'])

    @commands.Cog.listener()
    async def on_message(self, message):
        if re.fullmatch("<@(!)?812395879146717214>", message.content):
            await message.channel.send(f"My prefix(es) for **{message.guild.name}** are `{await self.bot.get_prefix(message)}`")
            return
        elif re.fullmatch("<@(!)?812395879146717214> help", message.content):
            await (await self.bot.get_context(message)).send_help()
            return

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        self.bot.logger.info(f'Joined guild {guild.name}')
        query_a = "INSERT INTO guilds VALUES (?)"
        await self.bot.db.execute(query_a, (guild.id,))
        query_b = "INSERT INTO guild_config (guild_id) VALUES (?)"
        await self.bot.db.execute(query_b, (guild.id,))

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        self.bot.logger.info(f'Left guild {guild.name}')
        query_c = "DELETE FROM guilds WHERE guild_id = ?"
        await self.bot.db.execute(query_c, (guild.id,))

    @commands.Cog.listener()
    async def on_command(self, ctx: customContext):
        try:
            self.cache[str(ctx.author.id)] += 1
            self.cache_usage[str(ctx.command.name)] += 1
        except KeyError:
            self.cache[str(ctx.author.id)] = 1
            self.cache_usage[str(ctx.command.name)] = 1

    @tasks.loop(minutes=1)
    async def loops(self):

        await self.bot.change_presence(
            activity=discord.Activity(
                type=0,
                name=f"g.help | {len(self.bot.users)} users | {len(self.bot.guilds)} guilds.",
            )
        )

        for item in self.cache:
            query_user_data = """
                              INSERT INTO users_data (user_id, commands_ran)
                              VALUES ((?), ?)
                              ON CONFLICT(user_id) DO UPDATE SET commands_ran = commands_ran+?
                              """
            await self.bot.db.execute(
                query_user_data, (int(item), self.cache[item], self.cache[item])
            )
        self.cache = {}

        for item in self.cache_usage:
            query = """
                    INSERT INTO usage (command, counter)
                    VALUES ((?), ?)
                    ON CONFLICT(command) DO UPDATE SET counter = counter+?
                    """

            await self.bot.db.execute(
                query, (str(item), self.cache_usage[item], self.cache_usage[item])
            )

        self.cache_usage = {}


    @loops.before_loop
    async def before_loops(self):
        await self.bot.wait_until_ready()


def setup(cog):
    cog.add_shard(Core(cog))
