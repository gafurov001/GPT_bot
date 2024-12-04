import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher, html, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, CallbackQuery, \
    FSInputFile, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder
from freeGPTFix import Client

from config import bot_token
from forms import Form
from functions import validate_full_name
from modles import create_table, User

TOKEN = bot_token

dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext, bot: Bot):
    is_auth = await User.filter(User.user_id == message.from_user.id)
    is_auth = [i for i in is_auth]
    if not len(is_auth):
        await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!\nIsim va Familyangizni kiriting")
        await state.set_state(Form.full_name)
    else:
        await save_contact(message, state, bot)


@dp.message(Form.phone_number)
async def save_contact(message: Message, state: FSMContext, bot: Bot):
    is_auth = await User.filter(User.user_id == message.from_user.id)
    is_auth = [i for i in is_auth]
    if not len(is_auth):
        if message.contact.user_id == message.from_user.id:
            data = await state.get_data()
            await User.create(phone_number=message.contact.phone_number, user_id=message.from_user.id,
                              full_name=data.get('full_name'))
            await message.answer("Ro'yxatdan muvofaqiyatli ottingiz!", reply_markup=ReplyKeyboardRemove())
            await command_start_handler(message, state, bot)
        else:
            await message.answer('Telegon raqam sizga tegishli emas, iltimos tugma orqali yuboring!')
            await state.set_state(Form.phone_number)
    else:
        if bot.id == message.message_id:
            await bot.delete_message(message.chat.id, message.message_id)
        ikb = InlineKeyboardBuilder().add(InlineKeyboardButton(text="Matin", callback_data='matin'),
                                          InlineKeyboardButton(text="Rasim", callback_data='rasim'))
        await message.answer("Savolingiz turini tanlang", reply_markup=ikb.as_markup())


@dp.callback_query(F.data == 'matin')
async def text_ai(callback: CallbackQuery, state: FSMContext, bot: Bot):
    is_auth = await User.filter(User.user_id == callback.from_user.id)
    is_auth = [i for i in is_auth]
    if not len(is_auth):
        await save_contact(callback.message, state, bot)
    else:
        await bot.delete_message(callback.message.chat.id, callback.message.message_id)
        await callback.message.answer('Savolingizni yozing')
        await state.set_state(Form.text)


@dp.callback_query(F.data == 'rasim')
async def image_ai(callback: CallbackQuery, state: FSMContext, bot: Bot):
    is_auth = await User.filter(User.user_id == callback.from_user.id)
    is_auth = [i for i in is_auth]
    if not len(is_auth):
        await save_contact(callback.message, state, bot)
    else:
        await bot.delete_message(callback.message.chat.id, callback.message.message_id)
        await callback.message.answer('Rasimni tasvirlab bering')
        await state.set_state(Form.image)


@dp.callback_query(F.data == 'update_question_type')
async def image_ai(callback: CallbackQuery, bot: Bot):
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    ikb = InlineKeyboardBuilder().add(InlineKeyboardButton(text="Matin", callback_data='matin'),
                                      InlineKeyboardButton(text="Rasim", callback_data='rasim'))
    await callback.message.answer("Savolingiz turini tanlang", reply_markup=ikb.as_markup())


@dp.message(Form.text)
async def text_generate(message: Message):
    try:
        msg = await message.answer('🔍')
        resp = Client.create_completion("gpt4", message.text)
        await msg.delete()
        await message.answer(f"🤖: {resp}\n\nYana yordam kerak bolsa yozishingiz mumkin!",
                             reply_markup=InlineKeyboardBuilder(
                                 markup=[[InlineKeyboardButton(text='Savol turini ozgartirish',
                                                               callback_data='update_question_type')]]).as_markup())
    except Exception as e:
        await message.answer(f"🤖: {e}")


@dp.message(Form.image)
async def image_generate(message: Message):
    try:
        msg = await message.answer('🔍')
        resp = Client.create_generation("pollinations", message.text)
        with open(f"{message.from_user.id}.png", "wb") as f:
            f.write(resp)
        await msg.delete()
        await message.answer_photo(FSInputFile(f'{message.from_user.id}.png'),
                                   caption="🤖: Mana sizning yaratilgan tasviringiz!\n\nYana yordam kerak bolsa yozishingiz mumkin!",
                                   reply_markup=InlineKeyboardBuilder(
                                       markup=[[InlineKeyboardButton(text='Savol turini ozgartirish',
                                                                     callback_data='update_question_type')]]).as_markup())
        os.remove(f"{message.from_user.id}.png")

    except Exception as e:
        await message.answer(f"🤖: {e}")


@dp.message(Form.full_name)
async def save_full_name(message: Message, state: FSMContext):
    if validate_full_name(message.text):
        await state.update_data(full_name=message.text)
        kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True,
                                 keyboard=[[KeyboardButton(text="Telefon raqanmi jo'natish☎️", request_contact=True)]])
        await message.answer('Telefon raqamingizni yuboring tugma orqali!', reply_markup=kb)
        await state.set_state(Form.phone_number)
    else:
        await message.answer("Isim yoki familyani noto'g'ri kiritdingiz boshqatdan harakat qilib koring!")
        await state.set_state(Form.full_name)


async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    create_table()
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
