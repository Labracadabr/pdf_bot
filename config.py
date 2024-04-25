from dataclasses import dataclass
from environs import Env
# from settings import prod


@dataclass
class Config:
    BOT_TOKEN: str = None           # телеграм бот
    translate_token: str = None
    ocr_token: str = None

    host: str = None                # хост
    dbname: str = None              # имя базы данных
    user: str = None                # пользователь
    password: str = None            # пароль
    port: int = None                # порт


# загрузить конфиг из переменных окружения
env = Env()
env.read_env()
config = Config(
    BOT_TOKEN=env('BOT_TOKEN_PROD'),
    translate_token=env('translate_token'),
    ocr_token=env('ocr_token'),
)

