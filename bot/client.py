import sys
import logging
import colorlog

from interactions import (
    Client,
    Activity,
    ActivityType,
    Intents
)

# custom imports
from bot.rate_limiter import RateLimitManager
from bot.channel_manager import TempChannelManager
from bot.config_loader import GuildConfigLoader

EXTENSIONS = [
    'bot.events.ready',
    'bot.events.voice',
    'bot.interface.send_cmd',
    'bot.interface.button_handler',
    'bot.commands.reload_server'
]


def make_logger(name: str) -> logging.Logger:
    '''Create a logger with a file handler and a console handler.'''

    # file handler
    file_handler = logging.FileHandler("bot.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)

    # console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    # color formatter for console handler with timestamps
    color_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(levelname)s:%(reset)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        }
    )
    # set formatters
    console_handler.setFormatter(color_formatter)
    file_handler.setFormatter(formatter)

    # Configure the logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


def make_client(
    version: str,
    bot_token: str,
    logger: logging.Logger = None
) -> Client:
    client = Client(

        activity=Activity(
            name="TempVoice",
            state=f"v{version}",
            type=ActivityType.PLAYING
        ),

        delete_unused_application_cmds=True,
        disable_dm_commands=True,
        send_command_tracebacks=True,  # todo: remove in production,
        logger=logger,
        intents=Intents.new(
            default=True,
            guild_members=True,
            guild_voice_states=True
        ),
        token=bot_token
    )

    # Bind custom attributes to the client
    client.version = version
    client.rlm = RateLimitManager(rate_limit_in_seconds=5)
    client.tcm = TempChannelManager(rate_limiter=client.rlm)
    client.gcl = GuildConfigLoader()

    # load extensions
    logger.info("-" * 50,)
    client.logger.info(f"Loading {len(EXTENSIONS)} extensions...")
    for extension in EXTENSIONS:
        try:
            client.load_extension(extension)
            client.logger.info(f"Loaded extension {extension}")
        except Exception as e:
            client.logger.error(f"Failed to load extension {extension}: {e}")
    logger.info("-" * 50,)

    return client
