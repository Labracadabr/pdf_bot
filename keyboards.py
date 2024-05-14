from aiogram.types import InlineKeyboardButton as Button, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

# кнопки меню
button_sign = KeyboardButton(text='Вставить подпись')
button_text = KeyboardButton(text='Вставить текст')
button_tran = KeyboardButton(text='Перевод')
button_read = KeyboardButton(text='Извлечь текст')

# кнопки способа чтения пдф
read_ocr = Button(text='OCR', callback_data=f'ocr')
read_txt = Button(text='Text', callback_data=f'text')

# шаги сдвига и зума
small, big, zoom = 20, 200, 30

# кнопки навигации
nav_right5 = Button(text='➡️', callback_data=f'x_+{small}')
nav_right100 = Button(text='➡️➡️', callback_data=f'x_+{big}')
nav_left5 = Button(text='⬅️', callback_data=f'x_-{small}')
nav_left100 = Button(text='⬅️⬅️', callback_data=f'x_-{big}')
nav_up5 = Button(text='⬆️', callback_data=f'y_-{small}')
nav_up100 = Button(text='⬆️⬆️', callback_data=f'y_-{big}')
nav_down5 = Button(text='⬇️', callback_data=f'y_+{small}')
nav_down100 = Button(text='⬇️⬇️', callback_data=f'y_+{big}')

# прочие кнопки
save_button = Button(text='✅', callback_data='save')
null = Button(text=' ', callback_data='0')
plus = Button(text='➕', callback_data=f'z_+{zoom}')  # масштаб
minus = Button(text='➖', callback_data=f'z_-{zoom}')  # масштаб
plus2 = Button(text='➕➕', callback_data=f'z_+{zoom * 3}')  # масштаб
minus2 = Button(text='➖➖', callback_data=f'z_-{zoom * 3}')  # масштаб

# списки из кнопок
read_kb_list = [[read_ocr, read_txt]]
nav_kb_list = [
    [plus2, null, nav_up100, null, minus2],
    [plus, null, nav_up5, null, minus],
    [nav_left100, nav_left5, save_button, nav_right5, nav_right100],
    [null, null, nav_down5, null, null],
    [null, null, nav_down100, null, null],
]
menu_kb_list = [[button_sign, button_text, ],
                [button_tran, button_read, ]]

# клавиатуры из кнопок
keyboard_read = InlineKeyboardMarkup(inline_keyboard=read_kb_list)
keyboard_nav = InlineKeyboardMarkup(inline_keyboard=nav_kb_list)
keyboard_menu = ReplyKeyboardMarkup(keyboard=menu_kb_list, resize_keyboard=True)
