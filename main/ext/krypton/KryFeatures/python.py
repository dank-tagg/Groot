import discord
from discord.ext import commands

from .base import KryFeature
from ..utils.codeblocks import CodeConvert

class PythonFeature(KryFeature):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_result = None

    def get_env(ctx: commands.Context):
        """
        Returns the dict to be used in REPL for a given Context.
        """

        env = {
            'author': ctx.author,
            'bot': ctx.bot,
            'channel': ctx.channel,
            'ctx': ctx,
            'find': discord.utils.find,
            'get': discord.utils.get,
            'guild': ctx.guild,
            'message': ctx.message,
            'msg': ctx.message
        }

        return env

    @KryFeature.Command(parent='krypton', name='eval', aliases=['run', 'py'])
    async def krypton_eval(self, ctx: commands.Context, *, to_compile: CodeConvert):
        env = self.get_env(ctx)
        await ctx.send('Work in progress')
