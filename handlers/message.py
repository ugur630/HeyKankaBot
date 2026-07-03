import time

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from memory.conversation import add_message, get_history
from services.ai_service import ask_ai
from utils.logger import logger


async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_message = update.message.text

    logger.info(f"👤 User: {user_message}")
    add_message(chat_id, "user", user_message)
    history = get_history(chat_id)

    await context.bot.send_chat_action(
        chat_id=chat_id,
        action=ChatAction.TYPING,
    )

    start = time.time()

    try:
        answer = ask_ai(history)
        elapsed = time.time() - start
        logger.info("🤖 AI cevap üretti.")
        logger.info(f"⏱️ {elapsed:.2f} saniye")

        add_message(chat_id, "assistant", answer)
        await update.message.reply_text(answer)
    except Exception:
        logger.exception("AI response failed")
        await update.message.reply_text(
            "Kanka, AI motoruna su an ulasamiyorum."
        )
