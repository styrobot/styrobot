import discord
from discord.ext import commands
import inspect
from styrobot.util import database
from styrobot.util import message as message_util

class CopypastaCog(commands.Cog):
    """
    Enabled individually via settings, "copypasta.<name>" (set it to "true", without quotes)
    """

    copypastas = {
        'ping': '''
        So, regarding your silly ping...  Did you consider that I'm a grown-ass man, with a life?   That perhaps your joke wouldn't be very funny to me?

        Granted, not much of a life, but I had to pause my youtube video, switch to discord, read back several pages to see what the deal was.
        ''',
        'embed': 'https://tenor.com/view/jesus-ballin-mars-bars-gif-19910027'
    }

    def __init__(self, bot):
        self.bot = bot
        self.conn_cache = {}
    
    async def conn_for_guild(self, id):
        if id in self.conn_cache:
            return self.conn_cache[id]
        ret = await database.open_guild_database(id)
        self.conn_cache[id] = ret
        return ret
    
    async def reply_copypasta(self, message: discord.Message, name):
        conn = await self.conn_for_guild(message.guild.id)
        if (await database.get_guild_setting(None, f'copypasta.{name}', con=conn)) == 'true':
            await message.reply(inspect.cleandoc(self.copypastas[name]))
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild:
            # only do this in guilds
            return
        if message.author.bot:
            # only do this for real users
            return
        conn = await self.conn_for_guild(message.guild.id)
        if (not message.author.guild_permissions.mention_everyone) and (('@everyone' in message.content) or ('@here' in message.content)):
            await self.reply_copypasta(message, 'ping')
        if message_util.url_re.search(message.content) and not message.channel.permissions_for(message.author).embed_links:
            await self.reply_copypasta(message, 'embed')
    
def setup(bot):
    bot.add_cog(CopypastaCog(bot))