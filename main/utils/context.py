import asyncio
import contextlib
import random
import time
import discord

from typing import Optional
from discord.ext import commands

__all__ = ('customContext')

class Processing:

    def __init__(self, ctx, **kwargs):
        self.ctx = ctx
        self.delete_after = kwargs.get("delete_after")
        self.message = kwargs.get("message")
        self.m = None
        self.task = None

        # Timer properties
        self._start = None
        self._end = None

    # Timer utilities
    def start(self):
        self._start = time.perf_counter()

    def stop(self):
        self._end = time.perf_counter()

    def __int__(self):
        return round(self.time)

    def __float__(self):
        return self.time

    def __str__(self):
        return str(self.time)

    # Actual methods
    async def __aenter__(self, *args, **kwargs):
        self.start()
        self.m = await self.ctx.send(f"{self.ctx.bot.icons['loading']} {self.message or 'Processing command, please wait...'}")
        self.task = self.ctx.typing().__enter__()
        return self

    async def __aexit__(self, *args, **kwargs):
        self.stop()
        if self.delete_after:
            try:
                await self.m.delete()
            except discord.HTTPException:
                pass
        self.task.__exit__(None, None, None)

    @property
    def time(self):
        if self._end is None:
            raise ValueError("Timer has not been ended.")
        return self._end - self._start

class customContext(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.processing = Processing

    @property
    def reference(self) -> Optional[discord.Message]:
        return getattr(self.message.reference, 'resolved', None)

    @property
    def now(self):
        return discord.utils.utcnow()


    async def send(self, content=None, **kwargs):
        if self.author.id in self.bot.cache["tips_are_on"]:
            tip = random.choice(
                [
                    "**TIP:** If you need any support, you can join https://discord.gg/nUUJPgemFE for help!",
                    "**TIP:** You can help us improve! DM dank tagg#6017 for suggestions!",
                    f"**TIP:** You can add this bot to your server if you want! `{self.prefix}invite`",
                    f"**TIP:** You can earn rewards by voting for the bot! `{self.prefix}vote`",
                    f"**TIP:** We've partnered with a bot called Stop Sign! Check them out: https://discordbotlist.com/bots/stop-sign/upvote",
                    f"**TIP:** If you find any bugs, report it in the support server! `{self.prefix}invite`",
                    f"**TIP:** Have you seen our website yet? <https://grootdiscordbot.xyz> :smile:",
                    f"**TIP:** Looking for a way to contribute? Here is the repository: <https://github.com/dank-tagg/Groot>",
                ]
            )
            if random.randint(1, 10) == 1:
                content = str(content) if content else ""
                content += f"\n\n{tip}"
                return await super().send(content, **kwargs)

        return await super().send(content, **kwargs)

    async def maybe_reply(self, content=None, mention_author=False, **kwargs):
        """Replies if there is a message in between the command invoker and the bot's message."""
        await asyncio.sleep(0.05)
        with contextlib.suppress(discord.HTTPException):
            if getattr(self.channel, "last_message", False) != self.message:
                return await super().reply(
                    content, mention_author=mention_author, **kwargs
                )
        return await self.send(content, **kwargs)

    async def reply(self, content=None, mention_author=False, **kwargs):
        mention = self.author.id in self.bot.cache['mentions_are_on']
        return await super().reply(content, mention_author=mention, **kwargs)

    class Confirm(discord.ui.View):
        def __init__(self, to_confirm: discord.Member):
            super().__init__()

            self.to_confirm = to_confirm
            self.value = None


        @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green)
        async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
            if interaction.user != self.to_confirm:
                return
            self.value = True
            button.disabled = True
            self.stop()

        # This one is similar to the confirmation button except sets the inner value to `False`
        @discord.ui.button(label='Cancel', style=discord.ButtonStyle.danger)
        async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
            if interaction.user != self.to_confirm:
                return
            self.value = False
            button.disabled = True
            self.stop()

    async def confirm(self, message, target, *, delete_after=True):
        view = self.Confirm(target)
        msg = await self.send(message, view=view)
        await view.wait()
        if delete_after:
            await msg.delete()
        return view.value


