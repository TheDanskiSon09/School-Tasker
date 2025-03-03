from calendar import monthrange
from datetime import date
from secrets import token_urlsafe
from logging import getLogger
from random import choice
from hammett.core.exceptions import PayloadIsEmpty
from sqlite3 import connect
from time import gmtime, strftime
from json import loads
from constants import *

connection = connect('school_tasker_database.db')
cursor = connection.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS SchoolTasker (
item_name TEXT,
item_index INTEGER,
group_number INTEGER,
task_description TEXT,
task_day INT,
task_month INT,
task_year INT,
hypertime INT
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS Users (
user_permission TEXT,
user_id INT PRIMARY KEY,
user_name TEXT
)
''')
LOGGER = getLogger('hammett')


# def media_handler(func):
#     async def wrapper(self, update, context, *args, **kwargs):
#         message = update.message
#         if message.photo:
#             file = message.photo[-1]
#             file_id = file.file_id
#             file = await context.bot.get_file(file_id)
#             await file.download('image.jpg')
#             await update.message.reply_text("GOT IMAGE!")
#         elif message.video:
#             file_id = message.video.file_id
#             file = await context.bot.get_file(file_id)
#             await file.download('video.mp4')
#             await update.message.reply_text("GOT VIDEO!")
#
#         elif message.audio:
#             file_id = message.audio.file_id
#             file = await context.bot.get_file(file_id)
#             await file.download('audio.mp3')
#             await update.message.reply_text("GOT AUDIO!")
#         else:
#             await update.message.reply_text("UNSUPORRTED FILE!")
#         return await func(self, update, context, *args, **kwargs)
#     return wrapper


class Global:
    last_day = int()
    last_month = int()
    last_year = int()
    index_store = int(0)
    open_date = True
    is_changing_task_description = False
    is_changing_day = False
    is_changing_month = False
    is_changing_group_number = False


async def get_week_day(task_year, task_month_int: int, task_day: int):
    week_day = date(int(task_year), task_month_int, task_day)
    week_day_new = WEEK_DAYS[week_day.weekday()]
    return str(week_day_new)


async def get_day_time(name):
    if datetime.now().hour < 4:
        greet = choice(["🌕", "🌙"])
        greet += "Доброй ночи, "
    elif 4 <= datetime.now().hour < 12:
        greet = choice(["🌅", "🌄"])
        greet += "Доброе утро, "
    elif 12 <= datetime.now().hour < 17:
        greet = choice(["🌞", "☀️"])
        greet += "Добрый день, "
    elif 17 <= datetime.now().hour < 23:
        greet = choice(["🌅", "🌄"])
        greet += "Добрый вечер, "
    else:
        greet = choice(["🌕", "🌙"])
        greet += "Доброй ночи, "
    greet += name + "!"
    return greet


async def get_clean_var(var, new_var_type: str, index: int, need_clear: bool):
    var = str(var[index])
    if new_var_type == "to_string":
        if need_clear:
            if var[0] == "(":
                var = var[1: -1]
            if var[-1] == ',':
                var = var[0: -1]
            if var[0] == "'":
                var = var[1: -1]
        return str(var)
    if new_var_type == "to_int":
        if var[0] == "(":
            var = var[1: -1]
        if var[-1] == ',':
            var = var[0: -1]
        return int(var)


async def recognise_month(month):
    month_dict = {"1": "января",
                  "2": "февраля",
                  "3": "марта",
                  "4": "апреля",
                  "5": "мая",
                  "6": "июня",
                  "7": "июля",
                  "8": "августа",
                  "9": "сентября",
                  "10": "октября",
                  "11": "ноября",
                  "12": "декабря",
                  }
    month = month_dict[str(month)]
    return month


async def recognise_n_tag(text: str):
    if r"\n" in text:
        text = text.replace(r"\n", "\n")
    return text


async def check_task_validity(day: int, month: int, year: int):
    if str(year) > str(datetime.now().year):
        return True
    elif str(year) == str(datetime.now().year):
        if str(month) > str(datetime.now().month):
            return True
        elif int(month) == int(datetime.now().month):
            if int(day) > int(datetime.now().day):
                return True
            else:
                return False
        else:
            return False
    else:
        return False


async def update_day(check_month, task_day):
    if task_day <= int(monthrange(int(strftime("%Y", gmtime())), int(check_month))[1]):
        return task_day
    else:
        return False


async def get_user_month(month):
    months_dict = {
        1: ["Январь", "Января", "январь", "января"],
        2: ["Февраль", "Февраля", "февраль", "февраля"],
        3: ["Март", "Марта", "март", "марта"],
        4: ["Апрель", "Апреля", "апрель", "апреля"],
        5: ["Май", "Мая", "май", "мая"],
        6: ["Июнь", "Июня", "июнь", "июня"],
        7: ["Июль", "Июля", "июль", "июля"],
        8: ["Август", "Августа", "август", "августа"],
        9: ["Сентябрь", "Сентября", "сентябрь", "сентября"],
        10: ["Октябрь", "Октября", "октябрь", "октября"],
        11: ["Ноябрь", "Ноября", "ноябрь", "ноября"],
        12: ["Декабрь", "Декабря", "декабрь", "декабря"],
    }
    for i in months_dict:
        month_list = months_dict[i]
        for a in month_list:
            if a == month:
                new_month = i
                return new_month


async def update_month(check_day, task_month):
    check_month = await get_user_month(task_month)
    if check_day <= int(monthrange(int(strftime("%Y", gmtime())), check_month)[1]):
        return check_month
    else:
        return False


async def get_hypertime(month: int, day: int, year: int):
    if int(month) < 10:
        hypertime = str(year) + "0" + str(month)
    else:
        hypertime = str(year) + str(month)
    if day < 10:
        hypertime += "0"
    hypertime += str(day)
    return str(hypertime)


async def get_var_from_database(index, need_variable, order: bool):
    global cursor
    if order:
        variable_order = {"item_name": "SELECT item_name FROM SchoolTasker ORDER BY hypertime ASC",
                          "group_number": "SELECT group_number FROM SchoolTasker ORDER BY hypertime ASC",
                          "task_description": "SELECT task_description FROM SchoolTasker ORDER BY hypertime ASC",
                          "task_day": "SELECT task_day FROM SchoolTasker ORDER BY hypertime ASC",
                          "task_month": "SELECT task_month FROM SchoolTasker ORDER BY hypertime ASC",
                          "item_index": "SELECT item_index FROM SchoolTasker ORDER BY hypertime ASC",
                          "database_length_SchoolTasker": "SELECT count(*) FROM SchoolTasker",
                          "database_length_Users": "SELECT count(*) FROM SchoolTasker",
                          "task_year": "SELECT task_year FROM SchoolTasker ORDER BY hypertime ASC"}
        title = variable_order[need_variable]
        cursor.execute(title)
        variable = cursor.fetchall()
        if need_variable == "database_length_SchoolTasker" or need_variable == "database_length_Users":
            variable = await get_clean_var(variable, "to_int", False, True)
            return int(variable)
        else:
            variable = await get_clean_var(variable, "to_string", index, True)
            return str(variable)
    else:
        variable_select = {"item_name": "SELECT item_name FROM SchoolTasker WHERE item_index = ?",
                           "group_number": "SELECT group_number FROM SchoolTasker WHERE item_index = ?",
                           "task_description": "SELECT task_description FROM SchoolTasker WHERE item_index = ?",
                           "task_day": "SELECT task_day FROM SchoolTasker WHERE item_index = ?",
                           "task_month": "SELECT task_month FROM SchoolTasker WHERE item_index = ?",
                           "task_year": "SELECT task_year FROM SchoolTasker WHERE item_index = ?"
                           }
        title = variable_select[need_variable]
        cursor.execute(title, (index,))
        variable = cursor.fetchone()
        if need_variable == "item_name":
            variable = await get_clean_var(variable, "to_string", False, True)
            return str(variable)
        elif need_variable == "task_description":
            variable = await get_clean_var(variable, "to_string", False, False)
            return str(variable)
        else:
            variable = await get_clean_var(variable, "to_int", False, True)
            return int(variable)


async def logger_alert(user: list, status: str, formattered_index, is_order: bool):
    global cursor
    item_name = await get_var_from_database(formattered_index, "item_name", is_order)
    task_description = await get_var_from_database(formattered_index, "task_description", is_order)
    group_number = await get_var_from_database(formattered_index, "group_number", is_order)
    task_day = await get_var_from_database(formattered_index, "task_day", is_order)
    task_month = await get_var_from_database(formattered_index, "task_month", is_order)
    status_dict = {"add": "added",
                   "delete": "deleted",
                   "change": "changed"}
    title = "The "
    if len(user) < 1:
        title += "SchoolTasker has "
    else:
        title += "user " + str(user[0]) + " (" + str(user[1]) + ")" + " has "
    status = status_dict[status]
    status += " task"
    title += status
    title += ": На " + str(task_day) + "." + str(task_month) + " по " + str(item_name)
    if item_name == "Английский язык" or item_name == "Информатика":
        title += "(" + str(group_number) + "ая группа)"
    title += ": " + str(task_description)
    LOGGER.info(title)


async def once_delete_task(school_tasks_screen):
    await logger_alert([], "delete", 0, False)
    cursor.execute("DELETE FROM SchoolTasker WHERE item_index = ?", (0,))
    connection.commit()
    school_tasks_screen.description = "<strong>На данный момент список заданий пуст!</strong>"


async def get_multipy_async(index, title):
    Global.index_store = await get_var_from_database(None, "database_length_SchoolTasker", True)
    task_day = await get_var_from_database(index, "task_day", True)
    check_day = int(task_day)
    task_month = await get_var_from_database(index, "task_month", True)
    check_month = int(task_month)
    task_year = await get_var_from_database(index, "task_year", True)
    check_year = int(task_year)
    task_month_int = int(task_month)
    task_month = await recognise_month(task_month)
    if Global.last_day == task_day and Global.last_month == task_month and Global.last_year == task_year:
        if Global.open_date:
            week_day = await get_week_day(task_year, task_month_int, int(task_day))
            if int(task_year) == datetime.now().year:
                task_time = ("<strong>На " + "<em>" + week_day + ", " + str(task_day) + " " + str(
                    task_month) + "</em>"
                             + " :</strong>" + "\n\n")
            else:
                task_time = ("<strong>На " + "<em>" + week_day + ", " + str(task_day) + " " + str(
                    task_month) + " " + str(task_year) + "го года" + "</em>"
                             + " :</strong>" + "\n\n")
        else:
            task_time = ""
    else:
        week_day = await get_week_day(task_year, task_month_int, int(task_day))
        if int(task_year) == datetime.now().year:
            task_time = ("<strong>На " + "<em>" + week_day + ", " + str(task_day) + " " + str(
                task_month) + "</em>"
                         + " :</strong>" + "\n\n")
        else:
            task_time = ("<strong>На " + "<em>" + week_day + ", " + str(task_day) + " " + str(
                task_month) + " " + str(task_year) + "го года" + "</em>"
                         + " :</strong>" + "\n\n")
    Global.last_day = task_day
    Global.last_month = task_month
    Global.last_year = task_year
    item_name = await get_var_from_database(index, "item_name", True)
    a = "<strong>"
    b = item_name
    emoji = str(ITEM_EMOJI[b])
    item_name = str(a) + str(emoji) + str(b)
    if item_name == "<strong>🇬🇧󠁧󠁢󠁧󠁢Английский язык" or item_name == "<strong>💻Информатика":
        item_name += " ("
        group_number = await get_var_from_database(index, "group_number", True)
        item_name += str(group_number)
        item_name += "ая группа)"
    item_name += " : </strong>"
    task_description = await get_var_from_database(index, "task_description", True)
    task_description = await recognise_n_tag(task_description)
    a = "<strong>"
    b = task_description
    c = "</strong>\n\n"
    task_description = str(a) + str(b) + str(c)
    current_title = task_time + item_name + task_description
    title += current_title
    return title, current_title, check_day, check_month, check_year


async def get_button_title(index):
    item_name = await get_var_from_database(index, "item_name", True)
    emoji = ITEM_EMOJI[item_name]
    item_name = str(emoji) + str(item_name)
    if item_name == "🇬🇧󠁧󠁢󠁧󠁢Английский язык" or item_name == "💻Информатика":
        group_number = await get_var_from_database(index, "group_number", True)
        item_name += " (" + str(group_number) + "ая группа) "
    task_description = await get_var_from_database(index, "task_description", True)
    task_description = await recognise_n_tag(task_description)
    title = item_name
    title += " : "
    title += task_description
    return title


async def get_notification_title(task_item, task_description, group_number, task_day, task_month_int, task_month,
                                 task_year, stat):
    status_dict = {"change": "изменено",
                   "add": "добавлено"}
    week_day = await get_week_day(task_year, task_month_int, int(task_day))
    title = "На " + "<em>" + week_day + ", " + str(task_day)
    if str(task_year) == str(datetime.now().year):
        add_month_txt = " " + str(task_month) + "</em>"
    else:
        add_month_txt = " " + str(task_month) + " " + str(task_year) + "го года" + "</em>"
    title += str(add_month_txt)
    status = status_dict[stat]
    title += " было " + status + " задание по "
    add_task_txt = ITEM_DICT[task_item]
    title += add_task_txt
    if add_task_txt == "🇬🇧󠁧󠁢󠁧󠁢Английскому языку" or add_task_txt == "💻Информатике":
        group_txt = " (" + str(group_number) + "ая " + "группа) "
        title += group_txt
    title += ": " + task_description + "</strong>"
    return title


async def main_get_payload(self, update, context, key_id: str, value: str):
    try:
        payload = loads(await self.get_payload(update, context))
    except PayloadIsEmpty:
        payload = context.user_data.get(key_id)
    else:
        context.user_data[key_id] = payload
    context.user_data[value] = payload[value]


async def check_task_status(context):
    check_db = str(context.user_data['db_check'])
    cursor.execute('SELECT * FROM SchoolTasker')
    real_db = cursor.fetchall()
    real_db = await get_clean_var(real_db, "to_string", False, True)
    if check_db != real_db:
        return False
    else:
        return True


async def is_informative_username(username):
    username = username.strip()
    if (not username or len(set(username)) == 1 or all(c in ' .-_/*!@#$%^:&()+=`~' for c in username) or len(username) <
            3):
        return False
    else:
        return True


async def get_username(first_name, last_name, username):
    data = [first_name, last_name, username]
    for check in data:
        if check and await is_informative_username(check):
            return check.strip()
    return "дорогой пользователь"


async def generate_id():
    new_id = token_urlsafe(15)
    return new_id
