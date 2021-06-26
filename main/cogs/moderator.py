import asyncio
import typing

import discord
from discord.ext import commands


class Moderator(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.group(name="mod", invoke_without_command=True, case_insensitive=True)
    @commands.is_owner()
    async def mod(self, ctx):
        await ctx.send(embed=ctx.bot.help_command.get_command_help(ctx.command))

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
            self.bot.cache["premium_users"].add(target.id)
        else:
            msg = f"<:Boosters:814930829461553152> **{target.name}** got their premium removed. oof..."
            try:
                self.bot.cache["premium_users"].remove(target.id)
            except KeyError:
                msg = f"{target.name} is not premium!"

        await ctx.send(msg)

    @mod.command(name="edit")
    async def _edit_(
        self, ctx, action, user: typing.Union[discord.Member, discord.User], amount: int
    ):
        self.bot.cache["users"][user.id][action] += amount
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

def setup(bot):
    bot.add_cog(Moderator(bot))
