import asyncio

from telegram import Bot


class TelegramSender:
    def __init__(self, bot_token: str) -> None:
        self.bot_token = bot_token

    def send_text(self, chat_id: int, text: str) -> None:
        asyncio.run(self._send_text(chat_id, text))

    async def _send_text(self, chat_id: int, text: str) -> None:
        async with Bot(token=self.bot_token) as bot:
            await bot.send_message(chat_id=chat_id, text=text)
