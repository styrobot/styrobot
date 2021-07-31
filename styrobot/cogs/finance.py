import yfinance
import discord
from discord.ext import commands
import threading
import asyncio
import traceback

class Asset(object):
    def __init__(self, symbol=None, name=None, price=None):
        self.symbol = symbol
        self.name = name
        self.price = price
    
    def to_embed(self):
        e = discord.Embed(title=self.symbol)
        e.add_field(name='Ticker', value=self.symbol, inline=False)
        e.add_field(name='Name', value=self.name, inline=False)
        e.add_field(name='Price (USD)', value=f'{self.price:0.2f}', inline=False)
        return e

class Market(object):
    def __init__(self, max_reqs, wait_time):
        self.semaphore = threading.Semaphore(value=max_reqs)
        self.wait_time = wait_time
    
    async def release(self):
        # wait, for rate limiting
        await asyncio.sleep(self.wait_time)
        self.semaphore.release()
    
    async def get(self, symbol):
        for i in range(20):
            if self.semaphore.acquire(blocking=False):
                try:
                    loop = asyncio.get_running_loop()
                    result = await loop.run_in_executor(None, self._get, symbol)
                except Exception:
                    traceback.print_exc()
                    result = None
                finally:
                    asyncio.create_task(self.release())
                    return result
            await asyncio.sleep(0.1)
        raise TimeoutError()

class StockMarket(Market):
    def _get(self, symbol):
        try:
            t = yfinance.Ticker(symbol)
            if symbol.startswith('^'):
                return Asset(symbol=symbol, name=t.info['shortName'], price=t.info['regularMarketPrice'])
            else:
                return Asset(symbol=symbol, name=t.info['longName'], price=t.info['currentPrice'])
        except KeyError:
            return None

class FinanceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stock_market = StockMarket(5, 30)
    
    async def get_info(self, ticker):
        if len(ticker) < 2:
            raise ValueError()
        t = ticker[0]
        a = ticker[1:]
        if t == '$':
            return await self.stock_market.get(a)
        elif t == '^':
            return await self.stock_market.get('^' + a)
        else:
            raise ValueError()

    @commands.group(name='stonks')
    async def stonks(self, ctx: commands.Context):
        pass
    
    @stonks.command(name='info')
    async def info(self, ctx: commands.Context, ticker):
        try:
            r = await self.get_info(ticker)
            if r is None:
                await ctx.reply('An error occurred while fetching price data.')
            else:
                await ctx.reply(embed=r.to_embed())
        except ValueError:
            await ctx.reply('The ticker supplied is invalid')
        except TimeoutError:
            await ctx.reply('Too many requests; try again in a minute or so.')
        except:
            traceback.print_exc()
    
def setup(bot):
    bot.add_cog(FinanceCog(bot))