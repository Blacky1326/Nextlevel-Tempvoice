from interactions import ActionRow

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

INTERFACE = [
    ActionRow(
        name,
        status,
        size,
        lock,
        unlock
    ),
    ActionRow(
        kick,
        ban,
        invite
    ),
    ActionRow(
        take_owner,
        transfer_owner,
        show_owner
    ),

]
