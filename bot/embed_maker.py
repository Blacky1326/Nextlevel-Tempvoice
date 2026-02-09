from interactions import Embed


def error_embed(
    title: str,
    description: str,
) -> Embed:
    '''
    Create a warning embed with the given title and description.
    '''
    embed = Embed(
        title=title,
        description=description,
        color=0xFF0000,  # Red color for warning
    )
    return embed
