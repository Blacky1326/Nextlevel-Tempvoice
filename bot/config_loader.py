import os
import json
from typing import List, Optional
from pydantic import BaseModel

from interactions import (
    GuildChannel,
    ChannelType,
    PermissionOverwrite,
    Permissions,
    Role,
    Member
)

GUILDS_CONFIG_PATH = "config/servers"


class CreatorRole(BaseModel):
    '''
    Role settings for the creator.
    the lists are used to store the ids of the roles that have the permission.
    '''

    cannot_be_kicked: Optional[List[int]] = []
    has_channel_owner_permissions: Optional[List[int]] = []


class CreatorDisable(BaseModel):
    text_chat: Optional[bool] = False
    video: Optional[bool] = False
    soundboard: Optional[bool] = False
    activities: Optional[bool] = False

    def generate_permission_overwrite(
        self,
        default_role: Role
    ) -> PermissionOverwrite:

        overwrite = PermissionOverwrite.for_target(default_role)

        if self.text_chat:
            overwrite.add_denies(
                Permissions.SEND_MESSAGES
            )
        if self.video:
            overwrite.add_denies(
                Permissions.STREAM
            )

        if self.soundboard:
            overwrite.add_denies(
                Permissions.USE_SOUNDBOARD
            )

        if self.activities:
            overwrite.add_denies(
                Permissions.START_EMBEDDED_ACTIVITIES
            )

        return overwrite


class CreatorDefault(BaseModel):
    channel_name: Optional[str] = "{}'s channel"
    channel_status: Optional[str] = None
    channel_size: Optional[int] = 0
    copy_permissions: Optional[bool] = False


class CreatorGeneral(BaseModel):
    name: Optional[str] = None
    channel: int
    category: int


class Creator(BaseModel):
    general: CreatorGeneral
    default: Optional[CreatorDefault] = CreatorDefault()
    disable: Optional[CreatorDisable] = CreatorDisable()
    role: Optional[CreatorRole] = CreatorRole()

    def member_can_not_be_kicked(
        self,
        member: Member,
    ) -> bool:
        """
        Check if the member cannot be kicked from the channel.
        A member cannot be kicked if:
        - they have a role that is in the list of roles that cannot be kicked.
        """
        if self.role is None:
            return False

        if self.role.cannot_be_kicked is None:
            return False

        for role_id in self.role.cannot_be_kicked:
            if role_id in self.get_user_roles_list(member):
                return True

        return False

    def get_user_roles_list(self, member: Member) -> List[int]:

        if self.role is None:
            return []

        return [role.id for role in member.roles]

    def member_has_channel_owner_permissions(
        self,
        member: Member,
    ) -> bool:
        """
        Check if the member has channel owner permissions.
        A member has channel owner permissions if:
        - they have a role that is in the list of roles that have channel owner permissions.
        """
        if self.role is None:
            return False

        if self.role.has_channel_owner_permissions is None:
            return False

        for role_id in self.role.has_channel_owner_permissions:
            if role_id in self.get_user_roles_list(member):
                return True

        return False

    def generate_permission_overwrite(
        self,
        default_role: Role
    ) -> PermissionOverwrite:
        return self.disable.generate_permission_overwrite(default_role)


