import asyncio
import pandas as pd
import os
from datetime import datetime
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

#.env-ро мехонем
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CSV_FILE = "users.csv"

if not TOKEN or not ADMIN_ID:
    raise ValueError("BOT_TOKEN ё ADMIN_ID дар.env нест!")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

class BroadcastState(StatesGroup):
    waiting_message = State()

def save_user(user_id: int, username: str | None, full_name: str) -> None:
    try:
        df = pd.read_csv(CSV_FILE)
    except FileNotFoundError:
        df = pd.DataFrame(columns=["user_id", "username", "full_name", "joined_date"])
    if user_id not in df["user_id"].values:
        new_user = {
            "user_id": user_id,
            "username": username or "н/д",
            "full_name": full_name,
            "joined_date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        df = pd.concat([df, pd.DataFrame([new_user])], ignore_index=True)
        df.to_csv(CSV_FILE, index=False, encoding='utf-8')

def get_stats() -> tuple[int, int]:
    try:
        df = pd.read_csv(CSV_FILE)
        total = len(df)
        today = datetime.now().strftime("%Y-%m-%d")
        today_users = len(df[df["joined_date"].str.startswith(today)])
        return total, today_users
    except:
        return 0, 0

def get_all_user_ids() -> list[int]:
    try:
        df = pd.read_csv(CSV_FILE)
        return df["user_id"].tolist()
    except:
        return []

def admin_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="📊 Омори бот")],
        [KeyboardButton(text="📢 Фиристодани паём")],
        [KeyboardButton(text="📁 Гирифтани CSV")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    save_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    if message.from_user.id == ADMIN_ID:
        await message.answer("Салом, Админ! Панели шумо 👨‍💼", reply_markup=admin_keyboard())
    else:
        await message.answer(f"Салом, <b>{message.from_user.full_name}</b>! Хуш омадед.")

@dp.message(F.text == "📊 Омори бот")
async def admin_stats(message: Message) -> None:
    if message.from_user.id!= ADMIN_ID: return
    total, today = get_stats()
    await message.answer(f"📊 <b>Омор:</b>\n\n👥 Ҳамагӣ: <code>{total}</code>\n🆕 Имрӯз: <code>{today}</code>")

@dp.message(F.text == "📁 Гирифтани CSV")
async def admin_get_csv(message: Message) -> None:
    if message.from_user.id!= ADMIN_ID: return
    try:
        await message.answer_document(FSInputFile(CSV_FILE), caption="Рӯйхати корбарон")
    except FileNotFoundError:
        await message.answer("❌ Корбаре нест.")

@dp.message(F.text == "📢 Фиристодани паём")
async def admin_broadcast_start(message: Message, state: FSMContext) -> None:
    if message.from_user.id!= ADMIN_ID: return
    await message.answer("Паёмро фиристед. /cancel барои бекор кардан")
    await state.set_state(BroadcastState.waiting_message)

@dp.message(BroadcastState.waiting_message, Command("cancel"))
async def cancel_broadcast(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Бекор шуд.", reply_markup=admin_keyboard())

@dp.message(BroadcastState.waiting_message)
async def admin_broadcast_send(message: Message, state: FSMContext) -> None:
    user_ids = get_all_user_ids()
    success = failed = 0
    status_msg = await message.answer(f"⏳ Фиристодан ба {len(user_ids)} нафар...")
    for user_id in user_ids:
        try:
            await bot.copy_message(user_id, message.chat.id, message.message_id)
            success += 1
        except:
            failed += 1
        await asyncio.sleep(0.04)
    await status_msg.edit_text(f"✅ Тайёр!\n📤 Муваффақ: {success}\n📛 Хато: {failed}")
    await state.clear()
    await message.answer("Панел:", reply_markup=admin_keyboard())

async def main() -> None:
    print("Бот оғоз шуд...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())