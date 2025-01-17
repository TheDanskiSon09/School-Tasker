from dotenv import load_dotenv
from pathlib import Path
from os import getenv
load_dotenv(".env")
HIDERS_CHECKER = 'hiders_checker.SchoolTaskerBotHiderChecker'
TOKEN = getenv("TOKEN", "")
ADMIN_GROUP = getenv("ADMIN_GROUP", "").split(",")
DIRECTOR_ID = getenv("DIRECTOR_ID", "")
SAVE_LATEST_MESSAGE = True
MEDIA_ROOT = Path(__file__).resolve().parent / 'media'
