import yfinance
import discord
from discord.ext import commands
import threading
import asyncio
import traceback
import requests
import time

class Asset(object):
    def __init__(self, symbol=None, name=None, price=None, url=None):
        self.symbol = symbol
        self.name = name
        self.price = price
        self.url = url
    
    def to_embed(self):
        e = discord.Embed(title=self.symbol)
        e.add_field(name='Ticker', value=self.symbol, inline=False)
        e.add_field(name='Name', value=self.name, inline=False)
        e.add_field(name='Price (USD)', value=f'{self.price:0.4f}', inline=False)
        if self.url is not None:
            e.set_image(url=self.url)
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

class OSRSMarket(Market):
    base_url = 'https://secure.runescape.com/m=itemdb_oldschool/api/catalogue/items.json?category=1&alpha=%23&page=1'
    def find_item(self, name, page=1):
        if name[0].isnumeric():
            url = f'https://secure.runescape.com/m=itemdb_oldschool/api/catalogue/items.json?category=1&alpha=%23&page={page}'
        else:
            url = f'https://secure.runescape.com/m=itemdb_oldschool/api/catalogue/items.json?category=1&alpha={name[0].lower()}&page={page}'
        j = requests.get(url).json()
        if len(j['items']) == 0:
            # no more items
            return None
        # try to find exact items
        items = [(x['name'], x['current']['price'], x['icon_large']) for x in j['items']]
        for (n, p, i) in items:
            if n.lower() == name:
                # we found it
                return (n, p, i)
        # we didn't find it
        # try searching deeper
        # rate limiting
        time.sleep(1.2)
        r = self.find_item(name, page=page+1)
        if r is None:
            # it doesn't exist verbatim anywhere
            # try seeing if a similar item exists
            for (n, p, i) in items:
                if name in n.lower():
                    # we found it, it just has a longer name
                    return (n, p, i)
            # it really isn't here
            return None
        # it does exist
        return r
    
    def _get(self, symbol):
        x = self.find_item(symbol.lower())
        if x is None:
            return None
        return Asset(symbol=symbol, name=x[0], price=x[1], url=x[2])

class ForexMarket(Market):
    initial_lock = threading.Lock()
    initial_done = False
    full_names = {}

    def _get(self, symbol):
        while not self.initial_done:
            if self.initial_lock.acquire(timeout=0.1):
                try:
                    if not self.initial_done:
                        j = requests.get('https://api.frankfurter.app/currencies').json()
                        for (k, v) in j.items():
                            self.full_names[k] = v
                        self.initial_done = True
                finally:
                    self.initial_lock.release()
        ticker = symbol.upper()
        if ticker not in self.full_names.keys():
            for x in self.full_names:
                if ticker in self.full_names[x].upper():
                    ticker = x
                    break
            else:
                return None
        j = requests.get('https://api.frankfurter.app/latest?from=USD').json()
        price = 1.0 / j['rates'][ticker]
        return Asset(symbol=ticker, name=self.full_names[ticker], price=price)

class CryptoMarket(Market):
    initial_lock = threading.Lock()
    initial_done = False
    coins = []

    def _get(self, symbol):
        while not self.initial_done:
            if self.initial_lock.acquire(timeout=0.1):
                try:
                    if not self.initial_done:
                        self.coins = requests.get('https://api.coingecko.com/api/v3/coins/list').json()
                        self.initial_done = True
                finally:
                    self.initial_lock.release()
        ticker = symbol
        for item in self.coins:
            if (item['name'].upper() == ticker.upper()) or (item['symbol'].upper() == ticker.upper()):
                id = item['id']
                j = requests.get(f'https://api.coingecko.com/api/v3/coins/{id}').json()
                return Asset(symbol=j['symbol'].upper(), name=j['name'], price=j['market_data']['current_price']['usd'])
        return None

class FinanceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stock_market = StockMarket(5, 30)
        self.osrs_market = OSRSMarket(4, 30)
        self.forex_market = ForexMarket(15, 30)
        self.crypto_market = CryptoMarket(4, 30)
    
    async def get_info(self, ticker):
        if len(ticker) < 2:
            raise ValueError()
        ticker = ticker.strip()
        t = ticker[0]
        a = ticker[1:]
        if any(not (c.isalnum() or (c in ' \'\"')) for c in a):
            raise ValueError()
        if t == '$':
            return await self.stock_market.get(a)
        elif t == '^':
            return await self.stock_market.get('^' + a)
        elif t == '%':
            return await self.osrs_market.get(a)
        elif t == '+':
            return await self.forex_market.get(a)
        elif t == ':':
            return await self.crypto_market.get(a)
        else:
            raise ValueError()

    @commands.group(name='stonks')
    async def stonks(self, ctx: commands.Context):
        pass
    
    @stonks.command(name='info')
    async def info(self, ctx: commands.Context, *ticker):
        """
        $stock
        ^index
        "%old school runescape"
        +forex
        :crypto
        """
        ticker = ' '.join(ticker)
        async with ctx.typing():
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
    
    @stonks.command(name='convert')
    async def info(self, ctx: commands.Context, fro, to):
        async with ctx.typing():
            try:
                fro_asset, to_asset = await asyncio.gather(
                    self.get_info(fro),
                    self.get_info(to)
                )
                
                if (fro_asset is None) or (to_asset is None):
                    await ctx.reply('An error occurred while fetching at least one of the assets')
                else:
                    e = discord.Embed(title='Asset Conversion')
                    e.add_field(name='From', value=fro_asset.name, inline=False)
                    e.add_field(name='To', value=to_asset.name, inline=False)
                    e.add_field(name='Rate', value=fro_asset.price / to_asset.price, inline=False)
                    await ctx.send(embed=e)
            except ValueError:
                await ctx.reply('At least one of the tickers supplied is invalid')
            except TimeoutError:
                await ctx.reply('Too many requests; try again in a minute or so.')
            except:
                traceback.print_exc()
    
def setup(bot):
    bot.add_cog(FinanceCog(bot))