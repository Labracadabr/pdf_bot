import json
from api_integrations.translate_api import translate
from cv_and_pdf import read_pdf_pages, process_pdf
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


# Фильтр, проверяющий принадлежность текста сообщения к списку
class InMenuList(BaseFilter):
    # фильтр принимает список со словами
    def __init__(self, array: list[str]) -> None:
        self.array = array

    async def __call__(self, message: Message) -> bool:
        return message.text in self.array


# Состояния FSM, в которых будет находиться бот в разные моменты взаимодействия с юзером
class FSM(StatesGroup):
    put_text = State()
    put_sign = State()
    wait_pdf = State()
    wait_lang = State()
    wait_page = State()  # ввод номера страницы
    wait_languages = State()  # ввод языков


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


# изменить пдф и рендерить фото страницы
def render_pdf_page(user: str) -> FSInputFile:
    # путь пдф
    raw_pdf_path = f'{users_data}/{user}_raw.pdf'
    # путь отрендеренной фотки
    tmp_jpg = f'{users_data}/{user}_tmp.jpg'

    # задать значения
    coord = get_pers_info(user, 'coord')
    if coord is None:
        coord = {"x0": 200, "y0": 200, "x1": 300, "y1": 300}
        set_pers_info(user, key='coord', val=coord)
    # прочитать БД
    coord = get_pers_info(user=user, key='coord')
    page = get_pers_info(user=user, key='page')
    if not page:
        page = 0

    # шрифт
    font = get_pers_info(user=user, key='font')
    if not font:
        font = 30

    # режим - текст или подпись
    mode = get_pers_info(user, key='mode')
    sign_path = put_text = None
    if mode == 'sign':
        sign_path = f'{users_data}/{user}_transp.png'
        put_text = None
    elif mode == 'text':
        sign_path = None
        put_text = get_pers_info(user, key='put_text')

    process_pdf(image_path=sign_path, put_text=put_text, xyz=coord, temp_jpg_path=tmp_jpg, font=font,
                pdf_path=raw_pdf_path, page=page)

    return FSInputFile(tmp_jpg)


# запуск перевода
def trans(user: str) -> (FSInputFile, FSInputFile, ):
    lang_pair = get_pers_info(user, key='lang_pair').split()
    read_mode = get_pers_info(user, key='read_mode')

    # чтение пдф
    raw_pdf_path = f'{users_data}/{user}_raw.pdf'
    text_path = f'{users_data}/{user}_text_from_pdf.txt'
    render_tmp_path = f'{users_data}/{user}_ocr_tmp.png'
    read_pdf_pages(raw_pdf_path, text_path, read_mode=read_mode, language=lang_pair[0], render_tmp_path=render_tmp_path)

    # запуск перевода
    with open(text_path, 'r', encoding='utf-8') as f:
        # текст, который надо перевести
        to_translate = f.read()
    translation = translate(query=to_translate, target=lang_pair[1])

    # сохранить текст из пдф
    file_translated = f'{users_data}/{user}_translated.txt'
    with open(file_translated, 'w', encoding='utf-8') as f:
        print(translation, file=f)

    return FSInputFile(text_path), FSInputFile(file_translated)
