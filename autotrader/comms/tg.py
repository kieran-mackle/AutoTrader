import os
import telegram
from autotrader.brokers.trading import Order
from autotrader.comms.notifier import Notifier
from autotrader.utilities import read_yaml, write_yaml, print_banner
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters


class Telegram(Notifier):
    def __init__(self, api_token: str = None, chat_id: str = None) -> None:
        self.api_token = api_token
        self.chat_id = chat_id

        if api_token is not None:
            self.bot = telegram.Bot(api_token)

    def __repr__(self) -> str:
        return "AutoTrader-Telegram communication module"

    def send_order(self, order: Order, *args, **kwargs) -> None:
        side = "long" if order.direction > 0 else "short"
        message = (
            f"New {order.instrument} {order.order_type} order created: "
            + f"{order.size} units {side}"
        )

        # Create bot and send message
        self.bot.send_message(chat_id=self.chat_id, text=message)

    def send_message(self, message: str, *args, **kwargs) -> None:
        """A generic method to send a custom message.

        Parameters
        ----------
        message : str
            The message to be sent.
        """
        # Send message
        self.bot.send_message(chat_id=self.chat_id, text=message)

    def run_bot(self) -> None:
        """A method to initialise your bot and get your chat ID.
        This method should be running before you send any messages
        to it on Telegram. To start, message the BotFather on
        Telegram, and create a new bot. Use the API token provided
        to run this method.

        Parameters
        ----------
        api_token : str
            The API token of your telegram bot.

        Returns
        -------
        None.

        """
        print_banner()
        print("                              AutoTrader Telegram Bot")
        print("\n  Listening for messages...")

        # Check for api token
        if self.api_token is None:
            path = "config/keys.yaml"
            if os.path.exists(path):
                # Look to fetch api token from config file
                config = read_yaml(path)
                if "TELEGRAM" in config:
                    if (
                        config["TELEGRAM"] is not None
                        and "api_key" in config["TELEGRAM"]
                    ):
                        self.api_token = config["TELEGRAM"]["api_key"]

                    else:
                        print(
                            "Please add your Telegram API key to the "
                            + "keys.yaml file."
                        )
                        return
                else:
                    print(
                        "Please add a 'TELEGRAM' key to the keys.yaml "
                        + "file, with a sub-key for the 'api_key'."
                    )
                    return

        updater = Updater(self.api_token, use_context=True)
        dp = updater.dispatcher

        dp.add_handler(CommandHandler("start", self._start_command))
        dp.add_handler(CommandHandler("help", self._help_command))

        dp.add_handler(MessageHandler(Filters.text, self._handle_message))

        updater.start_polling()
        updater.idle()

    @staticmethod
    def _start_command(
        update,
        context,
    ):
        # Extract user name and chat ID
        name = update.message.chat.first_name
        chat_id = str(update.message.chat_id)

        # Create response
        response = (
            f"Hi {name}, welcome to your very own AutoTrader "
            + f"Telegram bot. Your chat ID is {chat_id}. Use this to "
            + "set-up trading notifications. Note that this ID has also "
            + "been printed to your computer screen for reference."
        )
        print("\n  Start command activated.")
        print(f"    Chat ID: {chat_id}")

        # Send response
        update.message.reply_text(response)

    @staticmethod
    def _help_command(
        update,
        context,
    ):
        update.message.reply_text("Help is on the way!")

    # @staticmethod
    def _handle_message(self, update, context):
        text = str(update.message.text).lower()

        if "id" in text:
            chat_id = str(update.message.chat_id)

            if "write" in text:
                # Write chat ID to keys.yaml file
                path = "config/keys.yaml"
                if os.path.exists(path):
                    # Config file exists, proceed
                    config = read_yaml(path)

                    if "TELEGRAM" in config:
                        config["TELEGRAM"]["chat_id"] = chat_id
                    else:
                        config["TELEGRAM"] = {
                            "api_key": self.api_token,
                            "chat_id": chat_id,
                        }

                    # Write to file
                    write_yaml(config, path)

                    print("\n  Telegram API keys successfully written to file.")

                    response = "All done."

                else:
                    response = (
                        "I couldn't find your keys.yaml directory. "
                        + "Make sure you are running the bot from your project "
                        + "home directory, with config/keys.yaml within it."
                    )

            else:
                # Return chat ID
                response = f"Your chat ID is {chat_id}."

                if "print" in text or "show" in text:
                    print(f"\n  Chat ID: {chat_id}")
                    response += " This has also been printed to your computer."

        elif "thank" in text or "ty" in text:
            response = "You're welcome."

        else:
            response = "I'm not quite ready to respond to that..."
        update.message.reply_text(response)

    @staticmethod
    def _error(update, context):
        print(f"Update {update} caused error {context.error}")
