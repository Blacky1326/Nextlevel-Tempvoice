from typing import TYPE_CHECKING
import re
import time
import asyncio

from interactions import (
    Extension,
    component_callback,
    ComponentContext,
    Modal,
    ShortText,
    GuildVoice,
    PermissionOverwrite,
    Permissions,
    UserSelectMenu,
    ActionRow
)

# pylint: disable=broad-exception-raised

from ._buttons import (
    name,
    status,
    size,
    lock,
    unlock,
    kick,
    ban,
    invite,
    show_owner,
    take_owner,
    transfer_owner
)
from ..embed_maker import error_embed
from ..channel_logger import send_log_message
from ..channel_status import update_voice_channel_status
from ..channel_manager import TempChannel

if TYPE_CHECKING:
    from bot.channel_manager import TempChannelManager
    from bot.rate_limiter import RateLimitManager
    from bot.config_loader import GuildConfigLoader


class ButtonHandler(Extension):

    def get_rate_limiter(self) -> 'RateLimitManager':
        return self.bot.rlm

    def get_temp_channel_manager(self) -> 'TempChannelManager':
        return self.bot.tcm

    def get_guild_config(self) -> 'GuildConfigLoader':
        return self.bot.gcl

    @component_callback(re.compile(r"button|[a-zA-Z0-9_]+"))
    async def button_callback(self, ctx: ComponentContext) -> None:
        """Handle button click events."""

        user_voice = ctx.member.voice.channel if ctx.member.voice else None
        # check if user is in a voice channel
        if not user_voice:
            await ctx.send(
                embed=error_embed(
                    title="Fehler",
                    description="Du bist nicht in einem Sprachkanal."
                ),
                ephemeral=True,
                delete_after=5
            )
            return

        # check if user can perform action (rate limiting)
        button_ratelimit = False

        if button_ratelimit:
            rate_limiter = self.get_rate_limiter()
            can = rate_limiter.can_perform_action(ctx.member.id)
            if not can:
                descrition = f"Du kannst diesen Knopf verwenden: <t:{can.end_time()}:R>"
                await ctx.send(
                    embed=error_embed(
                        title="Nicht so schnell!",
                        description=descrition
                    ),
                    ephemeral=True,
                    delete_after=5
                )
                return

        # get channel manager and rate limiter
        channel_manager = self.get_temp_channel_manager()
        managed_channel = channel_manager.get_channel_by_id(
            user_voice.id)

        rate_limiter = self.get_rate_limiter()

        guild = self.get_guild_config()
        creator = guild.get_creator_by_category_id(user_voice.parent_id)

        if ctx.custom_id == take_owner.custom_id:
            await self.button_take_owner(ctx, user_voice)
            return

        if not managed_channel:
            await ctx.send(
                ephemeral=True,
                delete_after=5,
                embed=error_embed(
                    title="Fehler",
                    description="Dieser Kanal hat keinen Besitzer."
                )
            )
            return

        if ctx.custom_id not in [
            show_owner.custom_id,
            take_owner.custom_id
        ]:

            is_admin = creator.member_has_channel_owner_permissions(ctx.member)
            is_owner = managed_channel.owner == ctx.member.id

            # check if user is admin or owner of the channel
            if not is_admin and not is_owner:
                await ctx.send(
                    ephemeral=True,
                    delete_after=5,
                    embed=error_embed(
                        title="Fehler",
                        description="Du bist nicht der Besitzer dieses Kanals."
                    )
                )
                return

        match ctx.custom_id:
            # raw: general
            case name.custom_id:
                await self.button_name(ctx, user_voice)
            case status.custom_id:
                await self.button_status(ctx, user_voice)

            case size.custom_id:
                await self.button_size(ctx, user_voice)
            case lock.custom_id:
                await self.button_lock(ctx, user_voice)
            case unlock.custom_id:
                await self.button_unlock(ctx, user_voice)
            # raw: moderation
            case kick.custom_id:
                await self.button_kick(ctx, user_voice)
            case ban.custom_id:
                await self.button_ban(ctx, user_voice)
            case invite.custom_id:
                await self.button_invite(ctx, user_voice)
            # raw: ownership
            case show_owner.custom_id:
                await self.button_show_owner(ctx, user_voice)
            case take_owner.custom_id:
                await self.button_take_owner(ctx, user_voice)
            case transfer_owner.custom_id:
                await self.button_transfer_owner(ctx, user_voice)

        # todo: add modals for name and size
        # todo: add MemberSelecbutton|tMenu Response for kick, ban, invite, transfer
        # todo: record action in rate limiter

    # raw: general
    async def button_name(self, ctx: ComponentContext, user_voice: GuildVoice) -> None:
        '''sends a modal'''
        model = Modal(
            ShortText(
                label="Neuer Name",
                custom_id="channel_name",
                placeholder="Gib den neuen Namen ein",
                required=True,
                max_length=100,
                min_length=1
            ),
            title="Name des Kanals ändern",
            custom_id="channel_name",
        )
        await ctx.send_modal(model)

        try:
            model_ctx = await ctx.bot.wait_for_modal(modal=model, timeout=30)
        except asyncio.TimeoutError:
            return

        new_name = model_ctx.responses.get("channel_name")

        # rename channel
        try:
            await user_voice.edit(
                name=new_name,
                reason=f"Kanalname geändert von {ctx.member.username}",
            )
        except Exception:
            await model_ctx.send(
                ephemeral=True,
                delete_after=5,
                embed=error_embed(
                    title="Fehler",
                    description="Der Kanalname konnte nicht geändert werden."
                )
            )
            return

        # send confirmation message
        await model_ctx.send(
            ephemeral=True,
            delete_after=5,
            content=f"Kanalname geändert zu {new_name}",
        )

        # send log message
        try:
            config = self.get_guild_config()
            guild_config = config.get_guild_by_id(ctx.channel.guild.id)
            log_channel = ctx.guild.get_channel(guild_config.log_channel)
            await send_log_message(
                channel=log_channel,
                message=f"{ctx.member.mention} ({ctx.member.id}) hat den Kanalnamen geändert zu: **{new_name}**"
            )
        except Exception as e:
            print(e)

    async def button_status(self, ctx: ComponentContext, user_voice: GuildVoice) -> None:
        '''Sends a modal to update the status of the voice channel.'''
        model = Modal(
            ShortText(
                label="Neuer Status",
                custom_id="channel_status",
                placeholder="Gib den neuen Status ein",
                max_length=100
            ),
            title="Status des Kanals ändern",
            custom_id="channel_status",
        )
        await ctx.send_modal(model)

        try:
            model_ctx = await ctx.bot.wait_for_modal(modal=model, timeout=30)
        except asyncio.TimeoutError:
            return

        new_status = model_ctx.responses.get("channel_status")

        # Update the channel status
        try:
            bot_token = ctx.bot.token
            response = update_voice_channel_status(
                bot_token=bot_token,
                channel_id=str(user_voice.id),
                status=new_status,
                audit_log_reason=f"Status geändert von {ctx.member.username}"
            )
            print(response.status_code)
            if response.status_code != 204:
                raise Exception(
                    f"Failed to update status: {response.status_code}")
        except Exception:
            await model_ctx.send(
                ephemeral=True,
                delete_after=5,
                embed=error_embed(
                    title="Fehler",
                    description="Der Status konnte nicht geändert werden."
                )
            )
            return

        # Send confirmation message
        await model_ctx.send(
            ephemeral=True,
            delete_after=5,
            content=f"Status geändert zu: {new_status}",
        )

        # Send log message
        try:
            config = self.get_guild_config()
            guild_config = config.get_guild_by_id(ctx.channel.guild.id)
            log_channel = ctx.guild.get_channel(guild_config.log_channel)
            await send_log_message(
                channel=log_channel,
                message=f"{ctx.member.mention} ({ctx.member.id}) hat den Kanalstatus geändert zu: **{new_status}**"
            )
        except Exception as e:
            print(e)

    async def button_size(self, ctx: ComponentContext, user_voice: GuildVoice) -> None:
        '''sends a modal'''
        model = Modal(
            ShortText(
                label="Neue Größe",
                custom_id="channel_size",
                placeholder="Gib die neue Größe ein",
                required=True,
                max_length=2,
                min_length=1
            ),
            title="Größe des Kanals ändern",
            custom_id="channel_size",
        )
        await ctx.send_modal(model)

        try:
            model_ctx = await ctx.bot.wait_for_modal(modal=model, timeout=30)
        except asyncio.TimeoutError:
            return

        new_size = model_ctx.responses.get("channel_size")

        # check if new size is a number
        if not new_size.isdigit():
            await model_ctx.send(
                ephemeral=True,
                delete_after=5,
                embed=error_embed(
                    title="Fehler",
                    description="Die Größe muss eine Zahl sein."
                )
            )
            return

        # rename channel
        await user_voice.edit(
            user_limit=int(new_size),
            reason=f"Limit geändert von {ctx.member.username}",
        )

        # send confirmation message
        await model_ctx.send(
            ephemeral=True,
            delete_after=5,
            content=f"Limit geändert zu {new_size}"
        )

        # send log message
        try:
            config = self.get_guild_config()
            guild_config = config.get_guild_by_id(ctx.channel.guild.id)
            log_channel = ctx.guild.get_channel(guild_config.log_channel)
            await send_log_message(
                channel=log_channel,
                message=f"{ctx.member.mention} ({ctx.member.id}) hat das Kanal-Limit geändert zu: **{new_size}**"
            )
        except Exception as e:
            print(e)

    async def button_lock(self, ctx: ComponentContext, user_voice: GuildVoice) -> None:
        '''directly locks the channel'''

        everyone = user_voice.guild.default_role
        await user_voice.set_permission(everyone, connect=False, reason="Kanal wurde gesperrt")

        await ctx.send(
            ephemeral=True,
            delete_after=5,
            content="Kanal wurde gesperrt",
        )

        try:
            config = self.get_guild_config()
            guild_config = config.get_guild_by_id(ctx.channel.guild.id)
            log_channel = ctx.guild.get_channel(guild_config.log_channel)
            await send_log_message(
                channel=log_channel,
                message=f"{ctx.member.mention} ({ctx.member.id}) hat den Kanal gesperrt."
            )
        except Exception as e:
            print(e)

    async def button_unlock(self, ctx: ComponentContext, user_voice: GuildVoice) -> None:
        '''directly unlocks the channel'''

        everyone = user_voice.guild.default_role
        await user_voice.set_permission(everyone, connect=True, reason="Kanal wurde entsperrt")

        await ctx.send(
            ephemeral=True,
            delete_after=5,
            content="Kanal wurde entsperrt",
        )

        try:
            config = self.get_guild_config()
            guild_config = config.get_guild_by_id(ctx.channel.guild.id)
            log_channel = ctx.guild.get_channel(guild_config.log_channel)
            await send_log_message(
                channel=log_channel,
                message=f"{ctx.member.mention} ({ctx.member.id}) hat den Kanal entsperrt."
            )
        except Exception as e:
            print(e)

    # raw: moderation
    async def button_kick(self, ctx: ComponentContext, user_voice: GuildVoice) -> None:
        '''Sends an ephemeral message with a user select menu to kick a member from the channel.'''

        # Create a member select menu
        member_select = UserSelectMenu(
            custom_id="kick_member_select",
            placeholder="Wähle ein Mitglied aus",
            max_values=1
        )

        # Send the select menu to the user
        await ctx.send(
            ephemeral=True,
            delete_after=30,
            content="Wähle ein Mitglied aus, um es aus dem Kanal zu entfernen:",
            components=member_select
        )

        try:
            # Wait for the user's selection
            select_ctx = await ctx.bot.wait_for_component(
                components=member_select,
                timeout=30
            )
        except asyncio.TimeoutError:
            return

        # Get the selected member
        selected_member_id = select_ctx.ctx.values[0]
        selected_member = ctx.guild.get_member(int(selected_member_id))

        if not selected_member:
            await select_ctx.ctx.send(
                ephemeral=True,
                delete_after=5,
                embed=error_embed(
                    title="Fehler",
                    description="Das ausgewählte Mitglied konnte nicht gefunden werden."
                )
            )
            return

        # check if the selected member can not be kicked (creator config)
        creator = self.get_guild_config().get_creator_by_category_id(user_voice.parent_id)
        if creator.member_can_not_be_kicked(selected_member):
            await select_ctx.ctx.send(
                ephemeral=True,
                delete_after=5,
                embed=error_embed(
                    title="Fehler",
                    description="Das ausgewählte Mitglied kann nicht entfernt werden."
                )
            )
            return

        # Check if the selected member is in the voice channel
        if not selected_member.voice or selected_member.voice.channel.id != user_voice.id:
            await select_ctx.ctx.send(
                ephemeral=True,
                delete_after=5,
                embed=error_embed(
                    title="Fehler",
                    description="Das ausgewählte Mitglied ist nicht in diesem Kanal."
                )
            )
            return

        await selected_member.disconnect()

        # Send confirmation message
        await select_ctx.ctx.send(
            ephemeral=True,
            delete_after=5,
            content=f"{selected_member.mention} wurde erfolgreich aus dem Kanal entfernt."
        )

        # send log message
        try:
            config = self.get_guild_config()
            guild_config = config.get_guild_by_id(ctx.channel.guild.id)
            log_channel = ctx.guild.get_channel(guild_config.log_channel)
            await send_log_message(
                channel=log_channel,
                message=f"{ctx.member.mention} ({ctx.member.id}) hat {selected_member.mention} ({selected_member.id}) aus dem Kanal entfernt."
            )
        except Exception as e:
            print(e)

    async def button_ban(self, ctx: ComponentContext, user_voice: GuildVoice) -> None:
        '''Sends an ephemeral message with a user select menu to ban a member from the channel.'''

        # Create a member select menu
        member_select = UserSelectMenu(
            custom_id="ban_member_select",
            placeholder="Wähle ein Mitglied aus",
            max_values=1
        )

        # Send the select menu to the user
        await ctx.send(
            ephemeral=True,
            delete_after=30,
            content="Wähle ein Mitglied aus, um es aus dem Kanal zu verbannen:",
            components=member_select
        )

        try:
            # Wait for the user's selection
            select_ctx = await ctx.bot.wait_for_component(
                components=member_select,
                timeout=30
            )
        except asyncio.TimeoutError:
            return

        # Get the selected member
        selected_member_id = select_ctx.ctx.values[0]
        selected_member = ctx.guild.get_member(int(selected_member_id))

        if not selected_member:
            await select_ctx.ctx.send(
                ephemeral=True,
                delete_after=5,
                embed=error_embed(
                    title="Fehler",
                    description="Das ausgewählte Mitglied konnte nicht gefunden werden."
                )
            )
            return

        # Check if the selected member can not be banned (creator config)
        creator = self.get_guild_config().get_creator_by_category_id(user_voice.parent_id)
        if creator.member_can_not_be_kicked(selected_member):
            await select_ctx.ctx.send(
                ephemeral=True,
                delete_after=5,
                embed=error_embed(
                    title="Fehler",
                    description="Das ausgewählte Mitglied kann nicht verbannt werden."
                )
            )
            return

        await user_voice.set_permission(selected_member, connect=False, reason=f"Mitglied wurde von {ctx.member.username} verbannt")

        # only kick user if they are in the same voice channel
        if selected_member.voice and selected_member.voice.channel and selected_member.voice.channel.id == user_voice.id:
            await selected_member.disconnect()

        # Send confirmation message
        await select_ctx.ctx.send(
            ephemeral=True,
            delete_after=5,
            content=f"{selected_member.mention} wurde erfolgreich aus dem Kanal verbannt.",
        )

        # send log message
        try:
            config = self.get_guild_config()
            guild_config = config.get_guild_by_id(ctx.channel.guild.id)
            log_channel = ctx.guild.get_channel(guild_config.log_channel)
            await send_log_message(
                channel=log_channel,
                message=f"{ctx.member.mention} ({ctx.member.id}) hat {selected_member.mention} ({selected_member.id}) aus dem Kanal verbannt."
            )
        except Exception as e:
            print(e)

    async def button_invite(self, ctx: ComponentContext, user_voice: GuildVoice) -> None:
        '''Sends an ephemeral message with a user select menu to invite a member to the channel.'''

        # Create a member select menu
        member_select = UserSelectMenu(
            custom_id="invite_member_select",
            placeholder="Wähle ein Mitglied aus",
            max_values=1
        )

        # Send the select menu to the user
        await ctx.send(
            ephemeral=True,
            delete_after=30,
            content="Wähle ein Mitglied aus, um es in den Kanal einzuladen:",
            components=member_select
        )

        try:
            # Wait for the user's selection
            select_ctx = await ctx.bot.wait_for_component(
                components=member_select,
                timeout=30
            )
        except asyncio.TimeoutError:
            return

        # Get the selected member
        selected_member_id = select_ctx.ctx.values[0]
        selected_member = ctx.guild.get_member(int(selected_member_id))

        if not selected_member:
            await select_ctx.ctx.send(
                ephemeral=True,
                delete_after=5,
                embed=error_embed(
                    title="Fehler",
                    description="Das ausgewählte Mitglied konnte nicht gefunden werden."
                )
            )
            return

        await user_voice.set_permission(selected_member, connect=True, reason="Einladung in den Kanal")

        # Send confirmation message
        await select_ctx.ctx.send(
            ephemeral=True,
            delete_after=5,
            content=f"{selected_member.mention} wurde erfolgreich in den Kanal eingeladen."
        )

        # send log message
        try:
            config = self.get_guild_config()
            guild_config = config.get_guild_by_id(ctx.channel.guild.id)
            log_channel = ctx.guild.get_channel(guild_config.log_channel)
            await send_log_message(
                channel=log_channel,
                message=f"{ctx.member.mention} ({ctx.member.id}) hat {selected_member.mention} ({selected_member.id}) in den Kanal eingeladen."
            )
        except Exception as e:
            print(e)

    # raw: ownership
    async def button_show_owner(self, ctx: ComponentContext, user_voice: GuildVoice) -> None:
        '''Directly send an ephemeral message with the owner of the channel.'''
        channel_manager = self.get_temp_channel_manager()
        managed_channel = channel_manager.get_channel_by_id(user_voice.id)

        if not managed_channel:
            await ctx.send(
                ephemeral=True,
                delete_after=5,
                embed=error_embed(
                    title="Fehler",
                    description="Dieser Kanal hat keinen Besitzer."
                )
            )
            return

        owner_id = managed_channel.owner
        owner = ctx.guild.get_member(owner_id)

        if not owner:
            await ctx.send(
                ephemeral=True,
                delete_after=5,
                embed=error_embed(
                    title="Fehler",
                    description="Der Besitzer dieses Kanals konnte nicht gefunden werden."
                )
            )
            return

        await ctx.send(
            ephemeral=True,
            delete_after=10,
            content=f"Der Besitzer dieses Kanals ist: {owner.mention}"
        )

    async def button_take_owner(self, ctx: ComponentContext, user_voice: GuildVoice) -> None:
        '''Directly takes ownership of the channel if the current owner is not connected.'''

        # Get the channel manager and the managed channel
        channel_manager = self.get_temp_channel_manager()
        managed_channel = channel_manager.get_channel_by_id(user_voice.id)

        # users can claim a channel that doesnt have an owner
        if not managed_channel:
            channel_manager._add_channel(
                TempChannel(
                    channel=user_voice,
                    owner=ctx.bot.user,
                    created_at=int(time.time())
                )
            )

        # get newyl added channel
        managed_channel = channel_manager.get_channel_by_id(user_voice.id)

        # Check if the current owner is connected to the channel
        owner_id = managed_channel.owner
        owner = ctx.guild.get_member(owner_id)

        if owner and owner.voice and owner.voice.channel and owner.voice.channel.id == user_voice.id:
            await ctx.send(
                ephemeral=True,
                delete_after=5,
                embed=error_embed(
                    title="Fehler",
                    description="Der Besitzer ist noch im Kanal und kann nicht ersetzt werden."
                )
            )
            return

        # Transfer ownership to the user
        managed_channel.owner = ctx.member

        await ctx.send(
            ephemeral=True,
            delete_after=5,
            content=f"Du bist jetzt der Besitzer des Kanals: {user_voice.name}"
        )

        # send log message
        try:
            config = self.get_guild_config()
            guild_config = config.get_guild_by_id(ctx.channel.guild.id)
            log_channel = ctx.guild.get_channel(guild_config.log_channel)
            await send_log_message(
                channel=log_channel,
                message=f"{ctx.member.mention} ({ctx.member.id}) hat die Kanalbesitzerschaft übernommen: **{user_voice.name}**"
            )
        except Exception as e:
            print(e)

    async def button_transfer_owner(self, ctx: ComponentContext, user_voice: GuildVoice) -> None:
        '''Sends an ephemeral message with a user select menu to transfer ownership.'''

        # Get the channel manager and the managed channel
        channel_manager = self.get_temp_channel_manager()
        managed_channel = channel_manager.get_channel_by_id(user_voice.id)

        if not managed_channel:
            await ctx.send(
                ephemeral=True,
                delete_after=5,
                embed=error_embed(
                    title="Fehler",
                    description="Dieser Kanal hat keinen Besitzer."
                )
            )
            return

        # Create a member select menu
        member_select = UserSelectMenu(
            custom_id="transfer_owner_select",
            placeholder="Wähle ein Mitglied aus",
            max_values=1
        )

        # Send the select menu to the user
        await ctx.send(
            ephemeral=True,
            delete_after=30,
            content="Wähle ein Mitglied aus, um die Kanalbesitzerschaft zu übertragen:",
            components=member_select
        )

        try:
            # Wait for the user's selection
            select_ctx = await ctx.bot.wait_for_component(
                components=member_select,
                timeout=30
            )
        except asyncio.TimeoutError:
            return

        # Get the selected member
        selected_member_id = select_ctx.ctx.values[0]
        selected_member = ctx.guild.get_member(int(selected_member_id))

        if not selected_member:
            await select_ctx.ctx.send(
                ephemeral=True,
                delete_after=5,
                embed=error_embed(
                    title="Fehler",
                    description="Das ausgewählte Mitglied konnte nicht gefunden werden."
                )
            )
            return

        # Transfer ownership
        managed_channel.owner = selected_member.id

        await select_ctx.ctx.send(
            ephemeral=True,
            delete_after=5,
            content=f"Die Kanalbesitzerschaft wurde erfolgreich an {selected_member.mention} übertragen."
        )

        # send log message
        try:
            config = self.get_guild_config()
            guild_config = config.get_guild_by_id(ctx.channel.guild.id)
            log_channel = ctx.guild.get_channel(guild_config.log_channel)
            await send_log_message(
                channel=log_channel,
                message=f"{ctx.member.mention} ({ctx.member.id}) hat die Kanalbesitzerschaft an {selected_member.mention} ({selected_member.id}) übertragen."
            )
        except Exception as e:
            print(e)
