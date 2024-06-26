import os.path
from aiogram import Router, F
from aiogram.filters import Command, CommandStart, StateFilter, or_f
from utils import *
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Message, FSInputFile, InputMediaPhoto
from config import config
from settings import *
from cv_and_pdf import read_sign, process_pdf, count_pdf_pages, delete_pdf_pages
import keyboards
from api_integrations.translate_api import language_codes, translate

# Инициализация бота
TKN = config.BOT_TOKEN
router: Router = Router()
storage: MemoryStorage = MemoryStorage()


# команда /start
@router.message(CommandStart())
async def start_command(message: Message, bot: Bot, state: FSMContext):
    await state.clear()
    user = message.from_user
    msg_time = message.date.strftime('%Y-%m-%d %H:%M:%S')
    user_id = str(user.id)
    await log(logs, user_id, f'start {contact_user(user=user)}')

    # сохранить юзера
    user_data = get_pers_info(user=user_id, key='first_start')
    if user_data is None:
        set_pers_info(user=user_id, key='first_start', val=msg_time)
        set_pers_info(user=user_id, key='tg_fullname', val=user.full_name)
        coord = {"x0": 200, "y0": 200, "x1": 300, "y1": 300}
        set_pers_info(user=user_id, key='coord', val=coord)
        set_pers_info(user=user_id, key='font', val=30)

    # приветствие
    text = (
        'Привет! Этот бот предназначен для работы с документами PDF и их обработки. К его функциям относятся следующие:'
        '\n1. Подпись документа PDF.'
        '\n2. Добавление информации в определенное место документа PDF.'
        '\n3. Перевод страниц документа PDF на указанный язык с выводом в новый документ.'
        '\n4. Удаление указанных страниц.'
        '\nВыбери действие по обработке твоего PDF документа 👇')

    await message.answer(text=text, reply_markup=keyboards.keyboard_menu)
    # сообщить админу, кто стартанул бота
    alert = f'➕ user {contact_user(user=user)}'
    for i in admins:
        await bot.send_message(text=alert, chat_id=i, disable_notification=True, parse_mode='HTML')

    # логи
    await log(logs, user_id, f'{msg_time}, {user.full_name}, @{user.username}, id {user.id}, {user.language_code}')


# кнопка Назад
@router.message(F.text == 'Назад')
async def key_return(msg: Message, state: FSMContext):
    await log(logs, msg.from_user.id, msg.text)

    text = f'Выберите действие в меню 👇'
    await msg.answer(text=text, reply_markup=keyboards.keyboard_menu)
    await state.clear()


# команда translate > спросить языки
@router.message(or_f(Command('translate'), F.text == 'Перевод'))
async def ask_lang(msg: Message, state: FSMContext):
    await log(logs, msg.from_user.id, msg.text)

    text = f'Укажите, с какого языка на какой перевести - два кода через пробел, например:\nen ru'
    await msg.answer(text=text, reply_markup=keyboards.keyboard_return)

    # ожидание ввода языков
    await state.set_state(FSM.wait_languages)


# юзер указал языки > спросить способ чтения ПДФ
@router.message(StateFilter(FSM.wait_languages))
async def ask_read(msg: Message, state: FSMContext):
    user = str(msg.from_user.id)
    await log(logs, user, msg.text)

    # если нет текста
    alert = 'Я ожидаю два языковых кода через пробел, в формате:\nen ru'
    if not msg.text:
        await msg.answer(text=alert)
        return

    lang_pair = msg.text.lower().split()
    print(f'{lang_pair = }')

    # проверить правильность ввода
    if len(lang_pair) == 2 and lang_pair[0] in language_codes.keys() and lang_pair[1] in language_codes.keys():
        # сохранить
        set_pers_info(user=user, key='lang_pair', val=f'{lang_pair[0]} {lang_pair[1]}')
        set_pers_info(user, key='mode', val='translate')

        await msg.answer(text=f'✅ Сохранена пара языков: {lang_pair[0].upper()} -> {lang_pair[1].upper()}')
        await state.clear()

        # спросить способ чтения
        text = ('Выберите способ извлечение текста из PDF:\n'
                '▫️ OCR - оптическое распознавание символов с помощью компьютерного зрения '
                '(подходит, если текст расположен на картинке; при этом результат может быть неточный)\n'
                '▫️ TEXT - чтение текста из файла (если текст сохранен как текст)')
        await msg.answer(text=text, reply_markup=keyboards.keyboard_read)

    elif len(lang_pair) != 2:
        await msg.answer(text=alert)

    else:
        wrong = ''
        if lang_pair[0] not in language_codes.keys():
            wrong = lang_pair[0]
        elif lang_pair[1] not in language_codes.keys():
            wrong = lang_pair[1]
        await msg.answer(text=f'Язык {wrong.upper()} не поддерживается')


