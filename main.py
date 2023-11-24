import string
import subprocess
import random
import shutil
import os
from telegram import Update
from telegram.ext import (
    filters,
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
)

ENTER_LINK, PICK_FILETYPE = range(2)
user_data = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Hi! To download sheet music, please send a musescore link.",
    )
    context.user_data["state"] = ENTER_LINK


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text
    state = context.user_data.get("state")
    msg = ""
    if state == ENTER_LINK:
        user_data[user.id] = {"link": text}
        msg = (
            f"Type the file format you'd like to download the score in:\nmp3\nmidi\npdf"
        )

        context.user_data["state"] = PICK_FILETYPE

    else:
        if text not in ["mp3", "midi", "pdf"]:
            msg = "Invalid file type."
            await context.bot.send_message(chat_id=update.effective_chat.id, text=msg)
            return

        user_data[user.id]["filetype"] = text
        folder_name = "".join(
            random.choice(
                string.ascii_uppercase + string.ascii_lowercase + string.digits
            )
            for _ in range(5)
        )
        os.mkdir(f"tmp/{folder_name}")
        command = f'npx dl-librescore@latest -i {user_data[user.id]["link"]} -t {user_data[user.id]["filetype"]} -o ./tmp/{folder_name}/'
        subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        file_path = f"tmp/{folder_name}/{os.listdir(f'tmp/{folder_name}')[0]}"
        context.user_data["state"] = ENTER_LINK
        if user_data[user.id]["filetype"] == "mp3":
            await context.bot.send_audio(
                audio=open(file_path, "rb"), chat_id=update.effective_chat.id
            )
        else:
            await context.bot.send_document(
                document=open(file_path, "rb"), chat_id=update.effective_chat.id
            )

        shutil.rmtree(f"tmp/{folder_name}")
        return
    await context.bot.send_message(chat_id=update.effective_chat.id, text=msg)


with open("token.txt", "r") as file:
    token = file.read().strip()


application = ApplicationBuilder().token(token=token).build()

start_handler = CommandHandler("start", start)
application.add_handler(start_handler)
msg_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
application.add_handler(msg_handler)

application.run_polling()
