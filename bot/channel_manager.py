import time
from datetime import datetime
from dataclasses import dataclass
from typing import Optional
from interactions import GuildVoice, Member
from interactions import PermissionOverwrite, Permissions

# custom imports
from bot.config_loader import Creator
from bot.rate_limiter import RateLimitManager, RateLimitResponse


@dataclass
class TempChannel:
    channel: GuildVoice
    owner: Member
    created_at: int

    def time_since_creation(self) -> str:
        '''
        Get the time since the channel was created
        '''
        created_at = datetime.fromtimestamp(self.created_at)
        now = datetime.now()
        delta = now - created_at
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}h {minutes}m {seconds}s"

    def __repr__(self) -> str:
        return f"TempChannel(channel={self.channel}, owner={self.owner})"


class TempChannelManager:
    '''
    This class is used to manage the temporary channels.
    An instance of this class ist bound to the client
    '''

    def __init__(
        self,
        rate_limiter: RateLimitManager
    ):
        self.channels: dict[int, TempChannel] = {}
        self.rate_limiter = rate_limiter

    def _add_channel(self, tempchannel: TempChannel) -> None:
        self.channels[tempchannel.channel.id] = tempchannel

    def _remove_channel_by_id(self, channel_id: int) -> None:
        if channel_id in self.channels:
            del self.channels[channel_id]

    async def create_channel(
        self,
        previous_channel: GuildVoice,
        owner: Member,
        creator: Creator,
    ) -> GuildVoice:
        '''
        Create a new temporary channel while respecting the creator config
        '''

        default_role = owner.guild.default_role
        overwrites = []
        if creator.default.copy_permissions:
            overwrites = previous_channel.permission_overwrites
        else:
            overwrites.append(
                creator.generate_permission_overwrite(default_role)
            )

            # Grant CONNECT permission to cannot_be_kicked roles
            if creator.role and creator.role.cannot_be_kicked:
                for role_id in creator.role.cannot_be_kicked:
                    role = previous_channel.guild.get_role(role_id)
                    role = owner.guild.get_role(role_id)
                    if role:
                        ow = PermissionOverwrite.for_target(role)
                        ow.add_allows(Permissions.CONNECT)
                        overwrites.append(ow)

            # Grant CONNECT permission to the owner (host) of the channel
            owner_overwrite = PermissionOverwrite.for_target(owner)
            owner_overwrite.add_allows(Permissions.CONNECT)
            overwrites.append(owner_overwrite)

        try:
            name = owner.nickname or owner.username
            new_channel = await previous_channel.guild.create_voice_channel(

                # where
                category=creator.general.category,

                # why
                reason=f"User '{owner.username}' ({owner.id}) joined '{previous_channel.name}'",

                # default values
                name=creator.default.channel_name.format(name),
                user_limit=creator.default.channel_size,

                # other values
                bitrate=previous_channel.guild.bitrate_limit,

                # permission overwrites
                permission_overwrites=overwrites,
            )

            # add the new channel to the list of channels
            self._add_channel(
                TempChannel(
                    channel=new_channel,
                    owner=owner,
                    created_at=int(time.time())
                )
            )

            return new_channel

        except Exception as e:
            previous_channel.bot.logger.error(
                f"Error creating channel: {e}"
            )
            return None

    async def delete_channel(
        self,
        channel: GuildVoice,
    ) -> bool:
        '''
        Delete a temporary channel
        '''

        try:
            await channel.delete(
                reason=f"All users left the channel '{channel.name}'"
            )
            self._remove_channel_by_id(channel.id)
            return True

        except Exception as e:
            channel.bot.logger.error(
                f"Error deleting channel: {e}"
            )
            return False

    def get_channel_by_id(
        self,
        channel_id: int,
    ) -> Optional[TempChannel]:
        '''
        Get a temporary channel by its ID
        '''

        return self.channels.get(channel_id, None)