# указан способ чтения ПДФ
@router.callback_query(lambda x: x.data in ('ocr', 'text'))
async def put_command(callback: CallbackQuery, bot: Bot, state: FSMContext):
    user = str(callback.from_user.id)
    msg_id = callback.message.message_id

    # сохр способ чтения
    data = callback.data
    await log(logs, user, data)
    print(f'{data = }')
    set_pers_info(user, 'read_mode', val=data)
    text = f'✅ Выбран режим {data.upper()}\nОтправьте PDF документ, который нужно перевести'
    await bot.edit_message_text(text=text, reply_markup=None, message_id=msg_id, chat_id=user)
    await state.set_state(FSM.wait_pdf)


# команды 'put_text', 'put_sign'
@router.message(or_f(Command('put_text', 'put_sign'),
                     or_f(F.text == 'Вставить подпись', F.text == 'Вставить текст')))
async def put_command(msg: Message, state: FSMContext):
    user = str(msg.from_user.id)
    await log(logs, user, msg.text)

    # режим - текст или подпись
    if 'sign' in msg.text or 'Вставить подпись' in msg.text:
        mode = 'sign'
        text = 'Отправьте документ PDF, в который нужно вставить подпись'
    elif 'text' in msg.text or 'Вставить текст' in msg.text:
        mode = 'text'
        text = 'Отправьте документ PDF, в который нужно добавить текст'
    else:
        raise AssertionError
    await msg.answer(text=text, reply_markup=keyboards.keyboard_return)

    # сохранить режим
    set_pers_info(user, key='mode', val=mode)

    # запросить пдф
    await log(logs, user, 'waiting pdf')
    await state.set_state(FSM.wait_pdf)


# юзер прислал подпись -> спросить номер страницы
@router.message(or_f(StateFilter(FSM.put_sign), ))
async def save_sign(msg: Message, bot: Bot, state: FSMContext):
    user = str(msg.from_user.id)
    await log(logs, user, 'reading sign')

    # если нет фото
    if not msg.photo:
        await msg.answer(text='Я ожидаю фото подписи')
        return

    # download
    inp_path = f'{users_data}/{user}_raw.jpg'
    file_id = msg.photo[-1].file_id
    await msg.answer(text='Чтение фото')
    await bot.download(file=file_id, destination=inp_path)

    # обработать фото
    out_path = f'{users_data}/{user}_transp.png'
    read_sign(img_path=inp_path, out_path=out_path)

    print(f'sending {out_path}')
    await bot.send_photo(chat_id=user, photo=FSInputFile(out_path))
    await msg.answer(
        text='Подпись сохранена (можете сфотографировать и отправить её заново сейчас, если не получилась).'
             '\nТеперь отправьте номер страницы, на которую нужно вставить. (отчет начинается с 1).')

    # ожидание номера страницы
    await state.set_state(FSM.wait_page)


# юзер прислал свой ПДФ
@router.message(StateFilter(FSM.wait_pdf))
async def receive_pdf(msg: Message, bot: Bot, state: FSMContext):
    user = str(msg.from_user.id)
    await bot.send_chat_action(action='typing', chat_id=user)

    alert = 'Я ожидаю файл в формате PDF'
    if not msg.document:
        await msg.answer(text=alert)
        return

    doc_type = msg.document.mime_type
    await log(logs, user, f'{doc_type = }')
    if not doc_type.endswith('pdf'):
        await msg.answer(text=alert)
        return
    msg_to_delete = await msg.answer(text="Скачиваю ваш файл...")

    # download
    inp_path = f'{users_data}/{user}_raw.pdf'
    file_id = msg.document.file_id
    await bot.download(file=file_id, destination=inp_path)
    await bot.delete_message(chat_id=user, message_id=msg_to_delete.message_id)
    mode = get_pers_info(user, key='mode')

    # ожидание подписи
    if mode == 'sign':
        await msg.answer(text='Ваш PDF сохранен. '
                              'Теперь сделайте фото вашей подписи - для этого возьмите белый лист, распишитесь на нем '
                              'и сделайте фото, чтобы не попадал фон.')
        await state.set_state(FSM.put_sign)

    # ожидание текста
    elif mode == 'text':
        await msg.answer(text='Ваш PDF сохранен. Теперь введите текст, который нужно добавить в ваш документ.')
        await state.set_state(FSM.put_text)

    # ожидание номеров страниц на удаление
    elif mode == 'delete':
        await msg.answer(text='Ваш PDF сохранен. Теперь введите номера страниц, которые нужно удалить, через пробел. '
                              'Например:\n6 7 12')
        await state.set_state(FSM.delete_pages)

    # запустить перевод
    elif mode == 'translate':
        await msg.answer(text='Ваш PDF сохранен, ожидайте перевод.')
        text_path, file_translated = trans(user)

        # отправить файл с исходным текстом
        await bot.send_document(chat_id=user, document=text_path, caption="Исходный текст")
        # отправить файл с переводом
        await bot.send_document(chat_id=user, document=file_translated, caption="Перевод")

        await state.clear()


