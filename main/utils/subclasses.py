import inspect
import discord
import ctypes
import traceback
import sys
import asyncio
import contextlib
from collections import namedtuple
from discord.ext.menus import First, Last, Button
from discord.utils import maybe_coroutine
from discord.ext import commands, menus
import random

class customContext(commands.Context):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


    async def send(self, content=None, **kwargs):

        if self.author.id in self.bot.tips_on_cache:
            chance = random.randint(1,10)
            tip = random.choice(["**TIP:** If you need any support, you can join https://discord.gg/nUUJPgemFE for help!",
                                    "**TIP:** You can help us improve! DM dank tagg#6017 for suggestions!",
                                    f"**TIP:** You can add this bot to your server if you want! `{self.prefix}invite`",
                                    f"**TIP:** You can earn rewards by voting for the bot! `{self.prefix}vote`",
                                    f"**TIP:** We've partnered with a bot called Stop Sign! Check them out: https://discordbotlist.com/bots/stop-sign/upvote",
                                    f"**TIP:** If you find any bugs, report it in the support server! `{self.prefix}invite`"
                                    f"**TIP:** Have you seen our website yet? <https://dank-tagg.github.io/Groot-Website> :smile:"
                                    f"**TIP:** Looking for a way to contribute? Here is the repository: <https://github.com/dank-tagg/Groot>"])
            if chance == 1:
                content = str(content) if content else ""
                content += f"\n\n{tip}"
                return await super().send(content, **kwargs)

        return await super().send(content, **kwargs)
    
    async def maybe_reply(self, content=None, mention_author=False, **kwargs):
        """Replies if there is a message in between the command invoker and the bot's message."""
        await asyncio.sleep(0.05)
        with contextlib.suppress(discord.HTTPException):
            if getattr(self.channel,"last_message", False) != self.message:
                return await super().reply(content, mention_author=mention_author, **kwargs)
        return await super().send(content, **kwargs)


   