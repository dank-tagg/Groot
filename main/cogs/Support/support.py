from utils._type import *

import asyncio

from datetime import datetime as dt
from discord.ext import commands
from utils.useful import Embed


class Support(commands.Shard):
    def __init__(self, cog: commands.Cog):
        super().__init__(cog)
        self.bot = cog.bot

    @commands.command(name="report")
    async def _report(self, ctx: customContext):
        """Used to report something."""
        questions = [
            "What do you want to report?",
            "Write a descriptive overview of what you are reporting.\n"
            "Note that your answer must be about 20 characters.",
        ]
        answers = []
        for question in questions:
            await ctx.send(question)
            try:
                answer = await self.bot.wait_for(
                    "message",
                    timeout=60,
                    check=lambda m: m.author == ctx.author and m.channel == ctx.channel,
                )
            except asyncio.TimeoutError:
                raise commands.BadArgument(
                    "`60s` are over. I ended your report session, "
                    "since you didn't answer fast enough. Please be quicker next time."
                )
            else:
                answer = answer.content
                answers.append(answer)

        if len(answers[1]) < 20:
            raise commands.BadArgument("Sorry, your answer must be a little longer.")
        if answers:
            em = Embed(title=answers[0], description=answers[1], timestamp=dt.utcnow())
            em.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
            em.set_footer(text="ID: " + str(ctx.author.id))
            msg = await ctx.send(
                content="Are you sure you want to submit your report?", embed=em
            )
            for emoji in (emojis := [self.bot.icons['greenTick'], self.bot.icons['redTick']]): await msg.add_reaction(emoji)
            try:
                reaction, m = await self.bot.wait_for(
                    "reaction_add",
                    timeout=45,
                    check=lambda reaction, m: m == ctx.author
                    and str(reaction.emoji) in emojis,
                )
                if str(reaction) == self.bot.icons['greenTick']:
                    channel = self.bot.get_channel(823585906044174416)
                    await channel.send(embed=em)
                    return await ctx.send(
                        "Submitted your report here > " + channel.mention
                    )
                else:
                    return await ctx.send("Cancelled your report.")
            except asyncio.TimeoutError:
                raise commands.BadArgument(
                    "`60s` are over. I ended your report session, since you didn't answer fast enough. Next time please be quicker."
                )


    @commands.command(name="suggest")
    async def _suggest_feature(self, ctx: customContext, *, suggestion):
        """Used to suggest a feature for Groot."""
        channel = self.bot.get_channel(857544734338449448)
        msg = await channel.send(f"{ctx.author}: {suggestion}")
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")
        await ctx.send(f"Submitted your suggestion in {channel.mention}. Join the support server to see the status of your suggestion.")


def setup(cog):
    cog.add_shard(Support(cog))
