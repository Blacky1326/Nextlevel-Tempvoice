from interactions import (
    Extension,
    slash_command,
    Permissions,
    SlashContext
)

from ._interface import INTERFACE


class SendInterfaceCommand(Extension):

    @slash_command(
        name="interface",
        description="Sendet das Interface in den Kanal",
        default_member_permissions=Permissions.ADMINISTRATOR,
    )
    async def send_interface(self, ctx: SlashContext) -> None:

        await ctx.defer(ephemeral=True)

        # send the interface to the channel
        await ctx.channel.send(
            content="# Kanal-Einstellungen",
            components=INTERFACE
        )

        # send success message
        await ctx.send(
            content="Interface wurde gesendet.",
            ephemeral=True,
            delete_after=1
        )
