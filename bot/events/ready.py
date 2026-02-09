from interactions.api.events import Ready

from interactions import (
    Extension,
    listen
)


class ReadyEvent(Extension):

    @listen(Ready)
    async def on_ready(self) -> None:
        messages = [
            "-" * 50,
            "Bot is ready!",
            f"Bot version: {self.client.version}",
            f"Bot user: {self.client.user.username} ({self.client.user.id})",
            f"Bot is running on {self.client.guild_count} guild(s)",
            "-" * 50,
        ]
        for m in messages:
            self.bot.logger.info(m)
