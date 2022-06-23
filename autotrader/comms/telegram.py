import telegram
from autotrader import Order
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters


def send_oder(order: Order, api_token: str, chat_id: str):
    
    side = 'long' if order.direction > 1 else 'short'
    message = f'New {order.instrument} {order.order_type} order created: '+\
        f'{order.size} units {side}'
    
    # Create bot and send message
    bot = telegram.Bot(api_token)
    bot.send_message(chat_id=chat_id, text=message)


def send_message(api_token: str, chat_id: str, message: str):
    """A generic method to send a custom message.

    Parameters
    ----------
    api_token : str
        The API token of your telegram bot.
    chat_id : str
        The chat ID to send the message to.
    message : str
        The message to be sent.
    """
    # Create bot and send message
    bot = telegram.Bot(api_token)
    bot.send_message(chat_id=chat_id, text=message)


def sample_response(input_text):
    user_message = str(input_text).lower()
    
    if user_message in ("hello",):
        return "hello, back."

    return "Error"


def start_command(update, context,):
    update.message.reply_text("Type something to get started")
    


def help_command(update, context,):
    update.message.reply_text("Help is on the way!")


def handle_message(update, context):
    text = str(update.message.text).lower()
    response = sample_response(text)
    
    update.message.reply_text(response)
    
    print(str(update.message.chat_id))
    

def error(update, context):
    print(f"Update {update} caused error {context.error}")
    
def initialise_bot(api_token: str):
    """A method to initialise your bot and get your chat ID. This method
    should be running before you send any messages to it on Telegram. To start,
    message the BotFather on Telegram, and create a new bot. Use the API token 
    provided to run this method.

    Parameters
    ----------
    api_token : str
        The API token of your telegram bot.

    Returns
    -------
    None.

    """
    updater = Updater(api_token, use_context=True)
    dp = updater.dispatcher
    
    
    
    dp.add_handler(CommandHandler('start', start_command))
    dp.add_handler(CommandHandler('help', help_command))
    
    dp.add_handler(MessageHandler(Filters.text, handle_message))
    
    updater.start_polling()
    updater.idle()
    
    pass
    