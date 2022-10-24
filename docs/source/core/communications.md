(communications)=
# AutoTrader Communications Module


## Telegram
AutoTrader supports using a [Telegram Bot](https://core.telegram.org/bots/api)
for notifications. To make use of this, there are a few simple steps you 
must complete:

1. Create a new Telegram bot using the [BotFather](https://telegram.me/BotFather). 
Once you have gone through the prompts, you will be given a HTTP access token. 
Copy this token.
2. Run the code snippet below from within your [project directory](rec-dir-struc), 
passing in the token copied above from the BotFather as `telegram_token`. This
will start running the bot on your computer.
3. If you haven't already, start a conversation with your newly created bot
on Telegram: type and send the `/start` command. Your chat ID will be printed
to the console running the bot. This chat ID will be used for trading notifications.
4. Send the following message to the bot: "write id". This will automatically write
your Telegram details to your [`keys.yaml`](global-config) file. 
5. Press `ctrl+c` to kill the bot. Now you are ready to use Telegram
for trading notifications.


```python
from autotrader.comms import Telegram

# Instantiate the bot and run it to get chat ID
tb = Telegram(telegram_token)
tb.run_bot()
```


### Keys
Activating Telegram notifications requires the following keys
in your [`keys.yaml`](global-config) file. You can add them
manually, or use the code snippet above to let the bot do it! 

```yaml
TELEGRAM:
  api_key: < telegram api key >
  chat_id: < telegram chat ID >
```

Note that once you have added your details as shown below, the 
`Telegram` class can be instantiated without the API token; it
will locate it in your `keys.yaml` file.
