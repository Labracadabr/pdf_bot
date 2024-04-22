import json
from pprint import pprint
from aiogram.filters import BaseFilter
from aiogram.filters.state import State, StatesGroup
import os
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, CallbackQuery, FSInputFile, User
from aiogram import Bot
from datetime import datetime
from aiogram.types import BotCommand
from config import config
from settings import commands, users_data


# Инициализация бота
TKN = config.BOT_TOKEN
bot_func: Bot = Bot(token=TKN)


# получить значение
def get_pers_info(user: str, key: str):
    path = f'{users_data}/{user}.json'
    if os.path.exists(path):
        # прочитать бд
        with open(path, 'r', encoding='utf-8') as f:
            user_data: dict = json.load(f)
    else:
        user_data: dict = {}
    value = user_data.get(key)
    return value


# задать значение
def set_pers_info(user: str, key: str, val):
    path = f'{users_data}/{user}.json'

    if os.path.exists(path):
        # прочитать бд
        with open(path, 'r', encoding='utf-8') as f:
            user_data: dict = json.load(f)
    else:
        user_data: dict = {}
    old_val = user_data.get(key)

    # сохр изменение
    user_data[key] = val
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(user_data, f, indent=2, ensure_ascii=False)
    print(user, f'{key}: {old_val} => {val}')


# ссылка на скачивание тг-файла
async def download_link_by_id(file_id: str) -> str:
    file_info = await bot_func.get_file(file_id)
    file_url = file_info.file_path
    url = f'https://api.telegram.org/file/bot{TKN}/{file_url}'
    return url


# Фильтр, проверяющий доступ юзера
class Access(BaseFilter):
    # фильтр принимает список со строками id
    def __init__(self, access: list[str]) -> None:
        self.access = access

    # вернуть True если юзер в списке
    async def __call__(self, message: Message) -> bool:
        user_id_str = str(message.from_user.id)
        return user_id_str in self.access


# создать команды в меню
async def set_menu_commands(bot: Bot) -> None:
    await bot.set_my_commands([BotCommand(command=item[0], description=item[1]) for item in commands.items()])
    print('Команды созданы')

    # ссылка на бота
    bot_info = await bot.get_me()
    bot_link = f"https://t.me/{bot_info.username}"
    print(f'{bot_link = }')


# Состояния FSM, в которых будет находиться бот в разные моменты взаимодействия с юзером
class FSM(StatesGroup):
    put_text = State()
    put_sign = State()
    page = State()


# запись логов в tsv, консоль
async def log(file, key, item):
    t = str(datetime.now()).split('.')[0]
    log_text = '\t'.join((t, str(key), repr(item)))

    # сохранить в tsv
    try:
        with open(file, 'a', encoding='utf-8') as f:
            print(log_text, file=f)
    except Exception as e:
        log_text += f'\n🔴Ошибка записи в tsv:\n{e}'

    # дублировать логи в консоль
    print(log_text)


# айди из текста
def id_from_text(text: str) -> str:
    user_id = ''
    for word in text.split():
        if word.lower().startswith('id'):
            for symbol in word:
                if symbol.isnumeric():
                    user_id += symbol
            break
    return user_id


# написать имя и ссылку на юзера, даже если он без username
def contact_user(user: User) -> str:
    tg_url = f'<a href="tg://user?id={user.id}">{user.full_name}</a>'
    text = f'{tg_url} id{user.id} @{user.username}'
    return text
