import asyncio
import tempfile
import time
from functools import partial
from pathlib import Path

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from bot.core.agent import AssistantAgent
from bot.services.memory_service import MemoryService
from bot.services.speech_service import SpeechService
from bot.utils.helpers import split_message
from bot.utils.logger import logger


async def handle_voice_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    message = update.message
    if message is None or message.voice is None:
        return

    user_id = update.effective_chat.id

    memory_service: MemoryService = context.application.bot_data[
        "memory_service"
    ]
    agent: AssistantAgent = context.application.bot_data["agent"]
    speech_service: SpeechService = context.application.bot_data[
        "speech_service"
    ]

    await context.bot.send_chat_action(
        chat_id=user_id,
        action=ChatAction.TYPING,
    )

    start_time = time.time()
    temp_path: str | None = None

    try:
        telegram_file = await context.bot.get_file(message.voice.file_id)
        with tempfile.NamedTemporaryFile(
            suffix=".ogg", delete=False
        ) as temp_file:
            temp_path = temp_file.name
        await telegram_file.download_to_drive(temp_path)

        loop = asyncio.get_running_loop()
        transcript = await loop.run_in_executor(
            None,
            partial(speech_service.transcribe, temp_path),
        )

        for chunk in split_message(f"\U0001F3A4 Anladigim: {transcript}"):
            await message.reply_text(chunk)

        answer = await loop.run_in_executor(
            None,
            partial(
                agent.generate_reply,
                user_id=user_id,
                current_user_message=transcript,
            ),
        )
        elapsed = time.time() - start_time

        memory_service.save_message(user_id, "user", transcript)
        memory_service.save_message(user_id, "assistant", answer)
        memory_service.delete_old_messages(user_id)

        logger.info("Sesli mesaj cevabi uretildi.")
        logger.info("%.2f saniye", elapsed)

        for chunk in split_message(answer):
            await message.reply_text(chunk)
    except Exception:
        logger.exception("Voice message handling failed")
        await message.reply_text(
            "Kanka, sesli mesaji su an isleyemedim."
        )
    finally:
        if temp_path is not None:
            Path(temp_path).unlink(missing_ok=True)
