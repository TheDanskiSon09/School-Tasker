from dotenv import load_dotenv
from pathlib import Path
from os import getenv
load_dotenv(".env")
HIDERS_CHECKER = 'hiders_checker.SchoolTaskerBotHiderChecker'
TOKEN = getenv("TOKEN", "")
ADMIN_GROUP = getenv("ADMIN_GROUP", "").split(",")
DIRECTOR_ID = getenv("DIRECTOR_ID", "")
DATABASE_NAME = getenv('DATABASE_NAME', '')
DATABASE_USER = getenv('DATABASE_USER', '')
DATABASE_PASSWORD = getenv('DATABASE_PASSWORD', '')
DATABASE_PORT = getenv('DATABASE_PORT', '')
DATABASE_HOST = getenv('DATABASE_HOST', '')
SAVE_LATEST_MESSAGE = True
MAX_CAPTION_LENGTH = 1024
MEDIA_ROOT = Path(__file__).resolve().parent / 'media'
