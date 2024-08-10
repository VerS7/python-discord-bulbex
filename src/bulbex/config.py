"""
Конфиги
"""
from os import path, getenv
from distutils.util import strtobool

import dotenv

try:
    dotenv.load_dotenv(path.join(path.dirname(path.dirname(__file__)), ".env"))
except FileNotFoundError:
    pass

# Bot API
TOKEN = getenv("TOKEN")
GUILD_ID = int(getenv("GUILD_ID"))  # ID личной гильдии для дебага
TRUSTED_IDS = [int(user_id) for user_id in getenv("TRUSTED_IDS").split(",")]
ON_READY_GUILD_SYNC = strtobool(getenv("ON_READY_GUILD_SYNC"))

# FFMPEG
FFMPEG = getenv("FFMPEG")  # ffmpeg alias или абсолютный путь
BITRATE = getenv("BITRATE")

# Доступ к ВКонтакте
VK_LOGIN = getenv("VK_LOGIN")
VK_PASSWORD = getenv("VK_PASSWORD")
# Обход запроса на доступ если access_token уже есть
VK_BYPASS_AUTH = strtobool(getenv("VK_BYPASS_AUTH"))
VK_BYPASS_ACCESS_TOKEN = getenv("VK_BYPASS_ACCESS_TOKEN")

# Логгер
LOGGER_FILE_PATH = getenv("LOGGER_FILEPATH")
LOGGER_ROTATION = getenv("LOGGER_ROTATION")