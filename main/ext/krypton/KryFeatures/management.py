import traceback
import itertools


from discord.ext import commands
from .base import KryFeature
from ..utils.modules import ExtensionConverter

class ManagementFeature(KryFeature):

    @KryFeature.Command(parent='krypton', name='load', aliases=['reload'])
    async def krypton_load(self, ctx: commands.Context, *extensions: ExtensionConverter):
        paginator = commands.Paginator(prefix='', suffix='')
        if ctx.invoked_with == 'reload' and not extensions:
            extensions = [['ext.krypton']]


        for ext in itertools.chain(*extensions):
            method, icon = (
                (
                    self.bot.reload_extension, "\N{CLOCKWISE RIGHTWARDS AND LEFTWARDS OPEN CIRCLE ARROWS}"
                )
                if ext in self.bot.extensions else
                (
                    self.bot.load_extension, "\N{INBOX TRAY}"
                )
            )

            try:
                method(ext)
            except Exception as exc:
                traceback_data = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__, 1))
                paginator.add_line(
                    f"{icon}\N{WARNING SIGN} `{ext}`\n```py\n{traceback_data}\n```",
                    empty=True
                )
            else:
                paginator.add_line(f"{icon} `{ext}`", empty=True)

        for page in paginator.pages:
            await ctx.send(page)