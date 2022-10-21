(communications)=
# AutoTrader Communications Module


## Telegram
AutoTrader supports using a [Telegram Bot](https://core.telegram.org/bots/api)
for notifications. To make use of this, there are a few simple steps you 
must complete:
1. Create a new Telegram bot using the [BotFather](https://telegram.me/BotFather).
2. Run the code snippet below from your [project directory](rec-dir-struc).
3. If you haven't already, start a conversation with your newly created bot
on telegram.
4. Send the following message to it: "write id". This will automatically write
your Telegram details to your [`keys.yaml`](global-config) file.
5. Press `ctrl+c` to interrupt the bot. Now you are ready to use Telegram
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
manually, or use the code snippet above!

```yaml
TELEGRAM:
  api_key: < telegram api key >
  chat_id: < telegram chat ID >
```
