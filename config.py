from dataclasses import dataclass
from environs import Env
# from settings import prod


@dataclass
class Config:
    BOT_TOKEN: str = None           # телеграм бот
    SOME_MORE_TOKEN: str = None     # токен от еще чего-нибудь

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
    # SOME_MORE_TOKEN=env(''),

    host=env('host'),
    dbname=env('dbname'),
    user=env('user'),
    password=env('password'),
    port=env.int('port')
)

