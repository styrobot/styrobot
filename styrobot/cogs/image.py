import asyncio

import discord
from discord.ext import commands
from wand.image import Image
import io
from wand.color import Color
from styrobot.util import message
import imageio
import numpy as np


def image_command(name, use_imageio=False):
    def deco(func):
        async def wrapper(self, ctx: commands.Context):
            img = await message.image_walk(ctx.message, use_imageio=use_imageio)
            if img is None:
                await ctx.send('What image?')
                return
            async with ctx.typing():
                if isinstance(img, Image):
                    with img:
                        o = await self.bot.loop.run_in_executor(None, func, self, img)
                        if isinstance(o, Image):
                            b = io.BytesIO(o.make_blob('png'))
                            o.destroy()
                            b.seek(0)
                            f = discord.File(b, filename='output.png')
                            await ctx.channel.send(file=f, reference=ctx.message)
                            return

                elif isinstance(img, np.ndarray):
                    o = await self.bot.loop.run_in_executor(None, func, self, img)
                    if isinstance(o, np.ndarray):
                        with io.BytesIO() as b:
                            imageio.imwrite(b, o, format="png")
                            b.seek(0)
                            f = discord.File(b, filename='output.png')
                            await ctx.channel.send(file=f, reference=ctx.message)
                            return
        return commands.command(name=name)(wrapper)
    return deco


class ImageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @image_command('opacify', use_imageio=True)
    def opacify(self, img):
        with Image.from_array(img) as a:
            a.alpha_channel = "remove"
            a.background_color = Color("white")
            b = np.array(a)
        a.destroy()
        return b

    @image_command("magik", use_imageio=True)
    def magik(self, img):
        with Image.from_array(img) as a:
            a.liquid_rescale(width=int(a.width / 2), height=int(a.height / 2), delta_x=1, rigidity=0)
            a.liquid_rescale(width=int(a.width * 2), height=int(a.height * 2), delta_x=2, rigidity=0)
            b = np.array(a)
        a.destroy()
        return b


def setup(bot):
    bot.add_cog(ImageCog(bot))