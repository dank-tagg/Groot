from utils._type import *

import discord
import mystbin
import random

from discord.ext import commands

class Text(commands.Shard):
    def __init__(self, cog: commands.Cog):
        super().__init__(cog)
        self.bot = cog.bot

    @commands.command()
    async def post(self, ctx: customContext):
        """
        Posts a file containing text to mystbin.
        """
        if not ctx.message.attachments:
            await ctx.reply('No attachments were supplied to post.')
            return

        target = ctx.message.attachments[0]
        extension = target.filename.split('.')[1]
        text = (await target.read()).decode('ascii')

        client = mystbin.Client()
        paste = await client.post(text, syntax=extension)
        await ctx.send(f'Posted your file in {paste}')

    @commands.command()
    async def emojify(self, ctx: customContext, *, to_emojify: str):
        """
        Emojifies a piece of text.
        """
        special_chars = {
            "!": ':exclamation:',
            "?": ':question:',
            "+": ":heavy_plus_sign:",
            "-": ":heavy_minus_sign:",
            "×": ":heavy_multiplication_x:",
            "*": ":asterisk:",
            "$": ":heavy_dollar_sign:",
            "/": ":heavy_division_sign:",
            "#": ":hash:"
        }

        numbers = [':zero:',':one:',':two:',':three:',':four:', ':five:',':six:',':seven:',':eight:',':nine:']

        new = ""
        for char in to_emojify.lower():
            if char.isalpha():
                new += f':regional_indicator_{char}:'
            elif char.isnumeric():
                new += numbers[int(char)]
            else:
                new += special_chars.get(char, char)
        await ctx.send(new)

    @commands.command()
    async def clap(self, ctx: customContext, *, text: str):
        """
        Returns a text with 👏 in between.
        """
        await ctx.send(text.replace('', ' 👏 '))

    @commands.command(usage='[text]')
    async def codeblock(self, ctx: customContext, *, text: str):
        """
        Posts a piece of text in codeblock.
        """
        await ctx.send(f'```\n{text}```')

    @commands.command()
    async def rawtext(self, ctx: customContext, *, text: str):
        escape_markdown = discord.utils.escape_markdown(text)
        escape_mentions = discord.utils.escape_mentions(escape_markdown.replace('<', '\\<'))
        await ctx.send(escape_mentions)

    @commands.command()
    async def spoiler(self, ctx: customContext, *, text: str):
        await ctx.send(''.join(f'||{c}||' for c in text))

    @commands.command()
    async def lenny(self, ctx: customContext):
        lenny = random.choice([
            "( ͡° ͜ʖ ͡°)", "( ͠° ͟ʖ ͡°)", "ᕦ( ͡° ͜ʖ ͡°)ᕤ", "( ͡~ ͜ʖ ͡°)",
            "( ͡o ͜ʖ ͡o)", "͡(° ͜ʖ ͡ -)", "( ͡͡ ° ͜ ʖ ͡ °)﻿", "(ง ͠° ͟ل͜ ͡°)ง",
            "ヽ༼ຈل͜ຈ༽ﾉ"
        ])
        await ctx.send(lenny)

    @commands.command()
    async def reversecase(self, ctx: customContext, *, text: str):
        transform = lambda e: [e.lower(), e.upper()][e.islower()]
        await ctx.send(''.join(transform(char) for char in text))

    @commands.command()
    async def charcount(self, ctx: customContext, *, text: str):
        await ctx.reply(f'Your text is `{len(text)}` characters long.')

    @commands.command()
    async def wordcount(self, ctx: customContext, *, text: str):
        await ctx.reply(f'Your text is `{len(text.split(" "))}` words long.')



def setup(cog):
    cog.add_shard(Text(cog))