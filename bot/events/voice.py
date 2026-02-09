from typing import TYPE_CHECKING
from interactions.api.events import (
    VoiceUserJoin,
    VoiceUserMove,
    VoiceUserLeave
)

from interactions import (
    Extension,
    listen,
    GuildVoice,
    Member,
    Guild
)

if TYPE_CHECKING:
    from bot.channel_manager import TempChannelManager
    from bot.rate_limiter import RateLimitManager
    from bot.config_loader import GuildConfigLoader


from ..embed_maker import error_embed
from ..channel_logger import send_log_message


class VoiceEvents(Extension):

    def get_rate_limiter(self) -> 'RateLimitManager':
        return self.bot.rlm

    def get_temp_channel_manager(self) -> 'TempChannelManager':
        return self.bot.tcm

    def get_guild_config(self) -> 'GuildConfigLoader':
        return self.bot.gcl

    async def channel_is_empty(
        self,
        channel: GuildVoice
    ) -> bool:
        if len(channel.voice_members) == 1:
            return True
        return False

    async def log_guild_not_found(self, guild: Guild) -> None:
        """Log a warning if the guild is not found."""
        self.bot.logger.warning(f"Guild {guild.name} ({guild.id}) not found")

    async def handle_join(
        self,
        channel: GuildVoice,
        author: Member
    ) -> None:
        # load guild config
        config = self.get_guild_config()
        guild_config = config.get_guild_by_id(channel.guild.id)

        # skip if no config is found
        if not guild_config:
            await self.log_guild_not_found(channel.guild)
            return

        # check if the channel is a creator channel
        if not guild_config.is_creator_channel(channel.id):
            return

        # check if user can create a channel (rate limit)
        rate_limiter = self.get_rate_limiter()
        is_allowed = rate_limiter.can_perform_action(author.id)
        descrition = f"Du kannst einen neuen Kanal erstellen: <t:{is_allowed.end_time()}:R>"
        if not is_allowed:
            await author.send(
                embed=error_embed(
                    title="Nicht so schnell!",
                    description=descrition
                )
            )
            return

        # create a temp channel
        temp_channel_manager = self.get_temp_channel_manager()
        creator = guild_config.get_creator_by_channel_id(channel.id)
        temp_channel = await temp_channel_manager.create_channel(
            previous_channel=channel,
            owner=author,
            creator=creator
        )

        # move the user to the new channel
        if temp_channel:
            await author.move(temp_channel.id)

        # send a log message
        log_channel_id = guild_config.log_channel
        if not log_channel_id:
            return
        log_channel = channel.guild.get_channel(log_channel_id)
        if not log_channel:
            return
        await send_log_message(
            channel=log_channel,
            message=f"{author.mention} ({author.id}) erstellt **{temp_channel.name}.**"
        )

        # record the action in the rate limiter
        rate_limiter.record_action(author.id)

    async def handle_leave(
        self,
        channel: GuildVoice,
        author: Member
    ) -> None:
        # load guild config
        config = self.get_guild_config()
        guild_config = config.get_guild_by_id(channel.guild.id)

        # skip if no config is found
        if not guild_config:
            await self.log_guild_not_found(channel.guild)
            return

        # check if the channel is a temp channel
        if not guild_config.is_temp_channel(channel):
            return

        # check if the channel is empty
        if await self.channel_is_empty(channel):

            # channel name
            channel_name = channel.name

            # delete the channel
            temp_channel_manager = self.get_temp_channel_manager()

            # get the managed channel
            managed_channel = temp_channel_manager.get_channel_by_id(
                channel.id)
            if managed_channel:
                time_since_creation = managed_channel.time_since_creation()
            else:
                time_since_creation = "Unbekannt"

            await temp_channel_manager.delete_channel(
                channel=channel
            )

            # send a log message
            log_channel_id = guild_config.log_channel
            if not log_channel_id:
                return
            log_channel = channel.guild.get_channel(log_channel_id)
            if not log_channel:
                return

            await send_log_message(
                channel=log_channel,
                message=f"{author.mention} ({author.id}) hat **{channel_name}** verlassen und der Kanal wurde gelöscht. (Kanal existierte für {time_since_creation})"
            )

    @listen(VoiceUserJoin)
    async def on_voice_user_join(self, event: VoiceUserJoin) -> None:

        author = event.author
        new_channel = event.channel

        self.bot.logger.info(
            f"User {author.username} joined voice channel {new_channel.name}.")
        await self.handle_join(new_channel, author)

    @listen(VoiceUserMove)
    async def on_voice_user_move(self, event: VoiceUserMove) -> None:
        author = event.author
        previous_channel = event.previous_channel
        new_channel = event.new_channel

        self.bot.logger.info(
            f"User {author.username} moved from {previous_channel.name} to {new_channel.name}.")
        await self.handle_leave(previous_channel, author)
        await self.handle_join(new_channel, author)

    @listen(VoiceUserLeave)
    async def on_voice_user_leave(self, event: VoiceUserLeave) -> None:
        author = event.author
        previous_channel = event.channel

        self.bot.logger.info(
            f"User {author.username} left voice channel {previous_channel.name}.")
        await self.handle_leave(previous_channel, author)
