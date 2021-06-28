from utils._type import *

import wavelink
import typing
import textwrap
import asyncio
import functools
import re
import sqlite3
import sys
import traceback
import aiohttp
import discord

from datetime import datetime
from discord.ext import commands, menus
from discord.ext.menus import First, Last
from discord.utils import maybe_coroutine
from utils.checks import can_execute_action


PAGE_REGEX = r'(Page)?(\s)?((\[)?((?P<current>\d+)/(?P<last>\d+))(\])?)'

# ---Useful classes
class BaseMenu(menus.MenuPages):
    def __init__(self, source, *, generate_page=True, **kwargs):
        super().__init__(source, delete_message_after=kwargs.pop('delete_message_after', True), **kwargs)
        self.info = False
        self._generate_page = generate_page
    
    @menus.button('◀️', position=First(1))
    async def _go_before(self, payload):
        await self.show_checked_page(self.current_page - 1)
    @menus.button('▶️', position=Last(0))
    async def _go_next(self, payload):
        await self.show_checked_page(self.current_page + 1)
    @menus.button('⏹️', position=First(2))
    async def _stop(self, payload):
        self.stop()

    async def _get_kwargs_format_page(self, page):
        value = await discord.utils.maybe_coroutine(self._source.format_page, self, page)
        if self._generate_page:
            value = self.generate_page(value, self._source.get_max_pages())
        if isinstance(value, dict):
            return value
        elif isinstance(value, str):
            return { 'content': value, 'embed': None }
        elif isinstance(value, discord.Embed):
            return { 'embed': value, 'content': None }

    async def _get_kwargs_from_page(self, page):
        dicts = await self._get_kwargs_format_page(page)
        dicts.update({'allowed_mentions': discord.AllowedMentions(replied_user=False)})
        return dicts

    def generate_page(self, content, maximum):
        if maximum > 0:
            page = f"Page {self.current_page + 1}/{maximum}"
            if isinstance(content, discord.Embed):
                if embed_dict := getattr(content, "_author", None):
                    if not re.match(PAGE_REGEX, embed_dict["name"]):
                        embed_dict["name"] += f"[{page.replace('Page ', '')}]"
                    return content
                return content.set_author(name=page)
            elif isinstance(content, str) and not re.match(PAGE_REGEX, content):
                return f"{page}\n{content}"
        return content

    async def send_initial_message(self, ctx: customContext, channel):
        page = await self._source.get_page(0)
        kwargs = await self._get_kwargs_from_page(page)
        return await ctx.reply(**kwargs)

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
    def __init__(self, bot: GrootBot):
        self.bot = bot

    async def create_account(self, user_id):
        if user_id in self.bot.cache["users"]:
            return False
        query = "INSERT INTO currency_data (user_id) VALUES (?)"
        try:
            await self.bot.db.execute(query, (user_id,))
            await self.bot.db.commit()
            self.bot.cache["users"].setdefault(
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
        return self.bot.cache["users"][user_id][mode]

    async def update_data(self, user_id, amount: int, mode="wallet"):
        self.bot.cache["users"][user_id][mode] += amount
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


class Cooldown:
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

    def __call__(self, ctx: customContext):
        key, key1 = (ctx.author.id, getattr(ctx.guild, "id", None))
        if key in ctx.bot.cache["premium_users"] or key1 in ctx.bot.cache["premium_users"]:
            ctx.bucket = self.altered_mapping.get_bucket(ctx.message)
        else:
            ctx.bucket = self.default_mapping.get_bucket(ctx.message)
        retry_after = ctx.bucket.update_rate_limit()
        if retry_after:
            raise commands.CommandOnCooldown(ctx.bucket, retry_after)
        return True

class fuzzy:

    @staticmethod
    def finder(to_find, collection, *, key=None, lazy=True):
        suggestions = []
        text = str(to_find)
        pat = '.*?'.join(map(re.escape, text))
        regex = re.compile(pat, flags=re.IGNORECASE)
        for item in collection:
            to_search = key(item) if key else item
            r = regex.search(to_search)
            if r:
                suggestions.append((len(r.group()), r.start(), item))

        def sort_key(tup):
            if key:
                return tup[0], tup[1], key(tup[2])
            return tup

        if lazy:
            return (z for _, _, z in sorted(suggestions, key=sort_key))
        else:
            return [z for _, _, z in sorted(suggestions, key=sort_key)]

# ---Useful functions
def pages(per_page=1, show_page=True):
    """Compact ListPageSource that was originally made teru but was modified"""
    def page_source(coro):
        async def create_page_header(self, menu, entry):
            result = await discord.utils.maybe_coroutine(coro, self, menu, entry)
            return menu.generate_page(result, self._max_pages)

        def __init__(self, list_pages):
            super(self.__class__, self).__init__(list_pages, per_page=per_page)
        kwargs = {
            '__init__': __init__,
            'format_page': (coro, create_page_header)[show_page]
        }
        return type(coro.__name__, (menus.ListPageSource,), kwargs)
    return page_source

def WrapText(text : str, length : int):
    wrapper = textwrap.TextWrapper(width=length)
    words = wrapper.wrap(text=text)
    return words

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

def get_title(track, length=35):
    if isinstance(track, wavelink.Track):
        track = track.title
    if len(track) > length:
        track = f"{track[:length]}..."
    return track

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
    except Exception:
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

def run_in_executor(func: typing.Callable):
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        """Asynchrous function that wraps a sync function with an executor"""
        loop = asyncio.get_event_loop()
        to_run = functools.partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, to_run)
    
    return wrapper

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

def is_beta():
    def predicate(ctx):
        return ctx.author.id in ctx.bot.testers
    return commands.check(predicate)

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


async def get_grole(self, ctx: customContext):

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
    destination: discord.abc.Messageable, ctx, edit, verbosity: int, *exc_info
):
    """
    Sends a traceback of an exception to a destination.
    Used when REPL fails for any reason.

    :param destination: Where to send this information to
    :param verbosity: How far back this traceback should go. 0 shows just the last stack.
    :param exc_info: Information about this exception, from sys.exc_info or similar.
    :return: The last message sent
    """

    base = f"An error occured while **{ctx.author}** [`{ctx.author.id}`] ran the command `{ctx.command.name}` at {datetime.utcnow().strftime('%H:%M:%S')} UTC\n"
    
    etype, value, trace = exc_info

    traceback_content = "".join(
        traceback.format_exception(etype, value, trace, verbosity)
    ).replace("``", "`\u200b`")

    final = base + f"```py\n{traceback_content}```"
    if not edit[0]:
        msg = await destination.send(final)
    else:
        msg = await edit[1].edit(content=final)
    return msg


# ---Converters
class RoleConvert(commands.Converter):
    async def convert(self, ctx: customContext, argument):
        try:
            return await commands.RoleConverter().convert(ctx, argument)
        except commands.BadArgument:
            role_to_return = discord.utils.find(
                lambda x: x.name.lower() == argument.lower(), ctx.guild.roles
            )
            if role_to_return is not None:
                return role_to_return


class MemberConvert(commands.Converter):
    async def convert(self, ctx: customContext, argument):
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
