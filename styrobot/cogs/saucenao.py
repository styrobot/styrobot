import discord
from discord.ext import commands
import os
from styrobot.util import message, database
import asyncio
import aiohttp
import time

class SauceNaoCog(commands.Cog):
    def __init__(self, bot, token):
        self.bot = bot
        self.token = token
        self.lock = asyncio.Lock()
        self.short_limit_expiry = -1
        self.long_limit_expiry = -1

    async def get_source(self, url):
        if self.short_limit_expiry >= 0:
            if self.short_limit_expiry > time.time():
                raise OverflowError()
            else:
                self.short_limit_expiry = -1
        if self.long_limit_expiry >= 0:
            if self.long_limit_expiry > time.time():
                raise OverflowError()
            else:
                self.long_limit_expiry = -1
        async with aiohttp.ClientSession() as session:
            params = {
                'db': 999,
                'output_type': 2,
                'numres': 6,
                'url': url,
                'api_key': self.token
            }
            async with session.get('https://saucenao.com/search.php', params=params) as resp:
                j = await resp.json()
                if j['header']['long_remaining'] <= 5:
                    self.long_limit_expiry = time.time() + 86400
                if j['header']['short_remaining'] <= 1:
                    self.short_limit_expiry = time.time() + 30
                s = j['header']['status']
                if not (s == 0):
                    print('warning: got saucenao status {s} != 0')
                    raise ValueError()
                return j

    @commands.command(name='saucenao')
    async def saucenao(self, ctx: commands.Context):
        """
        Enabled via setting `saucenao.enable`; options are
        `nsfw` (default, only in nsfw channels), `false` (not enabled),
        and `all` (all channels, dangerous)
        """
        if not ctx.guild:
            # Don't DM NSFW stuff to people who could potentially be underage
            return
        else:
            setting = await database.get_guild_setting(ctx.guild.id, 'saucenao.enable', default='nsfw')
            if setting == 'false':
                return
            elif not (setting == 'all'):
                # setting = 'nsfw' or invalid
                if not (ctx.channel.is_nsfw()):
                    await ctx.reply('NSFW channels only!')
                    return
        async with ctx.typing():
            r = await message.image_walk(ctx.message, keep_urls=True)
            if r is None:
                await ctx.reply('What image?')
                return
            (_, url) = r
            try:
                async with self.lock:
                    resp = await self.get_source(url)
            except OverflowError:
                await ctx.reply('Too many requests, try again later.')
            except ValueError:
                await ctx.reply('An error occurred fetching the sauce.')
            else:
                if resp is None:
                    await ctx.reply('No results found.')
                    return
                links = '\n'.join(f'<{x["data"]["ext_urls"][0]}>' for x in resp['results'][:5] if (float(x['header']['similarity']) > 18) and ('ext_urls' in x['data']))
                links = links or '**(no links found, sorry!)**'
                links = '*Powered by SauceNAO.com:*\n' + links
                await ctx.reply(links)

def setup(bot):
    fn = '/tmp/secrets/saucenao.txt'
    if not os.path.exists(fn):
        print('saucenao token not found, disabling saucenao cog')
    else:
        with open(fn, 'r') as f:
            bot.add_cog(SauceNaoCog(bot, f.read().strip()))