import os


# Список id админов
dima = "992863889"
admins: list[str] = [dima]

# где хранятся данные
logs = 'logs.tsv'
users_data = 'users_data'  # папка с json-ами

# tg канал для логов
log_channel_id = ''
# log_channel_id = '-1002105757977'

# команды бота
commands = {
    "/start": "Запуск бота",
    "/put_text": "Разместить текст",
    "/put_sign": "Разместить подпись",
    "/pdf": "Получить PDF",
}

# проверить все ли на месте
def check_files():
    file_list = [logs, ]
    for file in file_list:
        if not os.path.isfile(file):
            if file.endswith('json'):
                with open(file, 'w', encoding='utf-8') as f:
                    print('Отсутствующий файл создан:', file)
                    print('{}', file=f)
            elif file.endswith('sv'):
                with open(file, 'w', encoding='utf-8') as f:
                    print('Отсутствующий файл создан:', file)
                    print('\t'.join(('Time', 'User', 'Action')), file=f)


check_files()
print('OK')
