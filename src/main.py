"""
Точка входа бота
"""
import discord
from discord.ext import commands

from loguru import logger

from bulbex.maincog import MusicCog
from bulbex.debugcog import DebugCog
from bulbex.config import TOKEN, ON_READY_GUILD_SYNC, LOGGER_FILE_PATH, LOGGER_ROTATION

# Доступы
intents = discord.Intents.default()

# Бот
bot = commands.Bot(command_prefix="/", intents=intents, case_insensitive=False)

# Логгера
logger.add(LOGGER_FILE_PATH, rotation=LOGGER_ROTATION)


@bot.event
async def on_ready():
    """Ивент на запуске бота"""
    await bot.change_presence(status=discord.Status.online,
                              activity=discord.Activity(type=discord.ActivityType.listening, name="muzzlo"))

    if ON_READY_GUILD_SYNC:
        logger.info("Сихронизация гильдий...")
        await bot.sync_commands(guild_ids=[guild.id for guild in bot.guilds])

    logger.info("Бот запущен!")


def start():
    """Запуск бота"""
    bot.add_cog(MusicCog(bot))
    bot.add_cog(DebugCog(bot))
    bot.run(token=TOKEN)


if __name__ == '__main__':
    try:
        logger.info("Приложение запущено.")
        start()
    except KeyboardInterrupt:
        logger.info("Выход из приложения.")
