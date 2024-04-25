import os.path
from aiogram import Router, Bot, F, types
from aiogram.filters import Command, CommandStart, StateFilter, CommandObject, or_f
from bot_logic import *
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Message, URLInputFile, FSInputFile, InputMediaPhoto
from config import config
from settings import *
from cv_and_pdf import read_sign, process_pdf
import keyboards
from translate_api import valid_codes
import ocr_api


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
    x = get_pers_info(user=user_id, key='first_start')
    if x is None:
        set_pers_info(user=user_id, key='first_start', val=msg_time)
        set_pers_info(user=user_id, key='tg_fullname', val=user.full_name)
        coord = {"x0": 200, "y0": 200, "x1": 300, "y1": 300}
        set_pers_info(user=user_id, key='coord', val=coord)

    # приветствие
    await message.answer(text='Привет!\nОтправьте ваш PDF')
    # сообщить админу, кто стартанул бота
    alert = f'➕ user {contact_user(user=user)}'
    for i in admins:
        await bot.send_message(text=alert, chat_id=i, disable_notification=True, parse_mode='HTML')

    # логи
    await log(logs, user_id, f'{msg_time}, {user.full_name}, @{user.username}, id {user.id}, {user.language_code}')


# команда translate
@router.message(Command('translate'))
async def put_command(msg: Message, bot: Bot):
    user = str(msg.from_user.id)
    await log(logs, user, msg.text)
    text = ('Выберите способ извлечение текста из PDF:\n'
            '▫️ OCR - распознавание текста с помощью компьютерного зрения '
            '(выбирать, если текст расположен внутри картинки, при этом результат может быть неточный)\n'
            '▫️ TEXT - чтение текста из файла')

    await msg.answer(text=text, reply_markup=keyboards.keyboard_read)


# нажата кнопка способа чтения ПДФ > спросить языки
@router.callback_query(lambda x: x.data in ('ocr', 'text'))
async def nav(callback: CallbackQuery, bot: Bot, state: FSMContext):
    # print(callback.model_dump_json(indent=4, exclude_none=True))
    data = callback.data

    msg_id = callback.message.message_id
    user = str(callback.from_user.id)
    await log(logs, user, data)
    print(f'{data = }')
    set_pers_info(user, 'read_mode', val=data)
    text = (f'Выбран режим {data.upper()} ✅\n\n'
            f'Укажите, с какого языка на какой перевести - два кода через пробел, например:\nen ru')
    await bot.edit_message_text(text=text, reply_markup=None, message_id=msg_id, chat_id=user)

    # ожидание ввода языков
    await state.set_state(FSM.page)


# юзер указал языки
@router.message(StateFilter(FSM.page))
async def page_num(msg: Message,  state: FSMContext):
    user = str(msg.from_user.id)
    await log(logs, user, msg.text)
    lang_pair = msg.text.lower().split()
    print(f'{lang_pair = }')

    # правильность ввода
    if len(lang_pair) == 2 and lang_pair[0] in valid_codes and lang_pair[1] in valid_codes:
        await msg.answer(text=f'Запущен перевод {lang_pair[0].upper()} > {lang_pair[1].upper()}, ожидайте')
        await state.clear()

    else:
        await msg.answer(text='Я ожидаю два языковых кода через пробел, в формате:\nen ru')


# команды 'put_text', 'put_sign'
@router.message(Command('put_text', 'put_sign'))
async def put_command(msg: Message, bot: Bot):
    user = str(msg.from_user.id)
    await log(logs, user, msg.text)
    raw_pdf_path = f'{users_data}/{user}_raw.pdf'

    # задать значения
    tmp_jpg = f'{users_data}/{user}_tmp.jpg'
    coord = get_pers_info(user, 'coord')
    if coord is None:
        coord = {"x0": 200, "y0": 200, "x1": 300, "y1": 300}
        set_pers_info(user, key='coord', val=coord)
    page = get_pers_info(user=user, key='page')
    if not page:
        page = 0
    font = get_pers_info(user=user, key='font')
    if not font:
        font = 100

    # режим - текст или подпись
    mode = msg.text.split('_')[-1]
    set_pers_info(user, key='mode', val=mode)

    if mode == 'sign':
        # проверить есть ли уже фото подписи
        sign_path = f'{users_data}/{user}_transp.png'
        print(f'{sign_path = }')
        if not os.path.exists(sign_path):
            await msg.answer(text='Сначала пришлите фото подписи')
            return

        # рендер подписи в пдф
        process_pdf(image_path=sign_path, xyz=coord, pdf_path=raw_pdf_path, temp_jpg_path=tmp_jpg, font=font, page=page)

    elif mode == 'text':
        # проверить есть ли уже текст
        put_text = get_pers_info(user, 'put_text')
        print(f'{put_text = }')
        if not put_text:
            await msg.answer(text='Сначала пришлите текст для вставки')
            return

        # рендер текста в пдф
        process_pdf(put_text=put_text, xyz=coord, pdf_path=raw_pdf_path, temp_jpg_path=tmp_jpg, font=font, page=page)

    await bot.send_photo(photo=FSInputFile(tmp_jpg), chat_id=user, caption=str(coord), reply_markup=keyboards.keyboard_nav)


