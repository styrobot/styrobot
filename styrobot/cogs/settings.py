import discord
from discord.ext import commands
from styrobot.util import database, auth
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
    
    async def send_help(self, ctx):
        embed = discord.Embed(title='Subcommands')
        embed.add_field(name='help', value='send this message', inline=True)
        embed.add_field(name='clear', value='reset the entire settings database (WARNING: DANGEROUS)', inline=True)
        embed.add_field(name='get <key>', value='get the value of a setting', inline=True)
        embed.add_field(name='set <key> <value>', value='set a setting', inline=True)
        embed.add_field(name='del <key>', value='remove a setting entry', inline=True)
        embed.add_field(name='list', value='list all the setting keys in use', inline=True)
        await ctx.send(embed=embed)
    
    @commands.command(name='settings')
    async def settings(self, ctx: commands.Context, *args):
        if ctx.guild is None:
            # these are guild settings, irrelevant outside of a guild
            return
        conn = await self.conn_for_guild(ctx.guild.id)
        # settings.manage is a role ID that dictates who, in addition
        # to admins, can manage guild settings.
        authorized = await auth.is_authorized(ctx.author, con=conn)
        if not authorized:
            await ctx.send('You are not authorized to manage settings. You must have either the "administrator" permission, or have the role given by the role ID in the `settings.manage` setting.')
            return
        
        await database.create_guild_settings_table(conn)

        if (len(args) == 0) or (args[0] == 'help'):
            await self.send_help(ctx)
        elif (args[0] == 'clear') and (len(args) == 1):
            await conn.execute('DROP TABLE settings')
            await conn.commit()
            await ctx.send('Cleared all guild settings.')
        elif (args[0] == 'get') and (len(args) == 2):
            if not self.valid_name(args[1]):
                await ctx.send('invalid key')
                return
            s = await database.get_guild_setting(None, args[1], default=None, con=conn)
            embed = discord.Embed()
            embed.title = 'Result'
            embed.add_field(name='key', value=args[1], inline=False)
            embed.add_field(name='is set', value=('no' if s is None else 'yes'), inline=False)
            if s is not None:
                embed.add_field(name='value', value=s, inline=False)
            await ctx.send(embed=embed)
        elif (args[0] == 'set') and (len(args) == 3):
            if not self.valid_name(args[1]):
                await ctx.send('invalid key')
                return
            if not self.valid_name(args[2]):
                await ctx.send('invalid value')
                return
            await conn.execute('INSERT OR REPLACE INTO settings VALUES (?,?)', (args[1], args[2]))
            await conn.commit()
            await ctx.send('Successfully set setting.')
        elif (args[0] == 'del') and (len(args) == 2):
            if not self.valid_name(args[1]):
                await ctx.send('invalid key')
                return
            await conn.execute('DELETE FROM settings WHERE key=?', (args[1],))
            await conn.commit()
            await ctx.send('Successfully removed key.')
        elif (args[0] == 'list') and (len(args) == 1):
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
        else:
            await self.send_help(ctx)

        

def setup(bot):
    bot.add_cog(SettingsCog(bot))