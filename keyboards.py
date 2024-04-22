from aiogram.types import InlineKeyboardButton as Button, InlineKeyboardMarkup

# шаги 
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
plus = Button(text='➕', callback_data=f'z_+{zoom}')   # масштаб
minus = Button(text='➖', callback_data=f'z_-{zoom}')  # масштаб
plus2 = Button(text='➕➕', callback_data=f'z_+{zoom*3}')   # масштаб
minus2 = Button(text='➖➖', callback_data=f'z_-{zoom*3}')  # масштаб

# клавиатура из таких кнопок
kb_list = [
    [plus2, null, nav_up100, null, minus2],
    [plus, null, nav_up5, null, minus],
    [nav_left100, nav_left5, save_button, nav_right5, nav_right100],
    [null, null, nav_down5, null, null],
    [null, null, nav_down100, null, null],
]
keyboard_nav = InlineKeyboardMarkup(inline_keyboard=kb_list)
