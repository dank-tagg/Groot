import datetime as dt

import discord
import humanize
from discord.ext import commands, tasks
from utils.useful import Embed, Cooldown, send_traceback
from utils.json_loader import read_json


class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cache = {}
        self.cache_usage = {}
        self.loops.start()
        self.update_status.start()

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Error handles everything"""
        if ctx.command and ctx.command.has_error_handler(): return

        if isinstance(error, commands.CommandInvokeError):
            error = error.original
            if isinstance(error, discord.errors.Forbidden):
                try:
                    return await ctx.reply(
                        f"{self.bot.redTick} I am missing permissions to do that!"
                    )
                except discord.Forbidden:
                    return await ctx.author.send(
                        f"{self.bot.redTick} I am missing permissions to do that!"
                    )

        elif isinstance(error, commands.MaxConcurrencyReached):
            return await ctx.send(
                f"{self.bot.redTick} The maximum concurrency is already reached for `{ctx.command}` ({error.number}). Try again later."
            )
        elif isinstance(error, commands.CommandOnCooldown):
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
        elif isinstance(error, commands.MissingRequiredArgument):
            cmd = self.bot.get_command("help")
            return await ctx.invoke(cmd, command=f"{ctx.command}")
        elif isinstance(error, commands.BadArgument):
            return await ctx.send(str(error))
        elif isinstance(error, commands.MissingPermissions):
            return await ctx.send(
                f"{self.bot.redTick} You are missing the `{error.missing_perms[0]}` permission to do that!"
            )
        elif isinstance(error, commands.MemberNotFound):
            return await ctx.send(
                f"{self.bot.redTick} I couldn't find `{error.argument}`. Have you spelled their name correctly? Try mentioning them."
            )
        elif isinstance(error, commands.RoleNotFound):
            return await ctx.send(
                f"{self.bot.redTick} I couldn't find the role `{error.argument}`. Did you spell it correctly? Capitalization matters!"
            )
        elif isinstance(error, commands.CommandNotFound):
            return

        await send_traceback(
            self.bot.error_channel, 10, type(error), error, error.__traceback__
        )
        return

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        query_a = "INSERT INTO guilds VALUES (?)"
        await self.bot.db.execute(query_a, (guild.id,))
        query_b = "INSERT INTO guild_config (guild_id) VALUES (?)"
        await self.bot.db.execute(query_b, (guild.id,))
        await self.bot.db.commit()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        query_c = "DELETE FROM guilds WHERE guild_id = ?"
        await self.bot.db.execute(query_c, (guild.id,))
        await self.bot.db.commit()

    @commands.Cog.listener()
    async def on_command(self, ctx):
        try:
            self.cache[str(ctx.author.id)] += 1
            self.cache_usage[str(ctx.command.name)] += 1
        except Exception:
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

    @loops.before_loop
    async def before_loops(self):
        await self.bot.wait_until_ready()

    @tasks.loop(seconds=10)
    async def update_status(self):
        status = read_json('status')
        status_emojis = {
            'online': '<:online:808613541774360576>', 
            'offline': '<:offline:817034738014879845>', 
            'idle': '<:idle:817035319165059102>'
            }
        
        groot_status = f"{status_emojis[status.get('groot', 'offline')]} {str.title(status.get('groot', 'offline'))}"
        message = f"**BOT STATUS** \n\n {groot_status} | Groot\n\nRefreshes every second"
    
        em = Embed(
                description=message,
                timestamp=dt.datetime.utcnow()
            )
        em.set_footer(text="Last updated at")
    
        channel = self.bot.get_channel(846450009721012294)
        try:
            await  channel.last_message.edit(embed=em)
        except Exception as error:
            await send_traceback(
                        self.bot.error_channel, 10, type(error), error, error.__traceback__
                    )

    @update_status.before_loop
    async def before_status(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(Core(bot))
