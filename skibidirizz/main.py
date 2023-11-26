import re
import subprocess
import sys
import tempfile
from urllib.parse import urlparse

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

ENTER_LINK, PICK_FILETYPE = range(2)
user_data = {}


def validate_ms_url(url: str | None):
    if url is None:
        return

    parsed = urlparse(url)
    path_pattern = re.compile(r"/user/\d+/scores/\d+", re.IGNORECASE)

    if parsed.hostname != "musescore.com":
        raise ValueError("Incorrect domain name!")
    elif path_pattern.match(parsed.path) is None:
        raise ValueError("Malformed URL!")


def validate_choice(inp: str, choices: list[str]) -> str:
    if inp not in choices:
        raise ValueError(f"`{inp}` not a valid choice!")

    return inp


def dl_librescore(url: str, format: str, file: str):
    cmd = ["npx", "dl-librescore@latest", "-i", url, "-t", format, "-o", file]
    subprocess.run(cmd, shell=True, check=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None:
        return

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Hi! To download sheet music, please send a musescore link.",
    )
    if context.user_data is None:
        context.user_data = {}

    context.user_data["state"] = ENTER_LINK


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return

    if update.effective_chat is None:
        return

    if context.user_data is None:
        return

    user = update.message.from_user
    text = update.message.text
    state = context.user_data.get("state")
    chat_id = update.effective_chat.id

    if user is None:
        return

    if state == ENTER_LINK and text:
        try:
            validate_ms_url(text)
        except ValueError as ve:
            await context.bot.send_message(chat_id, ve.args[0])
            return

        user_data[user.id] = {"link": text}
        await context.bot.send_message(
            chat_id,
            "Type the file format you'd like to download the score in:\nmp3\nmidi\npdf",
        )

        context.user_data["state"] = PICK_FILETYPE

    elif state == PICK_FILETYPE and text:
        user_data[user.id]["filetype"] = text.lower().strip()

        try:
            format = validate_choice(
                user_data[user.id]["filetype"], ["mp3", "midi", "pdf"]
            )
        except ValueError as ve:
            await context.bot.send_message(chat_id=chat_id, text=ve.args[0])
            return

        # Delete is false for windows reasons (beyond human comprehension)
        with tempfile.NamedTemporaryFile("w+b", delete=False) as score_dl:
            try:
                dl_librescore(user_data[user.id]["link"], format, score_dl.name)
            except subprocess.CalledProcessError as cpe:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"Operation Failed: `dl-librescore` exited with status {cpe.returncode}",
                )
                return

            if format == "mp3":
                await context.bot.send_audio(
                    chat_id, audio=score_dl, filename=f"{score_dl.name}.mp3"
                )
            elif format == "pdf":
                await context.bot.send_document(
                    chat_id, document=score_dl, filename=f"{score_dl.name}.pdf"
                )
            elif format == "midi":
                await context.bot.send_document(
                    chat_id, document=score_dl, filename=f"{score_dl.name}.mid"
                )

        await context.bot.send_message(chat_id, "File uploaded. Enjoy!")
        return


if len(sys.argv) >= 3 and (sys.argv[1] == "-t" or sys.argv[1] == "--token"):
    token = sys.argv[2]
else:
    with open("token.txt", "r") as file:
        token = file.read().strip()


application = ApplicationBuilder().token(token=token).build()

start_handler = CommandHandler("start", start)
application.add_handler(start_handler)
msg_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
application.add_handler(msg_handler)

application.run_polling()
