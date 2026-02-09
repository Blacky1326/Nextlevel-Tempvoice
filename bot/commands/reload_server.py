import os
from typing import TYPE_CHECKING

from interactions import (
    Extension,
    slash_command,
    Permissions,
    SlashContext
)


if TYPE_CHECKING:
    from bot.channel_manager import TempChannelManager
    from bot.rate_limiter import RateLimitManager
    from bot.config_loader import GuildConfigLoader


def perform_git_pull() -> None:
    os.system("git pull origin main")


class ReloadServer(Extension):

    def get_rate_limiter(self) -> 'RateLimitManager':
        return self.bot.rlm

    def get_temp_channel_manager(self) -> 'TempChannelManager':
        return self.bot.tcm

    def get_guild_config(self) -> 'GuildConfigLoader':
        return self.bot.gcl

    @slash_command(
        name="reload",
        description="Lade die Konfigurationen für alle Server neu",
        default_member_permissions=Permissions.ADMINISTRATOR,
    )
    async def reload_server(self, ctx: SlashContext) -> None:
        """Reload the server configurations."""
        # load guild config

        await ctx.defer(ephemeral=True)
        perform_git_pull()

        config = self.get_guild_config()
        config.guilds = config.load()

        await ctx.send(
            ephemeral=True,
            delete_after=5,
            content="Die Konfigurationen für alle Server wurden neu geladen."
        )
