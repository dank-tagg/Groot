import asyncio
import random

import discord
from discord.ext import commands
from discord.ext.commands import BucketType
from utils.useful import Embed


class Fun(commands.Cog, description="Fun commands"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="guessthenumber", aliases=["gtn"], brief="Guess the number game!"
    )
    @commands.max_concurrency(1, BucketType.user, wait=False)
    async def gtn(self, ctx):
        """Play a guess the number game! You have three chances to guess the number 1-10"""

        no = random.randrange(1, 10)
        await ctx.send(
            f"A number between **1 and 10** has been chosen, You have 3 attempts to guess the right number! Type your guess in the chat as a valid number!"
        )
        for i in range(0, 3):
            try:
                response = await self.bot.wait_for(
                    "message",
                    timeout=10,
                    check=lambda m: m.author == ctx.author and m.channel == ctx.channel,
                )
                guess = int(response.content)

                if guess > 10 or guess < 1:
                    if 2 - i == 0:
                        await ctx.send(
                            f"Unlucky, you ran out of attempts. The number was **{no}**"
                        )
                        return
                    else:
                        await ctx.send(
                            "That is not a valid number! It costed you one attempt..."
                        )

                else:
                    if guess > no:
                        if 2 - i == 0:
                            await ctx.send(
                                f"Unlucky, you ran out of attempts. The number was **{no}**"
                            )
                            return
                        else:
                            await ctx.send(
                                f"The number is smaller than {guess}\n`{2-i}` attempts left"
                            )
                    elif guess < no:
                        if 2 - i == 0:
                            await ctx.send(
                                f"Unlucky, you ran out of attempts. The number was **{no}**"
                            )
                            return
                        else:
                            await ctx.send(
                                f"The number is bigger than {guess}\n`{2-i}` attempts left"
                            )

                    else:
                        await ctx.send(
                            f"Good stuff, you got the number right. I was thinking of **{no}**"
                        )
                        return
            except asyncio.TimeoutError:
                await ctx.send(
                    "You got to give me a number... game ended due to inactivity"
                )
                return
            except Exception:
                if 2 - i == 0:
                    await ctx.send(
                        f"Unlucky, you ran out of attempts. The number was **{no}**"
                    )
                    return
                await ctx.send(
                    "That is not a valid number! It costed you one attempt..."
                )

    @commands.command(name="gayrate", aliases=["howgay"], brief="Rates your gayness")
    async def gayrate(self, ctx, member: discord.Member = None):
        """Rate your gayness or another users gayness. 1-100% is returned"""
        user = member.name if member else "You"

        emb = Embed(
            title="gay r8 machine",
            description=f"{user} is {random.randrange(0, 100)}% gay 🌈",
            color=discord.Color.random(),
        )
        await ctx.send(embed=emb)

    @gayrate.error
    async def gayrate_error(self, ctx, error):
        if isinstance(error, commands.MemberNotFound):
            emb = Embed(
                title="gay r8 machine",
                description=f"{error.argument} is {random.randrange(0, 100)}% gay 🌈",
                color=discord.Color.random(),
            )
            await ctx.send(embed=emb)

    @commands.command(aliases=["memes"], brief="Shows a meme from reddit")
    async def meme(self, ctx):
        """Shows a meme from r/memes."""
        async with self.bot.session() as cs:
            async with cs.get("https://www.reddit.com/r/memes/random/.json") as res:
                res = await res.json()

                image = res[0]["data"]["children"][0]["data"]["url"]
                permalink = res[0]["data"]["children"][0]["data"]["permalink"]
                url = f"https://reddit.com{permalink}"
                title = res[0]["data"]["children"][0]["data"]["title"]
                ups = res[0]["data"]["children"][0]["data"]["ups"]
                downs = res[0]["data"]["children"][0]["data"]["downs"]
                comments = res[0]["data"]["children"][0]["data"]["num_comments"]

                em = Embed(colour=discord.Color.blurple(), title=title, url=url)
                em.set_image(url=image)
                em.set_footer(text=f"👍 {ups} 👎 {downs} 💬 {comments}")
                await ctx.send(embed=em)

    @commands.command(name="8ball", brief="Ask the 8-ball a question!")
    async def eightball(self, ctx, *, question):
        """The almighty eightball answers all your questions"""
        answers = [
            "It is certain.",
            "It is decidedly so.",
            "Without a doubt.",
            "Is Trump's skin orange?",
            "Definitely",
            "Why don't you go ask your mom smh.",
            "What? No!",
            "Unscramble `esy`",
            "Doubtful...",
            "I'm lazy rn, don't want to answer it.",
            "Ok, no",
            "Possibly so!",
            "Yes. Yes. Yes.",
        ]

        em = Embed(
            title="Magic 8-ball",
            description=f"You: {question}\n🎱: {random.choice(answers)}",
            colour=discord.Color.random(),
        )
        await ctx.send(embed=em)

    @commands.group(
        invoke_without_command=True, case_insensitive=True, usage="<encode | decode>"
    )
    async def binary(self, ctx):
        """Encode or decode something to binary!"""
        cmd = self.bot.get_command("help")
        await ctx.invoke(cmd, command="binary")
        return

    @binary.command()
    async def encode(self, ctx, *, text):
        """Encodes given text to binary"""
        api = f"https://some-random-api.ml/binary?text={text}"
        
        async with self.bot.session() as cs:
            async with cs.get(api) as res:
                res = await res.json()
                bintext = res["binary"]
                await ctx.send(bintext)

    @binary.command()
    async def decode(self, ctx, *, binary):
        """Decodes given text to binary"""

        api = f"https://some-random-api.ml/binary?decode={binary}"
        async with self.bot.session() as cs:
            async with cs.get(api) as res:
                res = await res.json()
                decoded = res["text"]
                await ctx.send(decoded)

    @commands.command(name="fight")
    @commands.max_concurrency(1, BucketType.user, wait=False)
    async def fight(self, ctx, member: discord.Member):
        """
        Challenge an user to a duel!
        The user cannot be a bot.
        """
        if member.bot or member == ctx.author:
            return await ctx.send("You can't fight yourself or a bot stupid")

        users = [ctx.author, member]

        user1 = random.choice(users)
        user2 = ctx.author if user1 == member else member

        user1_hp = 100
        user2_hp = 100

        fails_user1 = 0
        fails_user2 = 0

        x = 2

        while True:
            if user1_hp <= 0 or user2_hp <= 0:
                winner = user1 if user2_hp <= 0 else user2
                loser = user2 if winner == user1 else user1
                winner_hp = user1_hp if user2_hp <= 0 else user2_hp
                await ctx.send(
                    random.choice(
                        [
                            f"Wow! **{winner.name}** totally melted down **{loser.name}**, winning with just `{winner_hp} HP` left!",
                            f"YEET! **{winner.name}** REKT **{loser.name}**, winning with `{winner_hp} HP` left.",
                            f"Woops! **{winner.name}** send **{loser.name}** home crying... with only `{winner_hp} HP` left!",
                            f"Holy cow! **{winner.name}** won from **{loser.name}** with `{winner_hp} HP` left. **{loser.name}** ran home to their mommy.",
                        ]
                    )
                )
                return

            alpha = user1 if x % 2 == 0 else user2
            beta = user2 if alpha == user1 else user1
            await ctx.send(
                f"{alpha.mention}, what do you want to do? `punch`, `kick`, `slap` or `end`?\nType your choice out in chat as it's displayed!"
            )

            def check(m):
                if alpha == user1:
                    return m.author == user1 and m.channel == ctx.channel
                else:
                    return m.author == user2 and m.channel == ctx.channel

            try:
                msg = await self.bot.wait_for("message", timeout=15.0, check=check)
            except asyncio.TimeoutError:
                await ctx.send(
                    f"**{alpha.name}** didn't react on time. What a noob. **{beta.name}** wins!"
                )
                return

            if msg.content.lower() == "punch":
                damage = random.choice(
                    [
                        random.randint(20, 60),
                        random.randint(0, 50),
                        random.randint(30, 70),
                        random.randint(0, 40),
                        random.randint(10, 30),
                        random.randint(5, 10),
                    ]
                )

                if alpha == user1:
                    user2_hp -= damage
                    hpover = 0 if user2_hp < 0 else user2_hp
                else:
                    user1_hp -= damage
                    hpover = 0 if user1_hp < 0 else user1_hp

                randommsg = random.choice(
                    [
                        f"**{alpha.name}** deals **{damage}** damage with an OP punch.\n**{beta.name}** is left with {hpover} HP",
                        f"**{alpha.name}** lands an amazing punch on **{beta.name}** dealing **{damage}** damage!\n**{beta.name}** is left over with {hpover} HP!",
                        f"**{alpha.name}** lands a dangerous punch on **{beta.name}** dealing **{damage}** damage!\n**{beta.name}** is left over with {hpover} HP!",
                    ]
                )
                await ctx.send(f"{randommsg}")

            elif msg.content.lower() == "kick":
                damage = random.choice(
                    [
                        random.randint(30, 45),
                        random.randint(30, 60),
                        random.randint(-50, -1),
                        random.randint(-40, -1),
                    ]
                )
                if damage > 0:

                    if alpha == user1:
                        user2_hp -= damage
                        hpover = 0 if user2_hp < 0 else user2_hp
                    else:
                        user1_hp -= damage
                        hpover = 0 if user1_hp < 0 else user1_hp

                    await ctx.send(
                        random.choice(
                            [
                                f"**{alpha.name}** kicks **{beta.name}** and deals **{damage}** damage\n**{beta.name}** is left over with **{hpover}** HP",
                                f"**{alpha.name}** lands a dank kick on **{beta.name}**, dealing **{damage}** damage.\n**{beta.name}** is left over with **{hpover}** HP",
                            ]
                        )
                    )
                elif damage < 0:

                    if alpha == user1:
                        user1_hp += damage
                        hpover = 0 if user1_hp < 0 else user1_hp
                    else:
                        user2_hp += damage
                        hpover = 0 if user2_hp < 0 else user2_hp

                    await ctx.send(
                        random.choice(
                            [
                                f"**{alpha.name}** flipped over while kicking their opponent, dealing **{-damage}** damage to themselves.",
                                f"{alpha.name} tried to kick {beta.name} but FELL DOWN! They took {-damage} damage!",
                            ]
                        )
                    )

            elif msg.content.lower() == "slap":
                damage = random.choice(
                    [
                        random.randint(20, 60),
                        random.randint(0, 50),
                        random.randint(30, 70),
                        random.randint(0, 40),
                        random.randint(10, 30),
                        random.randint(5, 10),
                    ]
                )

                if alpha == user1:
                    user2_hp -= damage
                    hpover = 0 if user2_hp < 0 else user2_hp
                else:
                    user1_hp -= damage
                    hpover = 0 if user1_hp < 0 else user1_hp

                await ctx.send(
                    f"**{alpha.name}** slaps their opponent, and deals **{damage}** damage.\n{beta.name} is left over with **{hpover}** HP"
                )

            elif msg.content.lower() == "end":
                await ctx.send(f"{alpha.name} ended the game. What a pussy.")
                return

            elif (
                msg.content.lower() != "kick"
                and msg.content.lower() != "slap"
                and msg.content.lower() != "punch"
                and msg.content.lower() != "end"
            ):
                if fails_user1 >= 1 or fails_user2 >= 1:
                    return await ctx.send(
                        "This game has ended due to multiple invalid choices. God ur dumb"
                    )
                if alpha == user1:
                    fails_user1 += 1
                else:
                    fails_user2 += 1
                await ctx.send("That is not a valid choice!")
                x -= 1

            x += 1

    @commands.command(brief="Let me tell a joke!")
    async def joke(self, ctx):
        """
        Returns a random joke from https://official-joke-api.appspot.com/jokes/random.
        """
        api = "https://official-joke-api.appspot.com/jokes/random"
        async with self.bot.session() as cs:
            async with cs.get(api) as res:
                result = await res.json()
                await ctx.send(f'{result["setup"]}\n||{result["punchline"]}||')

    @commands.command(name="challenge")
    async def challenge(self, ctx):
        """If you solve the challenge, you get premium forever"""
        await ctx.send(
            file=discord.File(f"{self.bot.cwd}/data/extra/challengeHidden.jpg")
        )


def setup(bot):
    bot.add_cog(Fun(bot), category="Fun")
