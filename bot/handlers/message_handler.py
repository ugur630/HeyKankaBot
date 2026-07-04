import time

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from bot.core.agent import AssistantAgent
from bot.services.memory_service import MemoryService
from bot.utils.logger import logger


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    del context
    await update.message.reply_text(
        "Selam kanka!\nHeyKankaBot hazir ve seni bekliyor."
    )


async def handle_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    message = update.message
    if message is None or message.text is None:
        return

    user_id = update.effective_chat.id
    user_message = message.text

    logger.info(f"User: {user_message}")

    memory_service: MemoryService = context.application.bot_data[
        "memory_service"
    ]
    agent: AssistantAgent = context.application.bot_data["agent"]

    await context.bot.send_chat_action(
        chat_id=user_id,
        action=ChatAction.TYPING,
    )

    start_time = time.time()

    try:
        answer = agent.generate_reply(
            user_id=user_id,
            current_user_message=user_message,
        )
        elapsed = time.time() - start_time

        memory_service.save_message(user_id, "user", user_message)
        memory_service.save_message(user_id, "assistant", answer)
        memory_service.delete_old_messages(user_id)

        logger.info("AI cevap uretti.")
        logger.info("%.2f saniye", elapsed)

        await message.reply_text(answer)
    except Exception:
        logger.exception("AI response failed")
        await message.reply_text(
            "Kanka, AI motoruna su an ulasamiyorum."
        )
