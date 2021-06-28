from utils._type import *

import datetime
import discord
import random



from collections import OrderedDict
from discord.ext import commands, tasks
from utils.chat_formatting import hyperlink as link
from utils.useful import (Embed, convert_to_int, Cooldown, progress_bar,
                          roman_num)


class Currency(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = bot.data
        self.cache = {}
        self.levels.start()

    async def cog_before_invoke(self, ctx: customContext):
        query = """
                DELETE FROM user_Inventory
                WHERE amount = 0
                """
        await self.bot.db.execute(query)
        if await self.data.create_account(ctx.author.id) is True:
            ctx.bucket.reset()
            raise commands.BadArgument(
                "Seems like you are new! I created an account for you."
            )
        if ctx.author.id not in self.bot.cache["users"]:
            query = "SELECT * FROM currency_data WHERE user_id = ?"
            cur = await self.bot.db.execute(query, (ctx.author.id,))
            r = await cur.fetchone()
            self.bot.cache["users"][ctx.author.id] = {
                "wallet": r[1],
                "bank": r[2],
                "max_bank": r[3],
                "boost": r[4],
                "exp": r[5],
                "lvl": r[6],
                "prestige": r[7],
            }

    async def cog_after_invoke(self, ctx: customContext):
        exp = random.randint(0, 3)
        if ctx.author.id in self.bot.cache["premium_users"]:
            exp += 2
        try:
            self.cache[ctx.author.id] += exp
        except KeyError:
            self.cache[ctx.author.id] = exp

    @commands.command(
        name="profile", aliases=["lvl"], brief="Shows your stats and level"
    )
    @commands.check(Cooldown(1, 10, 1, 5, commands.BucketType.user))
    async def _profile(self, ctx: customContext, member: discord.Member = None):
        """Shows your statistics and experience/level total and the commands issued."""
        member = member if member is not None else ctx.author
        if member.id not in self.bot.cache["users"]:
            return await ctx.maybe_reply(
                f"{self.bot.icons['redTick']} That user does not have an account yet!"
            )
        lvl = await self.data.get_data(member.id, mode="lvl")
        exp = await self.data.get_data(member.id, mode="exp")

        bank_amount = await self.data.get_data(member.id, mode="bank")
        wallet_amount = await self.data.get_data(member.id)

        query = "SELECT commands_ran FROM users_data WHERE user_id = ?"
        cur = await self.bot.db.execute(query, (member.id,))
        data = await cur.fetchone()

        em = Embed()
        em.add_field(
            name="Level",
            value=f"**`{lvl}`**\n{link(progress_bar(lvl), f'{discord.utils.oauth_url(812395879146717214)}')}",
        )
        em.add_field(
            name="Experience",
            value=f"**`{exp}`**\n"
            f"{link(progress_bar(exp-lvl*100), f'{discord.utils.oauth_url(812395879146717214)}')}",
        )
        em.add_field(
            name="Cash",
            value=f"**Wallet**: ⛻{wallet_amount:,}\n**Bank**: ⛻{bank_amount:,}\n**Net worth**: ⛻{wallet_amount+bank_amount:,}",
        )
        em.add_field(name="Misc", value=f"`{data[0]:,}` commands issued")
        em.set_author(
            name=f"{member.display_name}'s profile", icon_url=member.avatar_url
        )
        await ctx.send(embed=em)

    @commands.command(name="prestige")
    @commands.check(
        Cooldown(
            1, 1 * 60 * 60 * 24, 1, 1 * 60 * 60 * 24, commands.BucketType.user
        )
    )
    async def _prestige(self, ctx: customContext):
        check = lambda prestige, level: level > 15 * prestige + 15
        level = await self.data.get_data(ctx.author.id, mode="lvl")
        exp = await self.data.get_data(ctx.author.id, mode="exp")
        prestige = await self.data.get_data(ctx.author.id, mode="prestige")
        if check:
            await self.data.update_data(ctx.author.id, -level, mode="lvl")
            await self.data.update_data(ctx.author.id, -exp, mode="exp")
            await self.data.update_data(ctx.author.id, 1, mode="prestige")
            await self.data.update_data(ctx.author.id, 0.25, mode="boost")
            return await ctx.send(
                f":tada: Congratulations {ctx.author.mention}! You are now Prestige `{roman_num(prestige+1)}`.\n"
                "You've earned a **25%** multiplier, and a redeemable PREMIUM PASS!"
            )
        else:

            raise commands.BadArgument(
                f"You do not have enough funds to prestige!\nYou need `{prestige*15-level}` more levels."
            )

    @commands.command(name="balance", aliases=["bal"], brief="Displays your money.")
    @commands.check(Cooldown(1, 5, 1, 1, commands.BucketType.user))
    async def _balance(self, ctx: customContext, member: discord.Member = None):
        """Shows your balance (wallet, bank and net worth)"""
        member = member if member is not None else ctx.author
        if member.id not in self.bot.cache["users"]:
            return await ctx.maybe_reply(
                f"{self.bot.icons['redTick']} That user does not have an account yet!"
            )
        bank_amount = await self.data.get_data(member.id, mode="bank")
        wallet_amount = await self.data.get_data(member.id)
        max_bank = await self.data.get_data(member.id, mode="max_bank")

        em = Embed(
            title=f"{member.display_name}'s balance",
            description=f"**Wallet**: ⛻{wallet_amount:,}\n"
            f"**Bank**: ⛻{bank_amount:,} / {max_bank:,} `({round(bank_amount/max_bank*100, 1)}%)`\n"
            f"**Net worth**: ⛻{wallet_amount+bank_amount:,}",
            timestamp=datetime.datetime.utcnow(),
        )
        em.set_footer(
            text=random.choice(
                [
                    "ew poor",
                    "imagine being poor",
                    "sucks to suck",
                    "lmfaooo",
                    "nice balance",
                ]
            )
        )
        return await ctx.maybe_reply(embed=em)

    @commands.command(name="inventory", aliases=["inv"], brief="Display your inventory")
    async def _inventory(self, ctx: customContext):
        """
        Displays amount and item name of everything you own.
        """

        query = """
                SELECT item_info.item_name, user_Inventory.amount
                FROM   user_Inventory
                INNER JOIN item_info
                USING(item_id)
                WHERE  user_Inventory.user_id = ?
                """
        cur = await self.bot.db.execute(query, (ctx.author.id,))
        data = await cur.fetchall()
        inventory = ""
        for item, amount in data:
            inventory += f"`{amount:,}` **{item}**\n"
        em = Embed(
            description=inventory if inventory else "No items to see here..."
        ).set_author(name=f"{ctx.author.display_name}'s inventory")
        return await ctx.send(embed=em)

    @commands.command(name="buy", brief="Buy something from the shop")
    @commands.check(Cooldown(1, 10, 1, 5, commands.BucketType.user))
    async def _buy(self, ctx: customContext, amount: typing.Optional[int] = 1, *, item):
        """
        This command is used to buy something from the shop.
        Amount is an optional argument, which defaults to one.
        """
        item = item.lower()
        price = """
                SELECT item_price, item_name
                FROM item_info
                WHERE lower(item_name) LIKE ?
                """
        cur = await self.bot.db.execute(price, (f"%{item}%",))
        data = await cur.fetchone()
        if not data:
            raise commands.BadArgument("This item doesn't exist!")
        if await self.data.get_data(ctx.author.id) < data[0] * amount:
            raise commands.BadArgument(
                f"{ctx.author.mention} You do not have enough money for this purchase!"
            )
        await self.data.update_data(ctx.author.id, -data[0] * amount)
        item = data[1]
        query = """
                INSERT INTO user_Inventory
                VALUES (?, 
                (SELECT item_id 
                 FROM   item_info 
                 WHERE  item_name = ?), 
                ?)
                ON CONFLICT(user_id, item_id) DO UPDATE SET amount = amount + ?
                """
        await self.bot.db.execute(query, (ctx.author.id, item, amount, amount))
        await self.bot.db.commit()
        em = Embed(
            description=f"Successfully bought `{amount}` `{item}` for **⛻{data[0]*amount:,}**"
        )
        em.set_author(name="Successful purchase", icon_url=ctx.author.avatar_url)
        return await ctx.send(embed=em)

    @commands.command(name="shop", brief="Get something from the shop!")
    async def _shop(self, ctx: customContext, item=None):
        if item:
            query = """
                    SELECT item_name, item_description, item_price
                    FROM item_info
                    WHERE lower(item_name) = ?
                    """
            cur = await self.bot.db.execute(query, (item.lower(),))
            data = await cur.fetchone()
            if not data:
                raise commands.BadArgument(
                    f"{item} is not an recognized item. Please check your spelling."
                )
            em = Embed(title=data[0], description=data[1])
            em.add_field(
                name="Value",
                value=f"**BUY**: ⛻{data[2]:,}\n**SELL**: ⛻{round(data[2]*0.25):,}",
            )
            return await ctx.send(embed=em)
        else:
            query = """
                    SELECT item_name, item_description, item_price
                    FROM item_info
                    """
            cur = await self.bot.db.execute(query)
            data = await cur.fetchall()
            items = ""
            for i in data:
                items += f"**{i[0]}** — ⛻{i[2]:,}\n{i[1]}\n\n"
            await ctx.send(embed=Embed(title="Shop items", description=items))

    @commands.command(name="sell", brief="Sell something you own")
    @commands.check(Cooldown(1, 10, 1, 5, commands.BucketType.user))
    async def _sell(self, ctx: customContext, amount: typing.Optional[int] = 1, *, item):
        item = item.lower()
        query = """
                SELECT item_info.item_price, user_Inventory.amount, item_info.item_name, item_info.item_id
                FROM   user_Inventory
                INNER JOIN item_info
                USING(item_id)
                WHERE  user_Inventory.user_id = ? AND lower(item_info.item_name) LIKE ?
                """
        cur = await self.bot.db.execute(query, (ctx.author.id, f"%{item.lower()}%"))
        data = await cur.fetchone()
        data = data if data else (0, 0)
        if amount > data[1]:
            raise commands.BadArgument(
                f"{ctx.author.mention} You do not have `{amount:,}` {item} to sell! You only have `{data[1]}`"
            )
        item = data[2]
        query = """
                UPDATE user_Inventory 
                SET amount = amount - ? 
                WHERE user_id = ? AND item_id = ?
                """
        await self.bot.db.execute(query, (amount, ctx.author.id, data[3]))
        await self.data.update_data(ctx.author.id, round(data[0] * amount * 0.25))
        em = Embed(
            description=f"Successfully sold `{amount}` `{item}` for **⛻{int(data[0]*amount*0.25):,}**"
        )
        em.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        return await ctx.send(embed=em)

    @commands.command(
        name="deposit", aliases=["dep"], brief="Deposit money from your wallet."
    )
    @commands.check(Cooldown(1, 5, 1, 1, commands.BucketType.user))
    async def _deposit(self, ctx: customContext, amount: str):
        """
        Deposit money from your wallet into your bank.\n
        If the amount given is more than your wallet or if your bank has reached it's max space it will raise an error.
        """
        wallet = await self.data.get_data(ctx.author.id)
        bank = await self.data.get_data(ctx.author.id, mode="bank")
        max_bank = await self.data.get_data(ctx.author.id, mode="max_bank")
        amount = await convert_to_int(amount, wallet)
        if amount == 0:
            raise commands.BadArgument(
                f"{ctx.author.mention} You have no coins in your wallet."
            )
        if amount > wallet or amount < 1:
            raise commands.BadArgument(
                f"{ctx.author.mention} Your argument must be a positive number and cannot be more than you own (⛻{wallet:,})!"
            )
        amount = amount if amount + bank < max_bank else max_bank - bank
        if amount == 0:
            raise commands.BadArgument(
                f"You can only hold **⛻{max_bank:,}** in your bank right now."
            )

        await self.data.update_data(ctx.author.id, amount, mode="bank")
        await self.data.update_data(ctx.author.id, -amount)
        return await ctx.send(
            f"{ctx.author.mention} You deposited **⛻{amount:,}** into your bank. "
            f"Now you have **⛻{await self.data.get_data(ctx.author.id, mode='bank'):,}**"
        )

    @commands.command(name="withdraw", aliases=["with"], brief="Withdraw money")
    @commands.check(Cooldown(1, 5, 1, 1, commands.BucketType.user))
    async def _withdraw(self, ctx: customContext, amount: str):
        """
        Withdraw money from your bank.
        If you try to withdraw more than you have it will raise an error.
        """
        bank = await self.data.get_data(ctx.author.id, mode="bank")
        amount = await convert_to_int(amount, bank)
        if amount == 0:
            raise commands.BadArgument(
                f"{ctx.author.mention} You have no coins in your wallet."
            )
        if amount > bank or amount < 1:
            raise commands.BadArgument(
                f"{ctx.author.mention} Your argument must be a positive number and cannot be more than you own (⛻{bank:,})!"
            )
        await self.data.update_data(ctx.author.id, -amount, mode="bank")
        await self.data.update_data(ctx.author.id, amount)
        return await ctx.send(
            f"{ctx.author.mention} You withdrew **⛻{amount:,}** from your bank. "
            f"Now you have **⛻{await self.data.get_data(ctx.author.id, mode='bank'):,}**"
        )

    @commands.command(name="fish", brief="Fish for fishes and money.")
    @commands.check(Cooldown(1, 20, 1, 10, commands.BucketType.user))
    async def _fish(self, ctx: customContext, info=None):
        """Fish for fishes that you automatically sell for cash!"""
        if not await self.bot.data.has_item(ctx.author.id, "fishing rod"):
            raise commands.BadArgument(
                f"{self.bot.icons['redTick']} You need a `Fishing Rod` to use `fish`!"
            )
        boost = self.bot.cache["users"][ctx.author.id]["boost"]
        times_caught = random.randint(1, 3)

        fish_dict = {
            "🐟 Common Fish": 100,
            "🐡 Blow Fish": 300,
            "🐠 Tropical Fish": 700,
            "🦈 Shark": 1200,
            "🦑 Squid": 1000,
            "🦀 Crab": 2000,
        }
        randomized = {
            k: fish_dict[k] for k in random.sample(fish_dict.keys(), times_caught)
        }
        if info is not None and info == "info":
            fish_dict[f"{self.bot.icons['groot']}  Groot"] = 100000
            fish_list = [
                f"{k} | **⛻{v:,}**"
                for k, v in sorted(fish_dict.items(), key=lambda item: item[1])
            ]
            em = Embed(description="\n".join(fish_list))
            em.set_author(name=f"Values of fishes")
            ctx.bucket.reset()
            return await ctx.maybe_reply(embed=em)
        if random.randint(0, 100) < 1:
            randomized[f"{self.bot.icons['groot']}  Groot"] = 100000
        fish_caught_alpha = [
            random.choice(list(randomized.keys())) for _ in range(times_caught)
        ]
        fish_value = sum([randomized[fish] for fish in fish_caught_alpha])
        fish_caught = [
            f"{fish_caught_alpha.count(item)} {item}" for item in fish_caught_alpha
        ]
        fish_caught = list(OrderedDict.fromkeys(fish_caught))
        earnings = round(fish_value * boost)
        await self.data.update_data(ctx.author.id, earnings)
        txt = (
            f"Multiplier Bonus +{round(boost*100)-100}% (**`⛻{int(fish_value*boost-fish_value):,}`**)"
            if boost > 1
            else ""
        )
        em = Embed(
            description=f"You went to fish and caught...\n\n"
            + "\n".join(fish_caught)
            + f"\n\nYou sold them for **⛻{fish_value:,}**\n"
            + txt
        )

        em.set_author(
            name=f"{ctx.author.display_name}'s fishing trip",
            icon_url=ctx.author.avatar_url,
        )
        em.set_footer(text=f"Current Multiplier: {round(boost*100)}%")
        return await ctx.maybe_reply(content=ctx.author.mention, embed=em)

    @commands.command(name="hunt", brief="Hunt for animals and cash.")
    @commands.check(Cooldown(1, 20, 1, 10, commands.BucketType.user))
    async def _hunt(self, ctx: customContext, info=None):
        """Hunt for animals that you automatically sell for cash!"""
        boost = self.bot.cache["users"][ctx.author.id]["boost"]
        times_caught = random.randint(1, 3)
        animals_dict = {
            "🦌 Deer": 1200,
            "🐗 Boar": 1000,
            "🐰 Rabbit": 750,
            "🐓 Chicken": 500,
        }
        randomized = {
            k: animals_dict[k] for k in random.sample(animals_dict.keys(), times_caught)
        }
        if info is not None and info == "info":
            animals_dict["🦄 Unicorn"] = 25000
            animals_dict["🐲 Dragon"] = 50000
            animals_dict[f"{self.bot.icons['groot']}  Groot"] = 100000
            animals_list = [
                f"{k} | **⛻{v:,}**"
                for k, v in sorted(animals_dict.items(), key=lambda item: item[1])
            ]
            em = Embed(description="\n".join(animals_list))
            em.set_author(name=f"Values of animals")
            ctx.bucket.reset()
            return await ctx.maybe_reply(embed=em)
        if random.randint(0, 100) < 1:
            randomized[f"{self.bot.icons['groot']}  Groot"] = 100000
        if random.randint(0, 100) < 10:
            randomized["🐲 Dragon"] = 25000
        if random.randint(0, 100) < 25:
            randomized["🦄 Unicorn"] = 12500

        animals_caught_alpha = [
            random.choice(list(randomized.keys())) for _ in range(times_caught)
        ]
        animals_value = sum([randomized[animal] for animal in animals_caught_alpha])
        animals_caught = [
            f"{animals_caught_alpha.count(item)} {item}"
            for item in animals_caught_alpha
        ]
        animals_caught = list(OrderedDict.fromkeys(animals_caught))
        earnings = round(animals_value * boost)
        await self.data.update_data(ctx.author.id, earnings)
        txt = (
            f"Multiplier Bonus +{round(boost*100)-100}% (**`⛻{int(animals_value*boost-animals_value):,}`**)"
            if boost > 1
            else ""
        )
        em = Embed(
            description=f"You went to the woods and caught...\n\n"
            + "\n".join(animals_caught)
            + f"\n\nYou sold them for **⛻{animals_value:,}**\n"
            + txt
        )
        em.set_author(
            name=f"{ctx.author.display_name}'s hunt", icon_url=ctx.author.avatar_url
        )
        em.set_footer(text=f"Current Multiplier: {round(boost*100)}%")
        return await ctx.maybe_reply(content=ctx.author.mention, embed=em)

    @commands.command(name="give", brief="Share coins to someone else.")
    async def _give(self, ctx: customContext, amount, member: discord.Member):
        """
        Give your coins to another member!\n
        Numbers such as 5e5, 10k etc are supported. Some are not.
        """
        if member == ctx.author or member.bot:
            raise commands.BadArgument(
                f"{self.bot.icons['redTick']} You cannot share coins to yourself or a bot."
            )

        amount = await convert_to_int(amount, await self.data.get_data(ctx.author.id))
        if amount < 1:
            raise commands.BadArgument(
                f"{self.bot.icons['redTick']} Amount must be a positive number!"
            )

        if member.id not in self.bot.cache["users"]:
            return await ctx.maybe_reply(
                f"{self.bot.icons['redTick']} That user does not have an account yet!"
            )

        tax_rate = 0.05 if amount < 100000 else 0.10

        amount_shared = round(amount - tax_rate * amount)
        await self.data.update_data(ctx.author.id, -amount)
        await self.data.update_data(member.id, amount_shared)

        return await ctx.maybe_reply(
            f"{ctx.author.mention} You gave **⛻{int(amount_shared):,}** "
            f"to {member.display_name} after a **{int(tax_rate*100)}%** tax rate. "
            f"Now you have ⛻{await self.data.get_data(ctx.author.id):,} and "
            f"they've got ⛻{await self.data.get_data(member.id):,}"
        )

    @commands.command(name="slots", brief="Gamble your money for huuuge winnings!")
    @commands.check(Cooldown(1, 5, 1, 3, commands.BucketType.user))
    async def _slots(self, ctx: customContext, amount: str):
        """
        Slots some coins and get huge winnings (if you win)\n
        Number such as 5e5, 10k etc are supported. Some are not.
        """
        wallet = await self.data.get_data(ctx.author.id)
        if wallet >= 10000000:
            raise commands.BadArgument(
                f"{ctx.author.mention} You are too rich to gamble!"
            )
        boost = self.bot.cache["users"][ctx.author.id]["boost"]
        if wallet == 0:
            raise commands.BadArgument(
                f"{ctx.author.mention} You have no coins to gamble with."
            )
        amount = await convert_to_int(amount, 500000)
        if amount > 500000:
            raise commands.BadArgument(
                f"{ctx.author.mention} You can't slots more than ⛻500,000 coins"
            )
        if amount > wallet:
            if amount != 500000:
                raise commands.BadArgument(
                    f"{ctx.author.mention} You don't have that much coins!"
                )
            else:
                amount = wallet
        # Emojis
        emojis = [
            ":four_leaf_clover:",
            ":cherry_blossom:",
            ":wood:",
            ":shell:",
            ":maple_leaf:",
            ":fish:",
            ":octopus:",
            ":crab:",
            ":star:",
        ]
        result = random.choices(emojis, k=3)
        # Set vars to keep it simple
        triple = result[0] == result[1] == result[2]
        double = (
            result[0] == result[1] or result[1] == result[2] or result[0] == result[2]
        )
        # Set the color for lose or win
        color = 0x3CA374 if double or triple else 0xF04D4B
        # Calculate the winnings
        winnings = amount * random.uniform(1.1, 2) * boost if double else amount * -1
        winnings = amount * random.uniform(1.7, 2.5) * boost if triple else winnings
        winnings = int(winnings)
        # Won or lost
        won_or_lost = "won" if winnings > 0 else "lost"
        await self.data.update_data(ctx.author.id, winnings)

        em = Embed(
            title="",
            description=f"You {won_or_lost} **⛻{abs(winnings):,}**\n"
            f"**Multiplier**: {round(boost*100)}% | **Percent of bet {won_or_lost}**: {abs(round(winnings/amount*100))}%\n\n"
            f"You now have **⛻{await self.data.get_data(ctx.author.id):,}**",
            color=color,
        )
        em.add_field(name="Outcome", value="**\> " + " ".join(result) + "  <**")
        em.set_author(
            name=f"{ctx.author.display_name}'s slots table",
            icon_url=ctx.author.avatar_url,
        )
        await ctx.send(embed=em)

    @commands.command(name="blackjack", aliases=["bj"], brief="Play blackjack!")
    @commands.max_concurrency(1, commands.BucketType.user, wait=False)
    @commands.check(Cooldown(1, 5, 1, 3, commands.BucketType.user))
    async def _blackjack(self, ctx: customContext, amount: str):
        """
        Play blackjack! READ THE RULES FIRST, before calling it a scam.
        Aces count as 1 or 11. Counts as 11 if your total value is smaller than 11,
        counts as 1 if your total value is bigger than 11.
        """
        cmd = self.bot.get_command("play_blackjack")
        await ctx.invoke(cmd, amount=amount)

    @tasks.loop(seconds=10)
    async def levels(self):
        for user in self.cache:
            await self.data.update_data(user, self.cache[user], mode="exp")
            await self.data.update_data(user, self.cache[user] * 100, mode="max_bank")

            if (
                await self.data.get_data(user, mode="exp")
                > (lvl := await self.data.get_data(user, mode="lvl") + 1) * 100
            ):
                await self.data.update_data(user, 1, mode="lvl")
                await self.data.update_data(user, 0.01, mode="boost")
                self.bot.cache["users"][user]["boost"] = round(
                    await self.data.get_data(user, mode="boost"), 2
                )
        self.cache = {}

    @levels.before_loop
    async def before_levels(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Currency(bot), category="Currency")
