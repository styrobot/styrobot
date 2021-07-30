import discord
from discord.ext import commands
from wand.image import Image
import io

from styrobot.util import message

class ImageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='opacify')
    async def opacify(self, ctx: commands.Context):
        img = await message.image_walk(ctx.message)
        if img is None:
            await ctx.send('What image?')
            return
        with img:
            with Image(width=img.width, height=img.height, pseudo='canvas:lightgray') as bg:
                bg.composite(img)
                b = io.BytesIO(bg.make_blob('jpeg'))
                await ctx.send(file=discord.File(b, filename='opacify.jpg'))

def setup(bot):
    bot.add_cog(ImageCog(bot))