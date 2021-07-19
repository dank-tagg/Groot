import copy

import discord
from discord import audit_logs
from discord.ext import commands

async def copy_context_with(ctx: commands.Context, *, author=None, channel=None, **kwargs):
    message: discord.Message = copy.copy(ctx.message)
    message._update(kwargs)

    if author is not None:
        message.author = author
    
    if channel is not None:
        message.channel = channel

    return await ctx.bot.get_context(message, cls=type(ctx))