# юзер отправил номер страницы -> рендерить пдф и кнопки
@router.message(StateFilter(FSM.wait_page))
async def page_num(msg: Message, bot: Bot, state: FSMContext):
    user = str(msg.from_user.id)
    page = msg.text

    # если нет текста
    alert = 'Я ожидаю номер страницы'
    if not msg.text:
        await msg.answer(text=alert)
        return

    # правильность ввода
    if page.isnumeric():
        # проверить число страниц
        pdf_path = f'{users_data}/{user}_raw.pdf'
        pages = count_pdf_pages(pdf_path)
        if int(page) > pages:
            await msg.answer(text=f'Укажите число меньше. В вашем файле {pages} страниц.')
            return

        # сохранить
        set_pers_info(user=user, key='page', val=int(page) - 1)  # сохранить число на 1 меньше
        await msg.answer(text=f'Номер сохранен: {page}\n'
                              'С помощью кнопок двигайте подпись так, чтобы она стала на нужное место, '
                              'затем нажмите галочку ✅, чтобы сохранить и получить файл.')
        await state.clear()
    else:
        await msg.answer(text=alert)
        return

    # рендерить пдф
    coord = get_pers_info(user=user, key='coord')
    rendered_pdf = render_pdf_page(user)

    # отправить кнопки навигации
    await bot.send_photo(photo=rendered_pdf, chat_id=user, caption=str(coord), reply_markup=keyboards.keyboard_nav)


# юзер прислал текст для вставки -> спросить номер страницы
@router.message(StateFilter(FSM.put_text))
async def save_text(msg: Message, state: FSMContext):
    user = str(msg.from_user.id)

    # если нет текста
    alert = 'Я ожидаю текст для вставки в ПДФ'
    if not msg.text:
        await msg.answer(text=alert)
        return

    await log(logs, user, 'reading put_text')

    # сохранить
    set_pers_info(user=user, key='put_text', val=msg.text)
    await msg.answer(text='Текст для вставки сохранен. Отправьте номер страницы, на которую нужно вставить.'
                          ' (отчет начинается с 1).')

    # ожидание номера страницы
    await state.set_state(FSM.wait_page)


# нажата кнопка навигации -> рендерить пдф и кнопки
@router.callback_query(lambda x: x.data)
async def nav(callback: CallbackQuery, bot: Bot):
    # print(callback.model_dump_json(indent=4, exclude_none=True))
    data = callback.data
    msg_id = callback.message.message_id
    user = str(callback.from_user.id)
    await bot.send_chat_action(action='upload_photo', chat_id=user)
    print(f'callback {data = }')
    raw_pdf_path = f'{users_data}/{user}_raw.pdf'

    # режим - текст или подпись
    mode = get_pers_info(user, key='mode')
    coord = get_pers_info(user=user, key='coord')
    edit = False

    # сдвиг
    if 'x' in data or 'y' in data:

        axis, value = data.split('_')
        value = int(value)
        print(f'{axis, value = }')
        print(f'{coord = }')

        # координаты одной оси, обоих углов
        coord[f'{axis}0'] += value
        coord[f'{axis}1'] += value
        set_pers_info(user=user, key='coord', val=coord)
        edit = True

    # zoom
    elif 'z' in data:
        edit = True
        axis, value = data.split('_')
        value = int(value)
        font = get_pers_info(user=user, key='font')

        if mode == 'sign':
            # координаты одного угла, обоих осей
            coord['x1'] += value
            coord['y1'] += value
            set_pers_info(user=user, key='coord', val=coord)

        elif mode == 'text':
            # шрифт
            font += value // 10
            set_pers_info(user=user, key='font', val=font)

    # сохранить
    elif data in 'save':
        sign_path = put_text = None
        if mode == 'sign':
            sign_path = f'{users_data}/{user}_transp.png'
            put_text = None
        elif mode == 'text':
            sign_path = None
            put_text = get_pers_info(user, key='put_text')

        page = get_pers_info(user=user, key='page')
        font = get_pers_info(user=user, key='font')

        await bot.edit_message_caption(chat_id=user, message_id=msg_id, caption=f'✅ Сохранено\n{coord}')
        await bot.send_chat_action(action='upload_photo', chat_id=user)

        # создать пдф и отправить
        print(f'{sign_path, put_text = }')
        signed_pdf_path = f'{users_data}/{user}_{callback.from_user.first_name}-{callback.from_user.last_name}.pdf'
        process_pdf(save_path=signed_pdf_path, image_path=sign_path, put_text=put_text, xyz=coord,
                    font=font, pdf_path=raw_pdf_path, page=page)

        caption = "Ваш документ подписан" if mode == 'sign' else "Текст вставлен в документ"
        await bot.send_document(chat_id=user, document=FSInputFile(signed_pdf_path),
                                caption=caption, reply_markup=keyboards.keyboard_menu)

        # удалить файлы и данные юзера
        os.remove(signed_pdf_path)
        os.remove(raw_pdf_path)
        set_pers_info(user=user, key='put_text', val=None)
        set_pers_info(user=user, key='page', val=None)
        return

    if edit:
        rendered_pdf = render_pdf_page(user)
        await bot.edit_message_media(chat_id=user, message_id=msg_id, reply_markup=keyboards.keyboard_nav,
                                     media=InputMediaPhoto(media=rendered_pdf, caption=str(coord)), )


