
# .env imports
import os
from dotenv import load_dotenv

# custom imports
from bot.client import make_client, make_logger


load_dotenv()

__version__ = "1.3.4"


def main() -> None:
    bot = make_client(
        version=__version__,
        bot_token=os.getenv("DISCORD_BOT_TOKEN"),
        logger=make_logger(__name__)
    )
    bot.start()


if __name__ == '__main__':
    main()
