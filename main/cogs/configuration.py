import typing
import discord
from discord.ext import commands
from discord.ext.commands import guild_only, has_guild_permissions
from utils.useful import RoleConvert


class Configuration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="tips", usage="<on|off>", brief="Toggles tips on or off")
    async def _tips(self, ctx, *, mode: str):
        """
        Toggles tip to on or off, specified by the invoking user.
        If tips are on, you will see random messages including usefull fact/tip for the bot.
        """
        modus = mode.lower()
        if modus != "on" and modus != "off":
            raise discord.ext.commands.MissingRequiredArgument(ctx.command)

        modus = "TRUE" if modus == "on" else "FALSE"

        if modus == "TRUE":
            self.bot.cache["tips_are_on"].add(ctx.author.id)
        else:
            self.bot.cache["tips_are_on"].discard(ctx.author.id)

        query = "UPDATE users_data SET tips = ? WHERE user_id = ?"
        await self.bot.db.execute(query, (modus, ctx.author.id))
        await self.bot.db.commit()
        return await ctx.send(
            f"{self.bot.greenTick} Toggled your tips to `{mode.upper()}`"
        )

    @commands.group(
        invoke_without_command=False,
        case_insensitive=True,
        brief="Edit server settings",
    )
    @guild_only()
    @has_guild_permissions(manage_guild=True)
    async def config(self, ctx):
        """
        Configures settings for your server.
        Manage guild permission is needed to run this.
        """
        finder = await self.bot.db.execute(
            "SELECT * FROM guild_config WHERE guild_id=?", (ctx.guild.id,)
        )
        row = await finder.fetchone()
        if row is None:
            query = "INSERT INTO guild_config (guild_id) VALUES (?)"
            await self.bot.db.execute(query, (ctx.guild.id,))
            await ctx.send(
                f"Seems like you are new! I added this server ({ctx.guild.name}), to our database. Enjoy!"
            )

    @config.command(name="giveawaymanager", aliases=["gRole"])
    async def _grole(self, ctx, role: RoleConvert):
        """
        Sets the required role for starting giveaways to `role`
        """
        query = "INSERT INTO guild_config (guild_id, grole) VALUES (?, ?) ON CONFLICT (guild_id) DO UPDATE SET grole = ?"
        await self.bot.db.execute(query, (ctx.guild.id, role.id, role.id))
        await self.bot.db.commit()
        await ctx.send(f"The role required for giveaways is now set to **{role.name}**")

    @config.command(name="prefix", usage="<prefix>")
    async def _setprefix(self, ctx, *, prefix: str):
        """
        Changes the bot prefix for this guild.\n
        Only applicable if you are in a guild.
        """
        query = "INSERT INTO guild_config (guild_id, prefix) VALUES (?, ?) ON CONFLICT (guild_id) DO UPDATE SET prefix = ?"
        await self.bot.db.execute(query, (ctx.guild.id, prefix, prefix))
        await self.bot.db.commit()
        self.bot.cache["prefix"][ctx.guild.id] = prefix
        await ctx.send(
            f"The prefix has been set to `{prefix}`. To change the prefix again, use `{prefix}config prefix <prefix>`"
        )

    @commands.command(
        name="disable",
        brief="Disables a command for a server or channel",
        usage="[channel] <command>",
    )
    async def _disable(
        self, ctx, snowflake_id: typing.Optional[discord.TextChannel], *, command
    ):
        """
        You can use this command to disable a command for the server or channel.\n
        If no channel is given, it disables the command for the whole guild.
        """

        try:
            command = str(self.bot.get_command(command).name)
        except Exception:
            raise commands.BadArgument("That is not a valid command.")
        if snowflake_id is None:
            snowflake_id = ctx.guild
        query = "INSERT INTO disabled_commands VALUES (?, ?)"
        txt = (
            f" for {snowflake_id.mention}"
            if isinstance(snowflake_id, discord.TextChannel)
            else " for this server"
        )
        try:
            await self.bot.db.execute(query, (snowflake_id.id, command))
        except Exception:
            raise commands.BadArgument(
                f"{self.bot.redTick} That command is already disabled{txt}!"
            )
        else:
            await self.bot.db.commit()
            try:
                self.bot.cache["disabled_commands"][command].append(snowflake_id.id)
            except KeyError:
                self.bot.cache["disabled_commands"][command] = [ctx.guild.id]
            await ctx.send(f"{self.bot.greenTick} Disabled command `{command}`{txt}")

    @commands.command(
        name="enable",
        brief="Enables a disabled command for a server or channel",
        usage="[channel] <command>",
    )
    async def _enable(
        self, ctx, snowflake_id: typing.Optional[discord.TextChannel], *, command
    ):
        """
        You can use this command to enable a disabled command for the server or channel.\n
        If no channel is given, it enables the disabled for the whole guild.
        """
        try:
            command = self.bot.get_command(command).name
        except Exception:
            raise commands.BadArgument("That is not a valid command.")
        if snowflake_id is None:
            snowflake_id = ctx.guild

        txt = (
            f" for {snowflake_id.mention}"
            if isinstance(snowflake_id, discord.TextChannel)
            else " for this server"
        )
        cur = await self.bot.db.execute(
            "SELECT command_name FROM disabled_commands WHERE snowflake_id = ? AND command_name = ?",
            (snowflake_id.id, command),
        )
        row = await cur.fetchone()

        if row is None:
            raise commands.BadArgument(
                f"{self.bot.redTick} That command is not disabled{txt}!"
            )
        else:
            query = "DELETE FROM disabled_commands WHERE snowflake_id = ? AND command_name = ?"
            self.bot.cache["disabled_commands"][command].remove(snowflake_id.id)
            await self.bot.db.execute(query, (snowflake_id.id, command))
            await self.bot.db.commit()
            await ctx.send(f"{self.bot.greenTick} Enabled command `{command}`{txt}")


def setup(bot):
    bot.add_cog(Configuration(bot), category="Configuration")
