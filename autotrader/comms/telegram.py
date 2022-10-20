import telegram
from autotrader import Order
from autotrader.comms.notifier import Notifier
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters


class Telegram(Notifier):
    def __init__(self, api_token: str, chat_id: str = None) -> None:
        self.api_token = api_token
        self.chat_id = chat_id
        self.bot = telegram.Bot(self.api_token)
    
    def __repr__(self) -> str:
        return "AutoTrader-Telegram communication module"

    def send_order(self, order: Order, *args, **kwargs) -> None:
        side = 'long' if order.direction > 1 else 'short'
        message = f'New {order.instrument} {order.order_type} order created: '+\
            f'{order.size} units {side}'
        
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
        updater = Updater(self.api_token, use_context=True)
        dp = updater.dispatcher
        
        dp.add_handler(CommandHandler('start', self._start_command))
        dp.add_handler(CommandHandler('help', self._help_command))
        
        dp.add_handler(MessageHandler(Filters.text, self._handle_message))
        
        updater.start_polling()
        updater.idle()

        # TODO - add feature to write the chat ID to the keys.yaml 
        # config file
    
    @staticmethod
    def _start_command(update, context,):
        # Extract user name and chat ID
        name = update.message.chat.first_name
        chat_id = str(update.message.chat_id)

        # Create response
        response = f"Hi {name}, welcome to your very own AutoTrader "+\
            f"Telegram bot. Your chat ID is {chat_id}. Use this to "+\
            "set-up trading notifications. Note that this ID has also "+\
            "been printed to your computer screen for reference."
        print(f"Chat ID: {chat_id}")

        # Send response
        update.message.reply_text(response)

    @staticmethod
    def _help_command(update, context,):
        update.message.reply_text("Help is on the way!")

    @staticmethod
    def _handle_message(update, context):
        text = str(update.message.text).lower()

        if "id" in text:
            # Return chat ID
            chat_id = str(update.message.chat_id)
            response = f"Your chat ID is {chat_id}."

            if "print" in text or "show" in text:
                print(f"Chat ID: {chat_id}")
                response += " This has also been printed to your computer."

        else:
            response = "I'm not quite ready to respond to that..."
        update.message.reply_text(response)

    @staticmethod
    def _error(update, context):
        print(f"Update {update} caused error {context.error}")
    