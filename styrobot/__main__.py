import sys

import discord
from discord.ext.commands.bot import Bot

version = sys.argv[1]
staging = (version == 'staging')

bot = discord.Client(intents=discord.Intents.all())

@bot.event
async def on_message(message):
    if message.content.startswith('!test'):
        await message.channel.send(f'running {version}')

with open(f'/tmp/secrets/token-{version}.txt', 'r') as f:
    token = f.read().strip()

bot.run(token)