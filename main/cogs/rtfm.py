import discord
from discord.ext import commands
import aiodevision
from utils.useful import fuzzy, Embed
from utils.chat_formatting import hyperlink as link

class Docs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.token = self.bot.config.get('idevision')
        self.cache = {}
    
    @commands.group(name="rtfm", aliases=["docs"])
    async def rtfm(self, ctx, *, obj: str = None):
        await self.lookup_rtfm(ctx, 'latest', obj)

    async def lookup_rtfm(self, ctx, key, obj):
        page_types = {
            'latest': 'https://discordpy.readthedocs.io/en/latest',
            'python': 'https://docs.python.org/3',
            'master': 'https://discordpy.readthedocs.io/en/master',
        }
        if obj is None:
            await ctx.send(page_types[key])
            return

        matches = fuzzy.finder(obj, self.cache, lazy=False)[:8]
        to_send = ""
        if not matches:
            client = aiodevision.Client(self.token)
            res = await client.rtfm(obj, page_types.get(key, 'latest'))

            for result in res.nodes:
                to_send += f"{link(f'`{result}`', res.nodes[result])}\n"
                self.cache[result] = res.nodes[result]

        else:
            for match in matches:
                to_send += f"{link(f'`{match}`', self.cache[match])}\n"
        
        em = Embed(description=to_send)
        await ctx.send(embed=em)

def setup(bot):
    bot.add_cog(Docs(bot), category="Information")
