from os import getenv
from pathlib import Path

from dotenv import load_dotenv

load_dotenv('.env')

HIDERS_CHECKER = 'hiders_checker.SchoolTaskerBotHiderChecker'

TOKEN = getenv('TOKEN', '')

ADMIN_GROUP = getenv('ADMIN_GROUP', '').split(',')

SAVE_LATEST_MESSAGE = True

DIRECTOR_ID = getenv('DIRECTOR_ID', '')

MEDIA_ROOT = Path(__file__).resolve().parent / 'media'

#
# Database Settings
#

DATABASE_NAME = getenv('DATABASE_NAME', '')

DATABASE_USER = getenv('DATABASE_USER', '')

DATABASE_PASSWORD = getenv('DATABASE_PASSWORD', '')

DATABASE_PORT = getenv('DATABASE_PORT', '')

DATABASE_HOST = getenv('DATABASE_HOST', '')

#
# Telegram Features
#

MAX_CAPTION_LENGTH = 1024

ERROR_HANDLER_CONF = {
    'IGNORE_QUERY_IS_TOO_OLD': True,
    'IGNORE_TIMED_OUT': True,
    'IGNORE_UPDATE_MASSAGE_FAIL': True,
}
