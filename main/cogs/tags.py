from __future__ import annotations
import typing
if typing.TYPE_CHECKING:
    from utils._type import *

import re
import sqlite3
import time

from discord.ext import commands


class Tags(commands.Cog):
    def __init__(self, bot: GrootBot):
        self.bot = bot

    @commands.group(invoke_without_command=True, case_insensitive=True)
    async def tag(self, ctx: customContext, tag):
        tag = tag.lower()

        query = "SELECT tag_content FROM tags WHERE tag_guild_id = ? AND tag_name = ?"
        cur = await self.bot.db.execute(query, (ctx.guild.id, tag))
        row = await cur.fetchone()

        if not row:
            cur = await self.bot.db.execute(
                "SELECT tag_name FROM tags WHERE tag_guild_id = ? AND tag_name LIKE ?",
                (ctx.guild.id, f"%{tag}%"),
            )
            row = await cur.fetchall()
            if not row:
                return await ctx.send("Tag not found.")
            else:
                names = "\n".join(r[0] for r in row)
                return await ctx.send(f"Tag not found. Did you mean...\n{names}")

        await ctx.send(row[0])

    async def convert_tag(self, ctx: customContext, tag, content):

        tag = tag.lower()
        if re.match(r"<[#@](!?&)(\d+)>", tag):
            raise commands.BadArgument(
                f"{self.bot.icons['redTick']} The tag name cannot be a mention!"
            )
        first_word = tag.partition(" ")[0]
        root = self.bot.get_command("tag")
        if first_word in root.all_commands:
            raise commands.BadArgument(
                f"{self.bot.icons['redTick']} This tag name starts with a reserved word."
            )

        elif len(tag) > 32 or len(content) > 2000:
            raise commands.BadArgument(
                f"{self.bot.icons['redTick']} There are limits for tag name `(32 letters)` and content `(2000 letters)`!"
            )

        else:
            return (
                await commands.clean_content().convert(ctx, tag),
                await commands.clean_content().convert(ctx, content),
            )

    @tag.command()
    async def create(self, ctx: customContext, tag, content):
        """Creates a new tag owned by you.
        This tag is server-specific and cannot be used in other servers.
        Note that server moderators can delete your tag.
        """
        tag, content = await self.convert_tag(ctx, tag, content)

        query = "INSERT INTO tags (tag_guild_id,tag_name,tag_content,tag_author,tag_uses,tag_creation_date) VALUES (?, ?, ?, ?, ?, ?)"
        try:
            cur = await self.bot.db.execute(
                query, (ctx.guild.id, tag, content, ctx.author.id, 0, time.time())
            )
        except sqlite3.IntegrityError:
            await ctx.send(f"{self.bot.icons['redTick']} That tag already exists!")
        else:
            await self.bot.db.commit()
            return await ctx.send(
                f"{self.bot.icons['greenTick']} Done! Created tag **{tag}**. `{await self.bot.get_prefix(ctx.message)}tag {tag}`"
            )

    @tag.command()
    async def delete(self, ctx: customContext, tag):

        tag = tag.lower()
        query = "SELECT tag_author FROM tags WHERE tag_name = ? AND tag_guild_id = ?"
        cur = await self.bot.db.execute(query, (tag, ctx.guild.id))
        data = await cur.fetchone()
        if data is None:
            return await ctx.send(f"{self.bot.icons['redTick']} No tag is found called `{tag}`.")

        bypass_owner_check = (
            ctx.author.id == self.bot.owner_id
            or ctx.author.guild_permissions.manage_messages
        )

        if not bypass_owner_check and ctx.author.id != data[0]:
            return await ctx.send(
                f"{self.bot.icons['redTick']} You are not the owner of tag `{tag}`."
            )

        query = "DELETE FROM tags WHERE tag_name = ? AND tag_guild_id = ?"
        cur = await self.bot.db.execute(query, (tag, ctx.guild.id))
        await self.bot.db.commit()
        return await ctx.send(f"{self.bot.icons['greenTick']} Deleted tag `{tag}`.")


def setup(bot):
    bot.add_cog(Tags(bot), category="Utilities")
