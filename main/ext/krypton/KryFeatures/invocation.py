import discord
from discord.ext import commands
from .base import KryFeature
from ..utils.models import copy_context_with

class InvocationFeature(KryFeature):

    @KryFeature.Command(parent='krypton', name='superuser', aliases=['su'])
    async def krypton_superuser(self, ctx: commands.Context, target: discord.User, *, command: str):
        """
        Runs a command as someone else
        """

        alt = await copy_context_with(ctx, author=target, content=ctx.prefix + command)
        if alt.command is None:
            if alt.invoked_with is None:
                return await ctx.send('This bot has been hard-configured to ignore this user.')
            return await ctx.send(f'Command "{alt.invoked_with}" is not found')

        return await alt.command.invoke(alt)

    @KryFeature.Command(parent='krypton', name='sudo')
    async def krypton_sudo(self, ctx: commands.Context, *, command: str):
        """
        Runs a command bypassing all checks and cooldowns
        """
        
        alt = await copy_context_with(ctx, content=ctx.prefix + command)
        if alt.command is None:
            return await ctx.sned(f'Command "{alt.invoked_with}" is not found.')
        
        return await alt.command.reinvoke(alt)
    
    