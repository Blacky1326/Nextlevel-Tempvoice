import time
from interactions import GuildText, AllowedMentions


def now() -> int:
    return int(time.time())


def make_timestamp_string(
    current: int,
    version: str
) -> str:

    full_data = f"v{version} | <t:{current}:d>"
    full_time = f"<t:{current}:T>"
    return f"{full_data}@{full_time}"


async def send_log_message(
    channel: GuildText,
    message: str,
) -> bool:
    '''
    more infots at https://sesh.fyi/timestamp/
    '''
    t = make_timestamp_string(now(), channel.bot.version)
    content = f"{t}\n> {message}"

    try:
        await channel.send(
            content,
            allowed_mentions=AllowedMentions.none()
        )
        return True
    except Exception as e:
        return False
