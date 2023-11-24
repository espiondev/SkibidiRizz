# SkibidiRizz

Telegram bot for downloading music from MuseScore

# Dependancies

PyPi dependancies are in requirements.txt  
[NodeJS](https://nodejs.org/) must be installed with a user PATH entry (a global entry will not be recognized)

# Planned features

- Password authentication
- Musescore search
- Better UX (buttons, slash commands)

# Instructions

1. Register a Telegram bot with [@BotFather](https://t.me/BotFather)
2. Find its token, right after the line "`Use this token to access the HTTP API:`"
3. Create a `token.txt` file in the same directory as `main.py` and paste the token into the file
4. Run the python file
5. Use the /start command to start the bot

# Known issues

Any bugs relating to downloading music are caused by [dl-librescore](https://github.com/LibreScore/dl-librescore)
