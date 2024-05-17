import os


# Список id админов
dima = "992863889"
admins: list[str] = [dima]

# где хранятся данные
logs = 'logs.tsv'  # тсв с логами
users_data = 'users_data'  # папка с данными юзеров

# команды бота
commands = {
    "/start": "Запуск бота",
    "/put_text": "Разместить текст",
    "/put_sign": "Разместить подпись",
    "/translate": "Перевести текст из PDF",
    "/delete": "Удалить страницы",
}

# проверить все ли на месте
def check_files():
    os.makedirs(users_data, exist_ok=True)

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