# команда delete > спросить номера страниц
@router.message(or_f(Command('delete'), F.text == 'Удалить страницы'))
async def delete_command(msg: Message, state: FSMContext):
    user = str(msg.from_user.id)
    await log(logs, msg.from_user.id, msg.text)

    # сохранить режим
    set_pers_info(user, key='mode', val='delete')

    text = 'Отправьте PDF, из которого нужно удалить страницы'
    await msg.answer(text=text, reply_markup=keyboards.keyboard_return)

    # ожидание пдф
    await state.set_state(FSM.wait_pdf)


# юзер указал номера страниц > удалить их и отправить пдф
@router.message(StateFilter(FSM.delete_pages))
async def delete_pages(msg: Message, bot: Bot, state: FSMContext):
    user = str(msg.from_user.id)
    await bot.send_chat_action(action='typing', chat_id=user)

    # если нет текста
    alert = 'Я ожидаю номера страниц'
    if not msg.text:
        await msg.answer(text=alert)
        return

    await log(logs, msg.from_user.id, msg.text)
    pages_to_delete = msg.text.split()

    # проверить число страниц
    pdf_path = f'{users_data}/{user}_raw.pdf'
    pages = count_pdf_pages(pdf_path)
    if pages == 1:
        await msg.answer(text=f'Удаление невозможно - в вашем файле всего 1 страница.')
        await state.clear()
        return

    # правильность ввода
    for page in pages_to_delete:
        if page.isnumeric():
            if int(page) > pages:
                await msg.answer(text=f'Укажите числа меньше. В вашем файле {pages} страниц.')
                return
            if int(page) < 1:
                await msg.answer(text=f'Укажите числа больше нуля.')
                return
        else:
            await msg.answer(text="Неверный формат. Я ожидаю номера страниц через пробел.")
            return

    # убрать дубли
    pages_to_delete = list(set(pages_to_delete))

    # уведомить о работе
    msg_to_delete = await msg.answer(text="Обрабатываю ваш файл...")
    await bot.send_chat_action(action='upload_document', chat_id=user)

    # удалить страницы, сохранить и отправить
    caption = f"Удалено {len(pages_to_delete)} страниц: {', '.join(sorted(pages_to_delete, key=lambda x: int(x)))}."
    edited_pdf_path = f'{users_data}/{user}_del.pdf'
    delete_pdf_pages(pdf_path, edited_pdf_path, pages=pages_to_delete)
    await bot.send_document(chat_id=user, document=FSInputFile(edited_pdf_path),
                            caption=caption, reply_markup=keyboards.keyboard_menu)
    await bot.delete_message(chat_id=user, message_id=msg_to_delete.message_id)

    # удалить файлы и данные юзера
    os.remove(pdf_path)
    os.remove(edited_pdf_path)
    set_pers_info(user=user, key='mode', val=None)
    await state.clear()


# юзер делает что-то не нужное
@router.message()
async def key_return(msg: Message, state: FSMContext):
    await log(logs, msg.from_user.id, msg.text)

    text = f'Выберите действие в меню 👇'
    await msg.answer(text=text, reply_markup=keyboards.keyboard_menu)
    await state.clear()

