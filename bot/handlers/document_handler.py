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
from bot.services.pdf_service import PdfService
from bot.utils.logger import logger

DEFAULT_PDF_NOTE = "Bu PDF'i ozetle"


async def handle_pdf_document(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    message = update.message
    if message is None or message.document is None:
        return

    document = message.document
    if document.mime_type != "application/pdf":
        return

    user_id = update.effective_chat.id

    memory_service: MemoryService = context.application.bot_data[
        "memory_service"
    ]
    agent: AssistantAgent = context.application.bot_data["agent"]
    pdf_service: PdfService = context.application.bot_data["pdf_service"]

    await context.bot.send_chat_action(
        chat_id=user_id,
        action=ChatAction.TYPING,
    )

    start_time = time.time()
    temp_path: str | None = None

    try:
        telegram_file = await context.bot.get_file(document.file_id)
        with tempfile.NamedTemporaryFile(
            suffix=".pdf", delete=False
        ) as temp_file:
            temp_path = temp_file.name
        await telegram_file.download_to_drive(temp_path)

        loop = asyncio.get_running_loop()
        pdf_text = await loop.run_in_executor(
            None,
            partial(pdf_service.extract_text, temp_path),
        )

        caption = (message.caption or "").strip() or DEFAULT_PDF_NOTE
        user_message = (
            f"[PDF icerigi]\n{pdf_text}\n\n"
            f"Kullanicinin notu: {caption}"
        )

        answer = await loop.run_in_executor(
            None,
            partial(
                agent.generate_reply,
                user_id=user_id,
                current_user_message=user_message,
            ),
        )
        elapsed = time.time() - start_time

        memory_service.save_message(user_id, "user", user_message)
        memory_service.save_message(user_id, "assistant", answer)
        memory_service.delete_old_messages(user_id)

        logger.info("PDF cevabi uretildi.")
        logger.info("%.2f saniye", elapsed)

        await message.reply_text(answer)
    except ValueError as exc:
        logger.exception("PDF text extraction failed")
        await message.reply_text(f"Kanka, PDF'i okuyamadim: {exc}")
    except Exception:
        logger.exception("PDF handling failed")
        await message.reply_text(
            "Kanka, PDF'i okuyamadim: beklenmedik bir hata olustu."
        )
    finally:
        if temp_path is not None:
            Path(temp_path).unlink(missing_ok=True)
