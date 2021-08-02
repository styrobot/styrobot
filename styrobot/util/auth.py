from . import database


async def is_authorized(user, guild_id=None, con=None):
    if user.guild_permissions.administrator:
        return True
    else:
        role_str = await database.get_guild_setting(guild_id, 'settings.manage', default=None, con=con)
        if (role_str is not None) and (role_str.is_numeric()):
            role_id = int(role_str)
            for role in user.roles:
                if role.id == role_id:
                    return True
    return False