# юзер прислал подпись
@router.message(F.content_type.in_({'photo'}))
async def save_sign(msg: Message, bot: Bot):
    user = str(msg.from_user.id)
    await log(logs, user, 'reading sign')

    # download
    inp_path = f'{users_data}/{user}_raw.jpg'
    file_id = msg.photo[-1].file_id
    await bot.download(file=file_id, destination=inp_path)

    # обработать фото
    out_path = f'{users_data}/{user}_transp.png'
    read_sign(img_path=inp_path, out_path=out_path)

    print(f'sending {out_path}')
    await bot.send_photo(chat_id=user, photo=FSInputFile(out_path))
    await msg.answer(text='Подпись сохранена. Для создания PDF-файла с вашей подписью нажмите /put_sign. '
                          'Чтобы изменить подпись, отправьте новое фото.')


# юзер прислал свой ПДФ
@router.message(F.content_type.in_({'document'}))
async def save_pdf(msg: Message, bot: Bot, state: FSMContext):
    user = str(msg.from_user.id)
    await log(logs, user, 'saving pdf')

    doc_type = msg.document.mime_type
    print(f'{doc_type = }')

    # download
    inp_path = f'{users_data}/{user}_raw.pdf'
    file_id = msg.document.file_id
    await bot.download(file=file_id, destination=inp_path)
    await msg.answer(text='Ваш PDF сохранен. Отправьте номер страницы, на которой нужно что-либо вставить '
                          '(отчет начинается с 1).')

    # ожидание номера страницы
    await state.set_state(FSM.page)


# юзер отправил номер страницы
@router.message(StateFilter(FSM.page))
async def page_num(msg: Message,  state: FSMContext):
    user = str(msg.from_user.id)
    page = msg.text

    # правильность ввода
    if page.isnumeric():
        set_pers_info(user=user, key='page', val=int(page)-1)
        await msg.answer(text=f'Номер сохранен: {page}')
        await state.clear()
    else:
        await msg.answer(text='Я ожидаю номер страницы')


# юзер прислал текст для вставки
@router.message(F.content_type.in_({'text'}))
async def save_text(msg: Message, bot: Bot):
    user = str(msg.from_user.id)
    await log(logs, user, 'reading text')

    # сохранить
    set_pers_info(user=user, key='put_text', val=msg.text)
    await msg.answer(text='Текст для вставки сохранен. Для создания PDF-файла с вашей подписью нажмите /put_text. '
                          'Чтобы изменить текст - отправьте новый.')


# нажата кнопка навигации
@router.callback_query(lambda x: x.data)
async def nav(callback: CallbackQuery, bot: Bot):
    # print(callback.model_dump_json(indent=4, exclude_none=True))
    data = callback.data
    msg_id = callback.message.message_id
    user = str(callback.from_user.id)
    print(f'callback {user = }')
    print(f'{data = }')
    raw_pdf_path = f'{users_data}/{user}_raw.pdf'

    # прочитать БД
    coord = get_pers_info(user=user, key='coord')
    page = get_pers_info(user=user, key='page')
    if not page:
        page = 0

    font = get_pers_info(user=user, key='font')
    if not font:
        font = 30
    edit = False

    # режим - текст или подпись
    mode = get_pers_info(user, key='mode')
    sign_path = put_text = None
    if mode == 'sign':
        sign_path = f'{users_data}/{user}_transp.png'
        put_text = None
    elif mode == 'text':
        sign_path = None
        put_text = get_pers_info(user, key='put_text')

    # сдвиг
    if 'x' in data or 'y' in data:
        axis, value = data.split('_')
        value = int(value)
        print(f'{axis = }, {value = }')
        print(f'{coord = }')

        # координаты одной оси, обоих углов
        coord[f'{axis}0'] += value
        coord[f'{axis}1'] += value
        edit = True

    # zoom
    elif 'z' in data:
        edit = True
        axis, value = data.split('_')
        value = int(value)

        if mode == 'sign':
            # координаты одного угла, обоих осей
            coord['x1'] += value
            coord['y1'] += value

        elif mode == 'text':
            # шрифт
            font += value // 10
            set_pers_info(user=user, key='font', val=font)

    # сохранить
    elif data in 'save':
        await bot.edit_message_caption(chat_id=user, message_id=msg_id, caption=f'✅ Сохранено\n{coord}')

        # создать пдф и отправить
        signed_pdf_path = f'{users_data}/{user}_{callback.from_user.first_name}-{callback.from_user.last_name}.pdf'
        process_pdf(save_path=signed_pdf_path, image_path=sign_path, put_text=put_text, xyz=coord, font=font, pdf_path=raw_pdf_path, page=page)
        await bot.send_document(chat_id=user, document=FSInputFile(signed_pdf_path), caption="Ваш документ подписан")
        return

    if edit:
        set_pers_info(user=user, key='coord', val=coord)

        tmp_jpg = f'{users_data}/{user}_tmp.jpg'
        process_pdf(image_path=sign_path, put_text=put_text, xyz=coord, temp_jpg_path=tmp_jpg, font=font, pdf_path=raw_pdf_path, page=page)
        await bot.edit_message_media(chat_id=user, message_id=msg_id, reply_markup=keyboards.keyboard_nav,
                                     media=InputMediaPhoto(media=FSInputFile(tmp_jpg), caption=str(coord)), )