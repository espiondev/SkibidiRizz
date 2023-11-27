# SkibidiRizz

Telegram bot for downloading music from MuseScore

# Dependencies

PyPi dependencies are installed with [poetry](https://python-poetry.org/).
[NodeJS](https://nodejs.org/) must be installed with a user PATH entry (a global entry will not be recognized)

# Planned features

- Password authentication
- Musescore search
- Better UX (buttons, slash commands)

# Usage

1. Register a Telegram bot with [@BotFather](https://t.me/BotFather)
2. Find its token, right after the line "`Use this token to access the HTTP API:`"
3. Create a `token.txt` file in `%APPDATA%\skibidirizz\` on windows or `$HOME/.config/skibidirizz/` on linux (Alternatively, pass the file path as an argument to the `-t` or `--token` options)
4. Run `python -m skibidirizz` to start the bot
5. In Telegram, use the /start command to start the bot or reset its state

# Known issues

Any bugs relating to downloading music are most likely caused by [dl-librescore](https://github.com/LibreScore/dl-librescore), so file an issue over there!

# Development
See [DEVELOPMENT.md](./DEVELOPMENT.md "Development Intructions")
