import discord
from discord.ext import commands
from styrobot.util import database, auth, checks
import traceback

class SettingsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn_cache = {}
    
    async def conn_for_guild(self, id):
        if id in self.conn_cache:
            return self.conn_cache[id]
        ret = await database.open_guild_database(id)
        self.conn_cache[id] = ret
        return ret
    
    def valid_name(self, setting):
        return setting.replace('.', '').replace(',', '').isalnum()
    
    @commands.group(name='settings')
    @commands.check(checks.authorized)
    async def settings(self, ctx: commands.Context):
        if ctx.subcommand_passed is None:
            await ctx.send_help(self.settings)
    
    @settings.command(name='help')
    async def settings_help(self, ctx: commands.Context):
        await ctx.send_help(self.settings)
    
    @settings.command(name='clear')
    async def settings_clear(self, ctx: commands.Context):
        """
        reset the entire settings database (WARNING: DANGEROUS)
        """
        conn = await self.conn_for_guild(ctx.guild.id)
        await conn.execute('DROP TABLE settings')
        await conn.commit()
        await database.create_guild_settings_table(conn)
        await ctx.send('Cleared all guild settings.')
    
    @settings.command(name='get', usage='<key>')
    async def settings_get(self, ctx: commands.Context, arg):
        """
        get the value of a setting
        """
        conn = await self.conn_for_guild(ctx.guild.id)
        if not self.valid_name(arg):
            await ctx.send('invalid key')
            return
        s = await database.get_guild_setting(None, arg, default=None, con=conn)
        embed = discord.Embed()
        embed.title = 'Result'
        embed.add_field(name='key', value=arg, inline=False)
        embed.add_field(name='is set', value=('no' if s is None else 'yes'), inline=False)
        if s is not None:
            embed.add_field(name='value', value=s, inline=False)
        await ctx.send(embed=embed)
    
    @settings.command(name='set', usage='<key> <value>')
    async def settings_set(self, ctx: commands.Context, key, value):
        """
        set the value of a setting
        """
        conn = await self.conn_for_guild(ctx.guild.id)
        if not self.valid_name(key):
            await ctx.send('invalid key')
            return
        if not self.valid_name(value):
            await ctx.send('invalid value')
            return
        await conn.execute('INSERT OR REPLACE INTO settings VALUES (?,?)', (key, value))
        await conn.commit()
        await ctx.send('Successfully set setting.')
    
    @settings.command(name='del', usage='<key>')
    async def settings_del(self, ctx: commands.Context, key):
        """
        remove a setting entry
        """
        conn = await self.conn_for_guild(ctx.guild.id)
        if not self.valid_name(key):
            await ctx.send('invalid key')
            return
        await conn.execute('DELETE FROM settings WHERE key=?', (key,))
        await conn.commit()
        await ctx.send('Successfully removed key.')
    
    @settings.command(name='list')
    async def settings_list(self, ctx: commands.Context):
        """
        list all setting keys in use
        """
        conn = await self.conn_for_guild(ctx.guild.id)
        cur = await conn.execute('SELECT key FROM settings')
        s = ''
        while True:
            x = await cur.fetchone()
            if x is None:
                break
            if len(s) + len(x[0]) > 1980:
                await ctx.send('too many keys to send, some are omitted')
                break
            s = s + '\n' + x[0]
        s = '```' + s + '\n```'
        await ctx.send(s)

        

def setup(bot):
    bot.add_cog(SettingsCog(bot))