import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiohttp import web

# Безопасный импорт библиотеки Pocket Option
PocketClient = None
try:
    from pocketoptionapi_async import AsyncPocketOptionClient as PocketClient
except ImportError:
    try:
        from pocketoptionapi_async.client import client as PocketClient
    except ImportError:
        pass

BOT_TOKEN = os.getenv("BOT_TOKEN", "8069847497:AAFFl6NS1TX9NOQ5O_UB5u66wATI7GADfJI")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Встроенный веб-сервер для бесплатного тарифа Render ($0)
async def handle(request):
    return web.Response(text="Bot is running 24/7!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

user_ssids = {}

def get_main_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Баланс и Профиль", callback_data="get_profile")],
            [InlineKeyboardButton(text="⚙️ Ввести / Обновить SSID", callback_data="set_ssid")],
        ]
    )

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("👋 **Привет! Я твой трекер Pocket Option.**", reply_markup=get_main_keyboard(), parse_mode="Markdown")

@dp.callback_query(F.data == "set_ssid")
async def process_set_ssid(callback: types.CallbackQuery):
    await callback.message.answer("🔑 Отправь свой SSID сообщением в чат.")
    await callback.answer()

@dp.message()
async def save_ssid(message: types.Message):
    if "auth" in message.text or "session" in message.text or len(message.text) > 10:
        user_ssids[message.from_user.id] = message.text.strip()
        await message.answer("✅ **SSID сохранен!**", reply_markup=get_main_keyboard(), parse_mode="Markdown")

@dp.callback_query(F.data == "get_profile")
async def process_profile(callback: types.CallbackQuery):
    ssid = user_ssids.get(callback.from_user.id)
    if not ssid:
        await callback.message.answer("⚠️ Сначала укажи SSID!")
        await callback.answer()
        return

    if PocketClient is None:
        await callback.message.answer("❌ Ошибка загрузки модуля Pocket Option.")
        await callback.answer()
        return

    try:
        client = PocketClient(ssid=ssid)
        await client.connect()
        balance = await client.get_balance()
        await client.disconnect()
        await callback.message.answer(f"💵 **Баланс:** `{balance} $`", reply_markup=get_main_keyboard(), parse_mode="Markdown")
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {e}")
    await callback.answer()

async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
