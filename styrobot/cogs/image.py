import discord
from discord.ext import commands
from wand.image import Image
import io

from styrobot.util import message

def image_command(name):
    def deco(func):
        async def wrapper(self, ctx: commands.Context):
            img = await message.image_walk(ctx.message)
            if img is None:
                await ctx.send('What image?')
                return
            with img:
                o = await func(self, ctx, img)
                if isinstance(o, Image):
                    b = io.BytesIO(o.make_blob('jpeg'))
                    o.destroy()
                    f = discord.File(b, filename='output.jpg')
                    await ctx.channel.send(file=f, reference=ctx.message)
                    return
        return commands.command(name=name)(wrapper)
    return deco

class ImageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @image_command('opacify')
    async def opacify(self, ctx: commands.Context, img):
        bg = Image(width=img.width, height=img.height, pseudo='canvas:lightgray')
        bg.composite(img)
        return bg

def setup(bot):
    bot.add_cog(ImageCog(bot))