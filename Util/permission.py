# util/util.py
from discord import Interaction
from discord import app_commands

def has_admin_role():
    async def predicate(interaction: Interaction) -> bool:
        admin_role_ids = interaction.client.config.get('administrator_role_ids', [])
        return any(role.id in admin_role_ids for role in interaction.user.roles)
    return app_commands.check(predicate)
