from utils._type import *

import asyncio
import datetime
import random
import re
import string
import unicodedata
import discord
import humanize
import stringcase
import unidecode


from discord.ext import commands
from discord.ext.commands import BucketType, ColourConverter
from dpymenus import Page, PaginatedMenu
from utils.chat_formatting import box
from utils.useful import Embed, MemberConvert, RoleConvert, get_frozen


class Moderation(commands.Cog, description="Moderation commands"):
    def __init__(self, bot: GrootBot):
        self.bot = bot

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
        member: typing.Union[MemberConvert, discord.User],
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
    async def unban(self, ctx: customContext, *, member: discord.User):
        """
        Unbans an user from the server.
        Raises an error if the user is not a previously banned member.
        """
        banList = await ctx.guild.bans()
        for ban in banList:
            user = ban.user
            if user.id == member.id:
                await ctx.guild.unban(user)
                await ctx.send("unbanned **" + member.name + "**")
                return
        raise commands.BadArgument(
            "**" + member.name + "** was not a previously banned member."
        )

    @commands.command(usage="<amount> [user] [match]")
    @commands.max_concurrency(1, BucketType.channel, wait=False)
    @commands.has_permissions(manage_messages=True)
    async def purge(
        self,
        ctx,
        amount: int,
        user: typing.Optional[discord.Member] = None,
        *,
        matches=None,
    ):
        """
        Purges messages, searches the channel with the limit of `amount`.\n
        Optionally from `user` or contains `matches`.
        """
        pins = 0
        for msg in await ctx.channel.pins():
            pins += 1
        await ctx.message.delete()
        counter = 0
        async for msg in ctx.channel.history(limit=amount + pins):
            counter += 1
            if msg.pinned:
                counter += 1

        def check_msg(msg):
            if msg.id == ctx.message.id:
                return True
            if user is not None:
                if msg.author.id != user.id:
                    return False
            if matches is not None:
                if matches not in msg.content:
                    return False
            return not msg.pinned

        if amount > 1000:
            return await ctx.send(
                "You can not purge more than 1000 messages each time!"
            )
        amount = await ctx.channel.purge(limit=amount, check=check_msg)
        if amount == 0:
            return await ctx.send("There are no messages that I can delete!")
        await ctx.send(
            f"{len(amount)} messages have been purged by {ctx.author.mention}",
            delete_after=3,
        )

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

    def strip_accs(self, text):
        try:
            text = unicodedata.normalize("NFKC", text)
            text = unicodedata.normalize("NFD", text)
            text = unidecode.unidecode(text)
            text = text.encode("ascii", "ignore")
            text = text.decode("utf-8")
        except Exception as e:
            raise e
        return str(text)

    def is_cancerous(self, text: str) -> bool:
        for segment in text.split():
            for char in segment:
                if not (char.isascii() and char.isalnum()):
                    return True
        return False

    @commands.command(name="decancer", aliases=["dc"], usage="<member>")
    @commands.has_permissions(manage_nicknames=True)
    async def decancer(self, ctx: customContext, target: MemberConvert):
        """
        Decancers the given member's nickname.\n
        This means that it removes all _cancerous_ characters,\n
        such as Zalgo.
        """
        if self.is_cancerous(target.display_name) == True:
            display = target.display_name
            nick = await self.nick_maker(ctx.guild, target.display_name)
            await target.edit(nick=nick)
            await ctx.send(
                f"**{display}** was now changed to **{nick}**",
                allowed_mentions=discord.AllowedMentions.none(),
            )

        else:
            await ctx.send("Member is already decancered")

    async def nick_maker(self, guild: discord.Guild, old_shit_nick):
        old_shit_nick = self.strip_accs(old_shit_nick)
        new_cool_nick = re.sub("[^a-zA-Z0-9 \n.]", "", old_shit_nick)
        new_cool_nick = " ".join(new_cool_nick.split())
        new_cool_nick = stringcase.lowercase(new_cool_nick)
        new_cool_nick = stringcase.titlecase(new_cool_nick)
        default_name = "Moderated Nickname " + "".join(
            random.choices(string.ascii_uppercase + string.digits, k=6)
        )
        if len(new_cool_nick.replace(" ", "")) <= 1 or len(new_cool_nick) > 32:
            if default_name:
                new_cool_nick = default_name
            else:
                new_cool_nick = "simp name"
        return new_cool_nick

    @commands.max_concurrency(1, commands.BucketType.guild, wait=False)
    @commands.has_permissions(manage_nicknames=True)
    @commands.guild_only()
    @commands.command(
        cooldown_after_parsing=True, brief="Decancers all members in the given role."
    )
    async def dehoist(self, ctx: customContext, *, role: RoleConvert = None):
        """
        Decancers all members of the targeted role.
        Role defaults to all members of the server.
        This is the same as `decancer`, but is run for every member in the given role.
        """
        role = role or ctx.guild.default_role
        guild = ctx.guild
        cancerous_list = [
            member
            for member in role.members
            if not member.bot
            and self.is_cancerous(member.display_name)
            and ctx.me.top_role > member.top_role
        ]
        if not cancerous_list:
            await ctx.send(f"There's no one I can decancer in **`{role}`**.")
            ctx.command.reset_cooldown(ctx)
            return
        if len(cancerous_list) > 5000:
            await ctx.send(
                "There are too many members to decancer in the targeted role. "
                "Please select a role with less than 5000 members."
            )
            ctx.command.reset_cooldown(ctx)
            return
        member_preview = "\n".join(
            [
                f"{member} - {member.id}"
                for index, member in enumerate(cancerous_list, 1)
                if index <= 10
            ]
        ) + (
            f"\nand {len(cancerous_list) - 10} other members.."
            if len(cancerous_list) > 10
            else ""
        )
        case = "" if len(cancerous_list) == 1 else "s"
        msg = await ctx.send(
            f"Are you sure you want me to decancer the following {len(cancerous_list)} member{case}?`(y/n)`\n\n"
            + box(member_preview, "py")
        )

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=60)
        except asyncio.TimeoutError:
            await ctx.send("Action cancelled.")
            ctx.command.reset_cooldown(ctx)
            return

        if msg.content.lower() == "y":
            await ctx.send(
                f"Ok. This will take around **{humanize.naturaldelta(datetime.timedelta(seconds=len(cancerous_list) * 1.5))}**."
            )
            async with ctx.typing():
                for member in cancerous_list:
                    await asyncio.sleep(1)
                    old_nick = member.display_name
                    new_cool_nick = await self.nick_maker(guild, member.display_name)
                    if old_nick.lower() != new_cool_nick.lower():
                        try:
                            await member.edit(
                                reason=f"Dehoist | Old name ({old_nick}): contained special characters",
                                nick=new_cool_nick,
                            )
                        except discord.Forbidden:
                            await ctx.send("Dehoist failed due to invalid permissions.")
                            return
                        except discord.NotFound:
                            continue
            try:
                await ctx.send("Dehoist completed.")
            except (discord.NotFound, discord.Forbidden):
                pass
        else:
            await ctx.send("Action cancelled.")
            ctx.command.reset_cooldown(ctx)
            return

    @commands.command(brief="Freeze a member's nickname")
    @commands.has_guild_permissions(manage_nicknames=True)
    async def freezenick(self, ctx: customContext, member: MemberConvert, *, nickname: str):
        """
        Freeze a member's nickname.\n
        This means that when the frozen member changes their nickname,\n
        this changes back to the nickname given.
        """

        cur = await self.bot.db.execute(
            "SELECT * FROM frozen_names WHERE guild_id = ? AND user_id = ?",
            (ctx.guild.id, member.id),
        )
        finder = await cur.fetchall()

        if finder:
            return await ctx.send("Member is already frozen. Unfreeze them first.")

        valid_nick_check = None if len(nickname) > 32 else True
        if not valid_nick_check:
            await ctx.message.add_reaction(f"{self.bot.icons['redTick']}")
            return await ctx.send(
                "That nickname is too long. Keep it under 32 characters, please"
            )

        try:
            await member.edit(nick=nickname)
            await self.bot.db.execute(
                "INSERT INTO frozen_names VALUES (?,?,?)",
                (ctx.guild.id, member.id, nickname),
            )
            await ctx.message.add_reaction(f"{self.bot.icons['greenTick']}")

        except discord.errors.Forbidden:
            await ctx.send("Missing permissions.")

    @commands.command(brief="Unfreezes a member's nickname.")
    @commands.has_guild_permissions(manage_nicknames=True)
    async def unfreezenick(self, ctx: customContext, member: MemberConvert):
        """
        Removes a freezenick from the member given.\n
        If the member is not freezed, this raises an error.
        """
        cur = await self.bot.db.execute(
            "SELECT * FROM frozen_names WHERE guild_id = ? AND user_id = ?",
            (ctx.guild.id, member.id),
        )
        finder = await cur.fetchall()

        if finder:
            cur = await self.bot.db.execute(
                "DELETE FROM frozen_names WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, member.id),
            )
            return await ctx.send(f"Unfroze member **{member.name}**")
        else:
            raise commands.BadArgument("Member is not frozen")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.nick != after.nick:
            frozen = await get_frozen(self, after.guild, after)
            if frozen:
                try:
                    await after.edit(nick=frozen[0][2], reason="Nickname frozen.")
                except discord.Forbidden:
                    await self.bot.db.execute(
                        "DELETE FROM frozen_names WHERE guild_id = ? AND user_id = ?",
                        (after.guild.id, after.id),
                    )
                    pass

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
            value=", ".join(f"`{perms}`" for perms in required),
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
    async def _info(self, ctx: customContext, role: RoleConvert = None):
        if role == None:
            return await ctx.reply(
                "You need to give me a role id!", mention_author=False
            )
        else:
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

    @role.command(name="create", usage="<name> <color> [...]")
    @commands.has_permissions(manage_roles=True)
    async def _create(self, ctx: customContext, name: str, color, hoist=False, mentionable=False):
        """
        **Optional Parameters:**
        __hoist__ (`bool`) – Indicates if the role should be shown separately in the member list. Defaults to `False`

        __mentionable__ (`bool`) – Indicates if the role should be mentionable by others. Defaults to `False`

        **Full example:** `role create RoleName #FFEEFF True False`
        """
        color = await ColourConverter().convert(ctx, color)
        role = await ctx.guild.create_role(
            name=name, color=color, permissions=0, hoist=hoist, mentionable=mentionable
        )
        em = Embed(
            colour=role.color,
            description=f"{role.mention}\nID - `{role.id}`\n"
            f"Color: {role.color}\n"
            "**Created at:** {}\n".format(
                role.created_at.strftime("%a, %b %d, %Y %H:%M %p")
            )
            + f"**Members**: {len(role.members)} | **Position**: {role.position}\n",
        )
        em.add_field(name="Role mentionable", value="Yes" if role.mentionable else "No")
        em.set_author(name=f"Created role {role.name}")
        em.set_footer(text="Basic Info")
        await ctx.reply(embed=em)


def setup(bot):
    bot.add_cog(Moderation(bot), category="Moderation")
