from interactions import Button, ButtonStyle

name = Button(
    style=ButtonStyle.GRAY,
    label="Name",
    custom_id="button|name",
    emoji="<:name:1365789806776549518>"
)

status = Button(
    style=ButtonStyle.GRAY,
    label="Status",
    custom_id="button|status",
    emoji="<:status:1366524672543293541>"
)

size = Button(
    style=ButtonStyle.GRAY,
    label="Größe",
    custom_id="button|size",
    emoji="<:size:1365789860635480207>"
)

lock = Button(
    style=ButtonStyle.GRAY,
    label="Privat",
    custom_id="button|lock",
    emoji="<:lock:1365789938079105185>"
)

unlock = Button(
    style=ButtonStyle.GRAY,
    label="Öffentlich",
    custom_id="button|unlock",
    emoji="<:unlock:1365789902989688892>"
)

kick = Button(
    style=ButtonStyle.GRAY,
    label="Kicken",
    custom_id="button|kick",
    emoji="<:kick:1365790141482008698>"
)

ban = Button(
    style=ButtonStyle.GRAY,
    label="Bannen",
    custom_id="button|ban",
    emoji="<:ban:1365790175434899516>"
)

invite = Button(
    style=ButtonStyle.GRAY,
    label="Entbannen",
    custom_id="button|invite",
    emoji="<:invite:1365790248155746499>"
)

show_owner = Button(
    style=ButtonStyle.GRAY,
    label="Besitzer",
    custom_id="button|show_owner",
    emoji="<:owner_show:1365795100235534387>"
)

take_owner = Button(
    style=ButtonStyle.GRAY,
    label="Übernehmen",
    custom_id="button|take_owner",
    emoji="<:owner_take:1365795251381342350>"
)

transfer_owner = Button(
    style=ButtonStyle.GRAY,
    label="Übertragen",
    custom_id="button|transfer_owner",
    emoji="<:owner_transfer:1365795261544271982>"
)
