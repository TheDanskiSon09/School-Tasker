from dotenv import dotenv_values
config = dotenv_values(".env")
PREPARE_ADMIN_GROUP = config["ADMIN_GROUP"].split(",")
PREPARE_ADMIN_GROUP = list(PREPARE_ADMIN_GROUP)
ADMIN_GROUP = []
for a in PREPARE_ADMIN_GROUP:
    ADMIN_GROUP.append(int(a))
DIRECTOR_ID = int(config["DIRECTOR_ID"])
HIDERS_CHECKER = 'hiders_checker.HiderChecker'
SAVE_LATEST_MESSAGE = True
TOKEN = config['TOKEN']
