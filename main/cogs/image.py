from utils._type import *

import discord
import polaroid
import io
import re

from discord.ext import commands
from utils.useful import Embed, run_in_executor


IMAGE_REG = re.compile(r'(http)?s?:?(\/\/[^"\']*\.(?:png|jpg|jpeg|gif|png|svg))')

async def get_bytes(image: Union[discord.Emoji, discord.PartialEmoji, discord.Member, str], session, return_bytes=True) -> Union[bytes, str]:
    """Gets the byte-like object from the given param."""
    if isinstance(image, str):
        if re.match(IMAGE_REG, image):
            url = image
        elif len(image) == 1:
            digit = f'{ord(image):x}'
            url = f'https://twemoji.maxcdn.com/v/latest/72x72/{digit}.png'
        else:
            raise commands.BadArgument('Invalid image link provided. Try again with a different image.')    
    elif isinstance(image, discord.Member):
        url = image.avatar_url_as(format="png", size=1024)
    
    else:
        url = image.url_as(format="png")
    
    if not return_bytes:
        return url

    res = await session.get(str(url))
    if (size := int(res.headers['content-length'])//1000000) > 8:
        raise commands.BadArgument(f'⚠️ Image given (`{size} MB`) can not be larger than `8 MB`')
    return await res.read()
    
    
    


@run_in_executor
def edit_image(byte: bytes, method: str, args: tuple = (), kwargs: dict = {}) -> bytes:
    image = polaroid.Image(byte)
    do_polaroid = getattr(image, method)
    do_polaroid(*args, **kwargs)
    byt = io.BytesIO(image.save_bytes())
    return byt

ImageConvert = Optional[Union[discord.Emoji, discord.PartialEmoji, discord.Member, str]]

class Image(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='flip')
    async def _flip(self, ctx: customContext, obj: ImageConvert):
        obj = obj or ctx.author
        async with ctx.processing(ctx, delete_after=True) as process:
            byt = await get_bytes(obj, self.bot.session)
            res = await edit_image(byt, method='flipv')
        
        em = Embed(title=f'{ctx.command.name.title()} command took {process.time*1000:0.2f} ms')
        em.set_image(url=f'attachment://{ctx.command.name}.png')
        await ctx.send(embed=em, file=discord.File(res, filename=f'{ctx.command.name}.png'))

    @commands.command(name='rainbow')
    async def _rainbow(self, ctx: customContext, obj: ImageConvert):
        obj = obj or ctx.author
        async with ctx.processing(ctx, delete_after=True) as process:
            byt = await get_bytes(obj, self.bot.session)
            res = await edit_image(byt, method='apply_gradient')
        
        em = Embed(title=f'{ctx.command.name.title()} command took {process.time*1000:0.2f} ms')
        em.set_image(url=f'attachment://{ctx.command.name}.png')
        await ctx.send(embed=em, file=discord.File(res, filename=f'{ctx.command.name}.png'))

    @commands.command(name='mirror')
    async def _mirror(self, ctx: customContext, obj: ImageConvert):
        obj = obj or ctx.author
        async with ctx.processing(ctx, delete_after=True) as process:
            byt = await get_bytes(obj, self.bot.session)
            res = await edit_image(byt, method='fliph')
        
        em = Embed(title=f'{ctx.command.name.title()} command took {process.time*1000:0.2f} ms')
        em.set_image(url=f'attachment://{ctx.command.name}.png')
        await ctx.send(embed=em, file=discord.File(res, filename=f'{ctx.command.name}.png'))

    @commands.command(name='blur')
    async def _blur(self, ctx: customContext, obj: ImageConvert):
        obj = obj or ctx.author
        async with ctx.processing(ctx, delete_after=True) as process:
            byt = await get_bytes(obj, self.bot.session)
            res = await edit_image(byt, method='box_blur')
        
        em = Embed(title=f'{ctx.command.name.title()} command took {process.time*1000:0.2f} ms')
        em.set_image(url=f'attachment://{ctx.command.name}.png')
        await ctx.send(embed=em, file=discord.File(res, filename=f'{ctx.command.name}.png'))

    @commands.command(name='invert')
    async def _invert(self, ctx: customContext, obj: ImageConvert):
        obj = obj or ctx.author
        async with ctx.processing(ctx, delete_after=True) as process:
            byt = await get_bytes(obj, self.bot.session)
            res = await edit_image(byt, method='invert')
        
        em = Embed(title=f'{ctx.command.name.title()} command took {process.time*1000:0.2f} ms')
        em.set_image(url=f'attachment://{ctx.command.name}.png')
        await ctx.send(embed=em, file=discord.File(res, filename=f'{ctx.command.name}.png'))

    @commands.command(name='resize')
    async def _resize(self, ctx: customContext, height: int, width: int, obj: ImageConvert):
        if width > 1000 or height > 1000:
            return await ctx.send("The dimensions can't be over 1000 pixels", mention_author=False)
        
        obj = obj or ctx.author
        async with ctx.processing(ctx, delete_after=True) as process:
            byt = await get_bytes(obj, self.bot.session)
            res = await edit_image(byt, method='resize', args=(width,height,1))
        
        em = Embed(title=f'{ctx.command.name.title()} command took {process.time*1000:0.2f} ms')
        em.set_image(url=f'attachment://{ctx.command.name}.png')
        await ctx.send(embed=em, file=discord.File(res, filename=f'{ctx.command.name}.png'))

def setup(bot):
    bot.add_cog(Image(bot), cat_name='Image')