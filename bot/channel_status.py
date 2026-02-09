'''
This script updates the status of a voice channel on Discord using the Discord API.

Disclaimer:
The endpoint used in this script is not yet officially documented in the Discord API documentation.
Please note that this endpoint or its behavior might change in the future.

To keep track of the changes and discussions regarding this endpoint
you can refer to the following links:
- https://github.com/discord/discord-api-docs/pull/6400
- https://github.com/discord/discord-api-docs/pull/6398
'''

import requests


def update_voice_channel_status(
    bot_token: str,
    channel_id: str,
    status: str,
    audit_log_reason: str = None
) -> requests.Response:
    """
    Updates the voice channel status on Discord.

    Args:
        bot_token (str): The bot token for authentication.
        channel_id (str): The ID of the Discord channel.
        status (str): The status to set for the voice channel.
        audit_log_reason (str, optional): The reason for the audit log. Defaults to None.
    """
    # Discord API endpoint
    url = f"https://discord.com/api/v9/channels/{channel_id}/voice-status"

    payload = {
        "status": status,
    }
    headers = {
        "Authorization": f"Bot {bot_token}",
        "Content-Type": "application/json",
        "User-Agent": "DiscordBot",
    }

    # Add audit log reason if provided
    if audit_log_reason:
        headers["X-Audit-Log-Reason"] = audit_log_reason

    response = requests.put(url, json=payload, headers=headers, timeout=2)
    return response


# Example usage
if __name__ == "__main__":
    # Read the bot token from the file
    with open("config/bot.key", "r", encoding="utf-8") as file:
        token = file.read().strip()

    # Example channel ID and status
    example_channel_id = "1359565234305634476"
    new_status = "hey"
    reason = "Testing the voice channel status update"

    # Update the voice channel status
    update_voice_channel_status(token, example_channel_id, new_status, reason)
