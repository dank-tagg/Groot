from utils._type import *

import discord

from discord.ext import commands


class Moderator(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.group(name="mod", invoke_without_command=True, case_insensitive=True)
    @commands.is_owner()
    async def mod(self, ctx: customContext):
        await ctx.send(embed=ctx.bot.help_command.get_command_help(ctx.command))

    @mod.command(name="blacklist", hidden=True, aliases=["bl", "poo"])
    async def _blacklist(
        self,
        ctx,
        target: Union[discord.User, discord.Guild],
        *,
        mode: str = "add",
    ):
        """Blacklists a user or a guild."""

        if mode != "remove" and mode != "add":
            return await ctx.send(
                f"{self.bot.icons['redTick']} Accepted values are `add/remove` for `mode`"
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
            self.bot.cache["blacklisted_users"].add(target.id)
        else:
            msg = f"**{target.name}** now got unblacklisted! phew..."
            try:
                self.bot.cache["blacklisted_users"].remove(target.id)
            except KeyError:
                msg = f"{target.name} is not blacklisted!"

        await ctx.send(msg)

    @mod.command(name="givepremium", hidden=True, aliases=["givep"])
    async def _givepremium(
        self,
        ctx,
        target: Union[discord.User, discord.Guild],
        *,
        mode: str = "add",
    ):
        """Gives premium to a user or a guild."""

        if mode != "remove" and mode != "add":
            return await ctx.send(
                f"{self.bot.icons['redTick']} Accepted values are `add/remove` for `mode`"
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
            self.bot.cache["premium_users"].add(target.id)
        else:
            msg = f"<:Boosters:814930829461553152> **{target.name}** got their premium removed. oof..."
            try:
                self.bot.cache["premium_users"].remove(target.id)
            except KeyError:
                msg = f"{target.name} is not premium!"

        await ctx.send(msg)


def setup(bot):
    bot.add_cog(Moderator(bot))
