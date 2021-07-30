import discord
from discord.ext import commands


class ReactionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if "cum" in str(message.content).split(" "):
            await message.add_reaction("👀")


def setup(bot):
    bot.add_cog(ReactionCog(bot))
