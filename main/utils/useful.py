import asyncio
import functools
import re
import sqlite3
import sys
import traceback

import aiohttp
import discord
from discord.ext import commands
from discord.utils import maybe_coroutine
from utils.checks import can_execute_action

# ---Useful classes


class detect(aiohttp.ClientSession):
    async def find(self, url):
        source = str(await (await super().get(url)).content.read()).lower()
        phrases = ["rickroll", "rick roll", "rick astley", "never gonna give you up"]
        await super().close()
        return bool(re.findall("|".join(phrases), source, re.MULTILINE))


class ListCall(list):
    """Quick data structure for calling every element in the array regardless of awaitable or not"""

    def append(self, rhs):
        return super().append(rhs)

    def call(self, *args, **kwargs):
        return asyncio.gather(
            *(maybe_coroutine(func, *args, **kwargs) for func in self)
        )


class Embed(discord.Embed):
    def __init__(self, color=0x2F3136, fields=(), field_inline=False, **kwargs):
        super().__init__(color=color, **kwargs)
        for n, v in fields:
            self.add_field(name=n, value=v, inline=field_inline)


class currencyData:
    def __init__(self, bot):
        self.bot = bot

    async def create_account(self, user_id):
        if user_id in self.bot.cached_users:
            return False
        query = "INSERT INTO currency_data (user_id) VALUES (?)"
        try:
            await self.bot.db.execute(query, (user_id,))
            await self.bot.db.commit()
            self.bot.cached_users.setdefault(
                user_id,
                {
                    "wallet": 200,
                    "bank": 200,
                    "max_bank": 200,
                    "boost": 1,
                    "exp": 0,
                    "lvl": 0,
                },
            )
            return True
        except sqlite3.IntegrityError:
            return False

    async def get_data(self, user_id, mode="wallet"):
        return self.bot.cached_users[user_id][mode]

    async def update_data(self, user_id, amount: int, mode="wallet"):
        self.bot.cached_users[user_id][mode] += amount
        return True

    async def has_item(self, user_id, item):
        item = item.lower()
        query = """
                SELECT item_id
                FROM user_inventory
                INNER JOIN item_info
                USING(item_id)
                WHERE user_id = ? AND lower(item_name) = ?
                """
        cur = await self.bot.db.execute(query, (user_id, item))
        data = await cur.fetchone()
        return bool(data)


class grootCooldown:
    def __init__(
        self,
        rate: int,
        per: float,
        alter_rate: int,
        alter_per: float,
        bucket: commands.BucketType,
    ):
        self.default_mapping = commands.CooldownMapping.from_cooldown(rate, per, bucket)
        self.altered_mapping = commands.CooldownMapping.from_cooldown(
            alter_rate, alter_per, bucket
        )

    def __call__(self, ctx: commands.Context):
        key, key1 = (ctx.author.id, ctx.guild.id)
        if key in ctx.bot.premiums or key1 in ctx.bot.premiums:
            ctx.bucket = self.altered_mapping.get_bucket(ctx.message)
        else:
            ctx.bucket = self.default_mapping.get_bucket(ctx.message)
        retry_after = ctx.bucket.update_rate_limit()
        if retry_after:
            raise commands.CommandOnCooldown(ctx.bucket, retry_after)
        return True


# ---Useful functions
def roman_num(num):
    num_map = [
        (1000, "M"),
        (900, "CM"),
        (500, "D"),
        (400, "CD"),
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    ]

    roman = ""
    while num > 0:
        for i, r in num_map:
            while num >= i:
                roman += r
                num -= i
    return roman


def progress_bar(progress):
    progress = round(progress / 10)
    return ("■" * progress) + ("□" * (10 - progress))


async def convert_to_int(amount, max_amt):
    amount = amount.replace("max", f"{max_amt}")
    amount = amount.replace("all", f"{max_amt}")
    amount = re.sub(r"[^0-9ekEK.]", r"", amount)
    amount = amount.replace(".0", "")
    amount = amount.replace("k", "*1000")
    amount = amount.replace("e", "*10**")
    try:
        return int(eval(amount))
    except:
        raise commands.BadArgument("That is not a valid amount!")


def event_check(func):
    """Event decorator check."""

    def check(method):
        method.callback = method

        @functools.wraps(method)
        async def wrapper(*args, **kwargs):
            if await discord.utils.maybe_coroutine(func, *args, **kwargs):
                await method(*args, **kwargs)

        return wrapper

    return check


def call(func, *args, exception=Exception, ret=False, **kwargs):
    """one liner method that handles all errors in a single line which returns None, or Error instance depending on ret
    value.
    """
    try:
        return func(*args, **kwargs)
    except exception as e:
        return (None, e)[ret]


def print_exception(text, error):
    """Prints the exception with proper traceback."""
    print(text, file=sys.stderr)
    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
    etype = type(error)
    trace = error.__traceback__
    lines = traceback.format_exception(etype, error, trace)
    return "".join(lines)


def wait_ready(bot=None):
    async def predicate(*args, **_):
        nonlocal bot
        self = args[0] if args else None
        if isinstance(self, commands.Cog):
            bot = bot or self.bot
        if not isinstance(bot, commands.Bot):
            raise Exception(
                f"Bot must derived from commands.Bot not {bot.__class__.__name__}"
            )
        await bot.wait_until_ready()
        return True

    return event_check(predicate)


async def get_grole(self, ctx):

    cur = await self.bot.db.execute(
        "SELECT grole FROM guild_config WHERE guild_id=?", (ctx.guild.id,)
    )
    data = await cur.fetchone()
    return data[0]


async def get_frozen(self, guild: discord.Guild, member: discord.Member):
    cur = await self.bot.db.execute(
        "SELECT * FROM frozen_names WHERE guild_id = ? AND user_id = ?",
        (guild.id, member.id),
    )
    rows = await cur.fetchall()
    return rows


async def send_traceback(
    destination: discord.abc.Messageable, verbosity: int, *exc_info
):
    """
    Sends a traceback of an exception to a destination.
    Used when REPL fails for any reason.

    :param destination: Where to send this information to
    :param verbosity: How far back this traceback should go. 0 shows just the last stack.
    :param exc_info: Information about this exception, from sys.exc_info or similar.
    :return: The last message sent
    """

    etype, value, trace = exc_info

    traceback_content = "".join(
        traceback.format_exception(etype, value, trace, verbosity)
    ).replace("``", "`\u200b`")

    paginator = commands.Paginator(prefix="```py")
    for line in traceback_content.split("\n"):
        paginator.add_line(line)

    message = None

    for page in paginator.pages:
        message = await destination.send(page)

    return message


# ---Converters
class RoleConvert(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            return await commands.RoleConverter().convert(ctx, argument)
        except commands.BadArgument:
            role_to_return = discord.utils.find(
                lambda x: x.name.lower() == argument.lower(), ctx.guild.roles
            )
            if role_to_return is not None:
                return role_to_return


class MemberConvert(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            m = await commands.MemberConverter().convert(ctx, argument)
        except commands.BadArgument:
            m = discord.utils.find(
                lambda x: x.name.lower() == argument.lower(), ctx.guild.members
            )
            if m is None:
                raise commands.BadArgument(
                    f"{argument} is not a valid member or member ID"
                )

        if not can_execute_action(ctx, ctx.author, m):
            raise commands.BadArgument(
                f"{ctx.bot.redTick} You cannot do this action on this user due to role hierarchy."
            )
        return m
