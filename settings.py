from dotenv import load_dotenv
import os
load_dotenv(".env")
HIDERS_CHECKER = 'hiders_checker.SchoolTaskerBotHiderChecker'
TOKEN = os.getenv("TOKEN", "")
ADMIN_GROUP = os.getenv("ADMIN_GROUP", "").split(",")
DIRECTOR_ID = os.getenv("DIRECTOR_ID", "")
SAVE_LATEST_MESSAGE = True
BOT_NAME = "SchoolTaskerbot"
