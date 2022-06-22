import telegram
from autotrader import Order


def send_oder(order: Order, api_token: str, chat_id: str):
    
    
    message = ''
    
    # Create bot and send message
    bot = telegram.Bot(api_token)
    bot.send_message(chat_id=chat_id, text=message)


def send_message(api_token: str, chat_id: str, message):
    # Create bot and send message
    bot = telegram.Bot(api_token)
    bot.send_message(chat_id=chat_id, text=message)
    
    