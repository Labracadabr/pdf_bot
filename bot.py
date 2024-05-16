import asyncio
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher
from handlers import handler_user
from config import config
from aiogram.types import BotCommand
from settings import commands


async def main():
    # Инициализация бота
    storage: MemoryStorage = MemoryStorage()
    bot: Bot = Bot(token=config.BOT_TOKEN)
    dp: Dispatcher = Dispatcher(storage=storage)
    await on_start(bot=bot)

    # Регистрируем роутеры в диспетчере
    dp.include_router(handler_user.router)

    # Пропускаем накопившиеся апдейты и запускаем polling
    await bot.delete_webhook(drop_pending_updates=False)  # False > бот ответит на апдейты, присланные за время откл
    await dp.start_polling(bot)


# создать команды в меню
async def on_start(bot: Bot) -> None:
    await bot.set_my_commands([BotCommand(command=item[0], description=item[1]) for item in commands.items()])
    print('Команды созданы')

    # ссылка на бота
    bot_info = await bot.get_me()
    bot_link = f"https://t.me/{bot_info.username}"
    print(f'{bot_link = }')


if __name__ == '__main__':
    asyncio.run(main())
