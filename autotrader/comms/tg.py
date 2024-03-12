import os
import requests
from autotrader.brokers.trading import Order
from autotrader.comms.notifier import Notifier
from autotrader.utilities import read_yaml, write_yaml, get_logger


class Telegram(Notifier):
    """Simple telegram bot to send messages.

    To use this, you must first create a Telegram bot via the BotFather. Then,
    provide the API token generated here as the api_token. If you do not know
    your chat_id, send the bot a message on telegram, and it will be inferred
    when this class is instantiated with the api_token.
    """

    def __repr__(self) -> str:
        return "AutoTrader-Telegram communication module"

    def __init__(
        self, api_token: str, chat_id: str = None, logger_kwargs: dict = None
    ) -> None:
        """Instantiate the bot.

        Parameters
        ----------
        token : str
            The bot API token.

        chat_id : str, optional
            The default chat_id to send messages to.
        """
        # Create logger
        logger_kwargs = logger_kwargs if logger_kwargs else {}
        self.logger = get_logger(name="telegram_combot", **logger_kwargs)

        # Save attributes
        self.token = api_token
        if chat_id is None:
            # Try get chat ID
            self.logger.info(
                "No chat ID specified - attempting to load from recent updates."
            )
            _, chat_id = self.get_chat_id()
        self.chat_id = chat_id

    def get_chat_id(self):
        response = requests.get(f"https://api.telegram.org/bot{self.token}/getUpdates")
        try:
            chat = response.json()["result"][-1]["message"]["chat"]
            chat_id = chat["id"]
            name = chat["first_name"]
            self.logger.info(f"Found chat ID for {name}: {chat_id}.")

            # Write ID to file for future
            path = "config/keys.yaml"
            if os.path.exists(path):
                # Config file exists, proceed
                config = read_yaml(path)

                if "TELEGRAM" in config:
                    # Telegram in config
                    self.logger.info("Adding chat_id to configuration file.")
                    if "chat_id" not in config["TELEGRAM"]:
                        # Add chat ID
                        config["TELEGRAM"]["chat_id"] = chat_id
                else:
                    # Telegram not in config; insert fresh
                    self.logger.info(
                        "Adding telegram configuration details to configuration file."
                    )
                    config["TELEGRAM"] = {
                        "api_key": self.token,
                        "chat_id": chat_id,
                    }

                # Write to file
                write_yaml(config, path)

            return name, chat_id

        except IndexError:
            # No updates to read from
            self.logger.error(
                "Cannot find chat ID - please make sure you have recently messaged the bot."
            )
            return None, None

    def send_message(self, message: str, chat_id: str = None, *args, **kwargs):
        if chat_id is None:
            chat_id = self.chat_id
        self.logger.debug(f"Sending message to {chat_id}: {message}")
        url_req = f"https://api.telegram.org/bot{self.token}/sendMessage?chat_id={chat_id}&text={message}"
        response = requests.get(url_req)
        if response.status_code != 200:
            self.logger.error(f"Failed to send message to {chat_id}: {response.reason}")

    def send_order(self, order: Order, *args, **kwargs) -> None:
        side = "long" if order.direction > 0 else "short"
        message = (
            f"New {order.instrument} {order.order_type} order created: "
            + f"{order.size} units {side}"
        )

        # Create bot and send message
        self.send_message(message)
