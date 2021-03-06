from utils._type import *

import datetime
import discord

from collections import Counter
from discord.ext import commands
from discord.ext.commands import BucketType
from dpymenus import Page, PaginatedMenu
from utils.chat_formatting import box
from utils.useful import Embed, MemberConvert, RoleConvert


class Moderation(commands.Shard):
    def __init__(self, cog: commands.Cog):
        super().__init__(cog)
        self.bot = cog.bot

    @commands.command(name="kick", brief="Kicks a member")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx: customContext, member: MemberConvert):
        """
        Kicks a member from the server.\n
        Member must be in the server at the moment of running the command
        """
        await member.kick()
        await ctx.send("kicked **" + member.display_name + "**")

    @commands.command(name="ban", brief="Bans a member", usage="<member> [reason]")
    @commands.has_permissions(ban_members=True)
    async def ban(
        self,
        ctx,
        member: Union[MemberConvert, discord.User],
        *,
        reason: str = "No reason provided.",
    ):
        """
        Bans an user from the server.\n
        Unlike kick, the user musn't be in the server.
        """
        reason += f"\nResponsible moderator: {ctx.author}"
        await ctx.guild.ban(member, reason=reason)
        await ctx.send("banned **" + member.display_name + "**")

    @commands.command(name="unban", brief="Unbans a user")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx: customContext, *, user_id: int):
        """
        Unbans an user from the server. (param)
        Raises an error if the user is not a previously banned member.
        """
        try:
            await ctx.guild.unban(discord.Object(id=user_id))
        except discord.NotFound:
            raise commands.BadArgument(f"`{user_id}` was not a previously banned member.")
        else:
            await ctx.send(f'Successfully unbanned `{user_id}`.')

    @commands.group()
    @commands.max_concurrency(1, BucketType.channel)
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx: customContext):
        """Removes messages that meet a criteria.
        In order to use this command, you must have Manage Messages permissions.
        Note that the bot needs Manage Messages as well.
        When the command is done doing its work, you will get a message
        detailing which users got removed and how many messages got removed.
        """

        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    async def do_removal(self, ctx, limit, predicate, *, before=None, after=None):
        if limit > 2000:
            return await ctx.send(f'Too many messages to search given ({limit}/2000)')

        if before is None:
            before = ctx.message
        else:
            before = discord.Object(id=before)

        if after is not None:
            after = discord.Object(id=after)

        try:
            deleted = await ctx.channel.purge(limit=limit, before=before, after=after, check=predicate)
        except discord.Forbidden as e:
            return await ctx.send('I do not have permissions to delete messages.')
        except discord.HTTPException as e:
            return await ctx.send(f'Error: {e} (try a smaller search?)')

        spammers = Counter(m.author.display_name for m in deleted)
        deleted = len(deleted)
        messages = [f'{deleted} message{" was" if deleted == 1 else "s were"} removed.']
        if deleted:
            messages.append('')
            spammers = sorted(spammers.items(), key=lambda t: t[1], reverse=True)
            messages.extend(f'**{name}**: {count}' for name, count in spammers)

        to_send = '\n'.join(messages)

        if len(to_send) > 2000:
            await ctx.send(f'Successfully removed {deleted} messages.', delete_after=10)
        else:
            await ctx.send(to_send, delete_after=10)

    @purge.command()
    async def embeds(self, ctx: customContext, search=100):
        """Removes messages that have embeds in them."""
        await self.do_removal(ctx, search, lambda e: len(e.embeds))

    @purge.command(aliases=['bot'])
    async def bots(self, ctx: customContext, search=100):
        """Removes messages that have embeds in them."""
        await self.do_removal(ctx, search, lambda e: e.author.bot)

    @purge.command()
    async def files(self, ctx: customContext, search=100):
        """Removes messages that have attachments in them."""
        await self.do_removal(ctx, search, lambda e: len(e.attachments))

    @purge.command()
    async def images(self, ctx: customContext, search=100):
        """Removes messages that have embeds or attachments."""
        await self.do_removal(ctx, search, lambda e: len(e.embeds) or len(e.attachments))

    @purge.command()
    async def reactions(self, ctx: customContext, search=100):
        """Removes messages that have a reaction"""
        await self.do_removal(ctx, search, lambda e: len(e.reactions))

    @purge.command(name='all')
    async def _remove_all(self, ctx: customContext, search=100):
        """Removes all messages except for the pinned ones."""
        await self.do_removal(ctx, search, lambda e: not e.pinned)


    @commands.command()
    async def cleanup(self, ctx: customContext):
        """
        Cleanup the bot's messages
        """
        after = discord.utils.utcnow() - datetime.timedelta(minutes=15)
        await self.do_removal(ctx, 100, lambda e: e.author == ctx.me, after=int(after.timestamp()))

    @commands.command(name="lock", brief="Locks a channel")
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx: customContext, channel: discord.TextChannel = None):
        """
        Sets the `send_messages` permission to False for everyone.\n
        If no channel is given, this defaults to the channel the command is run in.\n
        Note that moderator permissions may override it.
        """
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(f"{self.bot.icons['greenTick']} Locked down **{channel}**.")

    @commands.command(name="unlock", brief="Unlocks a channel")
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx: customContext, channel: discord.TextChannel = None):
        """
        Sets the `send_messages` permission to True for everyone.\n
        If no channel is given, this defaults to the channel the command is run in.
        """
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = True
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(f"{self.bot.icons['greenTick']} Unlocked **{channel}**.")

    @commands.command(
        name="slowmode", aliases=["sm"], brief="Changes the slowmode of the channel."
    )
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx: customContext, interval=None):
        """
        Sets the slowmode in the current channel to the given amount of time.\n
        If no time is given, this disables the current slowmode.\n
        Time must end on s | m | h | d and cannot contain multiple values, such as 1m1s.
        """
        if interval:

            def convert(time):
                pos = ["s", "m", "h", "d"]

                time_dict = {"s": 1, "m": 60, "h": 3600, "d": 3600 * 24}

                unit = time[-1]

                if unit not in pos:
                    raise commands.BadArgument(
                        f"{self.bot.icons['redTick']} Number must end on a `s, m, h`"
                    )
                try:
                    val = int(time[:-1])
                except Exception:
                    return -2

                return val * time_dict[unit]

            interval1 = convert(interval)
            if interval1 < 1:
                raise commands.BadArgument(
                    f"{self.bot.icons['redTick']} The interval should be a positive number."
                )
            if interval1 < 21601:
                await ctx.channel.edit(slowmode_delay=interval1)
                await ctx.send(f"Set slowmode to `{interval}`")
            else:
                await ctx.send(f"Slowmode should be less than or equal to **6h**")
        else:
            await ctx.channel.edit(slowmode_delay=0)
            await ctx.send(f"Removed the slowmode")

    @commands.command(
        name="permissions",
        aliases=["perms"],
        brief="Lists the permissions the bot has.",
    )
    async def _permissions(self, ctx: customContext):
        """
        Shows a list of permissions the bot has in the server,\n
        if any recommended permission are missing, this will also show up.
        Again, the permissions are _recommended_, not required.
        """
        permlist = []
        for perm in ctx.guild.me.guild_permissions:
            if perm[1] == True:
                permlist.append(perm[0])

        required = [
            "send_messages",
            "embed_links",
            "manage_messages",
            "ban_members",
            "kick_members",
            "add_reactions",
            "manage_nicknames",
            "external_emojis",
        ]
        for perm in permlist:
            if perm in required:
                required.remove(perm)

        em = Embed(description=", ".join(f"`{perms}`" for perms in permlist))
        em.add_field(
            name="Recommended permissions missing",
            value=", ".join(f"`{perms}`" for perms in required) or "None!",
        )
        em.set_author(name="List of permissions the bot has in this server")
        await ctx.send(embed=em)

    @commands.group(
        invoke_without_command=True, case_insensitive=True, usage="<member> <role>"
    )
    @commands.has_guild_permissions(manage_roles=True)
    async def role(self, ctx: customContext, member: discord.Member, *, role: RoleConvert):
        """
        Gives a role to a member.\n
        """
        if role in member.roles:
            await member.remove_roles(role)
            return await ctx.send(f"Removed **{role}** from **{member}**")
        await member.add_roles(role)
        await ctx.send(f"Added **{role}** to **{member}**")

    @role.command(name="info", brief="Shows information about a role")
    async def _info(self, ctx: customContext, *, role: RoleConvert = None):
        """Sends some information about a role."""
        if not role:
            return await ctx.reply("You need to give me a role!")

        member_preview = "\n".join(
            [
                f"{member.display_name} - {member.id}"
                for index, member in enumerate(role.members, 1)
                if index <= 10
            ]
        ) + (
            f"\nand {len(role.members) - 10} other members..."
            if len(role.members) > 5
            else ""
        )

        em = Page(
            colour=role.color,
            description=f"{role.mention}\nID - `{role.id}`\n"
            f"Color: {role.color}\n"
            "**Created at:** {}\n".format(
                role.created_at.strftime("%a, %b %d, %Y %H:%M %p")
            )
            + f"**Members**: {len(role.members)} | **Position**: {role.position}\n",
        )
        em.add_field(
            name="Role mentionable", value="Yes" if role.mentionable else "No"
        )
        em.set_author(name=f"{role.name}")
        em.set_footer(text="Basic Info -Page 1/3")

        emb = Page(colour=role.color)
        emb.add_field(
            name=f"Members [{len(role.members)}]", value=box(member_preview, "py")
        )
        emb.set_footer(text="Role Members - Page 2/3")

        permission_names = ", ".join(
            f"`{perm}`" for perm, value in role.permissions if value
        )
        emb1 = Page(colour=role.color)
        emb1.add_field(name=f"Role Permissions", value=f"{permission_names}")
        emb1.set_footer(text="Role Permissions - Page 3/3")

        menu = PaginatedMenu(ctx)
        menu.add_pages([em, emb, emb1])
        await menu.open()

def setup(cog):
    cog.add_shard(Moderation(cog))
