from __future__ import annotations
import typing
if typing.TYPE_CHECKING:
    from utils._type import *

import asyncio
import datetime
import random
import discord
import json

from discord.ext import commands
from humanize.time import precisedelta
from PIL import Image, ImageDraw, ImageFont
from typing import Union
from utils.useful import Embed, detect, get_grole
from wonderwords import RandomSentence, RandomWord


class Utilities(commands.Cog, description="Handy dandy utils"):
    def __init__(self, bot: GrootBot):
        self.bot = bot
        self.index = 0
        self.snipe_cache = {}
        self.esnipe_cache = {}

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot:
            return
        self.esnipe_cache[before.channel.id] = {}
        self.esnipe_cache[before.channel.id]["before"] = [before.content, before.author]
        self.esnipe_cache[before.channel.id]["after"] = [after.content, after.author]
        await asyncio.sleep(60)
        self.esnipe_cache.pop(before.channel.id, None)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        self.snipe_cache[message.channel.id] = [message.content, message.author]
        await asyncio.sleep(60)
        self.snipe_cache.pop(message.channel.id, None)

    @commands.command(name="snipe", brief="Retrieves a recent deleted message")
    async def snipe(self, ctx: customContext):
        """
        Acts like a message log, but for channel specific and command only.\n
        Only returns the most recent message.
        A bot's deleted message is ignored.
        """
        channel = ctx.channel
        author = ctx.author
        try:
            em = Embed(
                name=f"Last deleted message in #{channel.name}",
                description=self.snipe_cache[channel.id][0],
                timestamp=datetime.datetime.utcnow(),
                colour=discord.Color.random(),
            )
            em.set_author(
                name=f"{self.snipe_cache[channel.id][1]}",
                icon_url=f"{self.snipe_cache[channel.id][1].avatar_url}",
            )
            em.set_footer(text=f"Sniped by: {author}")
            return await ctx.send(embed=em)
        except KeyError:
            return await ctx.send("There's nothing to snipe!")

    @commands.command(name="editsnipe", brief="Retrieves a recently edited message")
    async def editsnipe(self, ctx: customContext):
        """
        Same as `snipe`, but for edited messages.
        A bot's edited message is ignored.
        """
        channel = ctx.channel
        author = ctx.author
        try:
            em = Embed(
                name=f"Last edited message in #{channel.name}",
                description="**Before:**\n"
                f"+ {self.esnipe_cache[channel.id]['before'][0]}\n"
                f"\n**After:**\n- {self.esnipe_cache[channel.id]['after'][0]}",
                timestamp=datetime.datetime.utcnow(),
                colour=discord.Color.random(),
            )
            em.set_author(
                name=f"{self.esnipe_cache[channel.id]['before'][1]}",
                icon_url=f"{self.esnipe_cache[channel.id]['before'][1].avatar_url}",
            )

            em.set_footer(text=f"Sniped by: {author}")
            return await ctx.send(embed=em)
        except KeyError:
            return await ctx.send("There's nothing to snipe!")

    @commands.command(name="choose")
    async def choose(self, ctx: customContext, *, choice):
        choicelist = choice.split(" ")
        await ctx.send(random.choice(choicelist))

    def convert(self, time):
        pos = ["s", "m", "h", "d"]

        time_dict = {"s": 1, "m": 60, "h": 3600, "d": 3600 * 24}

        unit = time[-1]
        if unit not in pos:
            return -1
        try:
            val = int(time[:-1])
        except Exception:
            return -2

        return val * time_dict[unit]

    @commands.command(name="gstart", brief="Starts a giveaway")
    @commands.max_concurrency(5, commands.BucketType.channel, wait=False)
    async def gstart(self, ctx: customContext, time, winners: str, *, prize):
        """
        For this to work, the user has to have the giveaway role for the current server.\n
        Starts a giveaway, with given time, amount of winners and prize.\n
        A full example: `gstart` `10s` `1w` `Discord Nitro`
        """

        grole = ctx.guild.get_role(await get_grole(self, ctx))
        if grole is None:
            return await ctx.send(
                f"You've not set up a giveaway role for this server! Please do so with `{ctx.prefix}config grole <role>`"
            )
        if grole not in ctx.author.roles:
            return await ctx.send(
                f"{self.bot.icons['redTick']} You do not have the role `{grole.name}` that is required to start a giveaway!"
            )

        authorURL = ctx.author.avatar_url
        winners = int(winners.replace("w", ""))
        if winners > 30 or winners < 1:
            raise commands.BadArgument(
                f"{self.bot.icons['redTick']} Max. winners is 30, min. is 1"
            )

        if "s" in time:
            if int(time.replace("s", "")) < 3:
                raise commands.BadArgument(f"Minimum time is 3s")

        plural = "winners" if winners != 1 else "winner"
        plural1 = "Winners" if winners != 1 else "Winner"
        channel = ctx.channel
        guild = ctx.guild
        time1 = self.convert(time)
        if time1 > 86400:
            return await ctx.send("Max time is `1d`")
        delta = datetime.timedelta(seconds=time1)
        timeconverter = precisedelta(
            delta, minimum_unit="seconds", suppress=["microseconds"]
        )
        randomcolour = discord.Color.random()
        current_time = datetime.datetime.utcnow()
        time_added = datetime.timedelta(seconds=time1)
        future_time = current_time + time_added
        embed = Embed(
            title=f"{prize}",
            description=f"React with <a:party_tada:809202936600199209> to enter!\nEnds in **{timeconverter}**\nHosted by {ctx.author.mention}",
            timestamp=future_time,
            color=randomcolour,
        )
        embed.set_footer(text=f"{winners} {plural} | Ends at ")
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("<a:party_tada:809202936600199209>")
        while True:
            time1 -= 1
            delta = datetime.timedelta(seconds=time1)
            timeconverter = precisedelta(
                delta, minimum_unit="seconds", suppress=["microseconds"]
            )
            if time1 == 0:
                new_msg = await channel.fetch_message(msg.id)
                users = await new_msg.reactions[0].users().flatten()
                reactioncount = len(await new_msg.reactions[0].users().flatten()) - 1
                users.pop(users.index(self.bot.user))

                try:
                    winnerstr = []
                    if reactioncount < winners:
                        winners = reactioncount
                    for _ in range(winners):
                        winner = random.choice(users)
                        users.pop(users.index(winner))
                        await ctx.guild.fetch_member(winner.id)
                        emb = Embed(
                            title="You won!",
                            description=f"You have won the giveaway for [{prize}]({msg.jump_url}) in **{guild}** - {channel.mention}",
                            colour=discord.Color(0x4CAF50),
                        )
                        emb.set_footer(text="🎉 Congratulations!")
                        await winner.send(embed=emb)
                        winnerstr.append(winner.id)

                    if winnerstr == []:
                        em = Embed(
                            title=f"{prize}",
                            description=f"Could not determine a winner\nHosted by {ctx.author.mention}",
                            timestamp=future_time,
                            color=discord.Color(0x2F3136),
                        )
                        em.set_footer(text=f"{winners}w | Ended at ")
                        em.set_author(
                            name="This giveaway has ended", icon_url=f"{authorURL}"
                        )
                        await msg.edit(embed=em)
                    else:
                        await ctx.send(
                            ", ".join(
                                f"<@{users}>" for i, users in enumerate(winnerstr)
                            )
                            + f" has won the giveaway for **{prize}**\n{msg.jump_url}"
                        )
                        em = Embed(
                            title=f"{prize}",
                            description=f"{plural1} "
                            + ", ".join(
                                f"<@{users}>" for i, users in enumerate(winnerstr)
                            )
                            + f"\nHosted by {ctx.author.mention}",
                            timestamp=future_time,
                            color=discord.Color(0x2F3136),
                        )
                        em.set_footer(text=f"{winners}w | Ended at ")
                        em.set_author(
                            name="This giveaway has ended", icon_url=f"{authorURL}"
                        )
                        await msg.edit(embed=em)
                        emb1 = Embed(
                            title=f"Your giveaway has ended!",
                            url=msg.jump_url,
                            description=f"[__**Desktop Friendly URL**__]({msg.jump_url})\nYou have **{winners} {plural}**\n"
                            + "\n".join(
                                f"`{i + 1}` <@{users}> - [{users}]"
                                for i, users in enumerate(winnerstr)
                            ),
                            colour=discord.Color(0xFFF857),
                        )
                        await ctx.author.send(embed=emb1)

                except Exception:
                    em = Embed(
                        title=f"{prize}",
                        description=f"Could not determine a winner\nHosted by {ctx.author.mention}",
                        timestamp=future_time,
                        color=discord.Color(0x2F3136),
                    )
                    em.set_footer(text=f"{winners}w | Ended at ")
                    em.set_author(
                        name="This giveaway has ended", icon_url=f"{authorURL}"
                    )
                    await msg.edit(embed=em)
                break

            em = Embed(
                title=f"{prize}",
                description=f"React with <a:party_tada:809202936600199209> to enter!\nEnds in **{timeconverter}** \nHosted by {ctx.author.mention}",
                timestamp=future_time,
                color=randomcolour,
            )
            em.set_footer(text=f"{winners} {plural} | Ends at ")
            if time1 % 5 == 0:
                await msg.edit(embed=em)
            await asyncio.sleep(1)

    @commands.command(
        name="reroll",
        brief="Rerolls a giveaway from a message ID",
        usage="<channel> <messageID>",
    )
    async def reroll(self, ctx: customContext, id_: int):
        """
        Rerolls a giveaway from the current channel.\n
        For this to work, the user must have the giveaway role.\n
        Raises an error if the message is not in the current channel.
        """
        channel = ctx.channel
        grole = ctx.guild.get_role(await get_grole(self, ctx))

        if grole not in ctx.author.roles:
            return await ctx.send(
                f"{self.bot.icons['redTick']} You do not have the role `{grole.name}` that is required to reroll a giveaway!"
            )

        try:
            new_msg = await channel.fetch_message(id_)
        except Exception:
            raise commands.BadArgument(
                "The message with the given ID is not found in the current channel."
            )
        users = await new_msg.reactions[0].users().flatten()
        users.pop(users.index(self.bot.user))

        winner = random.choice(users)
        await channel.send(
            f"The new winner is {winner.mention}!\nhttps://discord.com/channels/{ctx.guild.id}/{ctx.channel.id}/{id_}"
        )

    @commands.group(
        invoke_without_command=True,
        case_insensitive=True,
        brief="A special form of giveaway.",
    )
    @commands.max_concurrency(1, commands.BucketType.channel, wait=False)
    async def drop(self, ctx: customContext):
        """
        This is a special form if giveaway.\n
        It drops a given or random sentence and the user that types it the fastest, gets the prize.\n
        To use the subcommands, the author must have the giveaway role set for the server.
        """
        await ctx.send(embed=ctx.bot.help_command.get_command_help(ctx.command))
    
    @drop.command(brief="Drops a prize with a custom sentence")
    @commands.max_concurrency(1, commands.BucketType.channel, wait=False)
    async def custom(self, ctx: customContext, *, prize):
        """
        Drops a prize with a custom sentence, that the author specifies after invoking the command.\n
        Note that timer is not supported here as it is in `drop normal`\n
        The author must have the giveaway role to start one.
        """
        grole = ctx.guild.get_role(await get_grole(self, ctx))

        if grole not in ctx.author.roles:
            return await ctx.send(
                f"{self.bot.icons['redTick']} You do not have the role `{grole.name}` that is required to start a drop!"
            )
        rarity = random.choice(
            [
                "<:green:819177876216610838>",
                "<:red:819177626278297620>",
                "<:purple:819177770793697280>",
            ]
        )

        def check1(m):
            return m.author == ctx.author

        try:
            await ctx.send(
                f"{ctx.author.mention}, please answer my question in your DM"
            )
            await ctx.author.send("What is the sentence? Type it here and send it! ")
            msg = await self.bot.wait_for("message", timeout=30, check=check1)
            await ctx.author.send(
                f"Ok, the sentence will now be `{msg.content}`.\nYou can now go back to {ctx.channel.mention}"
            )
            sentence = msg.content
        except asyncio.TimeoutError:
            await ctx.author.send("Aborting...")
            return

        def check(m):
            return m.channel == ctx.channel

        msgg = await ctx.send(
            content=f"{rarity} **`EVENT TIME!`**\n**Type it, type it, type it!**\nType the given sentence as fast as possible."
        )
        async with ctx.channel.typing():
            await asyncio.sleep(2)
        img = Image.open(f"{self.bot.cwd}/data/extra/Untitled.png")
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(
            f"{self.bot.cwd}/data/extra/JetBrainsMono-Regular.ttf", 12
        )
        text = sentence
        draw.text((24, 40), text, (255, 255, 255), font=font)
        img.save(f"{self.bot.cwd}/data/extra/text.png")
        f = await ctx.send(file=discord.File(f"{self.bot.cwd}/data/extra/text.png"))
        while True:
            try:
                msg = await self.bot.wait_for("message", timeout=30, check=check)
            except asyncio.TimeoutError:
                await ctx.send("Nobody won...")
                return
            if msg.content == str(sentence):
                await msgg.edit(
                    content=f"{rarity} **`EVENT TIME!`**\n**Type it, type it, type it!**\nType the given sentence as fast as possible.\n\n<:red:819177626278297620> `This event has expired. No new submissions will be accepted`"
                )
                await ctx.send(
                    content=f"{msg.author.mention} won **{prize}**! — Claim your prize from {ctx.author.mention}"
                )
                break

    @drop.command()
    @commands.max_concurrency(1, commands.BucketType.channel, wait=False)
    async def normal(self, ctx: customContext, prize, time=None):
        """
        Drops a prize with a random sentence.\n
        Unlike `drop normal`, you can specify the time after the prize.\n
        The author must have the giveaway role to start one.
        """
        grole = ctx.guild.get_role(await get_grole(self, ctx))

        if grole not in ctx.author.roles:
            return await ctx.send(
                f"{self.bot.icons['redTick']} You do not have the role `{grole.name}` that is required to start a drop!"
            )
        rarity = random.choice(
            [
                "<:green:819177876216610838>",
                "<:red:819177626278297620>",
                "<:purple:819177770793697280>",
            ]
        )

        def check(m):
            return m.channel == ctx.channel

        if time:
            time = time.replace("s", "")
            try:
                time = int(time)
            except Exception:
                await ctx.send("Time must be something like `1s`!")
                return
            if time > 59:
                await ctx.send("Max. time is `59s`", delete_after=3)
                return

            msg1 = await ctx.send(
                content=f"{rarity} **`EVENT TIME!`**\n**Type it, type it, type it!**\nType the given sentence as fast as possible.\n\nLanding in **{time}** seconds."
            )
            while True:
                if time < 0:
                    break
                async with ctx.channel.typing():
                    time -= 1
                    if time == 0:
                        await msg1.edit(
                            content=f"{rarity} **`EVENT TIME!`**\n**Type it, type it, type it!**\nType the given sentence as fast as possible.\n\nLanding NOW!!!"
                        )
                        r = RandomWord()
                        s = RandomSentence()
                        sentence = str.capitalize(s.sentence())[:-1]
                        img = Image.open(f"{self.bot.cwd}/data/extra/Untitled.png")
                        draw = ImageDraw.Draw(img)
                        font = ImageFont.truetype(
                            f"{self.bot.cwd}/data/extra/JetBrainsMono-Regular.ttf", 12
                        )
                        text = sentence
                        draw.text((24, 40), text, (255, 255, 255), font=font)
                        img.save(f"{self.bot.cwd}/data/extra/text.png")
                        f = await ctx.send(
                            file=discord.File(f"{self.bot.cwd}/data/extra/text.png")
                        )

                        while True:
                            try:
                                msg = await self.bot.wait_for(
                                    "message", timeout=25, check=check
                                )
                            except asyncio.TimeoutError:
                                await ctx.send("Nobody won...")
                            if msg.content == str(sentence):
                                await msg1.edit(
                                    content=f"{rarity} **`EVENT TIME!`**\n**Type it, type it, type it!**\nType the given sentence as fast as possible.\n\n<:red:819177626278297620> `This event has expired. No new submissions will be accepted`"
                                )
                                await ctx.send(
                                    content=f"{msg.author.mention} won **{prize}**! — Claim your prize from {ctx.author.mention}"
                                )
                                break
                        return

                    await msg1.edit(
                        content=f"{rarity} **`EVENT TIME!`**\n**Type it, type it, type it!**\nType the given sentence as fast as possible.\n\nLanding in **{time}** seconds."
                    )
                    await asyncio.sleep(1)
        else:
            msgg = await ctx.send(
                content=f"{rarity} **`EVENT TIME!`**\n**Type it, type it, type it!**\nType the given sentence as fast as possible."
            )
            async with ctx.channel.typing():
                await asyncio.sleep(2)
            r = RandomWord()
            s = RandomSentence()
            sentence = str.capitalize(s.sentence())[:-1]
            img = Image.open(f"{self.bot.cwd}/data/extra/Untitled.png")
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype(
                f"{self.bot.cwd}/data/extra/JetBrainsMono-Regular.ttf", 12
            )
            text = sentence
            draw.text((24, 40), text, (255, 255, 255), font=font)
            img.save(f"{self.bot.cwd}/data/extra/text.png")
            f = await ctx.send(file=discord.File(f"{self.bot.cwd}/data/extra/text.png"))
            while True:
                try:
                    msg = await self.bot.wait_for("message", timeout=30, check=check)
                except asyncio.TimeoutError:
                    await ctx.send("Nobody won...")
                    return
                if msg.content == str(sentence):
                    await msgg.edit(
                        content=f"{rarity} **`EVENT TIME!`**\n**Type it, type it, type it!**\nType the given sentence as fast as possible.\n\n<:red:819177626278297620> `This event has expired. No new submissions will be accepted`"
                    )
                    await ctx.send(
                        content=f"{msg.author.mention} won **{prize}**! — Claim your prize from {ctx.author.mention}"
                    )
                    break

    @commands.command(
        name="ui", aliases=["info", "whois"], brief="Displays an user's information"
    )
    async def ui(self, ctx: customContext, member: discord.Member = None):
        """
        Shows all the information about the specified user.\n
        If none is specified, it defaults to the author.
        """
        member = member if member else ctx.author
        guild = ctx.guild
        status = member.raw_status

        em = Embed(
            title="",
            description=f"{member.mention}",
            color=guild.me.colour,
            timestamp=datetime.datetime.utcnow(),
        )
        em.add_field(
            name="Joined", value=member.joined_at.strftime("%a, %b %d, %Y %H:%M %p")
        )
        em.add_field(
            name="Created", value=member.created_at.strftime("%a, %b %d, %Y %H:%M %p")
        )
        roles = member.roles[1:]

        if roles:
            em.add_field(
                name=f"Roles [{len(roles)}]",
                value=" ".join(f"{role.mention}" for role in roles),
                inline=False,
            )
        else:
            em.add_field(
                name=f"Roles [{len(roles)}]",
                value="This member has no roles",
                inline=False,
            )



        em.add_field(name=f"Status:", value=f"{self.bot.icons[status]} {status.capitalize()}")
        if member.activity:
            em.add_field(name="Activity:", value=member.activity, inline=False)
        else:
            em.add_field(name="Activity:", value="No activity currently", inline=False)
        em.set_thumbnail(url=member.avatar_url)
        em.set_author(name=f"{member}", icon_url=member.avatar_url)
        em.set_footer(text=f"User ID: {member.id}")
        await ctx.send(embed=em)

    @commands.command(name="avatar", aliases=["av"], brief="Displays a member's avatar")
    async def avatar(self, ctx: customContext, member: discord.Member = None):
        """
        Displays a 1024 pixel sized image of the given member's avatar.\n
        If no member is specified, it defaults to the author's avatar.
        """
        member = member if member else ctx.author
        if member:
            em = Embed(
                title=f"Avatar for {member}",
                description=f'Link as\n[png]({member.avatar_url_as(format="png",size=1024)}) | [jpg]({member.avatar_url_as(format="jpg",size=1024)}) | [webp]({member.avatar_url_as(format="webp",size=1024)})',
                colour=discord.Color.blurple(),
            )
            em.set_image(url=member.avatar_url)
            await ctx.send(embed=em)

    @commands.command(name="rickroll", brief="Detects rickroll from given link")
    async def _rickroll(self, ctx: customContext, *, link):
        """
        Detects if the given link is a rickroll.\n
        The link must start with https://.\n
        """
        i = link.replace("<", "").replace(">", "")
        if "https://" in link:
            if await detect().find(i):
                await ctx.message.reply("Rickroll detected :eyes:")
            else:
                await ctx.message.reply("That website is safe :>")
        else:
            await ctx.send(link + " is not a valid URL...")

    @commands.command(
        brief="Previews a hex color (format is #FFFFFF)", usage="<hexadecimal>"
    )
    async def hex(self, ctx: customContext, *, args=None):
        """Previews a hex color (format is #FFFFFF).\n
        Sends an embed with the color as the thumbnail"""
        if args:
            if not args.startswith("#"):
                raise discord.ext.commands.MissingRequiredArgument(ctx.command)
            args2 = args.replace("#", "")
            args1 = args.replace("#", "")
            args1 = "0x" + args1
            try:
                colour = await commands.ColourConverter().convert(ctx, args1)
            except Exception:
                raise discord.ext.commands.MissingRequiredArgument(ctx.command)
            em = Embed(description=f"Color `{args}`", colour=colour)
            em.set_author(name="Hex Viewer")
            em.set_thumbnail(
                url=f"https://some-random-api.ml/canvas/colorviewer?hex={args2}"
            )
            return await ctx.send(embed=em)
        else:
            args = random.randint(0, 0xFFFFFE)
            hex = "%6x" % args
            em = Embed(description=f"Color `#{hex}`", colour=args)
            em.set_author(name="Hex Viewer")
            em.set_thumbnail(
                url=f"https://some-random-api.ml/canvas/colorviewer?hex={hex}"
            )
            return await ctx.send(embed=em)
    
    @commands.command(name="id")
    async def _get_id(self, ctx: customContext, any: Union[discord.TextChannel, discord.VoiceChannel, discord.StageChannel, discord.CategoryChannel, discord.Emoji, discord.User]):
        return await ctx.send(any.id)
    
    @commands.command(name="embed")
    async def _send_embed(self, ctx: customContext, *, embed: str):
        em = discord.Embed.from_dict(json.loads(embed))
        await ctx.send(embed=em)

def setup(bot):
    bot.add_cog(Utilities(bot), category="Utilities")
