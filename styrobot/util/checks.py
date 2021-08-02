from . import auth


async def in_guild(ctx):
    return ctx.guild


async def authorized(ctx):
    if not ctx.guild:
        return False
    return await auth.is_authorized(ctx.message.author, guild_id=ctx.guild.id)