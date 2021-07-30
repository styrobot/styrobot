import discord
from discord.ext import commands

import re

class ReactionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if re.search(r'(^|[^a-zA-Z0-9])cum($|[^a-zA-Z0-9])', str(message.content).lower()) is not None:
            await message.add_reaction("👀")


def setup(bot):
    bot.add_cog(ReactionCog(bot))
