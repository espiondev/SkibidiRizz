import os
import re
import subprocess
import shutil
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

ENTER_LINK, PICK_FILETYPE, FILE_UPLOADED = range(3)
SUPPORTED_FORMATS = ["mp3", "midi", "pdf"]
user_data = {}


def cli_error(msg: str, fatal: bool = False, code: int = 1):
    err = "ERROR: " + msg

    if fatal:
        print(err + ". Exiting.")
        sys.exit(code)

    print(err)


def get_token(path: str) -> str:  # type: ignore
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        cli_error(f"Token file `{path}` not found", fatal=True)


def validate_ms_url(url: str | None):
    if url is None:
        return

    parsed = urlparse(url)
    path_pattern = re.compile(r"/user/\d+/scores/\d+", re.IGNORECASE)
    alt_path_pattern = re.compile(r"/[\d\w-]+/[\d\w-]+", re.IGNORECASE)

    if parsed.hostname != "musescore.com":
        raise ValueError("Incorrect domain name!")
    elif path_pattern.match(parsed.path) is None and alt_path_pattern.match(parsed.path) is None:
        raise ValueError("Malformed URL!")


def validate_choice(inp: str, choices: list[str]) -> str:
    if inp not in choices:
        raise ValueError(f"`{inp}` is not a valid choice!")

    return inp


def dl_librescore(url: str, format: str, file: str):
    cmd = ["npx", "--yes", "dl-librescore@latest", "-i", url, "-t", format, "-o", file]
    subprocess.run(cmd, capture_output=True, check=True)


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
    
    if state == FILE_UPLOADED and text:
        try:
            validate_ms_url(text)
            context.user_data["state"] = ENTER_LINK
            state = context.user_data.get("state")
        except ValueError:
            try:
                validate_choice(text, SUPPORTED_FORMATS)
                context.user_data["state"] = PICK_FILETYPE
                state = context.user_data.get("state")
            except ValueError:
                await context.bot.send_message(chat_id, "Error: Please send a musescore link to start another download or choose another format to download.")

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
                user_data[user.id]["filetype"], SUPPORTED_FORMATS
            )
        except ValueError as ve:
            await context.bot.send_message(chat_id=chat_id, text=ve.args[0])
            return

        # Delete is false for windows reasons (beyond human comprehension)
        with tempfile.TemporaryDirectory() as score_dir:
            try:
                dl_librescore(user_data[user.id]["link"], format, score_dir)
            except subprocess.CalledProcessError as cpe:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"Operation Failed: `dl-librescore` exited with status {cpe.returncode}",
                )
                return
            
            score = os.path.join(score_dir, os.listdir(score_dir)[0])

            if format == "mp3":
                await context.bot.send_audio(
                    chat_id, audio=score,
                )
            elif format == "pdf":
                await context.bot.send_document(
                    chat_id, document=score,
                )
            elif format == "midi":
                await context.bot.send_document(
                    chat_id, document=score,
                )

        await context.bot.send_message(chat_id, "File uploaded. Enjoy!")
        context.user_data["state"] = FILE_UPLOADED
        return


def run_bot():
    if "-h" in sys.argv[1:] or "--help" in sys.argv[1:]:
        print("Usage:")
        print(f"  skibidirizz [options]")
        print("\nOPTIONS")
        print("  -h, --help          Prints this help section")
        print(
            "  -t, --token TOKEN   Token is from TOKEN rather than configuration directory (default)"
        )
        sys.exit(0)

    if len(sys.argv) >= 3 and (sys.argv[1] == "-t" or sys.argv[1] == "--token"):
        token_path = sys.argv[2]

        token = get_token(token_path)

    else:
        token_dir = os.getcwd()
        if os.name == "nt":
            config_dir = os.getenv("APPDATA")
            token_dir = f"{config_dir}/skibidirizz"
        elif os.name == "posix":
            config_dir = os.getenv("HOME")
            token_dir = f"{config_dir}/.config/skibidirizz"

        if not os.path.isdir(token_dir):
            os.makedirs(token_dir)

        token = get_token(f"{token_dir}/token.txt")

    if shutil.which("npx") is None:
        cli_error("npx not found in PATH", fatal=True)
    
    application = ApplicationBuilder().token(token=token).build()

    start_handler = CommandHandler("start", start)
    application.add_handler(start_handler)
    msg_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    application.add_handler(msg_handler)

    print("Bot starting...")
    application.run_polling()


if __name__ == "__main__":
    run_bot()