class GuildConfig(BaseModel):
    '''
    config representation of one guild
    '''

    id: int
    name: Optional[str] = None
    log_channel: Optional[int] = None
    creators: List[Creator]

    @classmethod
    def load(
        cls,
        guild_id: int,
        guild_config_path: str = GUILDS_CONFIG_PATH
    ) -> Optional['GuildConfig']:
        """
        #! Use ConfigLoader.load instead
        Load a guild config from a JSON file.
        the file names are strings and do not contain the id.
        the script has to look for the id in the file content.
        """
        files = os.listdir(guild_config_path)

        for file in files:
            with open(os.path.join(guild_config_path, file), "r", encoding="utf-8") as f:

                try:
                    data = json.load(f)
                    if data["id"] == guild_id:
                        return cls(**data)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON from file {file}: {e}")

    @property
    def creator_category_ids(self) -> List[int]:
        """Get the list of all category IDs in the creators."""
        return [creator.general.category for creator in self.creators]

    @property
    def creator_channel_ids(self) -> List[int]:
        """Get the list of all channel IDs in the creators."""
        return [creator.general.channel for creator in self.creators]

    def is_creator_channel(self, channel_id: int) -> bool:
        """
        Check if a channel is a creator channel.
        A creator channel is a predefined voice channel that is explicitly listed in the guild's configuration.
        A channel is a creator channel if:
        - the channel.id is in the list of creator channels
        """
        if channel_id in self.creator_channel_ids:
            return True

        return False

    def is_temp_channel(self, channel: GuildChannel) -> bool:
        """
        Check if a channel is a temporary channel.
        Temporary channels are dynamically created voice channels that belong to a specific category associated with creators.
        A channel is a temporary channel if:
        - the channel is not a creator channel
        - the channel.category is in the list of creator category ids
        """
        if channel.type != ChannelType.GUILD_VOICE:
            return False

        # Check if the channel is a creator channel
        if self.is_creator_channel(channel):
            return False

        # check if the channel has a parent (category)
        channel_category = channel.parent_id
        if channel_category is None:
            return False

        # Check if the channel category is in the list of creator category ids
        if channel_category in self.creator_category_ids:
            return True

        return False

    def get_creator_by_channel_id(
        self, creator_channel_id: int
    ) -> Optional[Creator]:
        """
        Get the creator object by channel.
        A channel is a creator channel if:
        - the channel.id is in the list of creator channels
        """
        for creator in self.creators:
            if creator.general.channel == creator_channel_id:
                return creator
        return None

    def get_creator_by_category_id(
        self, category_id: int
    ) -> Optional[Creator]:
        """
        Get the creator object by category.
        A channel is a creator channel if:
        - the channel.id is in the list of creator channels
        """
        for creator in self.creators:
            if creator.general.category == category_id:
                return creator
        return None


class GuildConfigLoader:
    '''
    This class loads the configs of every guild.
    '''

    def __init__(
        self,
        guild_config_path: str = GUILDS_CONFIG_PATH
    ):
        self.guilds: List[GuildConfig] = []
        self.guilds = self.load(guild_config_path)

    def get_creator_by_creator_channel_id(
        self,
        channel_id: int
    ) -> Optional[Creator]:
        """
        Get the creator object by channel id.
        A channel is a creator channel if:
        - the channel.id is in the list of creator channels
        """
        for guild in self.guilds:
            creator = guild.get_creator_by_channel_id(channel_id)
            if creator is not None:
                return creator
        return None

    def get_creator_by_category_id(
        self,
        category_id: int
    ) -> Optional[Creator]:
        """
        Get the creator object by category id.
        A channel is a creator channel if:
        - the channel.id is in the list of creator channels
        """
        for guild in self.guilds:
            creator = guild.get_creator_by_category_id(category_id)
            if creator is not None:
                return creator
        return None

    def get_guild_by_id(
        self,
        guild_id: int
    ) -> Optional[GuildConfig]:
        """
        Get the guild object by id.
        A channel is a creator channel if:
        - the channel.id is in the list of creator channels
        """
        for guild in self.guilds:
            if guild.id == guild_id:
                return guild
        return None

    def get_guild_by_channel_id(
        self,
        channel_id: int
    ) -> Optional[GuildConfig]:
        """
        Get the guild object by channel id.
        A channel is a creator channel if:
        - the channel.id is in the list of creator channels
        """
        for guild in self.guilds:
            if guild.is_creator_channel(channel_id):
                return guild
        return None

    def load(
        self,
        guild_config_path: str = GUILDS_CONFIG_PATH
    ) -> List[GuildConfig]:
        """
        Load a guild config from a JSON file.
        the file names are strings and do not contain the id.
        the script has to look for the id in the file content.
        """

        # delete old guilds
        self.guilds = []

        files = os.listdir(guild_config_path)

        for file in files:
            with open(os.path.join(guild_config_path, file), "r", encoding="utf-8") as f:

                try:
                    data = json.load(f)
                    self.guilds.append(GuildConfig(**data))
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON from file {file}: {e}")
        return self.guilds
