import sys
import discord
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext

extensions = ["styrobot.cogs.reactions", "styrobot.cogs.settings", "styrobot.cogs.repost", "styrobot.cogs.image", "styrobot.cogs.copypasta"]

version = sys.argv[1]
staging = (version == 'staging')
testguild_id = [869748428303892530]

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
slash = SlashCommand(bot, sync_commands=True)

with open(f'/tmp/secrets/token-{version}.txt', 'r') as f:
    token = f.read().strip()

for ext in extensions:
    try:
        bot.load_extension(ext)
    except Exception as exc:
        print(f"error loading {ext}")
        raise exc

bot.run(token)
